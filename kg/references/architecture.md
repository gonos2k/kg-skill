# kg Architecture

System layout, source detection, operating modes, page template examples, and technical notes for the Knowledge Graph + LLM Wiki.

## Layout

```
project/
├── <source-dir>/           # Layer 1: Raw sources (immutable)
│   └── (auto-detected: gMeso/vault/, raw/, docs/, or user-specified)
│
├── wiki/                   # Layer 2: LLM-maintained wiki (optional)
│   ├── .schema/            #   Per-wiki schema pin (copied from global on /kg-init)
│   │   ├── core.yaml       #     Class definitions
│   │   ├── relations.yaml  #     Predicate vocabulary
│   │   ├── frontmatter.yaml#     Field spec
│   │   ├── pin.yaml        #     Version lock
│   │   └── migrations/     #     Schema history
│   ├── .schema-proposals/  #   Pending schema change proposals
│   ├── index.md            #   Content catalog — every page listed
│   ├── hot.md              #   Session context cache (~500 words)
│   ├── log.md              #   Chronological record of operations
│   ├── overview.md         #   High-level synthesis
│   ├── graph-report.md     #   Synced from graphify-out/GRAPH_REPORT.md
│   ├── entities/           #   Artifact pages (code, files, data)
│   │   └── _index.md       #     Folder-level index
│   ├── concepts/           #   Concept pages (abstract ideas)
│   │   └── _index.md
│   ├── procedures/         #   Procedure pages (how-to steps)
│   │   └── _index.md
│   ├── experiences/        #   Experience pages (case records)
│   │   └── _index.md
│   ├── heuristics/         #   Heuristic pages (rules of thumb, 비법)
│   │   └── _index.md
│   ├── decisions/          #   Decision pages (ADR style)
│   │   └── _index.md
│   ├── sources/            #   Source summaries (one per ingested file)
│   │   └── _index.md
│   └── queries/            #   Filed query results worth keeping
│       └── _index.md
│
├── graphify-out/           # Structural graph layer (graphify v0.8.x)
│   ├── graph.json          #   Nodes, edges, communities (NetworkX node_link_data)
│   ├── GRAPH_REPORT.md     #   God nodes, communities, surprises
│   ├── graph.html          #   Interactive visualization (default output)
│   ├── manifest.json       #   SHA256 manifest for incremental updates
│   ├── cache/              #   SHA256 extraction cache
│   ├── memory/             #   Q&A feedback loop (graphify save-result)
│   ├── merged-graph.json   #   Cross-repo merged graph (graphify merge-graphs)
│   ├── graph.svg           #   Optional: --svg export (Notion, GitHub embed)
│   ├── graph.graphml       #   Optional: --graphml export (Gephi, yEd)
│   └── cypher.txt          #   Optional: --neo4j export (Neo4j Cypher script)
│
└── CLAUDE.md               # Schema — conventions and workflows
```

## Source Directory Detection

Checked in order:
1. User-specified path (if given)
2. `gMeso/vault/` — KIM-meso project convention
3. `raw/` — Karpathy /raw pattern
4. `docs/` — common documentation folder
5. Current directory `.`

## Operating Modes

- **Graph-only** (default): Only `graphify-out/` exists. `/kg-orient`, `/kg-query`, `/kg-update` all work against the graph alone.
- **Graph + Wiki**: Both `graphify-out/` and `wiki/` exist. Wiki provides semantic depth on top of structural graph.

## Wiki Page Conventions

### Frontmatter

```yaml
---
title: Page Title
instance_of: Artifact | Concept | Procedure | Experience | Heuristic | Decision
page_kind: entity-page | concept-page | procedure-page | experience-page | heuristic-page | decision-page
epistemic_status: observed | inferred | hypothesis | validated | deprecated
confidence: high | medium | low
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
provenance:
  sources: [source-file-1.pdf]
  code_refs: ["file.F:123"]
relations:
  - {predicate: implements, target: "[[concept]]", rationale: ""}
---
```

Legacy pages (without `instance_of`) continue to work via `legacy_mode` in `core.yaml`.

### Wikilinks

Always use `[[wikilinks]]` for cross-references. This powers Obsidian's graph view and backlinks. Create links to pages that don't exist yet — Obsidian shows these as unresolved links (natural TODO list).

### Page Template Examples

Templates live at `~/.claude/skills/kg/templates/`. Each class has a template matching `core.yaml` contract.

**Artifact** (`wiki/entities/module-mp-kdm6.md`):
```markdown
---
title: module_mp_kdm6
instance_of: Artifact
page_kind: entity-page
epistemic_status: observed
provenance:
  code_refs: ["module_mp_kdm6.F"]
relations: []
---
# module_mp_kdm6

## Role
KDM6 microphysics module. Contains the main physics hotspot `kdm62D`.

## Key Facts
- Single live caller: [[module-microphysics-driver]] at line 2538
- ~2600 lines of Fortran, R8 precision

## Connections
- Called by: [[module-microphysics-driver]]
- Implements: [[register-pressure]]
```

**Heuristic** (`wiki/heuristics/item-nogradguard.md`):
```markdown
---
title: .item() 사용 시 반드시 NoGradGuard
instance_of: Heuristic
page_kind: heuristic-page
epistemic_status: validated
confidence: high
distilled_from: []
relations:
  - {predicate: prevents, target: "[[autograd-graph-break]]"}
---
# .item() 사용 시 반드시 NoGradGuard

## Rule
PyTorch 텐서에서 .item() 호출 시 반드시 torch.no_grad() 블록 안에서 수행.

## Why
.item()은 연산그래프를 끊어 자동미분이 불가능해짐. 반복된 실수 발생.

## Applies When
PyTorch autograd 컨텍스트에서 스칼라 값을 추출할 때.

## Does Not Apply When
추론 전용 코드(이미 no_grad 블록 내부).

## Evidence
CLAUDE.md Command Memories에 3회 이상 반복 경고 기록.
```

