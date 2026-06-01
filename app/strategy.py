from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import pandas as pd

ParamKind = Literal["int", "float", "select", "bool"]
Side = Literal["buy", "sell"]


@dataclass(frozen=True)
class ParamSpec:
    name: str
    kind: ParamKind
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    choices: Optional[list[Any]] = None
    label: Optional[str] = None  # display label; falls back to name

    def validate(self) -> None:
        if self.kind in ("int", "float"):
            if self.min is not None and self.default < self.min:
                raise ValueError(f"default {self.default} outside [{self.min},{self.max}]")
            if self.max is not None and self.default > self.max:
                raise ValueError(f"default {self.default} outside [{self.min},{self.max}]")
        if self.kind == "select":
            if not self.choices or self.default not in self.choices:
                raise ValueError(f"select param {self.name} default not in choices")

    def coerce(self, value: Any) -> Any:
        if self.kind == "int":
            v = int(value)
        elif self.kind == "float":
            v = float(value)
        elif self.kind == "bool":
            v = bool(value)
        elif self.kind == "select":
            v = value
        else:
            raise ValueError(f"unknown kind {self.kind}")
        if self.kind in ("int", "float"):
            if self.min is not None and v < self.min:
                raise ValueError(f"{self.name} {v} below min {self.min}")
            if self.max is not None and v > self.max:
                raise ValueError(f"{self.name} {v} above max {self.max}")
        if self.kind == "select" and v not in (self.choices or []):
            raise ValueError(f"{self.name} {v} not in {self.choices}")
        return v


@dataclass(frozen=True)
class Signal:
    side: Side
    size: float           # in base-asset units
    sl: Optional[float]   # stop-loss price, None if not used
    tp: Optional[float]   # take-profit price
    reason: str           # short human label, shown in trade log


@dataclass
class Context:
    ohlc: pd.DataFrame
    indicators: dict[str, pd.DataFrame]
    params: dict[str, Any]


class Strategy:
    """Base class. Subclasses define class attrs + on_candle()."""
    name: str = ""
    symbol: str = ""
    timeframe: str = ""
    params: list[ParamSpec] = []

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        for p in cls.params:
            p.validate()

    def resolve_params(self, overrides: dict[str, Any]) -> dict[str, Any]:
        spec_by_name = {p.name: p for p in self.params}
        for k in overrides:
            if k not in spec_by_name:
                raise KeyError(f"unknown param {k!r} for strategy {self.name}")
        out = {p.name: p.default for p in self.params}
        for k, v in overrides.items():
            out[k] = spec_by_name[k].coerce(v)
        return out

    def on_candle(self, ctx: Context) -> Signal | None:
        raise NotImplementedError
