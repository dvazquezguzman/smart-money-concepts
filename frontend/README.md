# SMC Dashboard Frontend

Next.js trading dashboard for Smart Money Concepts. Displays live candlestick charts with SMC indicators, strategy management, paper/live trading controls, and trade history.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/dashboard/overview` | Overview | Real-time stat cards: balances, PnL, positions, server health (10s poll) |
| `/dashboard/charts` | Charts | Candlestick chart with FVG, OB, BOS/CHoCH, liquidity overlays |
| `/dashboard/strategies` | Strategies | Create, edit, and backtest YAML-based trading strategies |
| `/dashboard/paper-trading` | Paper Trading | Start/stop paper engine, view simulated positions |
| `/dashboard/live-trading` | Live Trading | Start/stop live engine, exchange key status check, kill switch |
| `/dashboard/history` | History | Paper/Live trade history with sortable table |
| `/dashboard/config` | Config | Manage symbols and exchange API keys |

## Tech Stack

- **Next.js** (App Router, React Server Components)
- **Tailwind CSS** (dark theme)
- **TradingView Lightweight Charts** (candle + indicator rendering)
- **vitest** + **@testing-library/react** (unit tests)

## Development

```bash
# Install
npm ci

# Run full stack (API + frontend)
npm run dev

# Run frontend only (expects API on :8000)
npm run dev:web

# Test
npx vitest run        # single run
npx vitest            # watch mode

# Lint
npm run lint

# Build
npm run build
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── dashboard/
│   │   ├── overview/       Stat cards with live polling
│   │   ├── charts/         Candlestick + indicator charts
│   │   ├── strategies/     YAML strategy editor
│   │   ├── paper-trading/  Paper engine controls
│   │   ├── live-trading/   Live engine controls + key status
│   │   ├── history/        Trade history table
│   │   └── config/         Symbols + exchange keys
│   ├── error.tsx           Global error boundary
│   ├── loading.tsx         Global loading state
│   └── not-found.tsx       404 page
├── components/             Shared UI components
│   └── BotStatus.tsx       Dashboard sidebar status indicator
└── lib/
    ├── api.ts              API client (all backend endpoints)
    └── types.ts            TypeScript type definitions
```

## Dependencies

- `lightweight-charts` -- TradingView charting library
- `@testing-library/react` + `vitest` -- Testing
- `tailwindcss` -- Utility-first CSS
