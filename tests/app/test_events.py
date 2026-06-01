from __future__ import annotations

import asyncio

import pytest

from app.events import EventBus


@pytest.mark.asyncio
async def test_event_bus_delivers_to_all_subscribers() -> None:
    bus = EventBus()
    q1 = bus.subscribe("candle")
    q2 = bus.subscribe("candle")
    q3 = bus.subscribe("signal")

    await bus.publish("candle", {"symbol": "BTC/USDT"})
    await bus.publish("signal", {"side": "buy"})

    assert (await asyncio.wait_for(q1.get(), 0.1)) == {"symbol": "BTC/USDT"}
    assert (await asyncio.wait_for(q2.get(), 0.1)) == {"symbol": "BTC/USDT"}
    assert (await asyncio.wait_for(q3.get(), 0.1)) == {"side": "buy"}


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    q = bus.subscribe("candle")
    bus.unsubscribe("candle", q)
    await bus.publish("candle", {"x": 1})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q.get(), 0.05)
