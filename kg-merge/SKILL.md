---
name: kg-merge
description: "This skill should be used when the user asks to merge graphs across multiple projects, build a cross-repo knowledge graph, says '여러 프로젝트 통합 그래프', 'cross-project KG', 'merge graphs', or invokes /kg-merge. Reads each project's graphify-out/graph.json and produces a unified graphify-out/merged-graph.json via graphify v0.8.x merge-graphs. Read-only on source projects."
trigger: /kg-merge
---

# /kg-merge — Cross-Project Knowledge Graph

Combine multiple projects' graphify-out/ artifacts into one unified graph for cross-repo query, exploration, and visualization. Hard-depends on graphify v0.8.x (`graphify merge-graphs`).

## Activate When

- User asks "여러 프로젝트 통합 그래프", "cross-project KG", "cross-repo graph", "merge graphs"
- User invokes `/kg-merge <project1> <project2> [...] [--out <path>]`
- Multiple `graphify-out/` directories exist locally and user wants unified view
- Before cross-project `/kg-query` (which would otherwise need to query each separately)

## Do Not Activate When

- Single project → `/kg-update` is enough; no merge needed
- Project has wiki/ but no graphify-out/ → not applicable (this skill operates on graphs only, not wiki pages)
- User wants to query existing merged graph → `/kg-query` (which detects merged-graph.json automatically once present)

## Preconditions

- `graphify` CLI v0.8.x installed (`which graphify`; `uv tool install graphifyy`)
- ≥2 source projects each containing `graphify-out/graph.json`
- Write access to chosen `--out` location (default: `<cwd>/graphify-out/merged-graph.json`)

## Workflow

1. **Resolve sources**
   - Each positional argument is either a project root (auto-locate `graphify-out/graph.json`) or a direct `graph.json` path.
   - Verify every source exists. Report missing ones and stop.

2. **Freshness check** (per source, per `~/.claude/skills/kg/references/architecture.md` freshness gate)
   - For each source, check `graph.json mtime`.
   - **Any-stale (1+ source ≥7d)**: warn, list the stale paths in Caveats, and proceed. Suggest `/kg-update` for those sources as a Next command.
   - **All-stale (every source ≥7d)**: STOP. Require explicit user confirmation ("merge anyway") in a fresh command before proceeding. Do not auto-proceed on a "yes" response — user must re-state intent with the source list.

3. **Run merge**
   ```bash
   graphify merge-graphs <g1> <g2> [...] --out <output-path>
   ```
   - Default output: `<cwd>/graphify-out/merged-graph.json`
   - Custom output via `--out`

4. **Post-merge stats**
   - Total nodes, total edges, total communities (after re-clustering — Leiden if the optional `graspologic` extra is installed (Python<3.13), else Louvain fallback)
   - Per-source contribution: nodes from each source, overlap (label collision)
   - Cross-source bridges: edges connecting nodes from different sources (most interesting signal)

5. **Optional: regenerate cross-repo report**
   - If user wants a re-clustered report, run `graphify cluster-only --graph graphify-out/merged-graph.json merged` (v0.8.x accepts `--graph <file>` directly; writes a NEW graph at `merged/graphify-out/graph.json` — the merged-graph.json input is left untouched; see Exceptions for caveats). Use a distinct out-dir like `merged`, NOT `graphify-out` (nests) or `.` (overwrites primary graph). Community naming needs an LLM backend; without one it keeps `Community N` placeholders.

## graphify CLI integration

```bash
# Inspect input graphs
graphify explain "<node-label>" --graph <project>/graphify-out/graph.json

# Merge
graphify merge-graphs <g1> <g2> <g3> --out graphify-out/merged-graph.json

# Re-cluster the merged result if needed (v0.8.x: --graph reads the file read-only,
# writes a NEW graph under the distinct out-dir 'merged/' — input merged-graph.json untouched)
graphify cluster-only --graph graphify-out/merged-graph.json merged

# Query the merged graph
graphify query "<question>" --graph graphify-out/merged-graph.json --budget 2000
```

## Output Contract

