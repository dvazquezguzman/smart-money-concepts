import itertools
import logging
from datetime import datetime

import numpy as np

from ..db.base import BaseCandleRepository
from ..engine.indicators import IndicatorService
from .backtest import Backtester
from .models import ComboResult, OptimizerResult
from .parser import ParamRange, apply_params, detect_ranges, parse_strategy

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    def __init__(self, repo: BaseCandleRepository, indicator_service: IndicatorService):
        self.backtester = Backtester(repo, indicator_service)

    def optimize(
        self,
        strategy_yaml: str,
        start: datetime,
        end: datetime,
        initial_capital: float = 10000.0,
        max_combos: int = 500,
    ) -> OptimizerResult:
        base = parse_strategy(strategy_yaml)
        ranges = detect_ranges(strategy_yaml)

        if not ranges:
            result = self.backtester.run(base, start, end, initial_capital)
            combo = self._backtest_to_combo({}, result)
            return OptimizerResult(
                strategy_name=base.name,
                symbol=base.symbol,
                timeframe=base.timeframe,
                total_combos=1,
                combos_run=1,
                results=[combo],
            )

        all_values = [r.values for r in ranges]
        total = np.prod([len(v) for v in all_values])
        total = int(total)

        if total > max_combos:
            sampled = self._sample_combos(all_values, max_combos)
            combos_to_run = sampled
        else:
            combos_to_run = list(itertools.product(*all_values))

        results = []
        for combo in combos_to_run:
            modified_yaml = apply_params(strategy_yaml, ranges, combo)
            strategy = parse_strategy(modified_yaml)
            try:
                bt = self.backtester.run(strategy, start, end, initial_capital)
                results.append(
                    self._backtest_to_combo(
                        dict(zip([str(r.path) for r in ranges], combo)), bt
                    )
                )
            except Exception as e:
                logger.warning("Combo %s failed: %s", combo, e)

        return OptimizerResult(
            strategy_name=base.name,
            symbol=base.symbol,
            timeframe=base.timeframe,
            total_combos=total,
            combos_run=len(results),
            results=results,
        )

    def _backtest_to_combo(self, params: dict, bt) -> ComboResult:
        return ComboResult(
            params=params,
            total_trades=bt.total_trades,
            wins=bt.wins,
            losses=bt.losses,
            win_rate=bt.win_rate,
            total_pnl=bt.total_pnl,
            profit_factor=bt.profit_factor,
            max_drawdown=bt.max_drawdown,
            sharpe=bt.sharpe,
            avg_win=bt.avg_win,
            avg_loss=bt.avg_loss,
            largest_win=bt.largest_win,
            largest_loss=bt.largest_loss,
            avg_bars_held=bt.avg_bars_held,
        )

    def _sample_combos(self, all_values: list[list], n: int) -> list[tuple]:
        linspaced = []
        for vals in all_values:
            if len(vals) <= n:
                linspaced.append(vals)
            else:
                indices = np.linspace(0, len(vals) - 1, n, dtype=int)
                linspaced.append([vals[i] for i in indices])

        return list(itertools.product(*linspaced))[:n]
