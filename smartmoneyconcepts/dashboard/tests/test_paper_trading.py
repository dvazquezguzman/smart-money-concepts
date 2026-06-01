import sqlite3
import unittest
from datetime import datetime

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import (
    SQLiteCandleRepository,
    SQLiteTradeRepository,
)
from smartmoneyconcepts.dashboard.execution.paper import PaperTradingEngine
from smartmoneyconcepts.dashboard.execution.risk import RiskManager
from smartmoneyconcepts.dashboard.strategy.models import (
    Condition,
    ExitCondition,
    RiskConfig,
    Strategy,
    Trade,
)


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.risk = RiskManager(initial_balance=10000.0)

    def test_can_open_within_limits(self):
        ok, msg = self.risk.can_open_position(
            RiskConfig(max_positions=3), open_positions=1, side="buy"
        )
        self.assertTrue(ok)

    def test_cannot_exceed_max_positions(self):
        ok, msg = self.risk.can_open_position(
            RiskConfig(max_positions=2), open_positions=2, side="buy"
        )
        self.assertFalse(ok)

    def test_calculate_size(self):
        qty = self.risk.calculate_size(
            RiskConfig(position_size_pct=1.0),
            entry_price=100.0,
            sl_price=99.0,
        )
        expected = 10000.0 * 0.01 / 1.0
        self.assertAlmostEqual(qty, expected)

    def test_daily_loss_limit(self):
        risk_cfg = RiskConfig(max_daily_loss=100.0)
        trade = Trade(
            "test",
            "buy",
            0,
            datetime.now(),
            100,
            pnl=-60,
            status="closed",
            exit_price=99,
            quantity=1,
        )
        self.risk.record_trade(trade)
        ok, msg = self.risk.can_open_position(risk_cfg, 0, "buy")
        self.assertTrue(ok)

        trade2 = Trade(
            "test",
            "buy",
            0,
            datetime.now(),
            100,
            pnl=-50,
            status="closed",
            exit_price=98,
            quantity=1,
        )
        self.risk.record_trade(trade2)
        ok, msg = self.risk.can_open_position(risk_cfg, 0, "buy")
        self.assertFalse(ok)
        self.assertIn("daily loss", msg.lower())

    def test_update_balance(self):
        self.risk.update_balance(100)
        self.assertEqual(self.risk.balance, 10100.0)

    def test_negative_update_balance(self):
        self.risk.update_balance(-200)
        self.assertEqual(self.risk.balance, 9800.0)


class TestPaperTradingEngine(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.candle_repo = SQLiteCandleRepository(self.db)
        self.trade_repo = SQLiteTradeRepository(self.db)
        self.candle_repo.create_tables()
        self.candle_repo.create_tables_for_symbol("BTC/USDT")

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
        self.candle_repo.save_candles(candles)

        from smartmoneyconcepts.dashboard.engine.indicators import IndicatorService

        self.indicators = IndicatorService(self.candle_repo)
        self.engine = PaperTradingEngine(self.trade_repo, self.indicators)

    def tearDown(self):
        self.db.close()

    def test_start_stop(self):
        strategy = Strategy(
            name="test",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="bos", direction="bullish")],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
        )
        self.engine.start(strategy)
        self.assertTrue(self.engine.running)
        self.engine.stop()
        self.assertFalse(self.engine.running)

    def test_summary_returns_dict(self):
        summary = self.engine.get_summary()
        self.assertIn("balance", summary)
        self.assertIn("running", summary)
        self.assertEqual(summary["running"], False)

    def test_positions_empty_initially(self):
        self.assertEqual(self.engine.get_positions(), [])

    def test_exit_slippage_applied(self):
        from smartmoneyconcepts.dashboard.execution.paper import SLIPPAGE_PCT
        from smartmoneyconcepts.dashboard.execution.orders import Position

        pos = Position(
            symbol="BTC/USDT",
            side="buy",
            quantity=1,
            entry_price=100,
            current_price=100,
            sl_price=99,
            tp_price=105,
            strategy="test",
            mode="paper",
        )
        self.engine.positions.append(pos)
        candle = Candle(
            "BTC/USDT", datetime(2026, 1, 1, 10, 0), 98, 98.5, 97, 97.5, 1000, "1m"
        )
        self.engine._check_exit(pos, candle, 50)
        self.assertEqual(len(self.engine.positions), 0)
        expected_slippage = 99 * (1 - SLIPPAGE_PCT / 100)
        self.assertAlmostEqual(pos.realized_pnl, (expected_slippage - 100) * 1)

    def test_entry_no_slippage(self):
        from smartmoneyconcepts.dashboard.execution.orders import Order, OrderType

        order = Order(
            symbol="BTC/USDT",
            side="buy",
            order_type=OrderType.MARKET,
            quantity=0.1,
            price=100,
            strategy="test",
        )
        self.engine._fill_order(order, 100.0)
        self.assertEqual(order.avg_fill_price, 100.0)

    def test_trailing_stop_not_applied_in_paper(self):
        candle = Candle(
            "BTC/USDT", datetime(2026, 1, 1, 10, 5), 105, 110, 104, 108, 1000, "1m"
        )
        strategy = Strategy(
            name="ts",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[Condition(type="bos", direction="bullish")],
            exit_conditions=[ExitCondition(type="trailing_stop", trail_activation=2.0)],
        )
        self.engine.start(strategy)
        self.engine.on_candle(candle)
        self.assertTrue(self.engine.running)

    def test_multiple_positions_blocked_by_max(self):
        from smartmoneyconcepts.dashboard.execution.orders import Position

        strategy = Strategy(
            name="mp",
            timeframe="1m",
            symbol="BTC/USDT",
            entry_conditions=[
                Condition(
                    type="fvg_mitigation", direction="bullish", params={"lookback": 10}
                )
            ],
            exit_conditions=[ExitCondition(type="target", value=2.0)],
            risk=RiskConfig(position_size_pct=1.0, max_positions=1),
        )
        self.engine.positions.append(
            Position(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.1,
                entry_price=100,
                current_price=101,
                strategy="mp",
                mode="paper",
            )
        )
        ok, _ = self.engine.risk.can_open_position(
            strategy.risk, len(self.engine.positions), "buy"
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
