---
name: kg-connect
description: "This skill should be used when the user asks to find missing links between graph communities, bridge isolated concepts, connect two topics, or invokes /kg-connect. Proposes inferred semantic bridges with rationale and risk — never adds edges without user confirmation."
trigger: /kg-connect
---

# /kg-connect — Cross-Community Bridge Discovery

Find *missing bridges* between graph communities — connections that should exist based on semantic content but don't appear structurally. This is where the graph and the human co-create knowledge that neither could produce alone.

## Activate When

- User asks to "bridge isolated concepts", "find missing links", "connect two topics"
- After `/kg-update` adds new nodes that might cross community boundaries
- When `/kg-reflect` surfaces a "Community X has zero inbound edges from Y" blind spot
- When a user suspects two concepts are related but wiki structure doesn't reflect it
- Not for routine maintenance — this is targeted investigation

## Do Not Activate When

- User wants to query existing knowledge → `/kg-query`
- User wants graph drift signals → `/kg-reflect`
- User wants to test a single claim → `/kg-challenge`
- Routine scan / lint → `/kg-lint`

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

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- Call `get_community(community_id)` to enumerate community members objectively (vs reading GRAPH_REPORT.md text)
- Call `shortest_path(<anchor_A>, <anchor_B>, max_hops=8)` to verify the proposed bridge isn't already implicit (existing path) — only propose when shortest_path > 3 or returns no path
- If graph stale (≥7d) → suggest `/kg-update` first; this skill cannot operate reliably on stale community structure.

## Risks (false bridge)

- A bridge added without user confirmation calcifies into accepted truth
- Surface-level keyword matches can hide deeper category errors (e.g., "performance" in CPU context vs perf-monitoring tool)
- Always include "Risk if false" in proposal — forces user to think before approving

## Termination

Stop when no candidate pair scores above threshold (no shared keywords, no overlap signal). Reporting "no bridges worth proposing this cycle" is a valid outcome — do not manufacture connections.

## Output Contract

```text
Bridge candidates: <N> | none worth proposing this cycle

Candidate #1: C<A> ↔ C<B>
- Anchor A: [[node-a]] (degree=12 in C<A>)
- Anchor B: [[node-b]] (degree=8 in C<B>)
- Shared concern: <one sentence>
- Proposed predicate: implements | depends_on | about | derived_from | <other>
- Per-item confidence: low | medium
- Risk if false: <what breaks if this bridge is wrong>
- Existing shortest_path: <N hops | no path>
- User action: approve | reject | investigate

(Candidate #2 ... up to 5)

Confidence: high | medium | low (overall scan quality)

Caveats:
- <graph stale | only 1 community | none>

Approval needed: yes (per-candidate)
For each approved candidate, edge added with epistemic_status: inferred, logged to wiki/log.md.

Next command:
- <none | /kg-update (if graph stale) | /kg-reflect>
```

## Exceptions and Escalation

- **`GRAPH_REPORT.md` absent** → stop and suggest `/kg-update`.
- **Fewer than 2 communities exist** → report "no bridge work possible".
- **Candidate similarity is keyword-only with no semantic evidence** → mark per-item confidence low; recommend rejection in output.
- **Never mutate graph or wiki without explicit user approval** per candidate (per Authority Matrix).
- **Shortest_path already short (≤3)** → do not propose; bridge is implicit.

## Quality Gates

Before final answer:
- [ ] Every candidate cites both anchor nodes
- [ ] Every candidate has "Risk if false" sentence
- [ ] Approval needed flag set
- [ ] No edge added before user approves
