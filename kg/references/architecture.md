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
├── graphify-out/           # Structural graph layer (graphify v0.5.0+)
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

- **graph.json format**: Saved as NetworkX `node_link_data` — top-level keys are `nodes`, `links` (not `edges`). Load with `json_graph.node_link_graph(data, edges='links')`. For extraction format (with `edges` key), use `build_from_json()`.
- **Manifest location**: `graphify-out/manifest.json` (no `.graphify_` prefix). Used by `detect_incremental()` to identify changed files.
- **Graphify CLI**: Resolve via `which graphify`. Package name on PyPI is `graphifyy` (double-y). v0.5.0+ removed the `.graphify_python` interpreter sidecar.
- **MCP server**: `/graphify <path> --mcp` (slash-command orchestrator, **not** raw CLI — bare `graphify --mcp` returns `error: unknown command '--mcp'` in v0.5.0) exposes 7 stdio tools (`query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`). Use as soft-dependency in `/kg-query`, `/kg-orient`, `/kg-lint`, `/kg-connect` when available, typically registered via `/kg-mcp register --apply`.
- **CLI vs slash-command surface**: graphify v0.5.0 CLI exposes only a small set of subcommand-first verbs (`update <path>`, `path "A" "B"`, `query "..."`, `explain "X"`, `cluster-only <path>`, `add <url>`, `watch <path>`, `merge-graphs`, `clone`, `install`, `benchmark`, `check-update`, `hook`, plus per-platform installers). Flags like `--mcp / --svg / --graphml / --neo4j / --update / --mode deep / --directed / --watch / --html / --wiki` are **slash-command-only** features implemented by the graphify SKILL orchestrator (subagents + library calls). When a kg skill needs one of these, route via `/graphify <path> --<flag>`, not Bash.
- **Freshness gate**: Treat `graphify-out/graph.json` results as authoritative only when `mtime < 7 days`. If stale, fall back to wiki-only / BM25 paths and note the staleness in Caveats. Re-run `/kg-update` to refresh.
- **No git required** for Graphify (SHA256 cache). Wiki benefits from git for version history.
- **Cost**: Graph build ~ 1 API call per doc file. Wiki pages are part of the conversation (no extra cost). Incremental updates only process changed files.
