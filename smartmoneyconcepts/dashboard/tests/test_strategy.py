import sqlite3
import unittest
from datetime import datetime

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import SQLiteCandleRepository
from smartmoneyconcepts.dashboard.strategy.evaluator import (
    StrategyEvaluator,
    _calc_pnl,
    _evaluate_condition,
    _is_session,
    _last_ob_boundary,
)
from smartmoneyconcepts.dashboard.strategy.models import (
    Condition,
    ExitCondition,
    RiskConfig,
    Strategy,
    Trade,
)
from smartmoneyconcepts.dashboard.strategy.parser import (
    parse_strategy,
    serialize_strategy,
)
from smartmoneyconcepts.dashboard.strategy.backtest import Backtester
from smartmoneyconcepts.dashboard.engine.indicators import IndicatorService


def _candle(ts: datetime, o=100, h=105, l=95, c=102, v=1000):
    return Candle("BTC/USDT", ts, o, h, l, c, v, "1m")


class TestIsSession(unittest.TestCase):
    def test_asian_session(self):
        dt = datetime(2026, 5, 1, 3, 0)
        self.assertTrue(_is_session(dt, "Asian"))

    def test_london_session(self):
        dt = datetime(2026, 5, 1, 10, 0)
        self.assertTrue(_is_session(dt, "London"))

    def test_newyork_session(self):
        dt = datetime(2026, 5, 1, 15, 0)
        self.assertTrue(_is_session(dt, "NewYork"))

    def test_outside_session(self):
        dt = datetime(2026, 5, 1, 23, 0)
        self.assertFalse(_is_session(dt, "London"))


class TestCalcPnl(unittest.TestCase):
    def test_buy_profit(self):
        t = Trade("s", "buy", 0, datetime.now(), 100, exit_price=110, quantity=1)
        self.assertEqual(_calc_pnl(t), 10)

    def test_buy_loss(self):
        t = Trade("s", "buy", 0, datetime.now(), 100, exit_price=90, quantity=1)
        self.assertEqual(_calc_pnl(t), -10)

    def test_sell_profit(self):
        t = Trade("s", "sell", 0, datetime.now(), 100, exit_price=90, quantity=1)
        self.assertEqual(_calc_pnl(t), 10)

    def test_no_exit(self):
        t = Trade("s", "buy", 0, datetime.now(), 100, quantity=1)
        self.assertEqual(_calc_pnl(t), 0)


class TestLastOBBoundary(unittest.TestCase):
    def test_finds_bottom(self):
        indicators = {
            "ob": {
                "Top": [None, None, 105, None],
                "Bottom": [None, None, 100, None],
                "OB": [None, None, 1, None],
            }
        }
        result = _last_ob_boundary(indicators, 3, "bottom")
        self.assertEqual(result, 100)

    def test_finds_top(self):
        indicators = {
            "ob": {
                "Top": [None, None, 105, None],
                "Bottom": [None, None, 100, None],
                "OB": [None, None, 1, None],
            }
        }
        result = _last_ob_boundary(indicators, 3, "top")
        self.assertEqual(result, 105)

    def test_no_ob(self):
        indicators = {"ob": {"Top": [], "Bottom": [], "OB": []}}
        result = _last_ob_boundary(indicators, 0, "bottom")
        self.assertIsNone(result)


