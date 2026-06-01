from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np

from smartmoneyconcepts.smc import smc
from ..db.base import BaseCandleRepository, Candle
from .candle_aggregator import aggregate_candles, TIMEFRAME_MINUTES


class IndicatorService:
    def __init__(self, repo: BaseCandleRepository):
        self.repo = repo
        self._cache: dict[str, dict] = {}

    def _cache_key(self, symbol: str, timeframe: str, limit: int) -> str:
        return f"{symbol}:{timeframe}:{limit}"

    def _candles_to_df(self, candles: list[Candle]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": [c.open for c in candles],
                "high": [c.high for c in candles],
                "low": [c.low for c in candles],
                "close": [c.close for c in candles],
                "volume": [c.volume for c in candles],
            },
            index=pd.DatetimeIndex([c.timestamp for c in candles]),
        )

    def calculate(self, symbol: str, timeframe: str = "1m", limit: int = 500) -> dict:
        key = self._cache_key(symbol, timeframe, limit)

        candles = self.repo.get_candles(symbol, timeframe, limit)

        if len(candles) < 10 and timeframe != "1m":
            one_min_candles = self.repo.get_candles(
                symbol, "1m", limit * TIMEFRAME_MINUTES[timeframe]
            )
            if len(one_min_candles) >= 10:
                candles = aggregate_candles(one_min_candles, timeframe)

        if len(candles) < 10:
            return {
                "error": f"Not enough data for {symbol} ({timeframe}): {len(candles)} candles"
            }

        last_ts = candles[-1].timestamp.isoformat() if candles else None
        if key in self._cache and self._cache[key].get("last_timestamp") == last_ts:
            return self._cache[key]["data"]

        ohlc = self._candles_to_df(candles)
        swings = smc.swing_highs_lows(ohlc)
        result = {
            "fvg": smc.fvg(ohlc).replace({np.nan: None}).to_dict(orient="list"),
            "ob": smc.ob(ohlc, swings).replace({np.nan: None}).to_dict(orient="list"),
            "bos_choch": smc.bos_choch(ohlc, swings)
            .replace({np.nan: None})
            .to_dict(orient="list"),
            "liquidity": smc.liquidity(ohlc, swings)
            .replace({np.nan: None})
            .to_dict(orient="list"),
            "swings": swings.replace({np.nan: None}).to_dict(orient="list"),
            "retracements": smc.retracements(ohlc, swings)
            .replace({np.nan: None})
            .to_dict(orient="list"),
            "sessions_london": smc.sessions(ohlc, "London")
            .replace({np.nan: None})
            .to_dict(orient="list"),
            "previous_high_low": smc.previous_high_low(ohlc, "1D")
            .replace({np.nan: None})
            .to_dict(orient="list"),
            "candle_count": len(candles),
        }

        self._cache[key] = {"data": result, "last_timestamp": last_ts}
        return result

    def invalidate_cache(self, symbol: str, timeframe: str = "1m"):
        keys = [k for k in self._cache if k.startswith(f"{symbol}:{timeframe}:")]
        for k in keys:
            del self._cache[k]
