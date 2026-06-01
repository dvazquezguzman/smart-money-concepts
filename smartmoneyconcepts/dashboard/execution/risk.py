from datetime import date, datetime
from typing import Optional

from ..strategy.models import RiskConfig, Trade


class RiskManager:
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self._daily_trades: dict[date, list[Trade]] = {}

    def can_open_position(
        self,
        risk: RiskConfig,
        open_positions: int,
        side: str,
    ) -> tuple[bool, str]:
        if open_positions >= risk.max_positions:
            return False, f"max positions reached ({risk.max_positions})"

        if risk.max_daily_loss is not None:
            today = date.today()
            daily_pnl = sum(
                t.pnl or 0
                for t in self._daily_trades.get(today, [])
                if t.status == "closed" and t.pnl is not None
            )
            if daily_pnl <= -risk.max_daily_loss:
                return False, f"daily loss limit reached ({daily_pnl:.2f})"

        return True, ""

    def calculate_size(
        self,
        risk: RiskConfig,
        entry_price: float,
        sl_price: float,
    ) -> float:
        risk_amount = self.balance * (risk.position_size_pct / 100.0)
        price_risk = abs(entry_price - sl_price)
        if price_risk <= 0:
            return 0.0
        quantity = risk_amount / price_risk
        return round(quantity, 6)

    def record_trade(self, trade: Trade):
        if trade.exit_time:
            d = trade.exit_time.date()
        else:
            d = date.today()
        self._daily_trades.setdefault(d, []).append(trade)

    def update_balance(self, pnl: float):
        self.balance += pnl

    def reset_daily(self):
        today = date.today()
        self._daily_trades.pop(today, None)
