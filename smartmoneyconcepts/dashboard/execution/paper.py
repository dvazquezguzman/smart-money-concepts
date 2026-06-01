import logging
from datetime import datetime
from typing import Optional

from ..db.base import BaseTradeRepository, Candle
from ..engine.indicators import IndicatorService
from ..strategy.evaluator import StrategyEvaluator
from ..strategy.models import Strategy, Trade
from .orders import Order, OrderSide, OrderStatus, OrderType, Position
from .risk import RiskManager

logger = logging.getLogger(__name__)

SLIPPAGE_PCT = 0.05


class PaperTradingEngine:
    def __init__(
        self,
        trade_repo: BaseTradeRepository,
        indicator_service: IndicatorService,
        initial_balance: float = 10000.0,
    ):
        self.trade_repo = trade_repo
        self.indicators = indicator_service
        self.evaluator = StrategyEvaluator()
        self.risk = RiskManager(initial_balance)
        self.positions: list[Position] = []
        self.order_history: list[Order] = []
        self._running = False
        self._strategy: Optional[Strategy] = None
        self._order_id_seq = 0

    @property
    def balance(self) -> float:
        return self.risk.balance

    @property
    def running(self) -> bool:
        return self._running

    def start(self, strategy: Strategy):
        self._strategy = strategy
        self._running = True
        logger.info("Paper trading started for %s", strategy.name)

    def stop(self):
        self._running = False
        logger.info("Paper trading stopped")

    def on_candle(self, candle: Candle):
        if not self._running or not self._strategy:
            return
        if candle.symbol != self._strategy.symbol:
            return

        indicators = self.indicators.calculate(
            self._strategy.symbol,
            self._strategy.timeframe,
            limit=500,
        )
        if "error" in indicators:
            return

        candles = self.indicators.repo.get_candles(
            self._strategy.symbol,
            self._strategy.timeframe,
            limit=500,
        )
        if not candles:
            return

        idx = len(candles) - 1

        self._check_exits(candle, idx)
        self._check_entry(candle, indicators, idx, candles)
        self._update_positions(candle)

    def _check_exit(self, pos: Position, candle: Candle, idx: int) -> Optional[str]:
        if pos.side == "buy":
            if pos.sl_price and candle.low <= pos.sl_price:
                fill = pos.sl_price * (1 - SLIPPAGE_PCT / 100)
                self._close_position(pos, idx, fill, candle.timestamp, "stop_loss")
                return "stop_loss"
            if pos.tp_price and candle.high >= pos.tp_price:
                fill = pos.tp_price * (1 + SLIPPAGE_PCT / 100)
                self._close_position(pos, idx, fill, candle.timestamp, "take_profit")
                return "take_profit"
        else:
            if pos.sl_price and candle.high >= pos.sl_price:
                fill = pos.sl_price * (1 + SLIPPAGE_PCT / 100)
                self._close_position(pos, idx, fill, candle.timestamp, "stop_loss")
                return "stop_loss"
            if pos.tp_price and candle.low <= pos.tp_price:
                fill = pos.tp_price * (1 - SLIPPAGE_PCT / 100)
                self._close_position(pos, idx, fill, candle.timestamp, "take_profit")
                return "take_profit"
        return None

    def _check_exits(self, candle: Candle, idx: int):
        for pos in list(self.positions):
            self._check_exit(pos, candle, idx)

    def _check_entry(
        self,
        candle: Candle,
        indicators: dict,
        idx: int,
        candles: list[Candle],
    ):
        if not self._strategy:
            return

        can, reason = self.risk.can_open_position(
            self._strategy.risk,
            len(self.positions),
            candle.close > candle.open and "buy" or "sell",
        )
        if not can:
            return

        side = self.evaluator._check_entry(
            candle, self._strategy, indicators, idx, candles
        )
        if not side:
            return

        pos = self.evaluator._open_position(
            self._strategy, candle, idx, side, indicators
        )
        if not pos:
            return

        qty = self.risk.calculate_size(
            self._strategy.risk, pos.trade.entry_price, pos.sl_price
        )
        if qty <= 0:
            return

        order = Order(
            symbol=candle.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=qty,
            price=candle.close,
            strategy=self._strategy.name,
        )
        self._fill_order(order, candle.close)

        position = Position(
            symbol=candle.symbol,
            side=side,
            quantity=qty,
            entry_price=order.avg_fill_price or candle.close,
            current_price=candle.close,
            sl_price=pos.sl_price,
            tp_price=pos.tp_price,
            strategy=self._strategy.name,
            mode="paper",
        )
        self.positions.append(position)

        logger.info(
            "Paper %s %.4f @ %.2f sl=%.2f tp=%.2f",
            side,
            qty,
            position.entry_price,
            pos.sl_price,
            pos.tp_price,
        )

    def _close_position(
        self,
        pos: Position,
        idx: int,
        exit_price: float,
        exit_time: datetime,
        reason: str,
    ):
        if pos.side == "buy":
            pnl = (exit_price - pos.entry_price) * pos.quantity
        else:
            pnl = (pos.entry_price - exit_price) * pos.quantity

        pos.realized_pnl = pnl
        pos.current_price = exit_price
        self.risk.update_balance(pnl)

        trade = Trade(
            strategy=pos.strategy,
            side=pos.side,
            entry_index=0,
            entry_time=pos.entry_time,
            entry_price=pos.entry_price,
            exit_index=idx,
            exit_time=exit_time,
            exit_price=exit_price,
            exit_reason=reason,
            quantity=pos.quantity,
            pnl=pnl,
            status="closed",
        )
        self.risk.record_trade(trade)
        self._save_trade(trade)
        self.positions.remove(pos)

        logger.info("Paper closed %s pnl=%.2f reason=%s", pos.side, pnl, reason)

    def _fill_order(self, order: Order, price: float):
        self._order_id_seq += 1
        order.order_id = self._order_id_seq
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.avg_fill_price = price
        order.filled_at = datetime.now()
        self.order_history.append(order)

    def _save_trade(self, trade: Trade):
        try:
            self.trade_repo.save_trade(
                {
                    "symbol": self._strategy.symbol if self._strategy else "",
                    "side": trade.side,
                    "entry_price": trade.entry_price,
                    "quantity": trade.quantity,
                    "entry_index": trade.entry_index,
                    "mode": "paper",
                }
            )
        except Exception as e:
            logger.error("Failed to save trade: %s", e)

    def _update_positions(self, candle: Candle):
        for pos in self.positions:
            pos.current_price = candle.close
            if pos.side == "buy":
                pos.unrealized_pnl = (candle.close - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - candle.close) * pos.quantity

    def get_positions(self) -> list[dict]:
        return [
            {
                "symbol": p.symbol,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": round(p.unrealized_pnl, 2),
                "realized_pnl": round(p.realized_pnl, 2),
                "sl_price": p.sl_price,
                "tp_price": p.tp_price,
                "entry_time": p.entry_time.isoformat(),
                "strategy": p.strategy,
            }
            for p in self.positions
        ]

    def get_summary(self) -> dict:
        total_realized = sum(p.realized_pnl for p in self.positions)
        total_unrealized = sum(p.unrealized_pnl for p in self.positions)
        return {
            "balance": round(self.balance, 2),
            "open_positions": len(self.positions),
            "realized_pnl": round(total_realized, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "total_equity": round(self.balance + total_unrealized, 2),
            "running": self._running,
        }
