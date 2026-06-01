from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class OrderStatus:
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide:
    BUY = "buy"
    SELL = "sell"


class OrderType:
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass
class Order:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = OrderStatus.PENDING
    order_id: Optional[int] = None
    filled_quantity: float = 0.0
    avg_fill_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    strategy: str = ""
    strategy_id: Optional[int] = None
    reduce_only: bool = False


@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)
    strategy: str = ""
    mode: str = "paper"
    position_id: Optional[int] = None
