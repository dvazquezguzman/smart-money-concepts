from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

Side = Literal["buy", "sell"]
OrderStatus = Literal["pending", "filled", "rejected", "cancelled"]


@dataclass
class BrokerOrder:
    strategy: str
    symbol: str
    side: Side
    qty: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    id: Optional[int] = None
    status: OrderStatus = "pending"
    reject_reason: Optional[str] = None


@dataclass
class BrokerFill:
    order_id: int
    price: float
    qty: float
    fee: float
    ts: datetime


@dataclass
class BrokerPosition:
    strategy: str
    symbol: str
    qty: float       # signed: positive = long, negative = short
    avg_price: float


class Broker(ABC):
    @property
    @abstractmethod
    def mode(self) -> Literal["paper", "live"]: ...

    @abstractmethod
    async def place_order(self, order: BrokerOrder, mark_price: float) -> BrokerOrder:
        """Submit an order. Returns updated order with status set."""

    @abstractmethod
    async def get_position(self, strategy: str, symbol: str) -> BrokerPosition: ...

    @abstractmethod
    async def get_balance_quote(self) -> float: ...
