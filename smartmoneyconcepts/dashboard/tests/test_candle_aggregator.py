import unittest
from datetime import datetime, timedelta

from smartmoneyconcepts.dashboard.engine.candle_aggregator import (
    aggregate_candles,
    get_available_timeframes,
    round_to_timeframe,
)
from smartmoneyconcepts.dashboard.db.base import Candle


class TestAggregator(unittest.TestCase):
    def setUp(self):
        base = datetime(2026, 5, 1, 0, 0)
        self.one_min_candles = [
            Candle(
                "BTC/USDT",
                base + timedelta(minutes=i),
                100 + i,
                105 + i,
                99 + i,
                104 + i,
                1000,
                "1m",
            )
            for i in range(10)
        ]

    def test_round_to_timeframe(self):
        ts = datetime(2026, 5, 1, 0, 3, 45)
        rounded = round_to_timeframe(ts, 5)
        self.assertEqual(rounded.minute, 0)
        self.assertEqual(rounded.second, 0)

        ts = datetime(2026, 5, 1, 0, 7, 0)
        rounded = round_to_timeframe(ts, 5)
        self.assertEqual(rounded.minute, 5)

    def test_aggregate_to_5m(self):
        result = aggregate_candles(self.one_min_candles, "5m")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].timeframe, "5m")
        self.assertEqual(result[0].symbol, "BTC/USDT")
        self.assertEqual(result[0].open, 100)
        self.assertEqual(result[0].close, 108)

    def test_aggregate_volume(self):
        result = aggregate_candles(self.one_min_candles, "5m")
        self.assertEqual(result[0].volume, 5000)

    def test_empty_input(self):
        result = aggregate_candles([], "5m")
        self.assertEqual(result, [])

    def test_invalid_timeframe(self):
        with self.assertRaises(ValueError):
            aggregate_candles(self.one_min_candles, "invalid")

    def test_get_available_timeframes(self):
        timeframes = get_available_timeframes()
        self.assertIn("1m", timeframes)
        self.assertIn("5m", timeframes)
        self.assertIn("15m", timeframes)
        self.assertIn("1H", timeframes)
        self.assertIn("4H", timeframes)


if __name__ == "__main__":
    unittest.main()
