---
type: community
cohesion: 1.00
members: 2
---

# OpenCode Config

**Cohesion:** 1.00 - tightly connected
**Members:** 2 nodes

## Members
- [[opencode.json]] - code - .opencode/opencode.json
- [[plugin]] - code - .opencode/opencode.json

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/OpenCode_Config
SORT file.name ASC
```
