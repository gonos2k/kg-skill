---
name: kg-orient
description: Session start orientation — show graph/wiki status, god nodes, freshness. Run at the start of each session when graphify-out/ exists.
trigger: /kg-orient
---

# /kg-orient — Session Start Orientation

Read the full kg skill at `~/.claude/skills/kg/SKILL.md` section `/kg orient` for details.

**Quick steps:**

1. Detect layers: `graphify-out/GRAPH_REPORT.md` (graph), `wiki/index.md` (wiki)
2. Read GRAPH_REPORT.md first 60 lines (god nodes + communities)
3. If wiki exists, read `wiki/index.md` + tail of `wiki/log.md`
4. Check freshness: `graph.json` mtime vs newest source file
5. Present summary:
   ```
   Graph: X nodes · Y edges · Z communities
   Top god nodes: [top 3]
   Wiki: N pages | not initialized
   Freshness: FRESH | STALE (N files changed)
   ```

**Source directory detection** (checked in order):
1. User-specified path
2. `gMeso/vault/`
3. `raw/`
4. `docs/`
5. `.`
