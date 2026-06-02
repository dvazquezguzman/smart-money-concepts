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

        # --- Custom indicators ---
        typical_price = (ohlc["high"] + ohlc["low"] + ohlc["close"]) / 3
        vwap = (typical_price * ohlc["volume"]).cumsum() / ohlc["volume"].cumsum()
        result["vwap"] = vwap.replace({np.nan: None}).tolist()

        result["ema_9"] = (
            ohlc["close"].ewm(span=9).mean().replace({np.nan: None}).tolist()
        )
        result["ema_21"] = (
            ohlc["close"].ewm(span=21).mean().replace({np.nan: None}).tolist()
        )

        don_upper = ohlc["high"].rolling(20).max()
        don_lower = ohlc["low"].rolling(20).min()
        don_mid = (don_upper + don_lower) / 2
        don_trend = np.where(don_mid.diff() > 0, 1, np.where(don_mid.diff() < 0, -1, 0))
        result["donchian"] = {
            "upper": don_upper.replace({np.nan: None}).tolist(),
            "lower": don_lower.replace({np.nan: None}).tolist(),
            "mid": don_mid.replace({np.nan: None}).tolist(),
            "trend": pd.Series(don_trend).replace({np.nan: None}).tolist(),
        }

        half = ohlc["close"].ewm(span=10).mean()
        full = ohlc["close"].ewm(span=20).mean()
        raw = 2 * half - full
        hull = raw.ewm(span=int(np.sqrt(20))).mean()
        drift = hull.diff()
        hull_dir = np.where(drift > 0, 1, np.where(drift < 0, -1, 0))
        result["hull"] = {
            "hull": hull.replace({np.nan: None}).tolist(),
            "direction": pd.Series(hull_dir).replace({np.nan: None}).tolist(),
        }

        prev = ohlc["close"].shift(1)
        tr = pd.concat(
            [
                ohlc["high"] - ohlc["low"],
                (ohlc["high"] - prev).abs(),
                (ohlc["low"] - prev).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(10).mean()
        hl2 = (ohlc["high"] + ohlc["low"]) / 2
        st_upper = hl2 + 3.0 * atr
        st_lower = hl2 - 3.0 * atr
        st_trend = pd.Series(index=ohlc.index, dtype=float)
        for i in range(len(st_trend)):
            if i == 0:
                st_trend.iloc[i] = 1
            else:
                if ohlc["close"].iloc[i] > st_upper.iloc[i - 1]:
                    st_trend.iloc[i] = -1
                elif ohlc["close"].iloc[i] < st_lower.iloc[i - 1]:
                    st_trend.iloc[i] = 1
                else:
                    st_trend.iloc[i] = st_trend.iloc[i - 1]
        result["supertrend"] = {
            "trend": st_trend.replace({np.nan: None}).tolist(),
            "upper": st_upper.replace({np.nan: None}).tolist(),
            "lower": st_lower.replace({np.nan: None}).tolist(),
        }

        self._cache[key] = {"data": result, "last_timestamp": last_ts}
        return result

    def invalidate_cache(self, symbol: str, timeframe: str = "1m"):
        keys = [k for k in self._cache if k.startswith(f"{symbol}:{timeframe}:")]
        for k in keys:
            del self._cache[k]
