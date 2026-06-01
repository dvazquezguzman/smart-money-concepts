import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from ..db.base import Candle
from ..db.base import BaseCandleRepository
from .candle_aggregator import aggregate_candles, TIMEFRAME_MINUTES

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000
ONE_YEAR_1M = 365 * 24 * 60


class CCXTDataEngine:
    def __init__(
        self,
        exchange_id: str,
        symbols: list[str],
        repo: BaseCandleRepository,
        config: Optional[dict] = None,
        on_candle: Optional[Callable] = None,
    ):
        self.exchange_id = exchange_id
        self.symbols = symbols
        self.repo = repo
        self.config = config or {}
        self.on_candle = on_candle
        self._exchange = None
        self._running = False

    async def start(self):
        import ccxt.async_support as ccxt

        exchange_class = getattr(ccxt, self.exchange_id)
        self._exchange = exchange_class({**self.config, "enableRateLimit": True})
        try:
            await self._exchange.load_markets()
        except Exception as e:
            logger.warning(f"Market load error (non-fatal): {e}")
        self._running = True

        logger.info(f"Data engine started: {self.exchange_id} for {self.symbols}")

        for symbol in self.symbols:
            self.repo.create_tables_for_symbol(symbol)
            await self._sync_symbol(symbol)

        asyncio.create_task(self._poll_loop())

    async def stop(self):
        self._running = False
        if self._exchange:
            await self._exchange.close()

    async def _sync_symbol(self, symbol: str):
        last = self.repo.get_last_candle(symbol, "1m")
        if last is None:
            since_ms = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)
            limit = ONE_YEAR_1M
            logger.info(f"No local data for {symbol}, fetching 1 year...")
        else:
            since_ms = int(last.timestamp.timestamp() * 1000) + 60000
            now_ms = int(datetime.now().timestamp() * 1000)
            missing_ms = now_ms - since_ms
            limit = min(ONE_YEAR_1M, max(1000, missing_ms // 60000 + 1000))
            logger.info(
                f"Local data for {symbol} up to {last.timestamp}, "
                f"fetching ~{limit} missing candles..."
            )

        raw = await self._fetch_range(symbol, since_ms, limit)
        if not raw:
            return

        candles = [
            Candle(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(ts / 1000),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
                timeframe="1m",
            )
            for ts, o, h, l, c, v in raw
        ]
        self.repo.save_candles(candles)

        for tf in TIMEFRAME_MINUTES:
            if tf == "1m":
                continue
            agg = aggregate_candles(candles, tf)
            if agg:
                self.repo.save_candles(agg)

        logger.info(
            f"Stored {len(candles)} 1m candles for {symbol}, "
            f"pre-aggregated all higher timeframes"
        )

    async def _fetch_range(self, symbol: str, since_ms: int, limit: int) -> list[list]:
        all_raw: list[list] = []
        while len(all_raw) < limit:
            remaining = min(BATCH_SIZE, limit - len(all_raw))
            try:
                batch = await self._exchange.fetch_ohlcv(
                    symbol, "1m", since=since_ms, limit=remaining
                )
            except Exception as e:
                logger.warning(f"Fetch error for {symbol}: {e}")
                break
            if not batch:
                break
            all_raw.extend(batch)
            since_ms = batch[-1][0] + 60000
            if len(batch) < remaining:
                break
        return all_raw[:limit]

    async def _aggregate_new(self, symbol: str):
        for tf in TIMEFRAME_MINUTES:
            if tf == "1m":
                continue
            last_agg = self.repo.get_last_candle(symbol, tf)
            since = last_agg.timestamp if last_agg else None
            one_min = self.repo.get_candles(symbol, "1m", limit=5000, since=since)
            if len(one_min) < 2:
                continue
            agg = aggregate_candles(one_min, tf)
            if agg:
                self.repo.save_candles(agg)

    async def _poll_loop(self):
        while self._running:
            try:
                for symbol in self.symbols:
                    raw = await self._exchange.fetch_ohlcv(symbol, "1m", limit=2)
                    if len(raw) >= 2:
                        ts, o, h, l, c, v = raw[-2]
                        candle = Candle(
                            symbol=symbol,
                            timestamp=datetime.fromtimestamp(ts / 1000),
                            open=o,
                            high=h,
                            low=l,
                            close=c,
                            volume=v,
                            timeframe="1m",
                        )
                        last = self.repo.get_last_candle(symbol, "1m")
                        if last is None or candle.timestamp > last.timestamp:
                            self.repo.save_candles([candle])
                            await self._aggregate_new(symbol)
                            if self.on_candle:
                                self.on_candle(candle)
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Poll error: {e}")
                await asyncio.sleep(10)

    async def ensure_symbol(self, symbol: str):
        if symbol not in self.symbols:
            self.repo.create_tables_for_symbol(symbol)
            self.symbols.append(symbol)
            await self._sync_symbol(symbol)
            logger.info(f"Added symbol to tracking: {symbol}")
