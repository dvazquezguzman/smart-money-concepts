from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlmodel import Session, select

from app.brokers.base import Broker, BrokerFill, BrokerOrder, BrokerPosition
from app.db import Fill, Order, Position


class PaperBroker(Broker):
    """In-memory + DB-backed simulated broker.

    Fills the next call to place_order at `mark_price` adjusted by
    `slippage_bps` in the order's direction, charges `fee_rate` on notional.
    """

    def __init__(self, engine: object, starting_balance_quote: float,
                 fee_rate: float, slippage_bps: int) -> None:
        self._engine = engine
        self._balance = starting_balance_quote
        self._fee_rate = fee_rate
        self._slippage_bps = slippage_bps

    @property
    def mode(self) -> Literal["paper", "live"]:
        return "paper"

    def _fill_price(self, side: str, mark: float) -> float:
        adj = self._slippage_bps / 10_000.0
        return mark * (1 + adj) if side == "buy" else mark * (1 - adj)

    async def place_order(self, order: BrokerOrder, mark_price: float) -> BrokerOrder:
        price = self._fill_price(order.side, mark_price)
        notional = price * order.qty
        fee = notional * self._fee_rate
        signed = order.qty if order.side == "buy" else -order.qty
        now = datetime.now(timezone.utc)

        with Session(self._engine) as s:
            db_order = Order(
                strategy=order.strategy, symbol=order.symbol, side=order.side,
                qty=order.qty, status="filled", mode="paper", ts=now,
            )
            s.add(db_order)
            s.commit()
            s.refresh(db_order)

            s.add(Fill(order_id=db_order.id, price=price, qty=order.qty,
                       fee=fee, ts=now))

            pos = s.exec(
                select(Position).where(Position.strategy == order.strategy,
                                       Position.symbol == order.symbol)
            ).first()
            if pos is None:
                pos = Position(strategy=order.strategy, symbol=order.symbol,
                               qty=signed, avg_price=price)
                s.add(pos)
            else:
                _apply_fill_to_position(pos, signed, price)
                s.add(pos)

            s.commit()
            order.id = db_order.id
            order.status = "filled"

        # Cash accounting: buy debits, sell credits, fee always debits.
        if order.side == "buy":
            self._balance -= notional
        else:
            self._balance += notional
        self._balance -= fee
        return order

    async def get_position(self, strategy: str, symbol: str) -> BrokerPosition:
        with Session(self._engine) as s:
            pos = s.exec(
                select(Position).where(Position.strategy == strategy,
                                       Position.symbol == symbol)
            ).first()
        if pos is None:
            return BrokerPosition(strategy=strategy, symbol=symbol,
                                  qty=0.0, avg_price=0.0)
        return BrokerPosition(strategy=pos.strategy, symbol=pos.symbol,
                              qty=pos.qty, avg_price=pos.avg_price)

    async def get_balance_quote(self) -> float:
        return self._balance


def _apply_fill_to_position(pos: Position, signed_qty: float, price: float) -> None:
    """Update position qty + avg_price for a fill of signed_qty at price.

    - Same-direction add: weighted average.
    - Opposite direction (partial or full close): qty reduces; avg_price unchanged.
    - Cross through zero (e.g. long 0.4 -> -0.2): avg_price resets to fill price.
    """
    new_qty = pos.qty + signed_qty
    if pos.qty == 0 or (pos.qty > 0) == (signed_qty > 0):
        # Opening or adding in same direction.
        if new_qty != 0:
            pos.avg_price = (pos.avg_price * pos.qty + price * signed_qty) / new_qty
    elif (pos.qty > 0 and new_qty < 0) or (pos.qty < 0 and new_qty > 0):
        # Crossed zero: residual is a fresh position at fill price.
        pos.avg_price = price
    # Else partial close in opposite direction: avg_price unchanged.
    pos.qty = new_qty
