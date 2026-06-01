from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, func, select

from app.brokers.base import Broker, BrokerOrder
from app.config import RiskConfig
from app.db import Order, Position, Trade
from app.strategy import Signal

log = logging.getLogger(__name__)

_TIMEFRAME_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "2h": 7200, "4h": 14400, "1d": 86400,
}


class RiskManager:
    """The only path between strategies and brokers."""

    def __init__(self, engine: object, risk: RiskConfig,
                 paper: Broker, live: Optional[Broker],
                 stale_factor: float = 2.0) -> None:
        self._engine = engine
        self._risk = risk
        self._paper = paper
        self._live = live
        self._stale_factor = stale_factor
        self.kill_switch_armed: bool = False
        self.kill_reason: Optional[str] = None
        self.last_candle_ts: Optional[datetime] = None

    def trip_kill_switch(self, reason: str) -> None:
        self.kill_switch_armed = True
        self.kill_reason = reason
        log.warning("kill switch tripped: %s", reason)

    def clear_kill_switch(self) -> None:
        self.kill_switch_armed = False
        self.kill_reason = None

    async def submit(self, strategy: str, mode: str, symbol: str,
                     timeframe: str, sig: Signal, mark_price: float) -> BrokerOrder:
        order = BrokerOrder(strategy=strategy, symbol=symbol,
                            side=sig.side, qty=sig.size,
                            sl=sig.sl, tp=sig.tp)

        reason = self._reject_reason(symbol, timeframe, strategy)
        if reason is not None:
            order.status = "rejected"
            order.reject_reason = reason
            self._record_rejection(order, mode)
            return order

        broker = self._paper if mode == "paper" else self._live
        if broker is None:
            order.status = "rejected"
            order.reject_reason = "broker_unavailable"
            self._record_rejection(order, mode)
            return order
        return await broker.place_order(order, mark_price=mark_price)

    def _reject_reason(self, symbol: str, timeframe: str,
                       strategy: str) -> Optional[str]:
        if self.kill_switch_armed:
            return "kill_switch"
        if symbol not in self._risk.symbol_allowlist:
            return "symbol_not_allowed"
        if self.last_candle_ts is None:
            return "no_market_data"
        tf_secs = _TIMEFRAME_SECONDS.get(timeframe)
        if tf_secs is None:
            return "unknown_timeframe"
        age = (datetime.now(timezone.utc) - self.last_candle_ts).total_seconds()
        if age > tf_secs * self._stale_factor:
            return "stale_data"

        with Session(self._engine) as s:
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0)
            pnl_today = s.exec(
                select(func.coalesce(func.sum(Trade.pnl_quote), 0.0))
                .where(Trade.closed_at >= today_start)
            ).one()
            if pnl_today <= -abs(self._risk.daily_loss_limit_quote):
                return "daily_loss_limit"

            trades_today = s.exec(
                select(func.count(Order.id))
                .where(Order.ts >= today_start, Order.status == "filled")
            ).one()
            if trades_today >= self._risk.max_trades_per_day:
                return "max_trades_per_day"

            open_count = s.exec(
                select(func.count(Position.id))
                .where(Position.qty != 0, Position.strategy == strategy)
            ).one()
            if open_count >= self._risk.max_open_positions:
                return "max_open_positions"

        return None

    def _record_rejection(self, order: BrokerOrder, mode: str) -> None:
        with Session(self._engine) as s:
            s.add(Order(
                strategy=order.strategy, symbol=order.symbol, side=order.side,
                qty=order.qty, status="rejected", mode=mode,
                reject_reason=order.reject_reason,
                ts=datetime.now(timezone.utc),
            ))
            s.commit()
