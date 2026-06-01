---
tags: [dashboard, architecture]
---

# Dashboard Architecture

## System Diagram

```
Proxmox LXC Container
├── Nginx (HTTPS reverse proxy + Let's Encrypt)
├── Next.js Frontend (port 3000)
├── FastAPI Backend (port 8000)
├── Data Engine (Python + CCXT)
├── Bot Engine (Python)
└── SQLite Database
```

## Component Details

### FastAPI Backend
- Python-native async framework
- Directly imports [[SMC Indicators Library (smc.py)]]
- Serves REST API on port 8000
- WebSocket endpoint for real-time updates

### Next.js Frontend
- TypeScript-based React framework
- Uses [[TradingView Lightweight Charts]] for candlestick charts
- Communicates with FastAPI via REST + WebSocket

### Data Engine (CCXT)
- Fetches OHLCV data from [[Binance]] and [[Bybit]]
- WebSocket subscription for real-time 1m candle feed
- Candle aggregation: 1m -> 5m, 15m, 1H, 4H

### Database
- [[SQLite (Repository Pattern)]] by default
- Repository pattern allows swapping to Postgres
- Tables: candles, strategies, trades, config

## Data Flow

```
CCXT REST → SQLite Candle Table → Indicator Service → FastAPI → Next.js
CCXT WS → In-Memory Buffer → On Candle Close → Persist + Recalculate + Push
```

## Design Principles

1. Repository pattern for DB abstraction
2. CCXT abstraction for exchange swapping
3. Strategy evaluator decoupled from execution
4. All state persisted in DB (restart-safe)
5. API keys never leave the backend

## Related Notes
- [[Smart Money Dashboard]]
- [[Strategy System]]
- [[Testing Strategy]]
