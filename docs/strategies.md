# Strategy System

Strategies are defined in YAML and executed by the `StrategyEvaluator`. They can be paper-traded, live-traded, or backtested from the dashboard.

## YAML Format

```yaml
name: ICT FVG Breaker          # Required: strategy name
timeframe: 5m                   # Required: 1m, 5m, 15m, 1H, 4H
symbol: BTC/USDT                # Required for trading (optional for tests)

entry_conditions:               # All conditions must match (AND logic)
  - type: fvg_mitigation
    direction: bullish
    lookback: 10                # Type-specific parameter

exit_conditions:
  - type: target
    value: 2.0
  - type: stop_loss
    value: 1.0

risk:
  position_size_pct: 1.0       # % of balance per position
  max_positions: 1              # Max concurrent positions
  max_daily_loss: 100           # Optional: daily loss limit
```

## Entry Conditions

Entry conditions use AND logic -- all conditions must match for a position to open.

| Type | Directions | Parameters | Description |
|------|-----------|------------|-------------|
| `fvg_mitigation` | bullish, bearish | `lookback` (int) | Price retraces into and through a Fair Value Gap |
| `ob_break` | bullish, bearish | `lookback` (int) | Price breaks through an Order Block boundary |
| `liquidity_sweep` | bullish, bearish | -- | Price sweeps a liquidity level (recent equal highs/lows) |
| `bos` | bullish, bearish | -- | Break of Structure detected |
| `choch` | bullish, bearish | -- | Change of Character detected |
| `session` | bullish, bearish | `session` (string) | Candle falls within a trading session |
| `trend` | bullish, bearish | `lookback` (int) | Consecutive higher highs (bullish) or lower lows (bearish) |
| `vwap` | bullish, bearish | -- | Price closes above (bullish) or below (bearish) VWAP |
| `ema` | bullish, bearish | `period` (int) | Price closes above (bullish) or below (bearish) the EMA |
| `donchian_trend` | bullish, bearish | -- | Donchian channel midpoint is rising (bullish) or falling (bearish) |
| `hull_suite` | bullish, bearish | -- | Hull Moving Average is rising (bullish) or falling (bearish) |

### Session Values

`Asian`, `London`, `NewYork`, `Sydney`, `Tokyo`, `Asian kill zone`, `London open kill zone`, `New York kill zone`, `London close kill zone`

## Exit Conditions

| Type | Parameters | Description |
|------|-----------|------------|
| `target` | `value` (float) | Take profit at N x risk (R-multiple). `value: 2.0` = 2:1 reward |
| `stop_loss` | `value` (float) | Stop loss at N x ATR or fixed R multiple |
| `trailing_stop` | `trail_activation` (float) | Activates trailing after price moves N% in profit |

## Examples

### FVG + Session + Trend

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
  - type: trend
    direction: bullish
    lookback: 20
exit_conditions:
  - type: target
    value: 2.0
  - type: stop_loss
    value: 1.0
risk:
  position_size_pct: 1.0
  max_positions: 1
```

### OB Liquidity Sweep

```yaml
name: OB Liquidity Sweep
timeframe: 15m
symbol: ETH/USDT
entry_conditions:
  - type: liquidity_sweep
    direction: bearish
  - type: ob_break
    direction: bearish
    lookback: 15
exit_conditions:
  - type: target
    value: 3.0
  - type: trailing_stop
    trail_activation: 1.5
risk:
  position_size_pct: 0.5
  max_positions: 2
```

### Kill Zone Momentum

```yaml
name: ICT Kill Zone Momentum
timeframe: 1m
symbol: SOL/USDT
entry_conditions:
  - type: bos
    direction: bullish
  - type: session
    direction: bullish
    session: New York kill zone
exit_conditions:
  - type: target
    value: 1.5
  - type: stop_loss
    value: 0.5
risk:
  position_size_pct: 2.0
  max_positions: 1
```

## Parameter Optimization (Grid Search)

The `POST /api/strategies/optimize` endpoint accepts YAML with range syntax in place of any scalar parameter. The optimizer generates all combinations (cartesian product) and returns sorted results.

### Range Syntax

| Format | Example | Produces |
|--------|---------|----------|
| List | `lookback: [5, 10, 15]` | `5, 10, 15` |
| Dict range | `value: {min: 1.5, max: 3.0, step: 0.5}` | `1.5, 2.0, 2.5, 3.0` |

### Example

```yaml
name: Optimized Strategy
timeframe: 5m
symbol: BTC/USDT
entry_conditions:
  - type: fvg_mitigation
    direction: bullish
    lookback: [5, 10, 15]              # 3 values
exit_conditions:
  - type: target
    value: {min: 1.5, max: 3.0, step: 0.5}  # 4 values
  - type: stop_loss
    value: [1.0, 2.0]                  # 2 values
risk:
  position_size_pct: {min: 0.5, max: 2.0, step: 0.5}  # 4 values
```

Total combinations: `3 x 4 x 2 x 4 = 96`. If the total exceeds `max_combos` (default 500), log-spaced sampling is used automatically. Results are returned sorted by Sharpe ratio (descending) in the frontend, with all metrics available for sorting.

## Templates

Pre-built templates are available from the dashboard Strategies page and the API at `/api/strategies/templates/`. Included templates:

- ICT FVG Breaker
- ICT Order Block Liquidity Sweep
- ICT CHoCH Breaker
- ICT FVG + Order Block Combo
- ICT Asian Range Breakout

## Notes

- Entry conditions use AND logic: all must match to enter
- Only one position opens per signal (no pyramiding by default)
- Paper engine applies configurable slippage on exit
- Live engine submits real orders via CCXT
- Backtest metrics: win rate, profit factor, max drawdown, Sharpe ratio
