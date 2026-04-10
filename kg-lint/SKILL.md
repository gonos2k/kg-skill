---
name: kg-lint
description: Health check — verify graph integrity, manifest, freshness. If wiki exists, also check orphan pages, missing links, stale claims. Use to audit knowledge base quality.
trigger: /kg-lint
---

# /kg-lint — Health Check

**Graph-only checks** (always):
- `graph.json` exists and parseable
- `GRAPH_REPORT.md` exists
- `manifest.json` exists (for incremental updates)
- `.graphify_python` points to valid interpreter
- Freshness: source files newer than `graph.json`

**Wiki checks** (when `wiki/` exists):
- Orphan pages — no inbound `[[wikilinks]]`
- Missing pages — referenced but don't exist
- Missing cross-references
- Graph drift — `graph-report.md` older than newest wiki page
- Stale claims — superseded by recent ingests

Report findings, offer to fix. Log in `wiki/log.md` if wiki exists.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg lint`.
