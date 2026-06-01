from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.db import (
    Candle, Fill, Order, Position, StrategyState, Trade, init_db,
)


def test_init_db_creates_all_tables(tmp_data_dir: Path) -> None:
    db_path = tmp_data_dir / "smc.db"
    engine = init_db(db_path)
    assert db_path.exists()

    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add(Candle(
            symbol="BTC/USDT", timeframe="15m", ts=now,
            open=1.0, high=2.0, low=0.5, close=1.5, volume=100.0,
        ))
        session.add(StrategyState(name="example", mode="paper", enabled=True, params_json="{}"))
        session.add(Order(
            strategy="example", symbol="BTC/USDT", side="buy",
            qty=0.01, status="filled", mode="paper", ts=now,
        ))
        session.add(Fill(order_id=1, price=1.5, qty=0.01, fee=0.001, ts=now))
        session.add(Position(strategy="example", symbol="BTC/USDT", qty=0.01, avg_price=1.5))
        session.add(Trade(
            strategy="example", symbol="BTC/USDT", side="buy",
            entry_price=1.5, exit_price=1.6, qty=0.01,
            pnl_quote=0.001, opened_at=now, closed_at=now, mode="paper",
        ))
        session.commit()

        candles = session.exec(select(Candle)).all()
        states = session.exec(select(StrategyState)).all()
        assert len(candles) == 1
        assert states[0].mode == "paper"
        assert candles[0].ts.tzinfo is not None
        assert candles[0].ts == now
