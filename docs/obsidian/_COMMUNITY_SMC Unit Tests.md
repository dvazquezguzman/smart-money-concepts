---
type: community
cohesion: 0.18
members: 11
---

# SMC Unit Tests

**Cohesion:** 0.18 - loosely connected
**Members:** 11 nodes

## Members
- [[.test_bos_choch()]] - code - tests/unit_tests.py
- [[.test_fvg()]] - code - tests/unit_tests.py
- [[.test_fvg_consecutive()]] - code - tests/unit_tests.py
- [[.test_liquidity()]] - code - tests/unit_tests.py
- [[.test_ob()]] - code - tests/unit_tests.py
- [[.test_ob_early_data()]] - code - tests/unit_tests.py
- [[.test_previous_high_low()]] - code - tests/unit_tests.py
- [[.test_retracements()]] - code - tests/unit_tests.py
- [[.test_sessions()]] - code - tests/unit_tests.py
- [[.test_swing_highs_lows()]] - code - tests/unit_tests.py
- [[TestSmartMoneyConcepts]] - code - tests/unit_tests.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/SMC_Unit_Tests
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Python Standard Types]]

## Top bridge nodes
- [[TestSmartMoneyConcepts]] - degree 12, connects to 1 community