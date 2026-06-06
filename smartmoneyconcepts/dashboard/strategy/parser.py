from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from .models import Strategy, Condition, ExitCondition, RiskConfig


@dataclass
class ParamRange:
    path: list
    values: list


def parse_strategy(yaml_str: str) -> Strategy:
    data = yaml.safe_load(yaml_str)

    entry_conds = []
    for c in data.get("entry_conditions", []):
        entry_conds.append(
            Condition(
                type=c["type"],
                direction=c.get("direction"),
                params={k: v for k, v in c.items() if k not in ("type", "direction")},
            )
        )

    exit_conds = []
    for c in data.get("exit_conditions", []):
        exit_conds.append(
            ExitCondition(
                type=c["type"],
                value=c.get("value", 1.0),
                trail_activation=c.get("trail_activation"),
            )
        )

    risk_data = data.get("risk", {})
    risk = RiskConfig(
        position_size_pct=risk_data.get("position_size_pct", 1.0),
        max_positions=risk_data.get("max_positions", 1),
        max_daily_loss=risk_data.get("max_daily_loss"),
    )

    return Strategy(
        name=data["name"],
        timeframe=data["timeframe"],
        symbol=data.get("symbol", ""),
        entry_conditions=entry_conds,
        exit_conditions=exit_conds,
        risk=risk,
    )


def serialize_strategy(strategy: Strategy) -> str:
    data = {
        "name": strategy.name,
        "timeframe": strategy.timeframe,
        "symbol": strategy.symbol,
        "entry_conditions": [
            {"type": c.type, "direction": c.direction, **c.params}
            for c in strategy.entry_conditions
        ],
        "exit_conditions": [
            {"type": c.type, "value": c.value}
            | ({"trail_activation": c.trail_activation} if c.trail_activation else {})
            for c in strategy.exit_conditions
        ],
        "risk": {
            "position_size_pct": strategy.risk.position_size_pct,
            "max_positions": strategy.risk.max_positions,
            **(
                {"max_daily_loss": strategy.risk.max_daily_loss}
                if strategy.risk.max_daily_loss
                else {}
            ),
        },
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def load_template(path: Path) -> Strategy:
    return parse_strategy(path.read_text())


def _resolve_value(val) -> list:
    if isinstance(val, list):
        return [float(v) if isinstance(v, (int, float)) else v for v in val]
    if isinstance(val, dict) and "min" in val and "max" in val:
        step = val.get("step", 1)
        return np.arange(val["min"], val["max"] + step, step).tolist()
    return None


def detect_ranges(yaml_str: str) -> list[ParamRange]:
    data = yaml.safe_load(yaml_str)
    ranges = []

    for i, cond in enumerate(data.get("entry_conditions", [])):
        for key, val in cond.items():
            if key in ("type", "direction"):
                continue
            resolved = _resolve_value(val)
            if resolved is not None:
                ranges.append(
                    ParamRange(path=["entry_conditions", i, key], values=resolved)
                )

    for i, cond in enumerate(data.get("exit_conditions", [])):
        for key, val in cond.items():
            if key == "type":
                continue
            resolved = _resolve_value(val)
            if resolved is not None:
                ranges.append(
                    ParamRange(path=["exit_conditions", i, key], values=resolved)
                )

    for key, val in data.get("risk", {}).items():
        resolved = _resolve_value(val)
        if resolved is not None:
            ranges.append(ParamRange(path=["risk", key], values=resolved))

    return ranges


def apply_params(base_yaml: str, ranges: list[ParamRange], combo: tuple) -> str:
    data = deepcopy(yaml.safe_load(base_yaml))
    for r, val in zip(ranges, combo):
        target = data
        for key in r.path[:-1]:
            target = target[key]
        target[r.path[-1]] = val
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
