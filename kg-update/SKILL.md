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
2. Decision table — pick mode by `(graph exists?, code files present?)`:

| graph.json exists? | Code files present? | Mode | Action |
|---|---|---|---|
| **No** | **Yes** | `cli-bootstrap` | `graphify update <path>` (CLI does AST-extract from scratch when no graph; verified v0.5.0 — produces graph.json + GRAPH_REPORT.md from 0; no LLM tokens) |
| **No** | **No** (docs/papers only) | `slash-bootstrap` | Stop CLI; route to `/graphify <path>` (orchestrator does semantic extraction via subagents) |
| **Yes** | **Yes (changed)** | `cli-update` | `graphify update <path>` (incremental, SHA256 cache) |
| **Yes** | **No (only docs changed)** | `slash-update` | `/graphify <path> --update` (re-extract docs via subagents) |

3. Run the chosen command:
   - **`cli-bootstrap` / `cli-update`**: `graphify update <path>` — SHA256 cache finds new/changed code files; AST extraction; re-clusters communities; regenerates GRAPH_REPORT.md. No LLM cost.
   - **`slash-bootstrap` / `slash-update`**: invoke `/graphify <path>` (orchestrator skill). Costs LLM tokens proportional to doc/paper file count.

4. If `wiki/` exists, sync GRAPH_REPORT.md into `wiki/graph-report.md`
5. Report delta: new nodes, removed nodes, community changes, mode used.

## CLI vs slash-command forms

Two distinct invocation surfaces with different capabilities — do not conflate them:

| Form | Capability | Cost |
|---|---|---|
| `graphify update <path>` (CLI) | Re-extract **code files only** against existing graph | No LLM |
| `/graphify <path> --update` (slash, Claude Code orchestrator) | Re-extract code + docs + papers + images via subagents | LLM tokens |
| `/graphify <path>` (slash, no flag) | First-time build / semantic extraction on any corpus | LLM tokens |

The `--update / --mode deep / --directed / --svg / --graphml / --neo4j / --mcp / --wiki / --watch / --html` flags exist only in the **slash form** (the graphify SKILL orchestrator implements them via library calls + subagents). They are NOT raw CLI flags in graphify v0.5.0 — invoking `graphify <path> --<flag>` from Bash returns `error: unknown command '<path>'`.

**Technical:** Manifest at `graphify-out/manifest.json`. Graph at `graphify-out/graph.json` (NetworkX node_link_data format, `links` key not `edges`).

**Phase Lock relation**: `kg-update` operates outside the schema Phase Lock (Draft→Approve→Apply→Migrate→Validate). It writes `graphify-out/*` and the **derived mirror** `wiki/graph-report.md` only — it does NOT modify `.schema/`, content wiki pages (`entities/`, `concepts/`, etc.), or proposals. `graph-report.md` is a derived artifact (sync from GRAPH_REPORT.md), not a content page; writing it is bookkeeping, not ontology mutation. Safe to run in any phase. No receipt implication.

## Output Contract

```text
Update result: PASS | PARTIAL | FAIL
Source dir: <path>
Mode: cli-update | slash-update | bootstrap-needed | cluster-only

Delta:
- Files scanned: <N>
- Files extracted: <M> (skipped <N-M> via SHA256 cache)
- New nodes: <N>
- Removed nodes: <N>
- Modified nodes: <N>
- Community changes: <N> (added/merged/split)

GRAPH_REPORT.md: regenerated | unchanged | not-yet-built
wiki/graph-report.md: synced | skipped (no wiki/) | not-yet-built

Files NOT touched (per Phase Lock):
- .schema/, .schema-proposals/, content wiki pages

Confidence: high | medium | low

Caveats:
- <graphify CLI missing | graph absent (bootstrap needed) | no code files (CLI no-op) | source dir empty | manifest corrupt | none>

Next command:
- <none | /kg-orient | /kg-lint | /kg-reflect | /graphify <path> (bootstrap) | /graphify <path> --update (slash, doc/paper re-extract)>
```

## Exceptions and Escalation

- **Graphify CLI not found** (`which graphify` empty) → suggest `pip install graphifyy` and stop.
- **Source directory does not exist** → report all 5 detection candidates checked; ask user to specify path explicitly.
- **Graph absent + non-code corpus only** — if `graphify-out/graph.json` does NOT exist AND the corpus has no code files (only docs/papers/HTML), CLI `update` outputs "Nothing to update" + "[graphify watch] No code files found". Stop, set `Update result: PARTIAL`, `Mode: slash-bootstrap`, and recommend `Next command: /graphify <path>` (slash-command orchestrator does semantic extraction via subagents). Do not retry CLI.
- **Graph absent + code present** — `graphify update <path>` **does** bootstrap from scratch via AST extraction (verified empirically on graphify v0.5.0; e.g., 33 .py files → 427 nodes, 21 communities, no LLM). This is the "happy path" for code-only first-time runs. Emit `Mode: cli-bootstrap`.
- **Graph exists + no code changes** — if `graphify update <path>` reports no code files changed since last run, suggest `/graphify <path> --update` (slash form re-extracts docs/papers/images that the CLI ignores). Emit `Mode: slash-update`.
- **`graphify-out/` write permission denied** → stop; do not attempt fallback location.
- **Never modify** `.schema/`, `.schema-proposals/`, or content wiki pages. This skill is graph-layer only.
- **`--watch` / `--mode deep` / `--directed` / `--cluster-only` / `--svg` / `--graphml` / `--neo4j` / `--mcp` / `--wiki` modes** → these are slash-command orchestrator features only (not raw CLI). Suggest `/graphify <path> --<flag>` and stop; this skill delegates only the CLI `update` subcommand.
- **Migration/schema drift** → out of scope; emit message "schema mutation requires `/kg-schema`" and stop.

## Quality Gates

Before final answer:
- [ ] Output cites the exact source path used
- [ ] Delta numbers add up (files extracted + skipped = scanned)
- [ ] No file outside `graphify-out/` and `wiki/graph-report.md` was modified
- [ ] If `wiki/` present, graph-report.md synced
