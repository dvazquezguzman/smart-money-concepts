from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from sqlmodel import Session

from app.brokers.base import BrokerOrder
from app.brokers.paper import PaperBroker
from app.config import RiskConfig
from app.db import Trade, init_db
from app.risk import RiskManager
from app.strategy import Signal


@pytest.fixture
def base_risk() -> RiskConfig:
    return RiskConfig(
        daily_loss_limit_quote=50.0,
        max_open_positions=2,
        max_trades_per_day=10,
        symbol_allowlist=["BTC/USDT", "ETH/USDT"],
    )


@pytest.mark.asyncio
async def test_accepts_valid_signal(tmp_data_dir: Path, base_risk: RiskConfig) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=base_risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="test")
    out = await rm.submit("strat", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    assert out.status == "filled"


@pytest.mark.asyncio
async def test_rejects_unknown_symbol(tmp_data_dir: Path, base_risk: RiskConfig) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=base_risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="test")
    out = await rm.submit("strat", "paper", "XRP/USDT", "15m", sig, mark_price=1.0)
    assert out.status == "rejected"
    assert out.reject_reason == "symbol_not_allowed"


@pytest.mark.asyncio
async def test_rejects_when_kill_switch_armed(tmp_data_dir: Path,
                                              base_risk: RiskConfig) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=base_risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)
    rm.trip_kill_switch("manual test")

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="test")
    out = await rm.submit("strat", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    assert out.status == "rejected"
    assert out.reject_reason == "kill_switch"


@pytest.mark.asyncio
async def test_rejects_when_data_stale(tmp_data_dir: Path,
                                       base_risk: RiskConfig) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=base_risk, paper=pb, live=None,
                     stale_factor=2.0)
    # Last candle 1 hour ago; timeframe 15m → stale threshold = 30m.
    rm.last_candle_ts = datetime.now(timezone.utc) - timedelta(hours=1)

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="test")
    out = await rm.submit("strat", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    assert out.status == "rejected"
    assert out.reject_reason == "stale_data"


@pytest.mark.asyncio
async def test_rejects_when_daily_loss_exceeded(tmp_data_dir: Path,
                                                base_risk: RiskConfig) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=base_risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)

    today = datetime.now(timezone.utc)
    with Session(engine) as s:
        s.add(Trade(strategy="strat", symbol="BTC/USDT", side="buy",
                    entry_price=100.0, exit_price=50.0, qty=1.0,
                    pnl_quote=-60.0, opened_at=today, closed_at=today,
                    mode="paper"))
        s.commit()

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="test")
    out = await rm.submit("strat", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    assert out.status == "rejected"
    assert out.reject_reason == "daily_loss_limit"


@pytest.mark.asyncio
async def test_rejects_when_too_many_trades_today(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    risk = RiskConfig(daily_loss_limit_quote=1_000_000.0, max_open_positions=10,
                      max_trades_per_day=2, symbol_allowlist=["BTC/USDT"])
    pb = PaperBroker(engine=engine, starting_balance_quote=10000.0,
                     fee_rate=0.0, slippage_bps=0)
    rm = RiskManager(engine=engine, risk=risk, paper=pb, live=None)
    rm.last_candle_ts = datetime.now(timezone.utc)

    sig = Signal(side="buy", size=0.01, sl=None, tp=None, reason="t")
    await rm.submit("s", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    await rm.submit("s", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    out = await rm.submit("s", "paper", "BTC/USDT", "15m", sig, mark_price=100.0)
    assert out.status == "rejected"
    assert out.reject_reason == "max_trades_per_day"
