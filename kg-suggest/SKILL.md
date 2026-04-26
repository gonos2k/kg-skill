---
name: kg-suggest
description: "This skill should be used when the user asks what to read, ingest, research, or improve next in the kg wiki, says '다음에 뭘 봐야 해?', '지식 공백 찾아줘', or invokes /kg-suggest. Recommends 3-5 concrete next sources or maintenance actions based on unresolved links, stale topics, low-cohesion communities."
trigger: /kg-suggest
---

# /kg-suggest — Next Source Recommendation

Based on current knowledge gaps in the wiki, suggest what to ingest or read next. Goal is to strengthen the knowledge base where it is genuinely thin, not to expand for its own sake.

## Activate When

- User asks "다음에 뭘 봐야 해?", "지식 공백 찾아줘", "what should I read next?", "what should I ingest next?"
- Session start, after `/kg-orient`, when no specific work is queued
- After `/kg-reflect` surfaces blind spots
- Before deciding what external research to commission (`/kg-autoresearch`)

## Do Not Activate When

- User wants to query existing knowledge → `/kg-query`
- User wants to actually run research → `/kg-autoresearch`
- User has open `/kg-elicit` or `/kg-postmortem` queue → finish those first

## Detection priority

Scan in this order (cheapest signals first):

1. **Unresolved `[[wikilinks]]`** — pages referenced but not created. Read via grep for `[[name]]` not matching any existing page filename.
2. **Orphan concepts** — concepts mentioned in 3+ source pages but no dedicated `concepts/<name>.md`.
3. **Low-cohesion communities** — graph communities where internal edge density < 0.3 (run `/kg-update` if graph is stale).
4. **Stale topics** — pages whose `date_modified` is >30 days old AND whose `provenance.sources` are all >60 days old.
5. **Single-source claims** — pages with only 1 cited source. Vulnerable to source removal.

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- Call `god_nodes(top_n=10)` to identify anchor concepts; suggest reading any anchor that has `wiki/concepts/<name>.md` missing
- Call `get_community(community_id)` for low-cohesion communities to identify the "central but undocumented" nodes that would most strengthen the community
- If graph stale (≥7d), fall back to wiki-only signals (steps 1-2-4-5) and note in Caveats.

## Output format (per item)

Return 3-5 specific suggestions, each with action and rationale:

```
Suggestion #1: Ingest source covering <topic>
  Why: referenced 4 times across [[a]], [[b]], [[c]], [[d]] but never directly addressed
  Action: `/kg-ingest <file>` or `/kg-autoresearch "<topic>"`
  Estimated impact: orphan concept resolved, 1 wiki page created

Suggestion #2: Update [[stale-page]]
  Why: last modified 45 days ago, all 2 sources are 90+ days old
  Action: re-read source files, update Current Status section
  Estimated impact: confidence refresh, possible supersession discovery
```

## Skip conditions

- Knowledge base has ≥80% convergence (active frontier) — additional ingest may not be ROI-positive
- Last 3 ingests in same domain — diminishing returns, suggest different topic
- User has open `/kg-elicit` or `/kg-postmortem` queue — finish those first

## Quality bar

- Each suggestion cites concrete evidence (page names, dates, counts) — no vague "consider studying X"
- Estimated impact is honest — not all suggestions will resolve cleanly
- If no genuine gaps detected, say so: "Knowledge base is well-covered for the active frontier. Suggest reflect cycle instead."

## Distinction from related ops

- `/kg-autoresearch` *executes* research; `/kg-suggest` *plans* what to research
- `/kg-reflect` finds tensions in existing knowledge; `/kg-suggest` finds gaps where knowledge is thin
- `/kg-connect` finds missing graph edges; `/kg-suggest` finds missing source ingests

## Output Contract

```text
Suggestion result: <N> suggestions | no genuine gaps

Suggestion #1: <action verb + topic>
- Why: <count + page citations + dates>
- Evidence: [[page-a]], [[page-b]], ...
- Action: <`/kg-ingest <file>` | `/kg-autoresearch "<topic>"` | `update [[page]]`>
- Per-item confidence: high | medium | low
- Estimated impact: <one sentence — orphan resolved, claim strengthened, etc.>
- Priority: high | medium | low

(Suggestion #2 ... up to 5)

Confidence: high | medium | low

Caveats:
- <graph stale | small corpus | active frontier saturated | none>

Next command:
- <one suggestion's Action, or "none — wiki well-covered">
```

## Exceptions and Escalation

- **Knowledge base has no real gaps** → say "well-covered for the active frontier; suggest /kg-reflect instead". Do not invent suggestions.
- **User has pending postmortem/elicit queue** → suggest finishing that first; do not propose new ingests.
- **Do not recommend external research before checking internal coverage** (use `/kg-query --depth deep` first when in doubt).
- **Do not suggest vague topics** without page/date/count evidence.
- **Wiki absent** → suggest `/kg-init` and stop.

## Quality Gates

Before final answer:
- [ ] Every suggestion has page citations with dates or counts
- [ ] At most 5 suggestions
- [ ] At least one Action is a concrete next command
- [ ] Skip conditions checked before listing
