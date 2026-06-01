from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, TypeDecorator
from sqlmodel import Field, SQLModel, create_engine


class UtcDateTime(TypeDecorator):
    """DateTime that stores naively in SQLite but always returns UTC-aware datetimes.

    SQLite has no native datetime type; SQLAlchemy stores datetimes as naive
    ISO-8601 strings regardless of `timezone=True`. This decorator normalizes
    on the way in (convert to UTC, strip tzinfo) and on the way out
    (re-attach UTC tzinfo). Net effect: callers always see tz-aware UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            # Treat naive input as UTC.
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Candle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    timeframe: str = Field(index=True)
    ts: datetime = Field(sa_column=Column("ts", UtcDateTime, index=True, nullable=False))
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
    ts: datetime = Field(sa_column=Column("ts", UtcDateTime, nullable=False))


class Fill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(index=True)
    price: float
    qty: float
    fee: float
    ts: datetime = Field(sa_column=Column("ts", UtcDateTime, nullable=False))


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
    opened_at: datetime = Field(sa_column=Column("opened_at", UtcDateTime, nullable=False))
    closed_at: datetime = Field(sa_column=Column("closed_at", UtcDateTime, nullable=False))
    mode: str


def init_db(path: Path) -> object:
    """Create the SQLite database file and tables. Returns the SQLModel engine."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine
