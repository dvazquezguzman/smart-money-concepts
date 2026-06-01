from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pandas as pd
import pytest

from app.brokers.paper import PaperBroker
from app.config import RiskConfig
from app.db import init_db
from app.engine import StrategyEngine
from app.events import EventBus
from app.indicators import IndicatorCache
from app.risk import RiskManager
from app.strategy import Context, ParamSpec, Signal, Strategy


class _AlwaysBuy(Strategy):
    name = "always_buy"
    symbol = "BTC/USDT"
    timeframe = "15m"
    params = [ParamSpec(name="size", kind="float", default=0.01,
                        min=0.0001, max=1.0)]

    def on_candle(self, ctx: Context) -> Signal | None:
        return Signal(side="buy", size=ctx.params["size"], sl=None, tp=None,
                      reason="always")


class _Crash(Strategy):
    name = "crash"
    symbol = "BTC/USDT"
    timeframe = "15m"
    params = []

    def on_candle(self, ctx: Context) -> Signal | None:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_engine_routes_signal_to_broker(tmp_path) -> None:
    engine_db = init_db(tmp_path / "smc.db")
    bus = EventBus()
    pb = PaperBroker(engine=engine_db, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    risk = RiskConfig(daily_loss_limit_quote=1000.0, max_open_positions=10,
                      max_trades_per_day=10, symbol_allowlist=["BTC/USDT"])
    rm = RiskManager(engine=engine_db, risk=risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)
    cache = IndicatorCache(swing_length=2)

    df = pd.DataFrame({
        "open": [1, 2, 3, 4, 5], "high": [1, 2, 3, 4, 5],
        "low": [1, 2, 3, 4, 5], "close": [1, 2, 3, 4, 5],
        "volume": [1, 1, 1, 1, 1],
    }, index=pd.date_range("2024-01-01", periods=5, freq="15min"))

    eng = StrategyEngine(bus=bus, risk=rm, indicator_caches={"BTC/USDT|15m": cache})
    eng.register(_AlwaysBuy(), mode="paper", overrides={"size": 0.05})

    eng.update_market("BTC/USDT", "15m", df)
    order = await eng.run_once("BTC/USDT", "15m", mark_price=5.0)
    assert order is not None
    assert order.status == "filled"
    pos = await pb.get_position("always_buy", "BTC/USDT")
    assert pos.qty == pytest.approx(0.05)


@pytest.mark.asyncio
async def test_engine_disables_strategy_on_exception(tmp_path) -> None:
    engine_db = init_db(tmp_path / "smc.db")
    bus = EventBus()
    pb = PaperBroker(engine=engine_db, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    risk = RiskConfig(daily_loss_limit_quote=1000.0, max_open_positions=10,
                      max_trades_per_day=10, symbol_allowlist=["BTC/USDT"])
    rm = RiskManager(engine=engine_db, risk=risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)
    cache = IndicatorCache(swing_length=2)
    df = pd.DataFrame({
        "open": [1, 2, 3], "high": [1, 2, 3], "low": [1, 2, 3],
        "close": [1, 2, 3], "volume": [1, 1, 1],
    }, index=pd.date_range("2024-01-01", periods=3, freq="15min"))

    eng = StrategyEngine(bus=bus, risk=rm, indicator_caches={"BTC/USDT|15m": cache})
    eng.register(_Crash(), mode="paper", overrides={})
    eng.update_market("BTC/USDT", "15m", df)
    out = await eng.run_once("BTC/USDT", "15m", mark_price=3.0)
    assert out is None
    assert eng.is_disabled("crash")
    assert "boom" in (eng.last_error("crash") or "")
