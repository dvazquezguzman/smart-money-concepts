import sqlite3
import unittest
from datetime import datetime, timedelta

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import (
    SQLiteCandleRepository,
    SQLiteTradeRepository,
)
from smartmoneyconcepts.dashboard.engine.indicators import IndicatorService
from smartmoneyconcepts.dashboard.execution.paper import PaperTradingEngine
from smartmoneyconcepts.dashboard.strategy.backtest import Backtester
from smartmoneyconcepts.dashboard.strategy.evaluator import StrategyEvaluator
from smartmoneyconcepts.dashboard.strategy.models import (
    Condition,
    ExitCondition,
    RiskConfig,
    Strategy,
)


def _seed_trending_candles(repo, symbol="BTC/USDT", n=500, start_price=50000):
    candles = []
    base = datetime(2026, 5, 1, 0, 0)
    price = start_price
    for i in range(n):
        drift = (i % 50 - 20) * 2
        price += drift
        high = price + abs(i % 30) * 2 + 10
        low = price - abs(i % 20) * 2 - 10
        close = price + (1 if i % 3 == 0 else -1) * abs(i % 15)
        candles.append(
            Candle(
                symbol=symbol,
                timestamp=base + timedelta(seconds=i * 60),
                open=round(price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=round(500 + (i % 100), 2),
                timeframe="1m",
            )
        )
    repo.save_candles(candles)
    return candles


class TestStrategyToBacktest(unittest.TestCase):
    """Integration: DB -> IndicatorService -> Backtester"""

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.candle_repo = SQLiteCandleRepository(self.db)
        self.trade_repo = SQLiteTradeRepository(self.db)
        self.candle_repo.create_tables()
        self.candle_repo.create_tables_for_symbol("BTC/USDT")
        self.candles = _seed_trending_candles(self.candle_repo)
        self.indicators = IndicatorService(self.candle_repo)
        self.backtester = Backtester(self.candle_repo, self.indicators)

    def tearDown(self):
        self.db.close()

    def test_indicator_service_usable_by_evaluator(self):
        result = self.indicators.calculate("BTC/USDT", "1m", 200)
        self.assertNotIn("error", result)
        self.assertIn("fvg", result)
        self.assertIn("ob", result)

    def test_backtester_runs_full_pipeline(self):
        strategy = Strategy(
            name="integ-test",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="bos", direction="bullish")],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
            risk=RiskConfig(position_size_pct=1.0, max_positions=1),
        )
        start = self.candles[0].timestamp
        end = self.candles[-1].timestamp
        result = self.backtester.run(strategy, start, end, initial_capital=10000)
        self.assertEqual(result.strategy, "integ-test")
        self.assertEqual(result.symbol, "BTC/USDT")
        self.assertEqual(result.timeframe, "1m")
        self.assertIsInstance(result.total_trades, int)
        self.assertIsInstance(result.win_rate, float)

    def test_backtester_multiple_condition_types(self):
        strategy = Strategy(
            name="multi-cond",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 20}
                ),
                Condition(
                    type="session", direction="bullish", params={"session": "London"}
                ),
            ],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
            risk=RiskConfig(position_size_pct=0.5, max_positions=2),
        )
        start = self.candles[0].timestamp
        end = self.candles[-1].timestamp
        result = self.backtester.run(strategy, start, end, initial_capital=10000)
        self.assertEqual(result.strategy, "multi-cond")
        self.assertIsInstance(result.total_trades, int)


class TestStrategyToPaperTrade(unittest.TestCase):
    """Integration: IndicatorService -> Evaluator -> PaperTradingEngine"""

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.candle_repo = SQLiteCandleRepository(self.db)
        self.trade_repo = SQLiteTradeRepository(self.db)
        self.candle_repo.create_tables()
        self.candle_repo.create_tables_for_symbol("BTC/USDT")
        self.candles = _seed_trending_candles(self.candle_repo)
        self.indicators = IndicatorService(self.candle_repo)
        self.evaluator = StrategyEvaluator()
        self.engine = PaperTradingEngine(self.trade_repo, self.indicators)

        self.strategy = Strategy(
            name="paper-integ",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 15}
                )
            ],
            exit_conditions=[
                ExitCondition(type="target", value=2.0),
                ExitCondition(type="stop_loss", value=1.0),
            ],
            risk=RiskConfig(position_size_pct=1.0, max_positions=1),
        )

    def tearDown(self):
        self.db.close()

    def test_paper_engine_evaluator_pipeline(self):
        indicators = self.indicators.calculate("BTC/USDT", "1m", len(self.candles))
        self.assertNotIn("error", indicators)

        trades = self.evaluator.run(self.strategy, self.candles, indicators)
        self.assertIsInstance(trades, list)

    def test_paper_engine_on_candle_lifecycle(self):
        self.engine.start(self.strategy)
        self.assertTrue(self.engine.running)

        for c in self.candles[:100]:
            self.engine.on_candle(c)

        summary = self.engine.get_summary()
        self.assertIn("balance", summary)
        self.assertIn("open_positions", summary)
        self.assertIn("running", summary)
        self.assertTrue(summary["running"])

        self.engine.stop()
        self.assertFalse(self.engine.running)

    def test_paper_engine_trade_is_recorded(self):
        self.engine.start(self.strategy)
        for c in self.candles[:200]:
            self.engine.on_candle(c)
        self.engine.stop()

        positions = self.engine.get_positions()
        self.assertIsInstance(positions, list)

        summary = self.engine.get_summary()
        self.assertGreater(summary["balance"], 0)
        self.assertLessEqual(
            summary["open_positions"],
            self.strategy.risk.max_positions,
        )


class TestIndicatorToEvaluatorDirect(unittest.TestCase):
    """Direct pipeline: compute indicators -> evaluator -> trades"""

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteCandleRepository(self.db)
        self.repo.create_tables()
        self.repo.create_tables_for_symbol("BTC/USDT")
        base = datetime(2026, 5, 1, 0, 0)
        self.candles = []
        for i in range(500):
            self.candles.append(
                Candle(
                    "BTC/USDT",
                    base + timedelta(seconds=i * 60),
                    100 + (i % 50),
                    110 + (i % 30),
                    90 + (i % 20),
                    105 + (i % 15),
                    1000,
                    "1m",
                )
            )
        self.repo.save_candles(self.candles)
        self.indicators = IndicatorService(self.repo)
        self.evaluator = StrategyEvaluator()

    def tearDown(self):
        self.db.close()

    def test_indicators_produce_valid_fvg_data(self):
        result = self.indicators.calculate("BTC/USDT", "1m", len(self.candles))
        fvg = result["fvg"]
        self.assertEqual(len(fvg["FVG"]), len(self.candles))
        self.assertEqual(len(fvg["Top"]), len(self.candles))

    def test_indicators_produce_valid_ob_data(self):
        result = self.indicators.calculate("BTC/USDT", "1m", len(self.candles))
        ob = result["ob"]
        self.assertEqual(len(ob["OB"]), len(self.candles))

    def test_evaluator_with_real_indicators(self):
        indicators = self.indicators.calculate("BTC/USDT", "1m", len(self.candles))
        strategy = Strategy(
            name="real-data-test",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 10}
                ),
            ],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
            risk=RiskConfig(position_size_pct=1.0, max_positions=1),
        )
        trades = self.evaluator.run(strategy, self.candles, indicators)
        self.assertIsInstance(trades, list)
        for t in trades:
            self.assertEqual(t.status, "closed")
            self.assertIsNotNone(t.pnl)


if __name__ == "__main__":
    unittest.main()
