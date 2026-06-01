import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..engine.indicators import IndicatorService
from ..main import state

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, symbol: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(symbol, []).append(ws)

    def disconnect(self, symbol: str, ws: WebSocket):
        conns = self._connections.get(symbol, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, symbol: str, data: dict):
        for ws in self._connections.get(symbol, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(symbol.upper(), websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "subscribe":
                svc = IndicatorService(state.candle_repo)
                result = svc.calculate(symbol.upper(), msg.get("timeframe", "1m"))
                await websocket.send_json({"type": "indicators", **result})
    except WebSocketDisconnect:
        manager.disconnect(symbol.upper(), websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        manager.disconnect(symbol.upper(), websocket)
