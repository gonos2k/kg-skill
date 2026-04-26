---
name: kg-update
description: "This skill should be used when source files changed and the user asks to rebuild, refresh, or update the structural graph, says '그래프 갱신', 'Graphify 업데이트', 'changed files 반영', or invokes /kg-update. Delegates to graphify update, updates graphify-out/ only — never modifies schema or content wiki pages."
trigger: /kg-update
---

# /kg-update — Incremental Graph Rebuild

Rebuild the structural graph without re-ingesting into wiki. Delegates to Graphify v0.5.0+.

## Activate When

- Source files changed since last `/kg-update`
- User asks "그래프 갱신", "Graphify 업데이트", "changed files 반영"
- After `/kg-ingest` to refresh graph with new source content
- `/kg-orient` shows graph freshness STALE (mtime ≥ 7 days)
- User invokes `/kg-update [path]`

## Do Not Activate When

- User wants to add new wiki content → `/kg-ingest`
- User wants to query → `/kg-query`
- Source files unchanged AND graph fresh (< 7 days) — no work needed
- User wants schema changes → `/kg-schema` (kg-update never touches schema)

## Flow

1. Detect source directory (`gMeso/vault/` > `raw/` > `docs/` > `.`)
2. Run `graphify <path> --update` on the source directory
   - SHA256 cache finds only new/changed files
   - Code-only changes skip semantic extraction (no LLM cost)
   - Re-clusters communities, regenerates GRAPH_REPORT.md
3. If `wiki/` exists, sync GRAPH_REPORT.md into `wiki/graph-report.md`
4. Report delta: new nodes, removed nodes, community changes

## Optional flags (v0.5.0+)

- `--cluster-only` — re-cluster existing graph without re-extraction (fast, no LLM)
- `--mode deep` — thorough extraction with richer INFERRED edges
- `--directed` — preserve edge direction (source → target)
- `--watch` — long-running watcher; auto-rebuild on code changes (no LLM needed)

Use `--cluster-only` after schema/predicate changes; use `--mode deep` for major ingests; use `--watch` for active development sessions.

## Equivalent CLI forms

`graphify <path> --update` and `graphify update <path>` both work in v0.5.0+. Prefer the first form for consistency with other graphify flags.

**Technical:** Manifest at `graphify-out/manifest.json`. Graph at `graphify-out/graph.json` (NetworkX node_link_data format, `links` key not `edges`).

**Phase Lock relation**: `kg-update` operates outside the schema Phase Lock (Draft→Approve→Apply→Migrate→Validate). It writes `graphify-out/*` and the **derived mirror** `wiki/graph-report.md` only — it does NOT modify `.schema/`, content wiki pages (`entities/`, `concepts/`, etc.), or proposals. `graph-report.md` is a derived artifact (sync from GRAPH_REPORT.md), not a content page; writing it is bookkeeping, not ontology mutation. Safe to run in any phase. No receipt implication.

## Output Contract

```text
Update result: PASS | PARTIAL | FAIL
Source dir: <path>
Mode: standard | --cluster-only | --mode deep | --directed | --watch

Delta:
- Files scanned: <N>
- Files extracted: <M> (skipped <N-M> via SHA256 cache)
- New nodes: <N>
- Removed nodes: <N>
- Modified nodes: <N>
- Community changes: <N> (added/merged/split)

GRAPH_REPORT.md: regenerated | unchanged
wiki/graph-report.md: synced | skipped (no wiki/) | unchanged

Files NOT touched (per Phase Lock):
- .schema/, .schema-proposals/, content wiki pages

Confidence: high | medium | low

Caveats:
- <graphify CLI missing | source dir empty | manifest corrupt | none>

Next command:
- <none | /kg-orient | /kg-lint | /kg-reflect>
```

## Exceptions and Escalation

- **Graphify CLI not found** (`which graphify` empty) → suggest `pip install graphifyy` and stop.
- **Source directory does not exist** → report all 5 detection candidates checked; ask user to specify path explicitly.
- **`graphify-out/` write permission denied** → stop; do not attempt fallback location.
- **Never modify** `.schema/`, `.schema-proposals/`, or content wiki pages. This skill is graph-layer only.
- **`--watch` mode** → run as background process; user must manually stop. Skill returns immediately after spawn.
- **Migration/schema drift** → out of scope; emit message "schema mutation requires `/kg-schema`" and stop.

## Quality Gates

Before final answer:
- [ ] Output cites the exact source path used
- [ ] Delta numbers add up (files extracted + skipped = scanned)
- [ ] No file outside `graphify-out/` and `wiki/graph-report.md` was modified
- [ ] If `wiki/` present, graph-report.md synced
