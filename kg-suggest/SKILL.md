---
name: kg-suggest
description: Recommend what to read or ingest next based on knowledge gaps — orphan concepts, low-cohesion communities, unresolved wikilinks, stale topics.
trigger: /kg-suggest
---

# /kg-suggest — Next Source Recommendation

Based on current knowledge gaps in the wiki, suggest what to ingest or read next. Goal is to strengthen the knowledge base where it is genuinely thin, not to expand for its own sake.

## When to invoke
- Session start, after `/kg-orient`, when no specific work is queued
- After `/kg-reflect` surfaces blind spots
- Before deciding what external research to commission (`/kg-autoresearch`)
- When user asks "what should I read next?"

## Detection priority

Scan in this order (cheapest signals first):

1. **Unresolved `[[wikilinks]]`** — pages referenced but not created. Read via grep for `[[name]]` not matching any existing page filename.
2. **Orphan concepts** — concepts mentioned in 3+ source pages but no dedicated `concepts/<name>.md`.
3. **Low-cohesion communities** — graph communities where internal edge density < 0.3 (run `/kg-update` if graph is stale).
4. **Stale topics** — pages whose `date_modified` is >30 days old AND whose `provenance.sources` are all >60 days old.
5. **Single-source claims** — pages with only 1 cited source. Vulnerable to source removal.

## Output format

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

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-suggest`.
