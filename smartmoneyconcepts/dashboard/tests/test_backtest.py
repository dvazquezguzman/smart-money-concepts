import unittest
from datetime import datetime

from smartmoneyconcepts.dashboard.strategy.backtest import Backtester
from smartmoneyconcepts.dashboard.strategy.models import BacktestResult, Trade


class _StubRepo:
    def get_candles(self, symbol, timeframe, limit=500, since=None):
        return []


class _StubIndicators:
    def calculate(self, symbol, timeframe, limit=500):
        return {
            "fvg": {"FVG": [], "Top": [], "Bottom": []},
            "ob": {"OB": [], "Top": [], "Bottom": []},
            "bos_choch": {"BOS": [], "CHOCH": []},
            "liquidity": {"Liquidity": [], "Level": []},
            "swings": {"High": [], "Low": []},
        }


class TestBacktestMetrics(unittest.TestCase):
    def setUp(self):
        repo = _StubRepo()
        indicators = _StubIndicators()
        self.bt = Backtester(repo, indicators)

    def test_win_rate_3_of_4(self):
        trades = [
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=110,
                exit_reason="target",
                quantity=1,
                pnl=10,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=110,
                exit_reason="target",
                quantity=1,
                pnl=10,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=110,
                exit_reason="target",
                quantity=1,
                pnl=10,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=90,
                exit_reason="stop_loss",
                quantity=1,
                pnl=-10,
                status="closed",
            ),
        ]
        result = self.bt._compute_results(
            type("S", (), {"name": "t", "symbol": "X", "timeframe": "1m"})(),
            trades,
            10000,
        )
        self.assertEqual(result.total_trades, 4)
        self.assertEqual(result.wins, 3)
        self.assertEqual(result.losses, 1)
        self.assertAlmostEqual(result.win_rate, 0.75)

    def test_profit_factor(self):
        trades = [
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=200,
                exit_reason="target",
                quantity=1,
                pnl=100,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=200,
                exit_reason="target",
                quantity=1,
                pnl=200,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=50,
                exit_reason="stop_loss",
                quantity=1,
                pnl=-50,
                status="closed",
            ),
            Trade(
                "s",
                "buy",
                0,
                datetime.now(),
                100,
                exit_index=1,
                exit_price=50,
                exit_reason="stop_loss",
                quantity=1,
                pnl=-50,
                status="closed",
            ),
        ]
        result = self.bt._compute_results(
            type("S", (), {"name": "t", "symbol": "X", "timeframe": "1m"})(),
            trades,
            10000,
        )
        self.assertAlmostEqual(result.profit_factor, 300.0 / 100.0)

    def test_max_drawdown(self):
        equity = [10000, 10500, 10200, 9500, 10100]
        dd = self.bt._calc_max_drawdown(equity)
        expected = (10500 - 9500) / 10500
        self.assertAlmostEqual(dd, expected, places=4)

    def test_sharpe(self):
        equity = [10000, 10100, 10200, 10300]
        sharpe = self.bt._calc_sharpe(equity)
        self.assertGreater(sharpe, 0)

    def test_empty_trades(self):
        result = BacktestResult(
            "t", "X", "1m", 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, []
        )
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.win_rate, 0.0)
