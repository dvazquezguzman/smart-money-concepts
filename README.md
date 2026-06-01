[![PyPI](https://img.shields.io/pypi/v/smartmoneyconcepts.svg?style=flat-square)](https://pypi.org/project/smartmoneyconcepts/)
[![Downloads](https://pepy.tech/badge/smartmoneyconcepts/month)](https://pepy.tech/project/smartmoneyconcepts/month)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Bitcoin Donate](https://badgen.net/badge/Bitcoin/Donate/F19537?icon=bitcoin)](https://blockstream.info/address/bc1petss2mlqyjsajyzhu06wzl667v0f8svc0hnpqjj2d32frtx77g4sg5s0pg)

# Smart Money Concepts

Python library for Smart Money Concepts (ICT) trading indicators + a real-time trading dashboard with paper and live execution engines.

## Quick Start

```bash
pip install smartmoneyconcepts

python
from smartmoneyconcepts import smc
import pandas as pd

ohlc = pd.DataFrame({
    "open": [100, 102, 104], "high": [105, 108, 107],
    "low": [99, 101, 103], "close": [102, 107, 105],
    "volume": [1000, 1200, 1100],
})
fvg = smc.fvg(ohlc)
print(fvg)
```

## Dashboard

The project includes a full trading dashboard with:

- **Live charts** using TradingView Lightweight Charts
- **SMC indicators** (FVG, OB, BOS/CHoCH, Liquidity) rendered on candlestick charts
- **Strategy system** -- define entry/exit conditions in YAML
- **Paper trading** -- simulate trades with slippage, risk limits, trailing stops
- **Live trading** -- connect to exchanges via CCXT (Binance, Bybit, etc.)
- **Backtesting** -- run strategies against historical data with metrics (win rate, sharpe, drawdown)
- **WebSocket streaming** -- real-time candle updates

### Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│  Next.js (frontend/src/)                         │
│  ├── dashboard/overview     Stats overview       │
│  ├── dashboard/charts       Candle + indicators  │
│  ├── dashboard/strategies   YAML strategy editor │
│  ├── dashboard/paper-trading Paper engine UI     │
│  ├── dashboard/live-trading Live engine UI       │
│  ├── dashboard/history      Trade history        │
│  └── dashboard/config       Exchange keys etc.   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────────┐
│               FastAPI Backend                     │
│  smartmoneyconcepts/dashboard/                    │
│  ├── api/               REST endpoints            │
│  ├── engine/            Data pipeline + indicators│
│  ├── strategy/          Parser, evaluator, backtest│
│  ├── execution/         Paper + live engines      │
│  ├── db/                SQLite repositories       │
│  └── main.py            App entrypoint            │
└─────────────────────────────────────────────────┘
```

### Development Setup

```bash
# Clone and install backend
git clone https://github.com/your-org/smart-money-concepts
cd smart-money-concepts
pip install -e . uvicorn[standard]

# Install frontend
cd frontend
npm ci

# Start both (concurrent)
npm run dev
# API: http://localhost:8000  |  UI: http://localhost:3000

# Or start separately:
npm run dev:api   # backend only
npm run dev:web   # frontend only
```

### Environment

Copy `.env.template` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCHANGE_ID` | binance | CCXT exchange id |
| `API_KEY` | - | Exchange API key |
| `API_SECRET` | - | Exchange API secret |
| `SYMBOLS` | BTC/USDT | Comma-separated trading pairs |
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend URL for frontend |

### Deployment

See [deploy/](deploy/) for nginx + systemd configs.

```bash
cp deploy/smc-api.service /etc/systemd/system/
cp deploy/smc-frontend.service /etc/systemd/system/
cp deploy/nginx.conf /etc/nginx/sites-available/trading
```

## Indicators

All indicators take a DataFrame with lowercase columns: `open`, `high`, `low`, `close` (and `volume` where noted).

### Fair Value Gap (FVG)

```python
smc.fvg(ohlc, join_consecutive=False)
```

Detects when price gaps between consecutive candles. `join_consecutive=True` merges adjacent FVGs.

Returns: `FVG` (1 bullish, -1 bearish), `Top`, `Bottom`, `MitigatedIndex`

### Swing Highs and Lows

```python
smc.swing_highs_lows(ohlc, swing_length=50)
```

Returns: `HighLow` (1 high, -1 low), `Level`

### Break of Structure / Change of Character

```python
smc.bos_choch(ohlc, swing_highs_lows, close_break=True)
```

Returns: `BOS` (1 bullish, -1 bearish), `CHOCH` (1 bullish, -1 bearish), `Level`, `BrokenIndex`

### Order Blocks (OB)

```python
smc.ob(ohlc, swing_highs_lows, close_mitigation=False)
```

Returns: `OB` (1 bullish, -1 bearish), `Top`, `Bottom`, `OBVolume`, `Percentage`

### Liquidity

```python
smc.liquidity(ohlc, swing_highs_lows, range_percent=0.01)
```

Returns: `Liquidity` (1 bullish, -1 bearish), `Level`, `End`, `Swept`

### Previous High And Low

```python
smc.previous_high_low(ohlc, time_frame="1D")
```

Returns: `PreviousHigh`, `PreviousLow`, `BrokenHigh`, `BrokenLow`

### Sessions

```python
smc.sessions(ohlc, session, start_time, end_time, time_zone="UTC")
```

Sessions: Sydney, Tokyo, London, New York, Asian kill zone, London open kill zone, New York kill zone, London close kill zone, Custom.

Returns: `Active` (1 if in session), `High`, `Low`

### Retracements

```python
smc.retracements(ohlc, swing_highs_lows)
```

Returns: `Direction`, `CurrentRetracement%`, `DeepestRetracement%`

## Strategy System

Strategies are defined in YAML and can be paper-traded, live-traded, or backtested.

```yaml
name: ICT FVG Breaker
timeframe: 5m
symbol: BTC/USDT
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: 10
  - type: session
    direction: bullish
    session: London
exit_conditions:
  - type: target
    value: 2.0
  - type: stop_loss
    value: 1.0
risk:
  position_size_pct: 1.0
  max_positions: 1
```

Supported condition types: `fvg_mitigation`, `ob_break`, `liquidity_sweep`, `bos`, `choch`, `session`, `trend`.
Exit types: `target` (R-multiple), `stop_loss`, `trailing_stop`.

See [docs/strategies.md](docs/strategies.md) for full documentation.

## API

The backend exposes REST endpoints under `/api/`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/api/candles/{symbol}` | GET | OHLCV candles |
| `/api/indicators/{symbol}` | GET | Computed indicators |
| `/api/config/symbols` | GET/POST/DELETE | Manage tracked symbols |
| `/api/strategies` | GET/POST | List / create strategies |
| `/api/strategies/{id}` | GET/PUT/DELETE | CRUD individual strategy |
| `/api/strategies/backtest` | POST | Run backtest |
| `/api/strategies/templates/` | GET | List / load templates |
| `/api/trading/paper/*` | GET/POST | Paper engine status, start, stop, history |
| `/api/trading/live/*` | GET/POST | Live engine status, start, stop, kill, history |
| `/api/trading/exchange/keys` | GET/PUT | Exchange API key management |

See [docs/api.md](docs/api.md) for full endpoint documentation.

## Testing

```bash
# Backend (pytest)
pytest smartmoneyconcepts/dashboard/tests/ -v

# Frontend (vitest)
cd frontend && npx vitest run
```

## Hide Credit Message

```bash
export SMC_CREDIT=0
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

For educational purposes only. Not financial advice. Use at your own risk.
