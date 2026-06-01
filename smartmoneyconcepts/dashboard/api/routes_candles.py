import asyncio
import logging

from fastapi import APIRouter, Query

from ..main import state
from ..engine.candle_aggregator import get_available_timeframes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/candles", tags=["candles"])


@router.get("/{symbol:path}")
def get_candles(
    symbol: str,
    timeframe: str = Query("1m", description="Candle timeframe"),
    limit: int = Query(200, ge=1, le=1000, description="Number of candles"),
):
    valid_timeframes = get_available_timeframes()
    if timeframe not in valid_timeframes:
        return {"error": f"Invalid timeframe '{timeframe}'. Valid: {valid_timeframes}"}

    symbol = symbol.upper()
    candles = state.candle_repo.get_candles(symbol, timeframe, limit)

    if len(candles) == 0:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(state.data_engine.ensure_symbol(symbol))
        except RuntimeError:
            pass
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": 0,
            "candles": [],
            "loading": True,
        }

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": [
            {
                "timestamp": c.timestamp.isoformat(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in candles
        ],
    }
