from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RiskConfig:
    daily_loss_limit_quote: float
    max_open_positions: int
    max_trades_per_day: int
    symbol_allowlist: list[str]


@dataclass(frozen=True)
class PaperConfig:
    starting_balance_quote: float
    fee_rate: float
    slippage_bps: int


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    exchange: str
    poll_interval_seconds: int
    risk: RiskConfig
    paper: PaperConfig


_REQUIRED_TOP = ("data_dir", "exchange", "poll_interval_seconds", "risk", "paper")


def load_config(path: Path) -> AppConfig:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
    missing = [k for k in _REQUIRED_TOP if k not in raw]
    if missing:
        raise ValueError(f"config missing required fields: {missing}")
    return AppConfig(
        data_dir=Path(raw["data_dir"]),
        exchange=str(raw["exchange"]),
        poll_interval_seconds=int(raw["poll_interval_seconds"]),
        risk=RiskConfig(
            daily_loss_limit_quote=float(raw["risk"]["daily_loss_limit_quote"]),
            max_open_positions=int(raw["risk"]["max_open_positions"]),
            max_trades_per_day=int(raw["risk"]["max_trades_per_day"]),
            symbol_allowlist=list(raw["risk"]["symbol_allowlist"]),
        ),
        paper=PaperConfig(
            starting_balance_quote=float(raw["paper"]["starting_balance_quote"]),
            fee_rate=float(raw["paper"]["fee_rate"]),
            slippage_bps=int(raw["paper"]["slippage_bps"]),
        ),
    )
