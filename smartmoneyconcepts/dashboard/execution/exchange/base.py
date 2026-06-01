from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ExchangeBalance:
    total: float
    free: float
    used: float


@dataclass
class ExchangePosition:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    liquidation_price: Optional[float] = None


@dataclass
class ExchangeOrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: float
    filled: float
    price: Optional[float]
    average: Optional[float]
    status: str
    timestamp: Optional[datetime] = None


class Exchange(ABC):
    @abstractmethod
    async def connect(self) -> bool: ...

    @abstractmethod
    async def disconnect(self): ...

    @abstractmethod
    async def create_market_order(
        self, symbol: str, side: str, quantity: float, reduce_only: bool = False
    ) -> ExchangeOrderResult: ...

    @abstractmethod
    async def create_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> ExchangeOrderResult: ...

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool: ...

    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> ExchangeOrderResult: ...

    @abstractmethod
    async def get_positions(
        self, symbol: Optional[str] = None
    ) -> list[ExchangePosition]: ...

    @abstractmethod
    async def get_balance(self) -> ExchangeBalance: ...

    @abstractmethod
    async def fetch_price(self, symbol: str) -> float: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def connected(self) -> bool: ...
