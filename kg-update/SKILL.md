---
name: kg-update
description: Incremental graph rebuild — detect changed files via manifest, re-extract only new/changed, re-cluster. Delegates to graphify --update. Use when vault files changed since last build.
trigger: /kg-update
---

# /kg-update — Incremental Graph Rebuild

Rebuild the structural graph without re-ingesting into wiki. Delegates to Graphify.

1. Detect source directory (`gMeso/vault/` > `raw/` > `docs/` > `.`)
2. Run `graphify --update` on the source directory
   - SHA256 cache finds only new/changed files
   - Code-only changes skip semantic extraction (no LLM cost)
   - Re-clusters communities, regenerates GRAPH_REPORT.md
3. If `wiki/` exists, sync GRAPH_REPORT.md into `wiki/graph-report.md`
4. Report delta: new nodes, removed nodes, community changes

**Technical:** Manifest at `graphify-out/manifest.json`. Graph at `graphify-out/graph.json` (NetworkX node_link_data format, `links` key not `edges`).

**Phase Lock relation**: `kg-update` operates outside the schema Phase Lock (Draft→Approve→Apply→Migrate→Validate). It writes `graphify-out/*` and the **derived mirror** `wiki/graph-report.md` only — it does NOT modify `.schema/`, content wiki pages (`entities/`, `concepts/`, etc.), or proposals. `graph-report.md` is a derived artifact (sync from GRAPH_REPORT.md), not a content page; writing it is bookkeeping, not ontology mutation. Safe to run in any phase. No receipt implication.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-update`.
