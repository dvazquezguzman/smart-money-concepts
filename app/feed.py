from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Protocol

import pandas as pd
from sqlmodel import Session

from app.db import Candle
from app.events import EventBus

log = logging.getLogger(__name__)


class _ExchangeLike(Protocol):
    async def fetch_ohlcv(self, symbol: str, timeframe: str,
                          since: int | None = None,
                          limit: int | None = None): ...
    async def close(self) -> None: ...


class MarketFeed:
    """Polls a CCXT exchange and broadcasts new closed candles."""

    def __init__(self, exchange: _ExchangeLike, symbol: str, timeframe: str,
                 poll_interval_seconds: float, engine: Optional[object],
                 bus: EventBus, max_in_memory: int = 5000) -> None:
        self._ex = exchange
        self.symbol = symbol
        self.timeframe = timeframe
        self._poll = poll_interval_seconds
        self._engine = engine
        self._bus = bus
        self._max = max_in_memory
        self._df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        self._stopped = asyncio.Event()
        self._last_ts_ms: int = 0

    def stop(self) -> None:
        self._stopped.set()

    def dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    async def run(self) -> None:
        while not self._stopped.is_set():
            try:
                rows = await self._ex.fetch_ohlcv(self.symbol, self.timeframe)
            except Exception as e:  # noqa: BLE001 — feed must not die
                log.warning("fetch_ohlcv failed: %s", e)
                rows = []
            for row in rows:
                ts_ms, o, h, l, c, v = row
                if ts_ms <= self._last_ts_ms:
                    continue
                self._last_ts_ms = ts_ms
                ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                self._df.loc[ts] = [o, h, l, c, v]
                if len(self._df) > self._max:
                    self._df = self._df.iloc[-self._max:]
                if self._engine is not None:
                    with Session(self._engine) as s:
                        s.add(Candle(symbol=self.symbol, timeframe=self.timeframe,
                                     ts=ts, open=o, high=h, low=l, close=c, volume=v))
                        s.commit()
                await self._bus.publish("candle", {
                    "symbol": self.symbol, "timeframe": self.timeframe,
                    "ts": ts.isoformat(),
                    "open": o, "high": h, "low": l, "close": c, "volume": v,
                })
            try:
                await asyncio.wait_for(self._stopped.wait(),
                                       timeout=self._poll)
            except asyncio.TimeoutError:
                pass
        await self._ex.close()
