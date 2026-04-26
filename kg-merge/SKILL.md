---
name: kg-merge
description: "This skill should be used when the user asks to merge graphs across multiple projects, build a cross-repo knowledge graph, says '여러 프로젝트 통합 그래프', 'cross-project KG', 'merge graphs', or invokes /kg-merge. Reads each project's graphify-out/graph.json and produces a unified graphify-out/merged-graph.json via graphify v0.5.0+ merge-graphs. Read-only on source projects."
trigger: /kg-merge
---

# /kg-merge — Cross-Project Knowledge Graph

Combine multiple projects' graphify-out/ artifacts into one unified graph for cross-repo query, exploration, and visualization. Hard-depends on graphify v0.5.0+ (`graphify merge-graphs`).

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

- `graphify` CLI v0.5.0+ installed (`which graphify`); `graphifyy` PyPI package
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
   - Total nodes, total edges, total communities (after Leiden re-clustering)
   - Per-source contribution: nodes from each source, overlap (label collision)
   - Cross-source bridges: edges connecting nodes from different sources (most interesting signal)

5. **Optional: regenerate cross-repo report**
   - If user wants a `MERGED_GRAPH_REPORT.md`, run `graphify cluster-only <merged-graph.json>` to regenerate report from merged graph.

## graphify CLI integration

```bash
# Inspect input graphs
graphify explain "<node-label>" --graph <project>/graphify-out/graph.json

# Merge
graphify merge-graphs <g1> <g2> <g3> --out graphify-out/merged-graph.json

# Re-cluster the merged result if needed
graphify cluster-only graphify-out/merged-graph.json

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
Total communities (post-Leiden): <K>

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

- **graphify CLI not found** → stop, suggest `pip install graphifyy`.
- **Fewer than 2 sources** → stop; merge needs ≥2 inputs.
- **Source `graph.json` missing** for any specified project → report exact path, stop. Do not silently skip.
- **All sources stale (≥7d)** → require explicit user confirmation to merge stale data; default behavior is to suggest refreshing via `/kg-update` first.
- **Output path overwrites a non-merged `graph.json`** → refuse. Resolve the proposed `--out` path to its canonical absolute form (`Path.resolve()`), then refuse if it equals the canonical path of `graphify-out/graph.json` for the cwd OR for any input source. Symlinks resolve to their target; relative paths resolve against cwd. The output must be `merged-graph.json` or any path that does not collide with an input `graph.json`.
- **Never modify** input project sources, their `wiki/`, or their `graphify-out/graph.json`. This skill is read-only on inputs and write-only to the merged output.

## Quality Gates

Before final answer:
- [ ] All input source paths verified before merge starts
- [ ] Output path does not overwrite any input `graph.json`
- [ ] Per-source freshness reported in Output Contract
- [ ] Cross-source bridge count surfaced (this is the merge's main value-add)
- [ ] At least one `Next command` actionable on the merged graph
