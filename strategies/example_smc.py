"""Example SMC strategy: long when the most recent fully-formed bullish FVG
has not been mitigated and price is currently inside it; short for the
mirror case. Sizes a fixed quantity, sets SL at the FVG far edge and TP
at fill price + R*risk."""
from __future__ import annotations

import math

from app.strategy import Context, ParamSpec, Signal, Strategy


class ExampleSMC(Strategy):
    name = "example_smc"
    symbol = "BTC/USDT"
    timeframe = "15m"
    params = [
        ParamSpec(name="swing_length", kind="int", default=50, min=10, max=200),
        ParamSpec(name="size", kind="float", default=0.01, min=0.0001, max=1.0),
        ParamSpec(name="rr", kind="float", default=2.0, min=0.5, max=10.0),
    ]

    def on_candle(self, ctx: Context) -> Signal | None:
        fvg = ctx.indicators.get("fvg")
        if fvg is None or fvg.empty:
            return None
        # Most recent bullish FVG with no MitigatedIndex.
        bull = fvg[(fvg["FVG"] == 1) & (fvg["MitigatedIndex"].isna())]
        bear = fvg[(fvg["FVG"] == -1) & (fvg["MitigatedIndex"].isna())]
        last_close = float(ctx.ohlc["close"].iloc[-1])

        if not bull.empty:
            row = bull.iloc[-1]
            top, bot = float(row["Top"]), float(row["Bottom"])
            if bot <= last_close <= top:
                risk = max(last_close - bot, 1e-9)
                tp = last_close + ctx.params["rr"] * risk
                return Signal(side="buy", size=ctx.params["size"],
                              sl=bot, tp=tp, reason="bullish FVG retest")
        if not bear.empty:
            row = bear.iloc[-1]
            top, bot = float(row["Top"]), float(row["Bottom"])
            if bot <= last_close <= top:
                risk = max(top - last_close, 1e-9)
                tp = last_close - ctx.params["rr"] * risk
                return Signal(side="sell", size=ctx.params["size"],
                              sl=top, tp=tp, reason="bearish FVG retest")
        return None
