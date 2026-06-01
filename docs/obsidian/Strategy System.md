---
tags: [strategies, trading, config]
---

# Strategy System

Strategies are defined as **YAML config files**. No coding required for standard ICT patterns.

## Structure

```yaml
name: "Strategy Name"
timeframe: 5m
symbols: ["BTC/USDT", "ETH/USDT"]
entry:
  - indicator: ob
    direction: bullish
    confirm:
      - indicator: fvg
        direction: bullish
exit:
  take_profit: 2.0
  stop_loss: swing_low
risk:
  position_size_pct: 1.5
  max_positions: 3
```

## Components

- **Parser**: YAML -> validated Strategy model (Pydantic)
- **Evaluator**: Loops over candles, checks entry/exit conditions
- **Backtester**: Runs strategy on historical data, returns performance stats
- [[ICT Strategy Templates]]: Predefined strategies you can load one-click

## Workflow
1. Create strategy via dashboard form (generates YAML)
2. Run backtest -> review performance stats
3. Toggle paper trading -> live simulation
4. Promote to live -> automated execution

## Related
- [[Paper Trading Engine]]
- [[Live Trading Engine]]
- [[Risk Manager]]
