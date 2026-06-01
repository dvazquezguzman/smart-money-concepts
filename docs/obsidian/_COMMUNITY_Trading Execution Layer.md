---
type: community
cohesion: 0.31
members: 9
---

# Trading Execution Layer

**Cohesion:** 0.31 - loosely connected
**Members:** 9 nodes

## Members
- [[API Key Encryption (AES)]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Live Trading Engine]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Nginx Reverse Proxy + HTTPS]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Paper Trading Engine]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Phase 4 Paper Trading Engine]] - document - .opencode/plans/dashboard-implementation-plan.md
- [[Phase 5 Execution Engine]] - document - .opencode/plans/dashboard-implementation-plan.md
- [[Phase 6 Nginx and Deployment]] - document - .opencode/plans/dashboard-implementation-plan.md
- [[Proxmox LXC Container]] - document - .opencode/plans/smart-money-dashboard-design.md
- [[Risk Manager]] - document - .opencode/plans/smart-money-dashboard-design.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Trading_Execution_Layer
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Dashboard Core Stack]]

## Top bridge nodes
- [[Nginx Reverse Proxy + HTTPS]] - degree 4, connects to 1 community
- [[Paper Trading Engine]] - degree 4, connects to 1 community
- [[Phase 4 Paper Trading Engine]] - degree 3, connects to 1 community