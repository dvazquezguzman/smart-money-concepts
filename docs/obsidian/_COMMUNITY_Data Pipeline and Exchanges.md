---
type: community
cohesion: 0.40
members: 6
---

# Data Pipeline and Exchanges

**Cohesion:** 0.40 - moderately connected
**Members:** 6 nodes

## Members
- [[Binance Exchange]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Bybit Exchange]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[CCXT Unified API]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Data Engine (CCXT)]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Phase 0 Data Pipeline and DB]] - document - .opencode/plans/dashboard-implementation-plan.md
- [[SQLite Database (Repository Pattern)]] - document - .opencode/plans/smart-money-dashboard-design.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Data_Pipeline_and_Exchanges
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Dashboard Core Stack]]

## Top bridge nodes
- [[Data Engine (CCXT)]] - degree 4, connects to 1 community
- [[Phase 0 Data Pipeline and DB]] - degree 3, connects to 1 community