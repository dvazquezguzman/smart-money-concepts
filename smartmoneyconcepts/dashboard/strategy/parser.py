import yaml
from pathlib import Path

from .models import Strategy, Condition, ExitCondition, RiskConfig


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
