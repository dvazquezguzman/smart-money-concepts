import asyncio
import sqlite3
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from smartmoneyconcepts.dashboard.db.base import Candle
from smartmoneyconcepts.dashboard.db.sqlite import (
    SQLiteCandleRepository,
    SQLiteTradeRepository,
)
from smartmoneyconcepts.dashboard.execution.live import LiveTradingEngine
from smartmoneyconcepts.dashboard.execution.exchange.base import (
    Exchange,
    ExchangeBalance,
    ExchangeOrderResult,
    ExchangePosition,
)
from smartmoneyconcepts.dashboard.strategy.models import (
    Condition,
    ExitCondition,
    RiskConfig,
    Strategy,
)


class MockExchange(Exchange):
    def __init__(self):
        self._connected = False

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def disconnect(self):
        self._connected = False

    async def create_market_order(self, symbol, side, quantity, reduce_only=False):
        return ExchangeOrderResult(
            order_id="mock-1",
            symbol=symbol,
            side=side,
            quantity=quantity,
            filled=quantity,
            price=100.0,
            average=100.0,
            status="closed",
        )

    async def create_limit_order(self, symbol, side, quantity, price):
        return ExchangeOrderResult(
            order_id="mock-2",
            symbol=symbol,
            side=side,
            quantity=quantity,
            filled=0,
            price=price,
            average=None,
            status="open",
        )

    async def cancel_order(self, order_id, symbol):
        return True

    async def get_order(self, order_id, symbol):
        return ExchangeOrderResult(
            order_id=order_id,
            symbol=symbol,
            side="buy",
            quantity=0,
            filled=0,
            price=None,
            average=None,
            status="closed",
        )

    async def get_positions(self, symbol=None):
        return []

    async def get_balance(self):
        return ExchangeBalance(total=10000, free=9000, used=1000)

    async def fetch_price(self, symbol):
        return 50000.0

    @property
    def name(self):
        return "mock"

    @property
    def connected(self):
        return self._connected


class TestLiveTradingEngine(unittest.TestCase):
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
        self.exchange = MockExchange()
        self.engine = LiveTradingEngine(
            exchange=self.exchange,
            trade_repo=self.trade_repo,
            indicator_service=self.indicators,
        )

    def tearDown(self):
        self.db.close()

    def test_initial_state(self):
        self.assertFalse(self.engine.running)
        self.assertFalse(self.engine.connected)

    def test_summary_returns_dict(self):
        summary = self.engine.get_summary()
        self.assertIn("running", summary)
        self.assertIn("exchange", summary)
        self.assertFalse(summary["running"])

    def test_positions_empty_initially(self):
        self.assertEqual(self.engine.get_positions(), [])

    def test_exchange_connect(self):
        async def run():
            await self.engine.exchange.connect()
            self.assertTrue(self.engine.exchange.connected)
            await self.engine.exchange.disconnect()

        asyncio.run(run())

    def test_exchange_balance(self):
        async def run():
            bal = await self.engine.exchange.get_balance()
            self.assertEqual(bal.total, 10000)
            self.assertEqual(bal.free, 9000)

        asyncio.run(run())

    def test_exchange_create_market_order(self):
        async def run():
            result = await self.engine.exchange.create_market_order(
                "BTC/USDT", "buy", 0.01
            )
            self.assertEqual(result.symbol, "BTC/USDT")
            self.assertEqual(result.status, "closed")

        asyncio.run(run())

    def test_exchange_fetch_price(self):
        async def run():
            price = await self.engine.exchange.fetch_price("BTC/USDT")
            self.assertEqual(price, 50000.0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
