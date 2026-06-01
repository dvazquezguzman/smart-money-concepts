import sqlite3
import unittest
from datetime import datetime, timedelta

from smartmoneyconcepts.dashboard.db.sqlite import SQLiteCandleRepository
from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.engine.indicators import IndicatorService


class TestIndicatorService(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteCandleRepository(self.db)
        self.repo.create_tables()
        self.repo.create_tables_for_symbol("BTC/USDT")
        self._seed_data()

    def tearDown(self):
        self.db.close()

    def _seed_data(self):
        candles = []
        base = datetime(2026, 5, 1, 0, 0)
        open_px = 50000.0
        for i in range(500):
            open_px = open_px + (i % 50 - 25)
            high = open_px + abs(i % 30)
            low = open_px - abs(i % 20)
            close = open_px + (1 if i % 2 == 0 else -1) * abs(i % 15)
            candles.append(
                Candle(
                    symbol="BTC/USDT",
                    timestamp=base + timedelta(seconds=i * 60),
                    open=round(open_px, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    volume=round(100 + (i % 50), 2),
                    timeframe="1m",
                )
            )

        self.repo.save_candles(candles)
        self.service = IndicatorService(self.repo)

    def test_calculate_returns_expected_keys(self):
        result = self.service.calculate("BTC/USDT", "1m", 200)
        expected_keys = {
            "fvg",
            "ob",
            "bos_choch",
            "liquidity",
            "swings",
            "retracements",
            "sessions_london",
            "previous_high_low",
            "candle_count",
        }
        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertEqual(result["candle_count"], 200)

    def test_calculate_not_enough_data(self):
        result = self.service.calculate("BTC/USDT", "1m", 5)
        self.assertIn("error", result)

    def test_cache_returns_same_result(self):
        result1 = self.service.calculate("BTC/USDT", "1m", 200)
        result2 = self.service.calculate("BTC/USDT", "1m", 200)
        self.assertEqual(result1["candle_count"], result2["candle_count"])

    def test_invalidate_cache(self):
        result1 = self.service.calculate("BTC/USDT", "1m", 200)
        self.service.invalidate_cache("BTC/USDT")
        result2 = self.service.calculate("BTC/USDT", "1m", 200)
        self.assertEqual(result1["candle_count"], result2["candle_count"])

    def test_fvg_has_expected_shape(self):
        result = self.service.calculate("BTC/USDT", "1m", 200)
        fvg = result["fvg"]
        self.assertIn("FVG", fvg)
        self.assertIn("Top", fvg)
        self.assertIn("Bottom", fvg)
        self.assertEqual(len(fvg["FVG"]), 200)

    def test_ob_has_expected_shape(self):
        result = self.service.calculate("BTC/USDT", "1m", 200)
        ob = result["ob"]
        self.assertIn("OB", ob)
        self.assertIn("Percentage", ob)
        self.assertEqual(len(ob["OB"]), 200)

    def test_bos_choch_has_expected_shape(self):
        result = self.service.calculate("BTC/USDT", "1m", 200)
        bc = result["bos_choch"]
        self.assertIn("BOS", bc)
        self.assertIn("CHOCH", bc)
        self.assertEqual(len(bc["BOS"]), 200)

    def test_liquidity_has_expected_shape(self):
        result = self.service.calculate("BTC/USDT", "1m", 200)
        liq = result["liquidity"]
        self.assertIn("Liquidity", liq)
        self.assertIn("Level", liq)
        self.assertEqual(len(liq["Liquidity"]), 200)


if __name__ == "__main__":
    unittest.main()
