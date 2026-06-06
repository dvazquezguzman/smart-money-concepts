from datetime import datetime

from smartmoneyconcepts.dashboard.strategy.optimizer import StrategyOptimizer
from smartmoneyconcepts.dashboard.strategy.parser import (
    ParamRange,
    _resolve_value,
    apply_params,
    detect_ranges,
)


class TestResolveValue:
    def test_list_of_ints(self):
        assert _resolve_value([5, 10, 15]) == [5.0, 10.0, 15.0]

    def test_list_of_mixed(self):
        assert _resolve_value([1, 2.5, 3]) == [1.0, 2.5, 3.0]

    def test_dict_range(self):
        result = _resolve_value({"min": 1.5, "max": 3.0, "step": 0.5})
        assert result == [1.5, 2.0, 2.5, 3.0]

    def test_dict_range_int_step(self):
        result = _resolve_value({"min": 1, "max": 3, "step": 1})
        assert result == [1.0, 2.0, 3.0]

    def test_scalar_returns_none(self):
        assert _resolve_value(5) is None
        assert _resolve_value("hello") is None


class TestDetectRanges:
    YAML = """
name: Test Strategy
timeframe: 5m
symbol: BTC/USDT
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: [5, 10, 15]
exit_conditions:
  - type: target
    value: {min: 1.5, max: 3.0, step: 0.5}
  - type: stop_loss
    value: [1.0, 2.0]
risk:
  position_size_pct: {min: 0.5, max: 2.0, step: 0.5}
  max_positions: [1, 2]
"""

    def test_detects_entry_ranges(self):
        ranges = detect_ranges(self.YAML)
        paths = {str(r.path) for r in ranges}
        assert "['entry_conditions', 0, 'lookback']" in paths

    def test_detects_exit_ranges(self):
        ranges = detect_ranges(self.YAML)
        paths = {str(r.path) for r in ranges}
        assert "['exit_conditions', 0, 'value']" in paths
        assert "['exit_conditions', 1, 'value']" in paths

    def test_detects_risk_ranges(self):
        ranges = detect_ranges(self.YAML)
        paths = {str(r.path) for r in ranges}
        assert "['risk', 'position_size_pct']" in paths
        assert "['risk', 'max_positions']" in paths

    def test_correct_values(self):
        ranges = detect_ranges(self.YAML)
        for r in ranges:
            if r.path == ["entry_conditions", 0, "lookback"]:
                assert r.values == [5.0, 10.0, 15.0]
            elif r.path == ["risk", "position_size_pct"]:
                assert r.values == [0.5, 1.0, 1.5, 2.0]

    def test_no_ranges_returns_empty(self):
        yaml = """
name: No Ranges
timeframe: 5m
symbol: X
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: 10
exit_conditions:
  - type: target
    value: 2.0
risk:
  position_size_pct: 1.0
"""
        assert detect_ranges(yaml) == []


class TestParamRange:
    def test_param_range_creation(self):
        r = ParamRange(path=["entry_conditions", 0, "lookback"], values=[5, 10])
        assert r.path == ["entry_conditions", 0, "lookback"]
        assert r.values == [5, 10]


class TestApplyParams:
    BASE_YAML = """
name: Test
timeframe: 5m
symbol: BTC/USDT
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: 10
exit_conditions:
  - type: target
    value: 2.0
risk:
  position_size_pct: 1.0
  max_positions: 1
"""

    def test_applies_single_range(self):
        ranges = [
            ParamRange(path=["entry_conditions", 0, "lookback"], values=[5, 10, 15])
        ]
        result = apply_params(self.BASE_YAML, ranges, (15,))
        assert "lookback: 15" in result

    def test_applies_multiple_ranges(self):
        ranges = [
            ParamRange(path=["entry_conditions", 0, "lookback"], values=[5, 10, 15]),
            ParamRange(path=["risk", "position_size_pct"], values=[0.5, 1.0, 2.0]),
        ]
        result = apply_params(self.BASE_YAML, ranges, (15, 2.0))
        assert "lookback: 15" in result
        assert "position_size_pct: 2.0" in result
