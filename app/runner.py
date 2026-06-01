"""Run the SMC engine in paper mode against a live exchange.

Usage:
    python -m app.runner --config config.yaml
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
import signal
from datetime import datetime
from pathlib import Path

import ccxt.async_support as ccxt_async

from app.brokers.paper import PaperBroker
from app.config import load_config
from app.db import init_db
from app.engine import StrategyEngine
from app.events import EventBus
from app.feed import MarketFeed
from app.indicators import IndicatorCache
from app.risk import RiskManager
from app.strategy import Strategy

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("smc.runner")


def _load_strategies(modules: list[str]) -> list[Strategy]:
    strats: list[Strategy] = []
    for dotted in modules:
        mod = importlib.import_module(dotted)
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
                strats.append(obj())
    return strats


async def _amain(config_path: Path, strategy_modules: list[str]) -> None:
    cfg = load_config(config_path)
    db_engine = init_db(cfg.data_dir / "smc.db")
    bus = EventBus()

    exchange_cls = getattr(ccxt_async, cfg.exchange)
    exchange = exchange_cls({"enableRateLimit": True})

    paper = PaperBroker(engine=db_engine,
                        starting_balance_quote=cfg.paper.starting_balance_quote,
                        fee_rate=cfg.paper.fee_rate,
                        slippage_bps=cfg.paper.slippage_bps)
    risk = RiskManager(engine=db_engine, risk=cfg.risk, paper=paper, live=None)

    strategies = _load_strategies(strategy_modules)
    if not strategies:
        raise RuntimeError("no strategies loaded")

    caches: dict[str, IndicatorCache] = {}
    feeds: list[MarketFeed] = []
    engine = StrategyEngine(bus=bus, risk=risk, indicator_caches=caches)
    for strat in strategies:
        key = f"{strat.symbol}|{strat.timeframe}"
        if key not in caches:
            caches[key] = IndicatorCache(swing_length=50)
            feeds.append(MarketFeed(
                exchange=exchange, symbol=strat.symbol, timeframe=strat.timeframe,
                poll_interval_seconds=cfg.poll_interval_seconds,
                engine=db_engine, bus=bus,
            ))
        engine.register(strat, mode="paper", overrides={})

    candle_q = bus.subscribe("candle")
    stop = asyncio.Event()

    def _sigterm(*_a: object) -> None:
        stop.set()

    try:
        signal.signal(signal.SIGTERM, _sigterm)
        signal.signal(signal.SIGINT, _sigterm)
    except ValueError:
        pass  # not in main thread (e.g., tests)

    feed_tasks = [asyncio.create_task(f.run()) for f in feeds]

    async def _consume() -> None:
        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(candle_q.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, tf = msg["symbol"], msg["timeframe"]
            risk.last_candle_ts = datetime.fromisoformat(msg["ts"])
            for f in feeds:
                if f.symbol == symbol and f.timeframe == tf:
                    engine.update_market(symbol, tf, f.dataframe())
                    await engine.run_once(symbol, tf, mark_price=msg["close"])
                    break

    consume_task = asyncio.create_task(_consume())
    await stop.wait()
    for f in feeds:
        f.stop()
    for t in feed_tasks:
        await t
    consume_task.cancel()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass
    db_engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--strategy", action="append", required=True,
                   help="Dotted module path, e.g. strategies.example_smc")
    args = p.parse_args()
    asyncio.run(_amain(args.config, args.strategy))


if __name__ == "__main__":
    main()
