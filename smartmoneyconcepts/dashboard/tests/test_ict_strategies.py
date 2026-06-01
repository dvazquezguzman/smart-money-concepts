import csv
import json
import os
import sqlite3
import unittest
from datetime import datetime

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import SQLiteCandleRepository
from smartmoneyconcepts.dashboard.engine.indicators import IndicatorService
from smartmoneyconcepts.dashboard.strategy.backtest import Backtester
from smartmoneyconcepts.dashboard.strategy.parser import parse_strategy

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "scenarios")

SCENARIOS = [
    {
        "name": "FVG Breaker",
        "csv": "ict_fvg_breaker.csv",
        "expected": "ict_fvg_breaker_expected.json",
        "template_file": "ict-fvg-breaker.yaml",
    },
    {
        "name": "FVG-OB Combo",
        "csv": "ict_fvg_orderblock_combo.csv",
        "expected": "ict_fvg_orderblock_combo_expected.json",
        "template_file": "ict-fvg-orderblock-combo.yaml",
    },
    {
        "name": "OB-Liquidity Sweep",
        "csv": "ict_ob_liquidity_sweep.csv",
        "expected": "ict_ob_liquidity_sweep_expected.json",
        "template_file": "ict-ob-liquidity-sweep.yaml",
    },
    {
        "name": "CHOCH Breaker",
        "csv": "ict_choch_breaker.csv",
        "expected": "ict_choch_breaker_expected.json",
        "template_file": "ict-choCH-breaker.yaml",
    },
    {
        "name": "Asian Range Breakout",
        "csv": "ict_asian_range_breakout.csv",
        "expected": "ict_asian_range_breakout_expected.json",
        "template_file": "ict-asian-range-breakout.yaml",
    },
]

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "smartmoneyconcepts",
    "dashboard",
    "strategy",
    "templates",
)


def _load_csv(path):
    candles = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append(
                Candle(
                    symbol="BTC/USDT",
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    timeframe="5m",
                )
            )
    return candles


def _load_expected(path):
    with open(path) as f:
        return json.load(f)


def _load_strategy_template(template_file):
    path = os.path.join(TEMPLATES_DIR, template_file)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()


class TestICTScenarios(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteCandleRepository(self.db)
        self.repo.create_tables()
        self.repo.create_tables_for_symbol("BTC/USDT")
        self.indicators = IndicatorService(self.repo)
        self.backtester = Backtester(self.repo, self.indicators)

    def tearDown(self):
        self.db.close()

    def _run_scenario(self, scenario):
        csv_path = os.path.join(FIXTURES_DIR, scenario["csv"])
        expected_path = os.path.join(FIXTURES_DIR, scenario["expected"])
        self.assertTrue(os.path.exists(csv_path), f"Missing CSV: {csv_path}")
        self.assertTrue(
            os.path.exists(expected_path), f"Missing expected: {expected_path}"
        )

        candles = _load_csv(csv_path)
        self.repo.save_candles(candles)

        expected = _load_expected(expected_path)

        yaml_str = _load_strategy_template(scenario["template_file"])
        if yaml_str is None:
            self.skipTest(f"Template {scenario['template_file']} not found")

        strategy = parse_strategy(yaml_str)
        strategy.symbol = "BTC/USDT"

        start = candles[0].timestamp
        end = candles[-1].timestamp

        result = self.backtester.run(strategy, start, end, initial_capital=10000)
        self.assertEqual(result.strategy, expected.get("strategy", strategy.name))
        self.assertEqual(result.symbol, "BTC/USDT")
        self.assertGreaterEqual(result.total_trades, expected["min_trades"])
        self.assertLessEqual(result.total_trades, expected["max_trades"])

        if result.total_trades > 0:
            self.assertGreaterEqual(result.wins + result.losses, 1)
            self.assertAlmostEqual(
                result.win_rate, result.wins / result.total_trades, places=4
            )
            return result
        return result


for scenario in SCENARIOS:

    def make_test(s):
        def test(self):
            self._run_scenario(s)

        return test

    setattr(
        TestICTScenarios,
        f"test_{scenario['name'].lower().replace('-', '_').replace(' ', '_')}",
        make_test(scenario),
    )


class TestICTFixturesExist(unittest.TestCase):
    def test_all_fixture_files_exist(self):
        for s in SCENARIOS:
            csv_path = os.path.join(FIXTURES_DIR, s["csv"])
            expected_path = os.path.join(FIXTURES_DIR, s["expected"])
            self.assertTrue(os.path.exists(csv_path), f"Missing {s['csv']}")
            self.assertTrue(os.path.exists(expected_path), f"Missing {s['expected']}")
            self.assertGreater(os.path.getsize(csv_path), 0, f"Empty {s['csv']}")

    def test_all_templates_exist(self):
        for s in SCENARIOS:
            path = os.path.join(TEMPLATES_DIR, s["template_file"])
            self.assertTrue(
                os.path.exists(path), f"Missing template {s['template_file']}"
            )


if __name__ == "__main__":
    unittest.main()
