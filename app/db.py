from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine


class Candle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    timeframe: str = Field(index=True)
    ts: datetime = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    volume: float


class StrategyState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    mode: str  # "paper" | "live"
    enabled: bool = True
    params_json: str = "{}"
    last_error: Optional[str] = None


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy: str = Field(index=True)
    symbol: str = Field(index=True)
    side: str  # "buy" | "sell"
    qty: float
    status: str  # "pending" | "filled" | "rejected" | "cancelled"
    mode: str  # "paper" | "live"
    reject_reason: Optional[str] = None
    ts: datetime


class Fill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(index=True)
    price: float
    qty: float
    fee: float
    ts: datetime


class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy: str = Field(index=True)
    symbol: str = Field(index=True)
    qty: float  # signed: positive long, negative short
    avg_price: float


class Trade(SQLModel, table=True):
    """Closed round-trip: opened position -> flat. Used for win-rate / P&L stats."""
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy: str = Field(index=True)
    symbol: str
    side: str  # initial side that opened it
    entry_price: float
    exit_price: float
    qty: float
    pnl_quote: float
    opened_at: datetime
    closed_at: datetime
    mode: str


def init_db(path: Path) -> object:
    """Create the SQLite database file and tables. Returns the SQLModel engine."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine
