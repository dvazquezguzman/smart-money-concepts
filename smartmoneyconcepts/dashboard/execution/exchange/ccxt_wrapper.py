import logging
from datetime import datetime
from typing import Optional

from .base import Exchange, ExchangeBalance, ExchangeOrderResult, ExchangePosition

logger = logging.getLogger(__name__)


class CCXTExchange(Exchange):
    def __init__(self, exchange_id: str, config: dict):
        self._exchange_id = exchange_id
        self._config = config
        self._exchange = None
        self._connected = False

    async def connect(self) -> bool:
        import ccxt.async_support as ccxt

        exchange_class = getattr(ccxt, self._exchange_id, None)
        if not exchange_class:
            logger.error("Unknown exchange: %s", self._exchange_id)
            return False

        try:
            self._exchange = exchange_class(self._config)
            await self._exchange.load_markets()
            self._connected = True
            logger.info("Connected to %s", self._exchange_id)
            return True
        except Exception as e:
            logger.error("Exchange connect failed: %s", e)
            self._connected = False
            return False

    async def disconnect(self):
        if self._exchange:
            await self._exchange.close()
        self._connected = False

    async def create_market_order(
        self, symbol: str, side: str, quantity: float, reduce_only: bool = False
    ) -> ExchangeOrderResult:
        params = {"reduceOnly": reduce_only} if reduce_only else {}
        order = await self._exchange.create_market_order(
            symbol, side, quantity, None, params
        )
        return self._to_order_result(order)

    async def create_limit_order(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> ExchangeOrderResult:
        order = await self._exchange.create_limit_order(symbol, side, quantity, price)
        return self._to_order_result(order)

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.warning("Cancel order failed: %s", e)
            return False

    async def get_order(self, order_id: str, symbol: str) -> ExchangeOrderResult:
        order = await self._exchange.fetch_order(order_id, symbol)
        return self._to_order_result(order)

    async def get_positions(
        self, symbol: Optional[str] = None
    ) -> list[ExchangePosition]:
        try:
            raw = await self._exchange.fetch_positions([symbol] if symbol else None)
        except Exception:
            raw = await self._exchange.fetch_balance()
            positions = []
            for cur, data in raw.get("total", {}).items():
                if data and data > 0:
                    positions.append(
                        ExchangePosition(
                            symbol=cur,
                            side="long",
                            quantity=data,
                            entry_price=0,
                            current_price=0,
                            unrealized_pnl=0,
                        )
                    )
            return positions

        return [
            ExchangePosition(
                symbol=p.get("symbol", ""),
                side="long" if p.get("side") == "long" else "short",
                quantity=float(p.get("contracts", 0) or 0),
                entry_price=float(p.get("entryPrice", 0) or 0),
                current_price=float(p.get("markPrice", 0) or 0),
                unrealized_pnl=float(p.get("unrealizedPnl", 0) or 0),
                liquidation_price=float(p["liquidationPrice"])
                if p.get("liquidationPrice")
                else None,
            )
            for p in raw
            if float(p.get("contracts", 0) or 0) > 0
        ]

    async def get_balance(self) -> ExchangeBalance:
        raw = await self._exchange.fetch_balance()
        total = float(raw.get("total", {}).get("USDT", 0) or 0)
        free = float(raw.get("free", {}).get("USDT", 0) or 0)
        used = float(raw.get("used", {}).get("USDT", 0) or 0)
        return ExchangeBalance(total=total, free=free, used=used)

    async def fetch_price(self, symbol: str) -> float:
        ticker = await self._exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    @property
    def name(self) -> str:
        return self._exchange_id

    @property
    def connected(self) -> bool:
        return self._connected

    def _to_order_result(self, order: dict) -> ExchangeOrderResult:
        return ExchangeOrderResult(
            order_id=str(order.get("id", "")),
            symbol=order.get("symbol", ""),
            side=order.get("side", ""),
            quantity=float(order.get("amount", 0) or 0),
            filled=float(order.get("filled", 0) or 0),
            price=float(order["price"]) if order.get("price") else None,
            average=float(order["average"]) if order.get("average") else None,
            status=order.get("status", "unknown"),
            timestamp=(
                datetime.fromtimestamp(order["timestamp"] / 1000)
                if order.get("timestamp")
                else None
            ),
        )
