from __future__ import annotations

import pandas as pd
import pytest

from app.strategy import Context, ParamSpec, Signal, Strategy


class _Dummy(Strategy):
    name = "dummy"
    symbol = "BTC/USDT"
    timeframe = "15m"
    params = [
        ParamSpec(name="threshold", kind="float", default=0.5, min=0.0, max=1.0),
        ParamSpec(name="lookback", kind="int", default=50, min=10, max=200),
        ParamSpec(name="mode", kind="select", default="trend",
                  choices=["trend", "mean_revert"]),
    ]

    def on_candle(self, ctx: Context) -> Signal | None:
        if ctx.params["threshold"] >= 0.9:
            return Signal(side="buy", size=0.1, sl=None, tp=None, reason="high threshold")
        return None


def test_param_spec_validates_defaults() -> None:
    bad = ParamSpec(name="x", kind="float", default=2.0, min=0.0, max=1.0)
    with pytest.raises(ValueError, match="default 2.0 outside"):
        bad.validate()


def test_strategy_param_dict_uses_overrides_then_defaults() -> None:
    s = _Dummy()
    assert s.resolve_params({}) == {"threshold": 0.5, "lookback": 50, "mode": "trend"}
    assert s.resolve_params({"threshold": 0.95})["threshold"] == 0.95


def test_strategy_param_dict_rejects_unknown_key() -> None:
    s = _Dummy()
    with pytest.raises(KeyError, match="unknown param"):
        s.resolve_params({"bogus": 1})


def test_strategy_param_dict_rejects_out_of_range() -> None:
    s = _Dummy()
    with pytest.raises(ValueError, match="lookback"):
        s.resolve_params({"lookback": 5})


def test_on_candle_can_return_signal() -> None:
    df = pd.DataFrame({"open": [1.0], "high": [1.0], "low": [1.0],
                       "close": [1.0], "volume": [1.0]})
    ctx = Context(ohlc=df, indicators={}, params={"threshold": 0.95,
                                                  "lookback": 50, "mode": "trend"})
    sig = _Dummy().on_candle(ctx)
    assert sig is not None
    assert sig.side == "buy"
