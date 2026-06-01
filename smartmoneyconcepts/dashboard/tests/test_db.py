import sqlite3
import unittest
from datetime import datetime

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import (
    SQLiteCandleRepository,
    SQLiteConfigRepository,
    SQLiteStrategyRepository,
    SQLiteTradeRepository,
)


class TestCandleRepository(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteCandleRepository(self.db)
        self.repo.create_tables()
        self.repo.create_tables_for_symbol("BTC/USDT")

    def tearDown(self):
        self.db.close()

    def test_save_and_get_candles(self):
        candles = [
            Candle(
                symbol="BTC/USDT",
                timestamp=datetime(2026, 5, 1, 0, 0),
                open=100.0,
                high=105.0,
                low=99.0,
                close=104.0,
                volume=1000.0,
                timeframe="1m",
            ),
            Candle(
                symbol="BTC/USDT",
                timestamp=datetime(2026, 5, 1, 0, 1),
                open=104.0,
                high=106.0,
                low=103.0,
                close=105.0,
                volume=800.0,
                timeframe="1m",
            ),
        ]
        self.repo.save_candles(candles)
        result = self.repo.get_candles("BTC/USDT", "1m")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].symbol, "BTC/USDT")
        self.assertEqual(result[0].open, 100.0)
        self.assertEqual(result[0].close, 104.0)
        self.assertEqual(result[1].close, 105.0)

    def test_get_with_limit(self):
        candles = [
            Candle(
                symbol="BTC/USDT",
                timestamp=datetime(2026, 5, 1, 0, i),
                open=100.0 + i,
                high=105.0 + i,
                low=99.0 + i,
                close=104.0 + i,
                volume=1000.0,
                timeframe="1m",
            )
            for i in range(10)
        ]
        self.repo.save_candles(candles)
        result = self.repo.get_candles("BTC/USDT", "1m", limit=3)
        self.assertEqual(len(result), 3)

    def test_get_last_candle_empty(self):
        result = self.repo.get_last_candle("BTC/USDT", "1m")
        self.assertIsNone(result)

    def test_get_last_candle(self):
        candles = [
            Candle(
                symbol="BTC/USDT",
                timestamp=datetime(2026, 5, 1, 0, 0),
                open=100.0,
                high=105.0,
                low=99.0,
                close=104.0,
                volume=1000.0,
                timeframe="1m",
            ),
        ]
        self.repo.save_candles(candles)
        result = self.repo.get_last_candle("BTC/USDT", "1m")
        self.assertIsNotNone(result)
        self.assertEqual(result.close, 104.0)

    def test_delete_duplicates(self):
        self.repo.save_candles(
            [
                Candle("BTC/USDT", datetime(2026, 5, 1), 100, 105, 99, 104, 1000, "1m"),
            ]
        )
        self.repo.save_candles(
            [
                Candle("BTC/USDT", datetime(2026, 5, 1), 100, 105, 99, 104, 1000, "1m"),
            ]
        )
        self.repo.delete_duplicates("BTC/USDT", "1m")
        remaining = self.repo.get_candles("BTC/USDT", "1m")
        self.assertEqual(len(remaining), 1)


class TestStrategyRepository(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteStrategyRepository(self.db)
        SQLiteCandleRepository(self.db).create_tables()

    def tearDown(self):
        self.db.close()

    def test_save_and_get_strategy(self):
        self.repo.save_strategy("test", "name: test\ntimeframe: 5m")
        result = self.repo.get_strategy(1)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test")

    def test_list_strategies(self):
        self.repo.save_strategy("strat1", "name: strat1")
        self.repo.save_strategy("strat2", "name: strat2")
        strategies = self.repo.list_strategies()
        self.assertEqual(len(strategies), 2)

    def test_delete_strategy(self):
        self.repo.save_strategy("test", "name: test")
        self.repo.delete_strategy(1)
        result = self.repo.get_strategy(1)
        self.assertIsNone(result)


class TestConfigRepository(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteConfigRepository(self.db)
        SQLiteCandleRepository(self.db).create_tables()

    def tearDown(self):
        self.db.close()

    def test_save_and_get_config(self):
        self.repo.save_config("exchange_id", "binance")
        result = self.repo.get_config("exchange_id")
        self.assertEqual(result, "binance")

    def test_get_config_missing(self):
        result = self.repo.get_config("nonexistent")
        self.assertIsNone(result)

    def test_overwrite_config(self):
        self.repo.save_config("key", "value1")
        self.repo.save_config("key", "value2")
        result = self.repo.get_config("key")
        self.assertEqual(result, "value2")


class TestTradeRepository(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.repo = SQLiteTradeRepository(self.db)
        SQLiteCandleRepository(self.db).create_tables()

    def tearDown(self):
        self.db.close()

    def test_save_trade(self):
        self.repo.save_trade(
            {
                "symbol": "BTC/USDT",
                "side": "buy",
                "entry_price": 50000.0,
                "quantity": 0.1,
                "entry_index": 100,
                "mode": "paper",
            }
        )
        trades = self.repo.get_trades(mode="paper")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["status"], "open")

    def test_get_open_positions(self):
        self.repo.save_trade(
            {
                "symbol": "BTC/USDT",
                "side": "buy",
                "entry_price": 50000.0,
                "quantity": 0.1,
                "entry_index": 100,
                "mode": "paper",
            }
        )
        positions = self.repo.get_open_positions(mode="paper")
        self.assertEqual(len(positions), 1)


if __name__ == "__main__":
    unittest.main()
