import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..db.base import BaseStrategyRepository, BaseTradeRepository
from ..engine.indicators import IndicatorService
from ..main import state
from ..strategy.backtest import Backtester
from ..strategy.models import BacktestResult, Strategy
from ..strategy.parser import parse_strategy, serialize_strategy

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/strategies", tags=["strategies"])


def get_strategy_repo() -> BaseStrategyRepository:
    return state.strategy_repo


def get_trade_repo() -> BaseTradeRepository:
    return state.trade_repo


@router.get("")
def list_strategies(
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
):
    return repo.list_strategies()


@router.get("/{strategy_id}")
def get_strategy(
    strategy_id: int,
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
):
    s = repo.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return s


@router.post("")
def create_strategy(
    body: dict,
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
):
    name = body.get("name", "").strip()
    yaml_def = body.get("definition", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not yaml_def:
        raise HTTPException(status_code=400, detail="definition is required")
    try:
        parsed = parse_strategy(yaml_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    repo.save_strategy(name, yaml_def)
    return {"status": "ok", "name": parsed.name}


@router.put("/{strategy_id}")
def update_strategy(
    strategy_id: int,
    body: dict,
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
):
    existing = repo.get_strategy(strategy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Strategy not found")
    yaml_def = body.get("definition", "").strip()
    if not yaml_def:
        raise HTTPException(status_code=400, detail="definition is required")
    try:
        parse_strategy(yaml_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    repo.save_strategy(existing["name"], yaml_def)
    return {"status": "ok"}


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: int,
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
):
    repo.delete_strategy(strategy_id)
    return {"status": "ok"}


@router.get("/templates/list")
def list_templates():
    import pathlib

    templates_dir = (
        pathlib.Path(__file__).resolve().parent.parent / "strategy" / "templates"
    )
    if not templates_dir.exists():
        return []
    files = sorted(templates_dir.glob("*.yaml"))
    result = []
    for f in files:
        result.append({"name": f.stem.replace("-", " ").title(), "file": f.name})
    return result


@router.get("/templates/{file_name}")
def get_template(file_name: str):
    import pathlib

    templates_dir = (
        pathlib.Path(__file__).resolve().parent.parent / "strategy" / "templates"
    )
    f = templates_dir / file_name
    if not f.exists() or f.suffix != ".yaml":
        raise HTTPException(status_code=404, detail="Template not found")
    return {"name": file_name, "definition": f.read_text()}


@router.post("/backtest")
def run_backtest(body: dict) -> BacktestResult:
    yaml_def = body.get("definition", "").strip()
    start_str = body.get("start", "")
    end_str = body.get("end", "")
    initial_capital = body.get("initial_capital", 10000.0)
    symbol = body.get("symbol", "").strip()

    if not yaml_def:
        raise HTTPException(status_code=400, detail="definition is required")
    if not start_str or not end_str:
        raise HTTPException(status_code=400, detail="start and end are required")

    try:
        strategy = parse_strategy(yaml_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    if symbol:
        strategy.symbol = symbol
    elif not strategy.symbol:
        raise HTTPException(
            status_code=400, detail="symbol is required (set in YAML or request body)"
        )

    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {e}")

    indicator_service = IndicatorService(state.candle_repo)
    backtester = Backtester(state.candle_repo, indicator_service)
    result = backtester.run(strategy, start, end, initial_capital)
    return result


@router.get("/backtest/history/{strategy_id}")
def get_backtest_history(
    strategy_id: int,
    repo: BaseStrategyRepository = Depends(get_strategy_repo),
    trade_repo: BaseTradeRepository = Depends(get_trade_repo),
):
    s = repo.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    trades = trade_repo.get_trades(strategy_id, mode="paper")
    return {"strategy": s, "trades": trades}
