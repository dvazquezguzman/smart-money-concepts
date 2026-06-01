from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from ..db.base import Candle

TIMEFRAME_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1H": 60,
    "4H": 240,
}


def round_to_timeframe(ts: datetime, minutes: int) -> datetime:
    epoch = datetime(1970, 1, 1)
    delta = int((ts - epoch).total_seconds()) // 60
    rounded = (delta // minutes) * minutes
    return epoch + timedelta(minutes=rounded)


def aggregate_candles(
    one_min_candles: list[Candle], target_timeframe: str
) -> list[Candle]:
    if not one_min_candles:
        return []

    target_minutes = TIMEFRAME_MINUTES.get(target_timeframe)
    if target_minutes is None:
        raise ValueError(f"Unsupported timeframe: {target_timeframe}")

    rows = [
        {
            "timestamp": round_to_timeframe(c.timestamp, target_minutes),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in one_min_candles
    ]

    df = pd.DataFrame(rows)
    if df.empty:
        return []

    symbol = one_min_candles[0].symbol
    aggregated = (
        df.groupby("timestamp")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .reset_index()
    )

    return [
        Candle(
            symbol=symbol,
            timestamp=row.timestamp.to_pydatetime(),
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            timeframe=target_timeframe,
        )
        for row in aggregated.itertuples()
    ]


def get_available_timeframes() -> list[str]:
    return list(TIMEFRAME_MINUTES.keys())
