from __future__ import annotations

import pandas as pd
import pytest
from smartmoneyconcepts import smc

from app.indicators import IndicatorCache


def test_cache_outputs_match_raw_smc(eurusd_15m_df: pd.DataFrame) -> None:
    df = eurusd_15m_df.copy()
    cache = IndicatorCache(swing_length=50)
    snap = cache.recompute(df)

    raw_swing = smc.swing_highs_lows(df, swing_length=50)
    pd.testing.assert_frame_equal(snap["swing_highs_lows"], raw_swing)
    pd.testing.assert_frame_equal(snap["fvg"], smc.fvg(df))
    pd.testing.assert_frame_equal(snap["bos_choch"], smc.bos_choch(df, raw_swing))
    pd.testing.assert_frame_equal(snap["ob"], smc.ob(df, raw_swing))
    pd.testing.assert_frame_equal(snap["liquidity"], smc.liquidity(df, raw_swing))
    pd.testing.assert_frame_equal(snap["retracements"], smc.retracements(df, raw_swing))


def test_cache_keys_are_stable() -> None:
    df = pd.DataFrame({
        "open": [1.0, 1.0, 1.0], "high": [1.0, 1.0, 1.0],
        "low": [1.0, 1.0, 1.0], "close": [1.0, 1.0, 1.0],
        "volume": [1.0, 1.0, 1.0],
    }, index=pd.date_range("2024-01-01", periods=3, freq="15min"))
    cache = IndicatorCache(swing_length=2)
    snap = cache.recompute(df)
    assert set(snap.keys()) == {
        "swing_highs_lows", "fvg", "bos_choch", "ob", "liquidity", "retracements",
    }
