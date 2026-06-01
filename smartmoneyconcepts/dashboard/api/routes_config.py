import json
import logging

from fastapi import APIRouter

from ..main import state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/symbols")
def get_symbols():
    raw = state.config_repo.get_config("symbols")
    symbols = json.loads(raw) if raw else ["BTC/USDT"]
    return {"symbols": symbols}


@router.post("/symbols")
async def add_symbol(symbol: str):
    raw = state.config_repo.get_config("symbols")
    symbols = json.loads(raw) if raw else ["BTC/USDT"]
    symbol = symbol.upper()
    if symbol not in symbols:
        symbols.append(symbol)
        state.config_repo.save_config("symbols", json.dumps(symbols))
        await state.data_engine.ensure_symbol(symbol)
        logger.info(f"Symbol added via config: {symbol}")
    return {"symbols": symbols}


@router.delete("/symbols")
async def remove_symbol(symbol: str):
    raw = state.config_repo.get_config("symbols")
    symbols = json.loads(raw) if raw else ["BTC/USDT"]
    symbol = symbol.upper()
    if symbol in symbols:
        symbols.remove(symbol)
        state.config_repo.save_config("symbols", json.dumps(symbols))
    return {"symbols": symbols}
