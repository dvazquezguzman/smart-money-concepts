from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.brokers.base import Broker, BrokerOrder, BrokerFill, BrokerPosition


def test_dataclasses_construct() -> None:
    o = BrokerOrder(strategy="x", symbol="BTC/USDT", side="buy", qty=0.01)
    f = BrokerFill(order_id=1, price=10.0, qty=0.01, fee=0.001,
                   ts=datetime.now(timezone.utc))
    p = BrokerPosition(strategy="x", symbol="BTC/USDT", qty=0.01, avg_price=10.0)
    assert o.side == "buy"
    assert f.qty == 0.01
    assert p.avg_price == 10.0


def test_broker_is_abstract() -> None:
    with pytest.raises(TypeError):
        Broker()  # type: ignore[abstract]
