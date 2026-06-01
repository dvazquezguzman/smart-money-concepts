import logging

from fastapi import APIRouter, Depends, HTTPException

from ..db.base import BaseTradeRepository
from ..main import state
from ..strategy.parser import parse_strategy
from ..execution.exchange.encryption import decrypt, encrypt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trading", tags=["trading"])


def get_trade_repo() -> BaseTradeRepository:
    return state.trade_repo


@router.get("/paper/status")
def paper_status():
    engine = state.paper_engine
    return engine.get_summary()


@router.get("/paper/positions")
def paper_positions():
    return state.paper_engine.get_positions()


@router.post("/paper/start")
def paper_start(body: dict):
    yaml_def = body.get("definition", "").strip()
    if not yaml_def:
        raise HTTPException(status_code=400, detail="definition is required")
    try:
        strategy = parse_strategy(yaml_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    if not strategy.symbol:
        raise HTTPException(
            status_code=400, detail="symbol is required in strategy YAML"
        )

    state.paper_engine.start(strategy)
    return {"status": "started", "strategy": strategy.name}


@router.post("/paper/stop")
def paper_stop():
    state.paper_engine.stop()
    return {"status": "stopped"}


@router.get("/paper/history")
def paper_history(
    trade_repo: BaseTradeRepository = Depends(get_trade_repo),
):
    return trade_repo.get_trades(mode="paper")


@router.get("/live/status")
def live_status():
    engine = state.live_engine
    return engine.get_summary()


@router.get("/live/positions")
def live_positions():
    return state.live_engine.get_positions()


@router.post("/live/start")
async def live_start(body: dict):
    yaml_def = body.get("definition", "").strip()
    if not yaml_def:
        raise HTTPException(status_code=400, detail="definition is required")
    try:
        strategy = parse_strategy(yaml_def)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    if not strategy.symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    try:
        await state.live_engine.start(strategy)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"status": "started", "strategy": strategy.name}


@router.post("/live/stop")
async def live_stop():
    await state.live_engine.stop()
    return {"status": "stopped"}


@router.post("/live/kill")
async def live_kill():
    await state.live_engine.kill()
    return {"status": "killed"}


@router.post("/live/connect")
async def live_connect():
    engine = state.live_engine
    ok = await engine.exchange.connect()
    if not ok:
        raise HTTPException(status_code=502, detail="Connection failed")
    return {"status": "connected", "exchange": engine.exchange.name}


@router.get("/live/history")
def live_history(
    trade_repo: BaseTradeRepository = Depends(get_trade_repo),
):
    return trade_repo.get_trades(mode="live")


@router.get("/exchange/keys/status")
def exchange_key_status():
    raw = state.config_repo.get_config("exchange_keys_encrypted")
    return {"configured": raw is not None}


@router.put("/exchange/keys")
def save_exchange_keys(body: dict):
    exchange_id = body.get("exchange_id", "").strip()
    api_key = body.get("api_key", "").strip()
    secret = body.get("secret", "").strip()
    passphrase = body.get("passphrase", "").strip()

    if not all([exchange_id, api_key, secret, passphrase]):
        raise HTTPException(
            status_code=400,
            detail="exchange_id, api_key, secret, and passphrase are required",
        )

    payload = f"{exchange_id}|{api_key}|{secret}"
    encrypted = encrypt(payload, passphrase)
    state.config_repo.save_config("exchange_keys_encrypted", encrypted)
    state.config_repo.save_config("exchange_id", exchange_id)
    return {"status": "saved"}


@router.post("/exchange/test")
async def test_exchange_connection(body: dict):
    exchange_id = body.get("exchange_id", "").strip()
    api_key = body.get("api_key", "").strip()
    secret = body.get("secret", "").strip()

    if not all([exchange_id, api_key, secret]):
        raise HTTPException(
            status_code=400, detail="exchange_id, api_key, and secret are required"
        )

    from ..execution.exchange.ccxt_wrapper import CCXTExchange

    exchange = CCXTExchange(
        exchange_id,
        {"apiKey": api_key, "secret": secret},
    )
    ok = await exchange.connect()
    await exchange.disconnect()
    if not ok:
        raise HTTPException(status_code=502, detail="Connection test failed")
    return {"status": "ok"}
