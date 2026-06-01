# API Reference

Base URL: `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`)

## Health

### `GET /health`

Server health check.

**Response:** `{ "status": "ok" }`

## Candles

Prefix: `/api/candles`

### `GET /api/candles/{symbol}`

Fetch OHLCV candles.

**Params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `timeframe` | string | `1m` | One of: `1m`, `5m`, `15m`, `1H`, `4H` |
| `limit` | int | `200` | Max candles (1-1000) |

**Response:**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1m",
  "count": 200,
  "candles": [
    { "timestamp": "2026-06-01T00:00:00", "open": 100.0, "high": 105.0, "low": 99.0, "close": 104.0, "volume": 1000.0 }
  ]
}
```

Returns `{ "loading": true }` when data is being fetched for a new symbol.

## Indicators

Prefix: `/api/indicators`

### `GET /api/indicators/{symbol}`

Compute SMC indicators for a symbol.

**Params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `timeframe` | string | `1m` | Candle timeframe |
| `limit` | int | `500` | Candles to compute over (50-1000) |

**Response:** `{ "symbol": "...", "timeframe": "...", "fvg": {...}, "ob": {...}, "bos_choch": {...}, "liquidity": {...}, "swings": {...}, "candle_count": 500 }`

Each indicator dict has arrays of values (one per candle), with `null` where no signal exists. See the `smc` library indicator return values for field descriptions.

## Config

Prefix: `/api/config`

### `GET /api/config/symbols`

List tracked symbols.

**Response:** `{ "symbols": ["BTC/USDT", "ETH/USDT"] }`

### `POST /api/config/symbols?symbol=ETH/USDT`

Add a symbol to track. Triggers data engine to begin fetching.

**Response:** `{ "symbols": ["BTC/USDT", "ETH/USDT"] }`

### `DELETE /api/config/symbols?symbol=ETH/USDT`

Remove a tracked symbol.

**Response:** `{ "symbols": ["BTC/USDT"] }`

## Strategies

Prefix: `/api/strategies`

### `GET /api/strategies`

List all saved strategies.

**Response:** `[{ "id": 1, "name": "ICT FVG Breaker", "definition": "...", "created_at": ..., "updated_at": ... }]`

### `POST /api/strategies`

Create a new strategy.

**Body:** `{ "name": "...", "definition": "<YAML string>" }`

**Response:** `{ "status": "ok", "name": "..." }`

### `GET /api/strategies/{id}`

Get a single strategy by ID.

**Response:** `{ "id": 1, "name": "...", "definition": "...", ... }`

### `PUT /api/strategies/{id}`

Update a strategy's YAML definition.

**Body:** `{ "definition": "<updated YAML>" }`

### `DELETE /api/strategies/{id}`

Delete a strategy.

### `GET /api/strategies/templates/list`

List pre-built strategy templates.

**Response:** `[{ "name": "ICT FVG Breaker", "file": "ict-fvg-breaker.yaml" }, ...]`

### `GET /api/strategies/templates/{file_name}`

Load a template's YAML content.

**Response:** `{ "name": "...", "definition": "<YAML string>" }`

### `POST /api/strategies/backtest`

Run a backtest.

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `definition` | string | yes | YAML strategy definition |
| `start` | string (ISO) | yes | Backtest start date |
| `end` | string (ISO) | yes | Backtest end date |
| `symbol` | string | no | Override strategy symbol |
| `initial_capital` | number | no | Default: 10000 |

**Response:**
```json
{
  "strategy": "ICT FVG Breaker",
  "symbol": "BTC/USDT",
  "total_trades": 12,
  "wins": 8,
  "losses": 4,
  "win_rate": 0.667,
  "total_pnl": 452.0,
  "profit_factor": 2.1,
  "max_drawdown": 0.05,
  "sharpe": 1.8,
  "avg_win": 85.0,
  "avg_loss": -42.0,
  "largest_win": 150.0,
  "largest_loss": -60.0,
  "avg_bars_held": 24.0,
  "trades": [...]
}
```

## Trading

Prefix: `/api/trading`

### Paper Trading

#### `GET /api/trading/paper/status`

**Response:** `{ "balance": 10000.0, "equity": 10500.0, "realized_pnl": 250.0, "open_positions": 2, "running": true }`

#### `GET /api/trading/paper/positions`

**Response:** `[{ "symbol": "BTC/USDT", "side": "buy", "quantity": 0.1, "entry_price": 50000, ... }]`

#### `POST /api/trading/paper/start`

Start paper engine with a strategy.

**Body:** `{ "definition": "<YAML string>" }`

#### `POST /api/trading/paper/stop`

Stop paper engine.

#### `GET /api/trading/paper/history`

Get closed paper trades.

### Live Trading

#### `GET /api/trading/live/status`

**Response:** `{ "connected": true, "running": true, "exchange": "binance", "open_positions": 1, "kill_switch": false }`

#### `GET /api/trading/live/positions`

Get open live positions.

#### `POST /api/trading/live/connect`

Connect to the exchange.

#### `POST /api/trading/live/start`

Start live engine with a strategy.

**Body:** `{ "definition": "<YAML string>" }`

#### `POST /api/trading/live/stop`

Gracefully stop live engine (close positions per strategy exits).

#### `POST /api/trading/live/kill`

Emergency kill switch -- closes ALL positions with market orders.

#### `GET /api/trading/live/history`

Get closed live trades.

### Exchange Keys

#### `GET /api/trading/exchange/keys/status`

**Response:** `{ "configured": true }`

#### `PUT /api/trading/exchange/keys`

Save encrypted exchange API keys.

**Body:** `{ "exchange_id": "binance", "api_key": "...", "secret": "...", "passphrase": "..." }`

#### `POST /api/trading/exchange/test`

Test exchange connection with provided credentials.

**Body:** `{ "exchange_id": "binance", "api_key": "...", "secret": "..." }`

## WebSocket

### `ws://host/ws/{symbol}`

Real-time candle updates. The server pushes new candles as they arrive.

**Message format (JSON):** `{ "timestamp": "...", "open": ..., "high": ..., "low": ..., "close": ..., "volume": ... }`