class TestEvaluateCondition(unittest.TestCase):
    def setUp(self):
        base = datetime(2026, 5, 1, 10, 0)
        self.candles = [_candle(base, o=100, h=105, l=95, c=102)]
        self.indicators = {
            "fvg": {"FVG": [1], "Top": [104], "Bottom": [101]},
            "ob": {"OB": [1], "Top": [103], "Bottom": [100]},
            "bos_choch": {"BOS": [0], "CHOCH": [0]},
            "liquidity": {"Liquidity": [0], "Level": [0]},
            "swings": {"High": [None], "Low": [None]},
        }

    def test_fvg_bullish_mitigation(self):
        candle = _candle(datetime(2026, 5, 1, 10, 5), o=101, h=105, l=100, c=104)
        cond = Condition(
            type="fvg_mitigation", direction="bullish", params={"lookback": 10}
        )
        result = _evaluate_condition(cond, candle, self.indicators, 1, self.candles)
        self.assertEqual(result, "bullish")

    def test_ob_break_bullish(self):
        candle = _candle(datetime(2026, 5, 1, 10, 5), o=104, h=108, l=103, c=107)
        cond = Condition(type="ob_break", direction="bullish", params={"lookback": 5})
        result = _evaluate_condition(cond, candle, self.indicators, 1, self.candles)
        self.assertEqual(result, "bullish")

    def test_session_condition(self):
        candle = _candle(datetime(2026, 5, 1, 10, 0))
        cond = Condition(
            type="session", direction="bullish", params={"session": "London"}
        )
        result = _evaluate_condition(cond, candle, self.indicators, 0, self.candles)
        self.assertEqual(result, "bullish")

    def test_unknown_condition(self):
        candle = _candle(datetime(2026, 5, 1, 10, 0))
        cond = Condition(type="nonexistent", direction="bullish")
        result = _evaluate_condition(cond, candle, self.indicators, 0, self.candles)
        self.assertIsNone(result)

    def test_liquidity_sweep_triggers(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [1], "Level": [50000]},
            "swings": {"High": [None], "Low": [None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="liquidity_sweep", direction="bullish")
        result = _evaluate_condition(cond, candle, indicators, 0, self.candles)
        self.assertEqual(result, "bullish")

    def test_liquidity_sweep_no_level(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [0], "Level": [0]},
            "swings": {"High": [None], "Low": [None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="liquidity_sweep", direction="bullish")
        result = _evaluate_condition(cond, candle, indicators, 0, self.candles)
        self.assertIsNone(result)

    def test_bos_triggers_bullish(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [1], "CHOCH": [0]},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [None], "Low": [None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="bos", direction="bullish")
        result = _evaluate_condition(cond, candle, indicators, 0, self.candles)
        self.assertEqual(result, "bullish")

    def test_bos_no_match(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [0], "CHOCH": [0]},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [None], "Low": [None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="bos", direction="bullish")
        result = _evaluate_condition(cond, candle, indicators, 0, self.candles)
        self.assertIsNone(result)

    def test_choch_triggers_bearish(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [0], "CHOCH": [-1]},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [None], "Low": [None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="choch", direction="bearish")
        result = _evaluate_condition(cond, candle, indicators, 0, self.candles)
        self.assertEqual(result, "bearish")

    def test_trend_bullish_swings(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [101, 105, 110], "Low": [None, None, None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="trend", direction="bullish", params={"lookback": 5})
        result = _evaluate_condition(cond, candle, indicators, 2, self.candles)
        self.assertEqual(result, "bullish")

    def test_trend_bearish_no_lows(self):
        indicators = {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [None, None, None], "Low": [None, None, None]},
        }
        candle = _candle(datetime(2026, 5, 1, 10, 5))
        cond = Condition(type="trend", direction="bearish", params={"lookback": 5})
        result = _evaluate_condition(cond, candle, indicators, 2, self.candles)
        self.assertIsNone(result)

    def test_multi_condition_and(self):
        candle = _candle(datetime(2026, 5, 1, 10, 5), o=101, h=105, l=100, c=104)
        indicators = {
            "fvg": {"FVG": [1], "Top": [104], "Bottom": [101]},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [None], "Low": [None]},
        }
        s = Strategy(
            name="multi",
            timeframe="1m",
            symbol="X",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 10}
                ),
                Condition(
                    type="session", direction="bullish", params={"session": "London"}
                ),
            ],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
        )
        result = StrategyEvaluator()._check_entry(candle, s, indicators, 1, [candle])
        self.assertEqual(result, "buy")

    def test_trailing_stop_updates_sl(self):
        from smartmoneyconcepts.dashboard.strategy.evaluator import _Position

        base = datetime(2026, 5, 1, 10, 0)
        pos = _Position(
            trade=Trade("t", "buy", 0, base, 100, quantity=1),
            entry_index=0,
            sl_price=99.0,
            tp_price=105.0,
        )
        strategy = Strategy(
            name="t",
            timeframe="1m",
            symbol="X",
            entry_conditions=[],
            exit_conditions=[ExitCondition(type="trailing_stop", trail_activation=2.0)],
        )
        eval = StrategyEvaluator()
        eval._update_trailing(pos, _candle(base, o=103, h=106, l=102, c=105), strategy)
        self.assertGreater(pos.sl_price, 99.0)