## Technical Notes

- **graph.json format**: Saved as NetworkX `node_link_data` — top-level keys are `nodes`, `links` (not `edges`). Load with `json_graph.node_link_graph(data, edges='links')`. For extraction format (with `edges` key), use `build_from_json()`. graphify's own `query`/`affected` (v0.8.39+) load both `links` and `edges` top-level keys automatically.
- **Manifest location**: `graphify-out/manifest.json` (no `.graphify_` prefix). Used by `detect_incremental()` to identify changed files. Portable since v0.8.x — keys are relative paths re-anchored on load, so committing it is safe.
- **Graphify version**: Target **`graphifyy>=0.8.24`** (recommended: latest `0.8.39`). The v0.5.x line had no Fortran support and a much smaller bare-CLI surface; the notes below describe v0.8.x. Resolve via `which graphify`; PyPI package is `graphifyy` (double-y); prefer `uv tool install graphifyy` over `pip` on macOS/Windows. For Fortran corpora (scientific/HPC code — libraries, solvers, legacy, earth-system incl. WRF; `.F`/`.f90`) see `references/fortran.md`.
- **Version detection & upgrade nudge** (kg skills surface this so a stale install is upgraded, not silently under-used): run `graphify --version` — v0.8.x prints `graphify X.Y.Z`, while **pre-0.8 versions (e.g. 0.5.x) error with `unknown command '--version'`**. Parse the `X.Y.Z`; if the command errors OR the version is `< 0.8.24`, surface this nudge:
  > ⚠ graphify `<ver | "pre-0.8">` detected. kg's v0.8.x features — Fortran extraction, `affected` impact mode, `query --context`, `cluster-only --graph`, HTTP MCP, import cycles — need **`graphifyy>=0.8.24`** (recommended `0.8.39`). Upgrade: `uv tool install --force graphifyy` (or `pip install -U 'graphifyy>=0.8.24'`), then restart the session.

  `/kg-orient` surfaces this at session start; `/kg-update` checks before extracting and treats it as **blocking for Fortran corpora** (the 0.5.x line cannot parse Fortran at all).
- **MCP server**: launched as `python -m graphify.serve <graph.json>` (or the `graphify-mcp` console script in v0.8.36+) — **not** a bare CLI flag; `graphify --mcp` is not a CLI verb. Default transport is stdio; `--transport http --port 8080 --api-key <key>` (v0.8.34+) serves a whole team from one process. Exposes graph tools `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path` plus PR tools `list_prs`, `get_pr_impact`, `triage_prs` (PR tools need a git/PR context and are usually irrelevant to a kg corpus). Soft-dependency for `/kg-query`, `/kg-orient`, `/kg-lint`, `/kg-connect`; register via `/kg-mcp register --apply`.
- **Bare CLI surface (Bash-callable, v0.8.x)**: `extract <path>` (full AST+semantic; `--mode deep`, `--postgres DSN`, `--cargo`, `--out`), `update <path>` (AST-only, no LLM; `--force` to allow node-count shrink after refactors, `--no-cluster`), `query "..."` (`--context <edge-context>`, `--dfs`, `--budget N`), `path "A" "B"`, `explain "X"`, `affected "X"` (reverse-impact traversal; `--relation R`, `--depth N`), `cluster-only <path>` (`--graph <file>`, `--no-viz`, `--no-label`, `--backend`, `--resolution N`, `--exclude-hubs N`, `--model`, `--min-community-size=N`), `label <path>`, `tree` (D3 collapsible-tree HTML), `export {html|callflow-html|svg|graphml|neo4j|falkordb|obsidian|wiki}` (svg needs matplotlib; neo4j/falkordb support `--push <uri>`), `merge-graphs`, `add <url>`, `watch <path>`, `benchmark`, `check-update`, `diagnose multigraph`, `hook install`, plus per-platform installers. The `/graphify <path> [--mode deep|--directed|--wiki|--no-viz|--obsidian|--svg|--graphml|--neo4j|--falkordb|--watch|--mcp]` **slash form** is the orchestrator skill that wraps `extract` + clustering + visualization. Its `--wiki|--obsidian|--svg|--graphml|--neo4j|--falkordb` flags are just the orchestrator spelling of the bare `export <format>` subcommands above; `--mcp` = the `python -m graphify.serve` server; `--mode deep`/`--directed`/`--watch` are extract/build modifiers. Note the bare CLI has no `--<format>` flags — `graphify <existing-path> --svg` is rewritten to `graphify extract <path>` and silently ignores the flag (no export); use `graphify export svg` instead. Prefer the bare CLI from Bash for `update`/`query`/`affected`/`path`/`explain`/`cluster-only`/`export`; use the `/graphify` slash form for first-time semantic builds over docs/papers/images.
- **Freshness gate**: Treat `graphify-out/graph.json` results as authoritative only when `mtime < 7 days`. If stale, fall back to wiki-only / BM25 paths and note the staleness in Caveats. Re-run `/kg-update` to refresh.
- **No git required** for Graphify (SHA256 cache). Wiki benefits from git for version history.
- **Cost**: Graph build ~ 1 API call per doc file. Wiki pages are part of the conversation (no extra cost). Incremental updates only process changed files.
