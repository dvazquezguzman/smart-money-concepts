import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.base import (
    BaseCandleRepository,
    BaseConfigRepository,
    BaseStrategyRepository,
    BaseTradeRepository,
)
from .db.sqlite import (
    SQLiteCandleRepository,
    SQLiteConfigRepository,
    SQLiteStrategyRepository,
    SQLiteTradeRepository,
)
from .engine.data import CCXTDataEngine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class AppState:
    db: sqlite3.Connection
    candle_repo: BaseCandleRepository
    strategy_repo: BaseStrategyRepository
    trade_repo: BaseTradeRepository
    config_repo: BaseConfigRepository
    data_engine: CCXTDataEngine


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = Path("dashboard.db")
    state.db = sqlite3.connect(str(db_path), check_same_thread=False, timeout=10)
    state.db.execute("PRAGMA journal_mode=WAL")
    state.db.execute("PRAGMA busy_timeout=5000")
    state.db.execute("PRAGMA foreign_keys=ON")

    state.candle_repo = SQLiteCandleRepository(state.db)
    state.strategy_repo = SQLiteStrategyRepository(state.db)
    state.trade_repo = SQLiteTradeRepository(state.db)
    state.config_repo = SQLiteConfigRepository(state.db)
    state.candle_repo.create_tables()

    exchange_id = state.config_repo.get_config("exchange_id") or "binance"
    symbols_str = state.config_repo.get_config("symbols") or '["BTC/USDT"]'

    import json

    symbols = json.loads(symbols_str)

    state.data_engine = CCXTDataEngine(
        exchange_id=exchange_id,
        symbols=symbols,
        repo=state.candle_repo,
    )

    await state.data_engine.start()
    logger.info("Dashboard started")

    yield

    await state.data_engine.stop()
    state.db.close()
    logger.info("Dashboard stopped")


app = FastAPI(title="Smart Money Dashboard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from .api.routes_candles import router as candles_router
from .api.routes_indicators import router as indicators_router
from .api.routes_config import router as config_router
from .api.routes_strategies import router as strategies_router
from .api.ws import router as ws_router

app.include_router(candles_router)
app.include_router(indicators_router)
app.include_router(config_router)
app.include_router(strategies_router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}
