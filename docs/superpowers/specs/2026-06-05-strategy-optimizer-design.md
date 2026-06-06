# Strategy Parameter Optimizer

## Overview

Add a grid-search parameter optimizer to the SMC Dashboard. Users define parameter ranges inline in their strategy YAML, run the optimizer from the dashboard, and browse sorted results by any metric.

## YAML Range Syntax

Extend the strategy YAML to accept list or dict-range values in place of scalars:

| Format | Example | Produces |
|--------|---------|----------|
| List enumeration | `lookback: [5, 10, 15]` | `5, 10, 15` |
| Min/max/step | `value: {min: 1.5, max: 3.0, step: 0.5}` | `1.5, 2.0, 2.5, 3.0` |

Supports ranges on:
- Entry condition params: `lookback`, `period`, etc.
- Exit condition params: `value`, `trail_activation`
- Risk params: `position_size_pct`, `max_positions`

Scalar values (non-list, non-dict) are treated as fixed.

## Combinatorics

- Cartesian product of all range values = total combinations
- Hard cap at 500 (`max_combos` parameter, default 500)
- If total exceeds cap, log-spaced sampling per range to stay within limit
- No async/multi-processing needed for typical use

## Optimizer Engine

**File:** `smartmoneyconcepts/dashboard/strategy/optimizer.py`

New classes:

- `StrategyOptimizer(repo, indicator_service)` -- orchestrator
  - `optimize(strategy_yaml, start, end, initial_capital, max_combos) -> OptimizerResult`
  - Uses existing `Backtester` internally
  - Each combo: apply params via `apply_params()` -> parse -> backtest -> collect metrics

- `OptimizerResult` -- top-level result
  - `strategy_name`, `symbol`, `timeframe`, `total_combos`, `combos_run`, `results: list[ComboResult]`

- `ComboResult` -- single combination result
  - `params`, `total_trades`, `wins`, `losses`, `win_rate`, `total_pnl`, `profit_factor`, `max_drawdown`, `sharpe`, `avg_win`, `avg_loss`, `largest_win`, `largest_loss`, `avg_bars_held`

### Parser additions

**File:** `smartmoneyconcepts/dashboard/strategy/parser.py`

New functions:

- `ParamRange(path, values)` -- dataclass describing one scanned parameter
- `_resolve_value(val) -> list | None` -- converts a YAML value to list if it's a list or {min,max,step} dict
- `detect_ranges(yaml_str) -> list[ParamRange]` -- parses YAML, scans entry/exit/risk fields for range values
- `apply_params(base_yaml, ranges, combo) -> str` -- applies a specific combo of values to the base YAML and returns modified YAML string

## API Endpoint

`POST /api/strategies/optimize`

**Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `definition` | string | yes | -- | YAML strategy with optional range syntax |
| `start` | string (ISO) | yes | -- | Backtest start date |
| `end` | string (ISO) | yes | -- | Backtest end date |
| `initial_capital` | number | no | 10000 | Starting capital |
| `max_combos` | int | no | 500 | Max combinations to run |

**Response:** `OptimizerResult` JSON (list of `ComboResult` sorted by Sharpe desc).

## Frontend Optimize Page

**File:** `frontend/src/app/dashboard/optimize/page.tsx`

**Sidebar link:** "Optimize" added after "History" in dashboard nav.

Layout: Two-column grid on desktop.

### Left Panel (Inputs)

1. **YAML textarea** -- pre-filled with a demo strategy showing range syntax
2. **Date range** -- Start and End date inputs (type="date")
3. **Initial Capital** -- number input, default 10000
4. **Max Combos** -- number input, default 500
5. **"Run Optimization" button** -- blue, full width

### Right Panel (Results)

- Loading: spinner + "Scanning parameter space..."
- Empty: "No results returned"
- Results: count header ("144 of 144 combos"), sortable table

**Table columns:** #, Sharpe, PnL, Win Rate, Profit Factor, Max DD, Trades, Wins, Losses, Avg Win, Avg Loss, Largest Win, Largest Loss, Avg Bars Held, Params

- All metric columns sortable (click header, toggle asc/desc)
- PnL colored green/red
- Expandable row (click or "Show" button) shows `combo.params` as JSON

## Tests

### Backend (`test_optimizer.py`) -- 13 tests

- `TestResolveValue`: list of ints, mixed, dict range, dict range int step, scalar returns none
- `TestDetectRanges`: entry ranges, exit ranges, risk ranges, correct values, no ranges
- `TestParamRange`: creation
- `TestApplyParams`: single range, multiple ranges

### Frontend (`page.test.tsx`) -- 5 tests

- Renders form with YAML textarea and controls
- Renders default YAML in textarea
- Shows loading state on run
- Displays results table after successful optimization
- Displays error on failure

## File Changes

| File | Status |
|------|--------|
| `smartmoneyconcepts/dashboard/strategy/models.py` | Modified -- add ComboResult, OptimizerResult |
| `smartmoneyconcepts/dashboard/strategy/parser.py` | Modified -- add ParamRange, detect_ranges, apply_params |
| `smartmoneyconcepts/dashboard/strategy/optimizer.py` | Created |
| `smartmoneyconcepts/dashboard/api/routes_strategies.py` | Modified -- add /api/strategies/optimize |
| `smartmoneyconcepts/dashboard/tests/test_optimizer.py` | Created |
| `frontend/src/lib/types.ts` | Modified -- add ComboResult, OptimizerResult types |
| `frontend/src/lib/api.ts` | Modified -- add runOptimization() |
| `frontend/src/app/dashboard/layout.tsx` | Modified -- add "Optimize" nav link |
| `frontend/src/app/dashboard/optimize/page.tsx` | Created |
| `frontend/src/app/dashboard/optimize/__tests__/page.test.tsx` | Created |
| `docs/api.md` | Modified -- document optimize endpoint |
| `docs/strategies.md` | Modified -- document YAML range syntax |
