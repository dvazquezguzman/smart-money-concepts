from fastapi import APIRouter, Query

from ..main import state
from ..engine.indicators import IndicatorService
from ..engine.candle_aggregator import get_available_timeframes

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/{symbol:path}")
def get_indicators(
    symbol: str,
    timeframe: str = Query("1m", description="Candle timeframe"),
    limit: int = Query(500, ge=50, le=1000, description="Number of candles"),
):
    valid_timeframes = get_available_timeframes()
    if timeframe not in valid_timeframes:
        return {"error": f"Invalid timeframe '{timeframe}'. Valid: {valid_timeframes}"}

    svc = IndicatorService(state.candle_repo)
    result = svc.calculate(symbol.upper(), timeframe, limit)
    return {"symbol": symbol.upper(), "timeframe": timeframe, **result}
