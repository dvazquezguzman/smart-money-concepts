from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from app.brokers.base import BrokerOrder
from app.events import EventBus
from app.indicators import IndicatorCache
from app.risk import RiskManager
from app.strategy import Context, Strategy

log = logging.getLogger(__name__)


@dataclass
class _Registered:
    strat: Strategy
    mode: str  # "paper" | "live"
    params: dict[str, Any]
    disabled: bool = False
    last_error: Optional[str] = None


def _key(symbol: str, timeframe: str) -> str:
    return f"{symbol}|{timeframe}"


class StrategyEngine:
    def __init__(self, bus: EventBus, risk: RiskManager,
                 indicator_caches: dict[str, IndicatorCache]) -> None:
        self._bus = bus
        self._risk = risk
        self._caches = indicator_caches
        self._strats: dict[str, _Registered] = {}
        self._market: dict[str, pd.DataFrame] = {}

    def register(self, strat: Strategy, mode: str, overrides: dict[str, Any]) -> None:
        params = strat.resolve_params(overrides)
        self._strats[strat.name] = _Registered(strat=strat, mode=mode, params=params)

    def is_disabled(self, name: str) -> bool:
        return self._strats[name].disabled

    def last_error(self, name: str) -> Optional[str]:
        return self._strats[name].last_error

    def update_market(self, symbol: str, timeframe: str, df: pd.DataFrame) -> None:
        self._market[_key(symbol, timeframe)] = df

    async def run_once(self, symbol: str, timeframe: str,
                       mark_price: float) -> Optional[BrokerOrder]:
        k = _key(symbol, timeframe)
        df = self._market.get(k)
        if df is None or df.empty:
            return None
        cache = self._caches.get(k)
        snap = cache.recompute(df) if cache is not None else {}
        last_order: Optional[BrokerOrder] = None
        for reg in self._strats.values():
            if reg.disabled:
                continue
            if reg.strat.symbol != symbol or reg.strat.timeframe != timeframe:
                continue
            try:
                ctx = Context(ohlc=df, indicators=snap, params=reg.params)
                sig = reg.strat.on_candle(ctx)
            except Exception as e:  # noqa: BLE001
                reg.disabled = True
                reg.last_error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
                log.exception("strategy %s crashed; disabled", reg.strat.name)
                continue
            if sig is None:
                continue
            order = await self._risk.submit(
                strategy=reg.strat.name, mode=reg.mode,
                symbol=symbol, timeframe=timeframe, sig=sig,
                mark_price=mark_price,
            )
            await self._bus.publish("order", {
                "strategy": reg.strat.name, "status": order.status,
                "side": order.side, "qty": order.qty,
                "reject_reason": order.reject_reason,
            })
            last_order = order
        return last_order
