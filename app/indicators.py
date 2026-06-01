from __future__ import annotations

import pandas as pd
from smartmoneyconcepts import smc

INDICATOR_KEYS = ("swing_highs_lows", "fvg", "bos_choch", "ob", "liquidity", "retracements")


class IndicatorCache:
    """Recomputes the 6 bar-by-bar SMC indicators on each new bar.

    Designed for a single (symbol, timeframe) — instantiate one per pair.
    """

    def __init__(self, swing_length: int = 50) -> None:
        self.swing_length = swing_length
        self._snap: dict[str, pd.DataFrame] = {}

    def recompute(self, ohlc: pd.DataFrame) -> dict[str, pd.DataFrame]:
        swing = smc.swing_highs_lows(ohlc, swing_length=self.swing_length)
        snap = {
            "swing_highs_lows": swing,
            "fvg": smc.fvg(ohlc),
            "bos_choch": smc.bos_choch(ohlc, swing),
            "ob": smc.ob(ohlc, swing),
            "liquidity": smc.liquidity(ohlc, swing),
            "retracements": smc.retracements(ohlc, swing),
        }
        self._snap = snap
        return snap

    @property
    def snapshot(self) -> dict[str, pd.DataFrame]:
        return self._snap
