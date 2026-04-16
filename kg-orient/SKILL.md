---
name: kg-orient
description: Session start orientation — show graph/wiki status, god nodes, freshness. Run at the start of each session when graphify-out/ exists.
trigger: /kg-orient
---

# /kg-orient — Session Start Orientation

Read the full kg skill at `~/.claude/skills/kg/SKILL.md` section `/kg-orient` for details.

**Quick steps:**

1. Detect layers: `graphify-out/GRAPH_REPORT.md` (graph), `wiki/index.md` (wiki)
2. **Read `wiki/hot.md` FIRST** (session context cache)
3. **Read `wiki/overview.md`** (stable global synthesis, ~500 words — this is the compression layer between hot.md and full index)
4. Read GRAPH_REPORT.md first 60 lines (god nodes + communities)
5. **Only if hot.md is stale (>24h) AND overview.md is insufficient for routing**, fall back to `wiki/index.md` + tail of `wiki/log.md`. As wiki grows past 200 pages, index.md becomes a last resort, not a default read.
5. Check freshness: `graph.json` mtime vs newest source file
6. Present summary:
   ```
   Hot cache: [fresh/stale/absent]
   Graph: X nodes · Y edges · Z communities
   Top god nodes: [top 3]
   Wiki: N pages (E entities, C concepts, P procedures, X experiences, H heuristics, D decisions, S sources)
   Freshness: FRESH | STALE (N files changed)
   ```

7. **Maintenance Debt** (compute from log.md + _index.md):
   ```
   Reflect debt: N ingests since last reflect (warn if >= 3)
   Migration debt: N transitional pages with age > 21 days
   Proposal debt: N drift signals surfaced but not proposed/rejected
   Pin gap: global v{X} vs pinned v{Y} (suggest pull-global if gap > 0)
   Convergence: full_v1 / active_frontier = N% (target: 80%+)
   ```
   If reflect_debt >= 3, append: "Reflect 권장 — `/kg-reflect` 실행을 고려하세요."

**Source directory detection** (checked in order):
1. User-specified path
2. `gMeso/vault/`
3. `raw/`
4. `docs/`
5. `.`