class TestEvaluatorRun(unittest.TestCase):
    def setUp(self):
        base = datetime(2026, 5, 1, 9, 0)
        self.candles = [
            _candle(base, o=100, h=105, l=95, c=102),
            _candle(datetime(2026, 5, 1, 9, 1), o=102, h=108, l=101, c=107),
            _candle(datetime(2026, 5, 1, 9, 2), o=107, h=110, l=106, c=109),
            _candle(datetime(2026, 5, 1, 9, 3), o=109, h=112, l=108, c=111),
            _candle(datetime(2026, 5, 1, 9, 4), o=111, h=115, l=110, c=114),
        ]
        self.indicators = {
            "fvg": {
                "FVG": [0, 1, 0, 0, 0],
                "Top": [None, 105, None, None, None],
                "Bottom": [None, 103, None, None, None],
            },
            "ob": {
                "OB": [0, 0, 0, 0, 0],
                "Top": [None, None, None, None, None],
                "Bottom": [None, None, None, None, None],
            },
            "bos_choch": {"BOS": [0, 0, 0, 0, 0], "CHOCH": [0, 0, 0, 0, 0]},
            "liquidity": {"Liquidity": [0, 0, 0, 0, 0], "Level": [0, 0, 0, 0, 0]},
            "swings": {
                "High": [None, None, None, None, None],
                "Low": [None, None, None, None, None],
            },
        }
        self.strategy = Strategy(
            name="test",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 10}
                ),
            ],
            exit_conditions=[
                ExitCondition(type="target", value=2.0),
                ExitCondition(type="stop_loss", value=1.0),
            ],
            risk=RiskConfig(position_size_pct=1.0, max_positions=1),
        )
        self.evaluator = StrategyEvaluator()

    def test_run_opens_trade_on_fvg_condition(self):
        trades = self.evaluator.run(self.strategy, self.candles, self.indicators)
        self.assertGreaterEqual(len(trades), 1)

    def test_run_closes_all_at_end(self):
        trades = self.evaluator.run(self.strategy, self.candles, self.indicators)
        for t in trades:
            self.assertEqual(t.status, "closed")


class TestParser(unittest.TestCase):
    def test_roundtrip(self):
        s = Strategy(
            name="test",
            timeframe="5m",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="fvg_mitigation", direction="bullish")],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
        )
        yaml = serialize_strategy(s)
        parsed = parse_strategy(yaml)
        self.assertEqual(parsed.name, "test")
        self.assertEqual(parsed.timeframe, "5m")
        self.assertEqual(len(parsed.entry_conditions), 1)
        self.assertEqual(parsed.entry_conditions[0].type, "fvg_mitigation")

    def test_parse_from_string(self):
        yaml = """name: ICT FVG Breaker
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
        s = parse_strategy(yaml)
        self.assertEqual(s.name, "ICT FVG Breaker")
        self.assertEqual(s.timeframe, "5m")
        self.assertEqual(len(s.entry_conditions), 1)
        self.assertEqual(s.entry_conditions[0].params["lookback"], 10)


class TestBacktester(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteCandleRepository(self.db)
        self.repo.create_tables()
        self.repo.create_tables_for_symbol("BTC/USDT")

        base = datetime(2026, 1, 1, 9, 0)
        candles = []
        for i in range(100):
            candles.append(
                Candle(
                    "BTC/USDT",
                    datetime.fromtimestamp(base.timestamp() + i * 60),
                    100 + i * 0.1,
                    105 + i * 0.1,
                    95 + i * 0.1,
                    102 + i * 0.1,
                    1000,
                    "1m",
                )
            )
        self.repo.save_candles(candles)

    def tearDown(self):
        self.db.close()

    def test_backtest_insufficient_data_returns_empty(self):
        strategy = Strategy(
            name="test",
            timeframe="1H",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="bos", direction="bullish")],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
        )
        indicator_service = IndicatorService(self.repo)
        backtester = Backtester(self.repo, indicator_service)
        result = backtester.run(
            strategy,
            datetime(2026, 1, 1),
            datetime(2026, 1, 2),
        )
        self.assertEqual(result.total_trades, 0)

    def test_backtest_returns_result_object(self):
        strategy = Strategy(
            name="test",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="fvg_mitigation", direction="bullish")],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
        )
        indicator_service = IndicatorService(self.repo)
        backtester = Backtester(self.repo, indicator_service)
        result = backtester.run(
            strategy,
            datetime(2026, 1, 1),
            datetime(2026, 1, 2, 2, 0),
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.strategy, "test")
        self.assertEqual(result.symbol, "BTC/USDT")


if __name__ == "__main__":
    unittest.main()
