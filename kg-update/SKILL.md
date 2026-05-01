---
name: kg-update
description: "This skill should be used when source files changed and the user asks to rebuild, refresh, or update the structural graph, says '그래프 갱신', 'Graphify 업데이트', 'changed files 반영', or invokes /kg-update. Delegates to graphify update; writes graphify-out/, wiki/graph-report*.md (single-corpus or INDEX + per-corpus), and v0.5.7+ also maintains wiki/index.md Graph snapshot section + wiki/log.md audit entry. Never modifies schema or content wiki pages."
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

1. Detect source directory:
   - **Preferred (graphify v0.5.7+)**: if `graphify-out/.graphify_root` exists, use the path it contains — graphify CLI saved this on the previous run, and the same value is what `graphify update` (no args) would use.
   - **Fallback**: probe `gMeso/vault/` > `raw/` > `docs/` > `.` in order.
   - User-specified path on the command line always wins.
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

4. If `wiki/` exists, sync GRAPH_REPORT.md into wiki — see § Multi-corpus naming convention.
5. **Update wiki back-pointers** (added v0.5.7 — see § Wiki back-pointer maintenance):
   - If `wiki/index.md` exists and contains a `## Graph snapshot` section, rewrite that section to reflect the current corpus structure (single vs INDEX, per-corpus stats), and bump `date_modified` in frontmatter.
   - If `wiki/log.md` exists, append a single audit entry summarizing this run (mode, corpora, deltas, caveats).
   - These two files are **derived navigation/audit pages**, not ontology — kg-update may write them. They are NOT content pages in the Phase-Lock sense.
6. Report delta: new nodes, removed nodes, community changes, mode used.

## Multi-corpus naming convention (added v0.5.4)

A project may track **multiple separately-graphed corpora** (e.g., our own code + cloned reference repos). Single-file sync overwrites prior reports. Use this convention:

| State | Wiki file | Role |
|---|---|---|
| Single corpus | `wiki/graph-report.md` | The report itself (existing v0.5.x behavior) |
| Multi corpus (≥2) | `wiki/graph-report-<corpus-slug>.md` (one per corpus) | Per-corpus report |
| Multi corpus | `wiki/graph-report.md` | INDEX page listing all per-corpus reports + multi-corpus convention note |

**Detection rule for kg-update**:
- If `wiki/graph-report.md` does NOT exist → write the report to `wiki/graph-report.md` (single-corpus path).
- If `wiki/graph-report.md` exists AND was previously the report (no INDEX header) AND we're now syncing a DIFFERENT corpus → migrate: rename existing file to `wiki/graph-report-<old-slug>.md` and write index in `wiki/graph-report.md` with both entries.
- If `wiki/graph-report.md` is already an INDEX → simply add new corpus row + write `wiki/graph-report-<new-slug>.md`.

**Slug derivation**: from the corpus root directory name, kebab-cased lowercase. Examples: `MyProject` → `my-project`; `VendoredLib_v2` → `vendored-lib-v2`; nested path → use the last directory component only.

**Why**: a project may track multiple separately-graphed corpora — e.g., the project's own implementation alongside cloned reference repos, or per-language sub-corpora of a polyglot codebase. Single-file sync (one `wiki/graph-report.md` for the whole project) would silently destroy whichever corpus was synced earlier. The INDEX-with-per-corpus pattern preserves history for all corpora and lets each evolve on its own cadence.

## Wiki back-pointer maintenance (added v0.5.7)

When kg-update changes the structure of `wiki/graph-report.md` (e.g., single-corpus → INDEX migration, or just refreshes node counts), other wiki pages that reference the report go stale unless updated in the same run. This section defines what to update and how.

### `wiki/index.md` — Graph snapshot section

If `wiki/index.md` contains a `## Graph snapshot` section, rewrite it to match current state.

**Single-corpus state** (one report file):
```markdown
## Graph snapshot
- [[graph-report]] — <N> nodes / <E> edges / <C> communities (<corpus-slug>, <YYYY-MM-DD>)
```

**Multi-corpus state** (INDEX + per-corpus reports):
```markdown
## Graph snapshot
- [[graph-report]] — INDEX page (multi-corpus, <K> corpora since <YYYY-MM-DD>)
  - [[graph-report-<slug-1>]] — <N1> nodes / <E1> edges / <C1> communities (<path-1>, <date-1>)
  - [[graph-report-<slug-2>]] — <N2> nodes / <E2> edges / <C2> communities (<path-2>, <date-2>)
  - …
```

Also bump frontmatter `date_modified:` to today.

If `wiki/index.md` has no `## Graph snapshot` section, do nothing — do not invent one.

### `wiki/log.md` — audit entry

If `wiki/log.md` exists, append one entry per kg-update run:

```markdown
## [<YYYY-MM-DD>] kg-update | <one-line summary>
- Source dir(s): <paths>
- Mode: <cli-bootstrap | cli-update | slash-bootstrap | slash-update> [× N if multiple corpora]
- Per-corpus delta: <N nodes / E edges / C communities, extraction quality>
- Wiki sync: <single | INDEX migration | INDEX add row>
- Caveats: <one line per non-fatal issue>
```

If `wiki/log.md` does not exist, do not create it — log.md is part of the wiki initialization (`/kg-init`), not kg-update's responsibility.

### Why

`wiki/index.md` and `wiki/log.md` describe what the graph layer looks like and how it has changed. When kg-update reshapes that layer (single → INDEX migration, per-corpus rebuild, freshly bootstrapped graph), those descriptions go stale unless they are refreshed in the same run. Stale back-pointers are easy to miss on review and turn the wiki into a self-contradicting record — the index claims one corpus structure while `graph-report.md` shows another. Mandating refresh in the same skill that caused the change is the simplest defense; relying on a follow-up `/kg-lint` or manual edit is unreliable. v0.5.4 introduced multi-corpus migration without the back-pointer obligation, which is why v0.5.7 adds it explicitly.

