---
tags: [testing, quality]
---

# Testing Strategy

## Framework
- `pytest` for new dashboard code
- `unittest` for existing [[SMC Indicators Library (smc.py)]] tests

## Test Categories

### Unit Tests
| Layer | What |
|-------|------|
| Repository | CRUD, aggregation, time range queries |
| Data Engine | CCXT mock, WS stream parsing, reconnect |
| Indicator Service | Correct shape/keys, caching, recalculation |
| Strategy Evaluator | YAML parse, entry/exit conditions |
| Risk Manager | Position sizing, max positions, daily loss |
| Paper Trading | Order fill, slippage, P&L calculation |
| Encryption | AES encrypt/decrypt roundtrip |

### ICT Strategy Validation Tests
Six ICT patterns validated against real historical BTC/USDT data:

1. **FVG + OB + BOS (Kill Zone)** — liquidity sweep, FVG, OB holds, BOS confirms
2. **Silver Bullet** — 1m entry during London kill zone
3. **Breaker Block** — CHOCH, retrace, continuation
4. **FVG Mitigation Entry** — bounce off FVG midpoint
5. **Liquidity Sweep + Flip** — daily high/low sweep, retest
6. **FVG Gap Fill** — gap fill and continue

Plus negative tests that should NOT fire (BOS without sweep, weak OB, wrong kill zone).

### Integration Tests
- Data -> Indicator pipeline
- Strategy -> Paper trade
- API -> Frontend format

### Coverage Target
- Core engine: 90%+
- API/UI: 70%+

## Running Tests
```bash
pytest tests/
python tests/unit_tests.py  # existing SMC tests
```
