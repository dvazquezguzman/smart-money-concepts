from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, select

from app.db import Candle, init_db
from app.events import EventBus
from app.feed import MarketFeed


class _FakeExchange:
    def __init__(self, batches: list[list[list[float]]]) -> None:
        self._batches = list(batches)
        self.calls = 0

    async def fetch_ohlcv(self, symbol: str, timeframe: str,
                          since: int | None = None, limit: int | None = None):
        self.calls += 1
        if not self._batches:
            return []
        return self._batches.pop(0)

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_feed_publishes_new_candles(tmp_path) -> None:
    engine = init_db(tmp_path / "smc.db")
    bus = EventBus()
    candle_q = bus.subscribe("candle")

    base_ms = 1_700_000_000_000
    minute = 60_000
    batch1 = [
        [base_ms,             100.0, 101.0, 99.5, 100.5, 1.0],
        [base_ms + 15*minute, 100.5, 102.0, 100.0, 101.5, 1.2],
    ]
    batch2 = [
        [base_ms + 15*minute, 100.5, 102.0, 100.0, 101.5, 1.2],
        [base_ms + 30*minute, 101.5, 103.0, 101.0, 102.5, 1.5],
    ]
    fake = _FakeExchange([batch1, batch2])

    feed = MarketFeed(exchange=fake, symbol="BTC/USDT", timeframe="15m",
                      poll_interval_seconds=0.0, engine=engine, bus=bus,
                      max_in_memory=1000)
    task = asyncio.create_task(feed.run())
    received = []
    for _ in range(3):
        msg = await asyncio.wait_for(candle_q.get(), 1.0)
        received.append(msg)
    feed.stop()
    await asyncio.wait_for(task, 1.0)

    assert len(received) == 3
    assert received[0]["symbol"] == "BTC/USDT"
    assert received[0]["timeframe"] == "15m"
    with Session(engine) as s:
        rows = s.exec(select(Candle)).all()
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_feed_keeps_rolling_window() -> None:
    engine = init_db(":memory:")  # not used by this test path, see note
    bus = EventBus()
    base_ms = 1_700_000_000_000
    minute = 60_000
    batch = [[base_ms + i * 15*minute, 1.0, 1.0, 1.0, 1.0, 1.0] for i in range(5)]
    fake = _FakeExchange([batch])
    feed = MarketFeed(exchange=fake, symbol="BTC/USDT", timeframe="15m",
                      poll_interval_seconds=0.0, engine=None, bus=bus,
                      max_in_memory=3)
    task = asyncio.create_task(feed.run())
    q = bus.subscribe("candle")
    for _ in range(5):
        await asyncio.wait_for(q.get(), 1.0)
    feed.stop()
    await asyncio.wait_for(task, 1.0)
    assert len(feed.dataframe()) == 3
