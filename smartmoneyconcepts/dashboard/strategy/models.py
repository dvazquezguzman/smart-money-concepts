from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class RiskConfig:
    position_size_pct: float = 1.0
    max_positions: int = 1
    max_daily_loss: Optional[float] = None


@dataclass
class Condition:
    type: str
    direction: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExitCondition:
    type: str
    value: float = 1.0
    trail_activation: Optional[float] = None


@dataclass
class Strategy:
    name: str
    timeframe: str
    symbol: str
    entry_conditions: list[Condition] = field(default_factory=list)
    exit_conditions: list[ExitCondition] = field(default_factory=list)
    risk: RiskConfig = field(default_factory=RiskConfig)


@dataclass
class Trade:
    strategy: str
    side: str
    entry_index: int
    entry_time: datetime
    entry_price: float
    exit_index: Optional[int] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    quantity: float = 0.0
    pnl: Optional[float] = None
    status: str = "open"


@dataclass
class ComboResult:
    params: dict
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    profit_factor: float
    max_drawdown: float
    sharpe: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_bars_held: float


@dataclass
class OptimizerResult:
    strategy_name: str
    symbol: str
    timeframe: str
    total_combos: int
    combos_run: int
    results: list[ComboResult] = field(default_factory=list)


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    timeframe: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    profit_factor: float
    max_drawdown: float
    sharpe: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_bars_held: float
    trades: list[Trade] = field(default_factory=list)
