import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import SQLiteCandleRepository
from smartmoneyconcepts.dashboard.main import app, state


def seed_test_db(db):
    repo = SQLiteCandleRepository(db)
    repo.create_tables()
    repo.create_tables_for_symbol("BTC/USDT")
    candles = []
    base = datetime(2026, 5, 1, 0, 0)
    for i in range(200):
        candles.append(
            Candle(
                symbol="BTC/USDT",
                timestamp=base + timedelta(seconds=i * 60),
                open=50000.0 + i,
                high=50100.0 + i,
                low=49900.0 + i,
                close=50050.0 + i,
                volume=100.0,
                timeframe="1m",
            )
        )
    repo.save_candles(candles)
    return repo


class TestCandlesAPI(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db = sqlite3.connect(self._tmp.name, check_same_thread=False)
        self.repo = seed_test_db(self.db)
        state.candle_repo = self.repo
        state.db = self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        os.unlink(self._tmp.name)

    def test_get_candles(self):
        resp = self.client.get("/api/candles/BTC%2FUSDT?timeframe=1m&limit=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["symbol"], "BTC/USDT")
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["candles"]), 10)

    def test_get_candles_invalid_timeframe(self):
        resp = self.client.get("/api/candles/BTC%2FUSDT?timeframe=invalid")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.json())

    def test_get_indicators(self):
        resp = self.client.get("/api/indicators/BTC%2FUSDT?timeframe=1m&limit=200")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("fvg", data)
        self.assertIn("ob", data)
        self.assertEqual(data["symbol"], "BTC/USDT")

    def test_get_indicators_invalid_timeframe(self):
        resp = self.client.get("/api/indicators/BTC%2FUSDT?timeframe=invalid")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.json())

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


class TestIndicatorsAPIData(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db = sqlite3.connect(self._tmp.name, check_same_thread=False)
        self.repo = seed_test_db(self.db)
        state.candle_repo = self.repo
        state.db = self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        os.unlink(self._tmp.name)

    def test_fvg_in_response(self):
        resp = self.client.get("/api/indicators/BTC/USDT?timeframe=1m&limit=200")
        data = resp.json()
        fvg = data["fvg"]
        self.assertIn("FVG", fvg)
        self.assertEqual(len(fvg["FVG"]), 200)

    def test_ob_in_response(self):
        resp = self.client.get("/api/indicators/BTC/USDT?timeframe=1m&limit=200")
        data = resp.json()
        ob = data["ob"]
        self.assertIn("OB", ob)
        self.assertIn("Percentage", ob)

    def test_bos_choch_in_response(self):
        resp = self.client.get("/api/indicators/BTC/USDT?timeframe=1m&limit=200")
        data = resp.json()
        bc = data["bos_choch"]
        self.assertIn("BOS", bc)
        self.assertIn("CHOCH", bc)


if __name__ == "__main__":
    unittest.main()
