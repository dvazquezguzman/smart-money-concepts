# Dashboard Polish & Test Coverage

## Overview

Complete 5 remaining gaps in the SMC Dashboard: fix CI pipeline, populate the Overview and History pages, add Next.js error/loading/not-found pages, show exchange key status on the Live Trading page, and add proper test coverage for both backend and frontend.

## Scope

### 1. CI Fix
**File:** `.github/workflows/ci.yaml:19`
**Change:** Remove orphaned `tests/` from pytest path.

### 2. Overview Page
**File:** `frontend/src/app/dashboard/overview/page.tsx`
**Behavior:** Fetch 4 endpoints on mount + poll every 10s:
- `GET /api/trading/paper/status` — balance, equity, PnL, open positions, running
- `GET /api/trading/live/status` — connected, running, exchange, open positions
- `GET /api/strategies` — strategy count
- `GET /health` — server health indicator

**Layout:** Two rows of stat cards (reuse existing StatCard pattern):
- Row 1: Paper Balance, Paper Equity, Realized PnL, Paper Positions, Strategy Count
- Row 2: Live Exchange, Live Status (green/red dot), Engine State, Live Positions, Server Health

**States:** Loading spinner, error banner, data (with "not connected" prompt in row 2).

### 3. History Page
**File:** `frontend/src/app/dashboard/history/page.tsx`
**Behavior:** Two-tab UI ("Paper" / "Live"), each fetches from:
- `GET /api/trading/paper/history` — paper trade records
- `GET /api/trading/live/history` — live trade records

**Table:** Symbol, Side (buy/sell badge), Entry Price, Exit Price, Qty, PnL (green/red), Exit Reason, Opened At. Sorted by opened_at DESC (API default).

**States:** Loading, empty ("No trades yet."), error, data.

### 4. Error / Loading / Not-Found Pages
3 Next.js convention files in `frontend/src/app/`:
- **`loading.tsx`** — Centered spinner, "Loading..." subtitle, dark bg
- **`error.tsx`** — Error icon, "Something went wrong" title, error message, "Try Again" button (calls `reset()`), "Return to Dashboard" link
- **`not-found.tsx`** — "404" heading, "Page not found", "Return to Dashboard" link

All use the existing dark theme (`bg-gray-950`, `text-gray-300`, `border-gray-800`).

### 5. Live Trading Key Status
**File:** `frontend/src/app/dashboard/live-trading/page.tsx`
**Behavior:** On mount, check `GET /api/trading/exchange/keys/status` → `{ configured: boolean }`.
- If `configured === false`: amber banner "Exchange API keys not configured. [Configure in Settings]" → links to `/dashboard/config`
- Start button disabled until keys are configured
- Key status fetched once on mount (not polled)

No backend changes needed -- endpoint already exists.

## Test Coverage

### Backend Tests (~24 new)

**5.1 Strategy evaluator** (8 tests in `test_strategy.py`):
- `test_liquidity_sweep` — entry triggers when price sweeps liquidity level
- `test_liquidity_sweep_no_level` — no entry when no liquidity exists
- `test_bos` — break of structure triggers entry
- `test_choch` — change of character triggers entry
- `test_trend_bullish` — trend condition with uptrend candles
- `test_trend_bearish` — trend condition with downtrend candles
- `test_multi_condition_and` — multiple conditions must all match
- `test_trailing_stop` — trailing stop updates correctly

**5.2 Backtest metrics** (5 tests in new `test_backtest.py`):
- Win rate: 3 wins / 4 closed → 0.75
- Profit factor: gross_win 300 / gross_loss 100 → 3.0
- Max drawdown: peak-to-trough ratio
- Sharpe: annualized returns / std
- Zero-win / zero-loss edge cases

**5.3 Paper engine** (4 tests in `test_paper_trading.py`):
- Slippage applied on exit
- Entry slippage on price fill
- Trailing stop triggered by price movement
- Multiple positions with shared risk limits

**5.4 Candle aggregation** (4 tests in `test_candle_aggregator.py`):
- Partial closing group (e.g., 7 candles → 1 full + remainder)
- Day boundary crossing
- Single candle in → single candle out
- Large gap in timestamps

**5.5 Database edge cases** (3 tests in `test_db.py`):
- Two symbols interleaved
- Non-existent symbol returns empty
- Config overwrite preserves key constraint

### Frontend Tests (5 tests, new setup)

**New dependencies:** `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `@vitejs/plugin-react`

**Config:** `frontend/vitest.config.ts` with jsdom environment.

**Tests:**
- `overview/page.test.tsx` — renders stat cards, loading state, error state
- `history/page.test.tsx` — renders two tabs, trade rows, empty state
- `error.test.tsx` — renders error with retry button
- `loading.test.tsx` — renders spinner
- `not-found.test.tsx` — renders 404 with dashboard link

**CI update:** Add `npx vitest run` to frontend CI job (after lint).

## Files Changed

| File | Change |
|------|--------|
| `.github/workflows/ci.yaml:19` | Fix pytest path |
| `.github/workflows/ci.yaml` | Add vitest run step |
| `frontend/src/app/dashboard/overview/page.tsx` | Full rewrite (live data) |
| `frontend/src/app/dashboard/history/page.tsx` | Full rewrite (tabs + table) |
| `frontend/src/app/error.tsx` | New file |
| `frontend/src/app/loading.tsx` | New file |
| `frontend/src/app/not-found.tsx` | New file |
| `frontend/src/app/dashboard/live-trading/page.tsx` | Add key status check |
| `frontend/package.json` | Add dev dependencies |
| `frontend/vitest.config.ts` | New file |
| `frontend/src/test/setup.ts` | New file |
| `smartmoneyconcepts/dashboard/tests/test_strategy.py` | Add 8 evaluator tests |
| `smartmoneyconcepts/dashboard/tests/test_backtest.py` | New file (5 tests) |
| `smartmoneyconcepts/dashboard/tests/test_paper_trading.py` | Add 4 tests |
| `smartmoneyconcepts/dashboard/tests/test_candle_aggregator.py` | Add 4 tests |
| `smartmoneyconcepts/dashboard/tests/test_db.py` | Add 3 tests |

Total: ~29 new tests, ~12 files changed/created.
