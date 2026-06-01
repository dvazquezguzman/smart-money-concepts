import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..db.base import BaseTradeRepository
from ..engine.indicators import IndicatorService
from ..strategy.evaluator import StrategyEvaluator
from ..strategy.models import Strategy, Trade
from .exchange.base import Exchange
from .paper import PaperTradingEngine, SLIPPAGE_PCT
from .risk import RiskManager

logger = logging.getLogger(__name__)


class LiveTradingEngine:
    def __init__(
        self,
        exchange: Exchange,
        trade_repo: BaseTradeRepository,
        indicator_service: IndicatorService,
        initial_balance: float = 10000.0,
    ):
        self.exchange = exchange
        self.trade_repo = trade_repo
        self.indicators = indicator_service
        self.evaluator = StrategyEvaluator()
        self.risk = RiskManager(initial_balance)
        self._running = False
        self._strategy: Optional[Strategy] = None
        self._positions: dict[str, dict] = {}
        self._kill_switch = False
        self._poll_task: Optional[asyncio.Task] = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def connected(self) -> bool:
        return self.exchange.connected

    async def start(self, strategy: Strategy):
        if not self.exchange.connected:
            ok = await self.exchange.connect()
            if not ok:
                raise RuntimeError("Failed to connect to exchange")
        self._strategy = strategy
        self._running = True
        self._kill_switch = False
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Live trading started for %s", strategy.name)

    async def stop(self):
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        logger.info("Live trading stopped")

    async def kill(self):
        self._kill_switch = True
        for sym in list(self._positions.keys()):
            try:
                pos = self._positions[sym]
                side = "sell" if pos["side"] == "buy" else "buy"
                await self.exchange.create_market_order(
                    sym, side, pos["quantity"], reduce_only=True
                )
                logger.info("Kill switch closed %s", sym)
            except Exception as e:
                logger.error("Kill switch failed for %s: %s", sym, e)
        self._positions.clear()
        await self.stop()

    async def on_candle(self, candle):
        if not self._running or not self._strategy:
            return
        if candle.symbol != self._strategy.symbol:
            return

        indicators = self.indicators.calculate(
            self._strategy.symbol,
            self._strategy.timeframe,
            limit=500,
        )
        if "error" in indicators:
            return

        candles = self.indicators.repo.get_candles(
            self._strategy.symbol,
            self._strategy.timeframe,
            limit=500,
        )
        if not candles:
            return

        idx = len(candles) - 1

        await self._check_live_exits(candle, idx, candles)
        await self._check_live_entry(candle, indicators, idx, candles)

    async def _check_live_exits(self, candle, idx, candles):
        for sym in list(self._positions.keys()):
            pos = self._positions[sym]
            side = pos["side"]
            qty = pos["quantity"]
            sl = pos.get("sl_price")
            tp = pos.get("tp_price")

            exit_reason = None
            if side == "buy":
                if sl and candle.low <= sl:
                    exit_reason = "stop_loss"
                    exit_price = sl
                elif tp and candle.high >= tp:
                    exit_reason = "take_profit"
                    exit_price = tp
            else:
                if sl and candle.high >= sl:
                    exit_reason = "stop_loss"
                    exit_price = sl
                elif tp and candle.low <= tp:
                    exit_reason = "take_profit"
                    exit_price = tp

            if exit_reason:
                close_side = "sell" if side == "buy" else "buy"
                try:
                    result = await self.exchange.create_market_order(
                        sym, close_side, qty, reduce_only=True
                    )
                    avg_price = result.average or exit_price
                    pnl = (
                        (avg_price - pos["entry_price"]) * qty
                        if side == "buy"
                        else (pos["entry_price"] - avg_price) * qty
                    )
                    self.risk.update_balance(pnl)

                    trade = Trade(
                        strategy=self._strategy.name if self._strategy else "",
                        side=side,
                        entry_index=0,
                        entry_time=pos["entry_time"],
                        entry_price=pos["entry_price"],
                        exit_index=idx,
                        exit_time=candle.timestamp,
                        exit_price=avg_price,
                        exit_reason=exit_reason,
                        quantity=qty,
                        pnl=pnl,
                        status="closed",
                    )
                    self.risk.record_trade(trade)
                    self._save_trade(trade)
                    del self._positions[sym]
                    logger.info(
                        "Live closed %s pnl=%.2f reason=%s", sym, pnl, exit_reason
                    )
                except Exception as e:
                    logger.error("Failed to close %s: %s", sym, e)

    async def _check_live_entry(self, candle, indicators, idx, candles):
        if not self._strategy:
            return
        can, reason = self.risk.can_open_position(
            self._strategy.risk, len(self._positions), "buy"
        )
        if not can:
            return

        side = self.evaluator._check_entry(
            candle, self._strategy, indicators, idx, candles
        )
        if not side:
            return

        pos = self.evaluator._open_position(
            self._strategy, candle, idx, side, indicators
        )
        if not pos:
            return

        qty = self.risk.calculate_size(
            self._strategy.risk, pos.trade.entry_price, pos.sl_price
        )
        if qty <= 0:
            return

        try:
            result = await self.exchange.create_market_order(candle.symbol, side, qty)
            fill_price = result.average or candle.close

            self._positions[candle.symbol] = {
                "side": side,
                "quantity": result.filled or qty,
                "entry_price": fill_price,
                "sl_price": pos.sl_price,
                "tp_price": pos.tp_price,
                "entry_time": candle.timestamp,
            }
            logger.info("Live %s %.4f @ %.2f", side, qty, fill_price)
        except Exception as e:
            logger.error("Live entry failed: %s", e)

    async def _poll_loop(self):
        while self._running and not self._kill_switch:
            try:
                for sym in list(self._positions.keys()):
                    price = await self.exchange.fetch_price(sym)
                    if sym in self._positions:
                        self._positions[sym]["current_price"] = price
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Live poll error: %s", e)
                await asyncio.sleep(30)

    def _save_trade(self, trade: Trade):
        try:
            self.trade_repo.save_trade(
                {
                    "symbol": self._strategy.symbol if self._strategy else "",
                    "side": trade.side,
                    "entry_price": trade.entry_price,
                    "quantity": trade.quantity,
                    "entry_index": trade.entry_index,
                    "mode": "live",
                    "strategy_id": 0,
                }
            )
        except Exception as e:
            logger.error("Failed to save live trade: %s", e)

    def get_positions(self) -> list[dict]:
        return [
            {
                "symbol": sym,
                "side": p["side"],
                "quantity": p["quantity"],
                "entry_price": p["entry_price"],
                "current_price": p.get("current_price", p["entry_price"]),
                "sl_price": p.get("sl_price"),
                "tp_price": p.get("tp_price"),
                "entry_time": p["entry_time"].isoformat()
                if isinstance(p["entry_time"], datetime)
                else str(p["entry_time"]),
                "strategy": self._strategy.name if self._strategy else "",
            }
            for sym, p in self._positions.items()
        ]

    def get_summary(self) -> dict:
        total_realized = 0
        return {
            "connected": self.exchange.connected,
            "running": self._running,
            "exchange": self.exchange.name,
            "open_positions": len(self._positions),
            "kill_switch": self._kill_switch,
        }
