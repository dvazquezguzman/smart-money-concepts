from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.brokers.base import BrokerOrder
from app.brokers.paper import PaperBroker
from app.db import Fill, Order, Position, init_db


@pytest.mark.asyncio
async def test_buy_then_sell_realizes_pnl(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=1000.0,
                     fee_rate=0.001, slippage_bps=2)

    o1 = await pb.place_order(
        BrokerOrder(strategy="s1", symbol="BTC/USDT", side="buy", qty=0.1),
        mark_price=100.0,
    )
    assert o1.status == "filled"
    pos = await pb.get_position("s1", "BTC/USDT")
    assert pos.qty == pytest.approx(0.1)
    # Fill price = 100 * (1 + 2bps) = 100.02
    assert pos.avg_price == pytest.approx(100.02)

    bal_after_buy = await pb.get_balance_quote()
    # Spent 0.1 * 100.02 = 10.002, fee 0.001 * 10.002 = 0.010002
    assert bal_after_buy == pytest.approx(1000.0 - 10.002 - 0.010002)

    o2 = await pb.place_order(
        BrokerOrder(strategy="s1", symbol="BTC/USDT", side="sell", qty=0.1),
        mark_price=110.0,
    )
    assert o2.status == "filled"
    pos2 = await pb.get_position("s1", "BTC/USDT")
    assert pos2.qty == pytest.approx(0.0)

    with Session(engine) as session:
        orders = session.exec(select(Order)).all()
        fills = session.exec(select(Fill)).all()
        positions = session.exec(select(Position)).all()
        assert len(orders) == 2
        assert len(fills) == 2
        assert all(o.mode == "paper" for o in orders)
        # Position row remains (qty 0); engine task closes it as Trade later.
        assert len(positions) == 1


@pytest.mark.asyncio
async def test_partial_close_preserves_avg_price(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=10000.0,
                     fee_rate=0.0, slippage_bps=0)
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="buy", qty=1.0),
        mark_price=100.0,
    )
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="sell", qty=0.4),
        mark_price=120.0,
    )
    pos = await pb.get_position("s", "BTC/USDT")
    assert pos.qty == pytest.approx(0.6)
    assert pos.avg_price == pytest.approx(100.0)


@pytest.mark.asyncio
async def test_short_then_cover(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=10000.0,
                     fee_rate=0.0, slippage_bps=0)
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="sell", qty=0.5),
        mark_price=100.0,
    )
    pos = await pb.get_position("s", "BTC/USDT")
    assert pos.qty == pytest.approx(-0.5)
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="buy", qty=0.5),
        mark_price=90.0,
    )
    pos2 = await pb.get_position("s", "BTC/USDT")
    assert pos2.qty == pytest.approx(0.0)
    bal = await pb.get_balance_quote()
    # Sold 0.5 @ 100 = +50; bought back 0.5 @ 90 = -45; net +5
    assert bal == pytest.approx(10005.0)


@pytest.mark.asyncio
async def test_same_direction_add_uses_weighted_average(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=10000.0,
                     fee_rate=0.0, slippage_bps=0)
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="buy", qty=0.1),
        mark_price=100.0,
    )
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="buy", qty=0.1),
        mark_price=200.0,
    )
    pos = await pb.get_position("s", "BTC/USDT")
    assert pos.qty == pytest.approx(0.2)
    # Weighted average: (100 * 0.1 + 200 * 0.1) / 0.2 = 150
    assert pos.avg_price == pytest.approx(150.0)


@pytest.mark.asyncio
async def test_cross_zero_resets_avg_price(tmp_data_dir: Path) -> None:
    engine = init_db(tmp_data_dir / "smc.db")
    pb = PaperBroker(engine=engine, starting_balance_quote=10000.0,
                     fee_rate=0.0, slippage_bps=0)
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="buy", qty=0.4),
        mark_price=100.0,
    )
    await pb.place_order(
        BrokerOrder(strategy="s", symbol="BTC/USDT", side="sell", qty=0.6),
        mark_price=120.0,
    )
    pos = await pb.get_position("s", "BTC/USDT")
    # Long 0.4 reversed by sell 0.6 leaves -0.2 short, repriced at the new fill.
    assert pos.qty == pytest.approx(-0.2)
    assert pos.avg_price == pytest.approx(120.0)
