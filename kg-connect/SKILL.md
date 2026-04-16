---
name: kg-connect
description: Cross-community bridge discovery — find missing connections between graph communities based on semantic similarity. Co-create knowledge that neither human nor LLM could produce alone.
trigger: /kg-connect
---

# /kg-connect — Cross-Community Bridge Discovery

Find *missing bridges* between graph communities — connections that should exist based on semantic content but don't appear structurally. This is where the graph and the human co-create knowledge that neither could produce alone.

## When to invoke
- After `/kg-update` adds new nodes that might cross community boundaries
- When `/kg-reflect` surfaces a "Community X has zero inbound edges from Y" blind spot
- When a user suspects two concepts are related but wiki structure doesn't reflect it
- Not for routine maintenance — this is targeted investigation

## Prerequisite
Requires `graphify-out/GRAPH_REPORT.md` with at least 2 communities. If absent, run `/kg-update` first.

## Selection algorithm

Not all community pairs deserve attention. Prioritize in this order:

1. **High-mass, low-bridge**: pairs where both communities have ≥10 nodes but ≤2 cross-edges
2. **Recently grown**: communities that gained ≥3 nodes since last `/kg-connect`
3. **Topic-overlapping**: pairs whose representative nodes share ≥2 keywords (heuristic)
4. **Anchor-disconnected**: pairs where both contain god nodes (top 10 degree) but no direct edge

Skip pairs that are *intentionally isolated* (e.g., legacy + active) — note this in output if known.

## Steps

1. Load communities + god nodes from `graphify-out/GRAPH_REPORT.md`
2. Apply selection algorithm — pick top 3-5 candidate pairs
3. For each pair, read 2-3 representative nodes (highest degree within community)
4. Identify potential semantic relationship: shared concept, sequential dependency, complementary purpose, contradictory framing
5. **Propose** with concrete rationale: "Node A in C0 (`role`) and Node B in C4 (`role`) both deal with [shared concern] but have never been linked. Possible relation: `<predicate>`. Confidence: low/medium."
6. **Wait for user confirmation** — never auto-add edges
7. If confirmed, add edge to graph: `epistemic_status: inferred`, with `rationale` field, log to `wiki/log.md`

## Output format

```
Bridge candidate #1: C0 ↔ C4
  Anchor A: [[node-a]] (degree=12 in C0)
  Anchor B: [[node-b]] (degree=8 in C4)
  Shared concern: <one sentence>
  Proposed predicate: implements | depends_on | about | derived_from
  Confidence: low|medium
  Risk if false: <what breaks if this bridge is wrong>
```

## Risks (false bridge)

- A bridge added without user confirmation calcifies into accepted truth
- Surface-level keyword matches can hide deeper category errors (e.g., "performance" in CPU context vs perf-monitoring tool)
- Always include "Risk if false" in proposal — forces user to think before approving

## Termination

Stop when no candidate pair scores above threshold (no shared keywords, no overlap signal). Reporting "no bridges worth proposing this cycle" is a valid outcome — do not manufacture connections.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-connect`.
