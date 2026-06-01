from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str


class BaseCandleRepository(ABC):
    @abstractmethod
    def create_tables(self): ...

    @abstractmethod
    def create_tables_for_symbol(self, symbol: str): ...

    @abstractmethod
    def save_candles(self, candles: list[Candle]): ...

    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since: Optional[datetime] = None,
    ) -> list[Candle]: ...

    @abstractmethod
    def get_last_candle(self, symbol: str, timeframe: str) -> Optional[Candle]: ...

    @abstractmethod
    def delete_duplicates(self, symbol: str, timeframe: str): ...


class BaseStrategyRepository(ABC):
    @abstractmethod
    def save_strategy(self, name: str, definition: str): ...

    @abstractmethod
    def get_strategy(self, strategy_id: int) -> Optional[dict]: ...

    @abstractmethod
    def list_strategies(self) -> list[dict]: ...

    @abstractmethod
    def delete_strategy(self, strategy_id: int): ...


class BaseTradeRepository(ABC):
    @abstractmethod
    def save_trade(self, trade: dict): ...

    @abstractmethod
    def get_trades(
        self, strategy_id: Optional[int] = None, mode: str = "paper"
    ) -> list[dict]: ...

    @abstractmethod
    def get_open_positions(self, mode: str = "paper") -> list[dict]: ...


class BaseConfigRepository(ABC):
    @abstractmethod
    def save_config(self, key: str, value: str): ...

    @abstractmethod
    def get_config(self, key: str) -> Optional[str]: ...
