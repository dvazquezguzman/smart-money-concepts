---
tags: [dashboard, smc, trading]
aliases: [SMC Dashboard, Smart Money Dashboard]
---

# Smart Money Dashboard

A web-based trading dashboard built on top of the [[SMC Indicators Library (smc.py)]] library.

## Overview

Enables live charting, strategy configuration, paper trading, and automated execution across [[Binance]] and [[Bybit]] exchanges, with extensibility to stocks.

## Architecture (5-Layer)

| Layer | Component | Tech |
|-------|-----------|------|
| 5 - Remote Access | Nginx Reverse Proxy | Nginx + Let's Encrypt |
| 4 - Dashboard UI | Next.js Frontend | Next.js + [[TradingView Lightweight Charts]] |
| 3 - Execution Engine | Live/Paper Trading | Python + CCXT |
| 2 - Strategy System | YAML-based Strategy Definitions | PyYAML + Custom Evaluator |
| 1 - Indicator Engine | SMC Indicator Wrapper | Python (wraps [[smc class]]) |
| 0 - Data Pipeline | CCXT Data Engine | Python + CCXT |

## Deployment

- Runs in a [[Proxmox]] LXC container
- Accessible via HTTPS at `https://trading.yourdomain.com`
- Database: [[SQLite (Repository Pattern)]] (swappable to Postgres)

## Key Pages

- [[Dashboard Overview Page]]
- [[Chart View Page]]
- [[Strategy Configuration]]
- [[Paper Trading Console]]
- [[Live Trading Page]]
- [[Configuration Page]]

## Build Phases

1. [[Phase 0: Data Pipeline and DB]] — FastAPI, CCXT, SQLite
2. [[Phase 1: Indicator Engine and API]] — Indicator wrapper, REST endpoints
3. [[Phase 2: Frontend and Charts]] — Next.js, Lightweight Charts
4. [[Phase 3: Strategy System and Backtester]] — YAML strategies, backtester
5. [[Phase 4: Paper Trading Engine]] — Paper trading, ICT validation tests
6. [[Phase 5: Execution Engine]] — Live trading, API key encryption
7. [[Phase 6: Nginx and Deployment]] — HTTPS, systemd, deployment

## Related Notes

- [[ICT Strategy Templates]]
- [[SMC Indicators Reference]]
- [[Testing Strategy]]