## CLI vs slash-command forms

Two distinct invocation surfaces with different capabilities — do not conflate them:

| Form | Capability | Cost |
|---|---|---|
| `graphify update <path>` (CLI) | Re-extract **code files only** against existing graph | No LLM |
| `graphify update` (CLI, no args, v0.5.7+) | Same as above; reads `graphify-out/.graphify_root` saved by the prior run | No LLM |
| `/graphify <path> --update` (slash, Claude Code orchestrator) | Re-extract code + docs + papers + images via subagents | LLM tokens |
| `/graphify <path>` (slash, no flag) | First-time build / semantic extraction on any corpus | LLM tokens |

The `--update / --mode deep / --directed / --svg / --graphml / --neo4j / --mcp / --wiki / --watch / --html` flags exist only in the **slash form** (the graphify SKILL orchestrator implements them via library calls + subagents). They are NOT raw CLI flags in graphify v0.5.0 — invoking `graphify <path> --<flag>` from Bash returns `error: unknown command '<path>'`.

**Technical:** Manifest at `graphify-out/manifest.json`. Graph at `graphify-out/graph.json` (NetworkX node_link_data format, `links` key not `edges`). Scan-root memo at `graphify-out/.graphify_root` (v0.5.7+) — written by the CLI on every run, used by argument-less `graphify update`.

**Phase Lock relation**: `kg-update` operates outside the schema Phase Lock (Draft→Approve→Apply→Migrate→Validate). It writes:

| Path | Role | In scope? |
|---|---|---|
| `graphify-out/*` | Graph artifacts (graph.json, GRAPH_REPORT.md, cache/, html) | ✅ primary output |
| `wiki/graph-report.md` and `wiki/graph-report-<slug>.md` | Derived mirrors of GRAPH_REPORT.md | ✅ derived sync |
| `wiki/index.md` `## Graph snapshot` section + `date_modified` | Navigation back-pointer | ✅ back-pointer (v0.5.7+) |
| `wiki/log.md` (append-only) | Audit log of kg operations | ✅ audit (v0.5.7+) |
| `wiki/.schema/`, `wiki/.schema-proposals/` | Ontology + proposals | ❌ off-limits (use `/kg-schema`) |
| `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/decisions/`, `wiki/heuristics/`, `wiki/experiences/`, `wiki/procedures/`, `wiki/queries/` | Content pages | ❌ off-limits (use `/kg-ingest`, `/kg-elicit`, etc.) |
| Anything in `wiki/index.md` outside the `## Graph snapshot` section | Content navigation | ❌ off-limits |

The principle: kg-update may write **derived artifacts** (graph reports, back-pointers, audit logs) but never **ontology** (schema, content). Safe to run in any phase. No receipt implication.

## Output Contract

```text
Update result: PASS | PARTIAL | FAIL
Source dir: <path>
Mode: cli-bootstrap | cli-update | slash-bootstrap | slash-update

Delta:
- Files scanned: <N>
- Files extracted: <M> (skipped <N-M> via SHA256 cache)
- New nodes: <N>
- Removed nodes: <N>
- Modified nodes: <N>
- Community changes: <N> (added/merged/split)

GRAPH_REPORT.md: regenerated | unchanged | not-yet-built
wiki/graph-report.md: synced | rewritten as INDEX | skipped (no wiki/) | not-yet-built
wiki/graph-report-<slug>.md: created | updated | n/a (single-corpus)
wiki/index.md "Graph snapshot": updated | unchanged | section absent | n/a (no index.md)
wiki/log.md: appended | n/a (no log.md)

Files NOT touched (per Phase Lock — ontology only):
- wiki/.schema/, wiki/.schema-proposals/
- wiki/entities/, wiki/concepts/, wiki/sources/, wiki/decisions/, wiki/heuristics/,
  wiki/experiences/, wiki/procedures/, wiki/queries/
- wiki/index.md sections other than `## Graph snapshot`

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
- **Never modify** `wiki/.schema/`, `wiki/.schema-proposals/`, or content wiki pages (`entities/`, `concepts/`, `sources/`, `decisions/`, `heuristics/`, `experiences/`, `procedures/`, `queries/`). This skill is graph-layer + derived-navigation only.
- **`wiki/index.md` outside `## Graph snapshot`** is off-limits. If you need to touch other sections, that's a content-layer change → `/kg-ingest` or manual edit.
- **`wiki/log.md` insertion** is append-only. Never rewrite or reorder existing entries.
- **`--watch` / `--mode deep` / `--directed` / `--cluster-only` / `--svg` / `--graphml` / `--neo4j` / `--mcp` / `--wiki` modes** → these are slash-command orchestrator features only (not raw CLI). Suggest `/graphify <path> --<flag>` and stop; this skill delegates only the CLI `update` subcommand.
- **Migration/schema drift** → out of scope; emit message "schema mutation requires `/kg-schema`" and stop.

## Quality Gates

Before final answer:
- [ ] Output cites the exact source path used
- [ ] Delta numbers add up (files extracted + skipped = scanned)
- [ ] No file outside the in-scope list (see § Phase Lock relation table) was modified
- [ ] If `wiki/` present, graph-report.md synced (or INDEX written for multi-corpus)
- [ ] If multi-corpus migration occurred, prior single-corpus report preserved as `wiki/graph-report-<old-slug>.md`
- [ ] If `wiki/index.md` has `## Graph snapshot` section, it cites the current corpus structure (single vs INDEX, current node/edge/community counts)
- [ ] If `wiki/log.md` exists, an audit entry was appended for this run