```text
Merge result: PASS | PARTIAL | FAIL
Sources merged: <N>
- [<source-1>] graph.json — <nodes>n / <edges>e (mtime: <date>, FRESH | STALE)
- [<source-2>] graph.json — ...

Output: <merged-graph-path>
Total nodes: <N>
Total edges: <M>
Total communities (post-clustering): <K>

Cross-source bridges: <N> edges
Top bridges (by degree on each side):
- [<src-A>:node-x] ↔ [<src-B>:node-y] (predicate: <type>)
- ...

Label overlaps (same label across sources): <N>
Top overlaps:
- "<label>" appears in <N> sources

Re-clustered: yes | no | not requested
MERGED_GRAPH_REPORT.md: regenerated | skipped | not requested

Confidence: high | medium | low

Caveats:
- <N stale source(s) | label-collision count high | none>

Next command:
- graphify query "<question>" --graph <merged-path>
- /kg-canvas community <N>  (visualize merged communities)
- /kg-update <stale-source> (refresh stale source then re-merge)
```

## Exceptions and Escalation

- **graphify CLI not found** → stop, suggest `uv tool install graphifyy` (recommended over `pip`).
- **Fewer than 2 sources** → stop; merge needs ≥2 inputs.
- **Source `graph.json` missing** for any specified project → report exact path, stop. Do not silently skip.
- **All sources stale (≥7d)** → require explicit user confirmation to merge stale data; default behavior is to suggest refreshing via `/kg-update` first.
- **Output path overwrites a non-merged `graph.json`** → refuse. Resolve the proposed `--out` path to its canonical absolute form (`Path.resolve()`), then refuse if it equals the canonical path of `graphify-out/graph.json` for the cwd OR for any input source. Symlinks resolve to their target; relative paths resolve against cwd. The output must be `merged-graph.json` or any path that does not collide with an input `graph.json`.
- **Never modify** input project sources, their `wiki/`, or their `graphify-out/graph.json`. This skill is read-only on inputs and write-only to the merged output.
- **Re-clustering a merged graph (v0.8.x — limitation resolved).** The old v0.5.0 restriction (`cluster-only` rejected arbitrary file paths) **no longer applies**. v0.8.39 accepts `--graph <file>` directly — verified: `graphify cluster-only --graph graphify-out/merged-graph.json <out-dir>` reads the merged JSON via `--graph` (**read-only — the source file is NOT modified**; md5 unchanged after the run) and writes a **NEW** `<out-dir>/graphify-out/graph.json` plus `GRAPH_REPORT.md` + `graph.html`. So the re-clustered graph is a *different file* — point downstream `query`/`/kg-canvas` at it, or copy it over `merged-graph.json` to fold the communities back. Pick a **distinct** `<out-dir>` (e.g. `merged`): using `graphify-out` nests output at `graphify-out/graphify-out/graph.json`, and using `.` would overwrite the project's primary `graph.json` (violates the no-overwrite rule above). Community **naming** needs an LLM backend (an API key, or `--backend`/`--model`) — without one it keeps `Community N` placeholders (`--no-label` to skip naming). For a pure-offline alternative, load the merged JSON (`links` key) and run `networkx.community.louvain_communities(G)`.
- **`merge-graphs` does NOT auto-detect cross-source bridges** — it produces a **UNION** graph (concatenation). Bridges between conceptually-related nodes with different identifiers (e.g., your reimplementation's `EML` class vs paper's `compile_to_eml` function) require either:
  1. **Manual annotation**: post-process the merged JSON to add explicit cross-edges
  2. **LLM-based semantic matching**: out of CLI scope; use `/kg-connect` workflow on the merged graph after Claude Code restart with MCP server activated
  Empirically (2026-04-26): merging eml-net (162n/303e) + SymbolicRegressionPackage (427n/1076e) → 589n/1379e, **0 cross-source edges**, **0 label collisions** (entirely disjoint identifiers). Cross-source bridges come from semantic understanding, not graphify's union operation.

## Quality Gates

Before final answer:
- [ ] All input source paths verified before merge starts
- [ ] Output path does not overwrite any input `graph.json`
- [ ] Per-source freshness reported in Output Contract
- [ ] Cross-source bridge count surfaced (this is the merge's main value-add)
- [ ] At least one `Next command` actionable on the merged graph
