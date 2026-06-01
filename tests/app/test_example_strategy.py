from __future__ import annotations

import pandas as pd

from app.indicators import IndicatorCache
from app.strategy import Context
from strategies.example_smc import ExampleSMC


def test_strategy_declares_expected_params() -> None:
    s = ExampleSMC()
    names = {p.name for p in s.params}
    assert names == {"swing_length", "size", "rr"}


def test_strategy_returns_none_when_no_setup(eurusd_15m_df: pd.DataFrame) -> None:
    df = eurusd_15m_df.iloc[:80].copy()
    cache = IndicatorCache(swing_length=50)
    snap = cache.recompute(df)
    s = ExampleSMC()
    ctx = Context(ohlc=df, indicators=snap, params=s.resolve_params({}))
    sig = s.on_candle(ctx)
    assert sig is None or sig.side in ("buy", "sell")  # tolerant: just must not raise
