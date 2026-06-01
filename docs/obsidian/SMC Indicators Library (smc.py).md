---
tags: [smc, indicators, library]
---

# SMC Indicators Library (smc.py)

The existing Python library that computes Smart Money Concepts / ICT trading indicators from OHLCV data.

## Dependencies

- pandas >= 2.0.2
- numpy >= 1.24.3
- numba >= 0.58.1

## Available Indicators

### [[Fair Value Gap (FVG)]]
Detects fair value gaps — when previous high < next low (bullish) or previous low > next high (bearish).

### [[Swing Highs and Lows]]
Identifies swing points — highest high / lowest low within a window of N candles.

### [[BOS and CHoCH]]
- **Break of Structure (BOS)**: Price breaks through a swing high/low
- **Change of Character (CHoCH)**: Market structure reversal

### [[Order Blocks (OB)]]
Detects order blocks — high-volume price ranges where institutions place large orders.

### [[Liquidity Detection]]
Identifies liquidity clusters — multiple highs/lows within a small range.

### [[Previous High and Low]]
Returns the previous period's high/low for a given timeframe (15m, 1H, 4H, 1D, 1W, 1M).

### [[Trading Sessions]]
Identifies candles within specific trading sessions (London, New York, Asian kill zone, etc.).

### [[Retracements]]
Calculates retracement percentages from swing highs/lows.

## Usage

```python
from smartmoneyconcepts.smc import smc

# Prepare OHLCV DataFrame
fvg = smc.fvg(ohlc)
swings = smc.swing_highs_lows(ohlc)
ob = smc.ob(ohlc, swings)
bos = smc.bos_choch(ohlc, swings)
liq = smc.liquidity(ohlc, swings)
```

## Related
- [[Smart Money Dashboard]] (builds on this library)
- [[Indicator Service]] (dashboard wrapper)
