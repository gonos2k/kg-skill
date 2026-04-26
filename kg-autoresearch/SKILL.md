---
name: kg-autoresearch
description: Autonomous multi-round web research loop (자율 웹 조사/자료조사/문헌 검토). Decomposes a topic into angles, searches, fetches, extracts findings, and queues results for user approval before filing into the wiki. Governed by research-policy.yaml. Use when /kg-query --depth deep says "insufficient wiki coverage" or 새로운 주제를 체계적으로 조사할 때.
trigger: /kg-autoresearch
---

# /kg-autoresearch — Supervised Autonomous Research

Autonomy with guardrails. The loop runs unsupervised, but nothing enters the wiki without user approval.

## Activate When

- User asks for "자율 웹 조사", "자료조사", "문헌 검토", "literature review"
- `/kg-query --depth deep` returned "insufficient wiki coverage" for the topic
- User wants systematic external research on a new topic
- User invokes `/kg-autoresearch "<topic>"`

## Do Not Activate When

- Question answerable from existing wiki → `/kg-query --depth deep` first
- Topic is internal/proprietary (autoresearch uses public web)
- Wiki not bootstrapped (need `/kg-init` first)
- User wants to ingest a specific file they already have → `/kg-ingest <file>`

## Preconditions
- Wiki bootstrapped (`/kg-init` has run)
- `wiki/.schema/research-policy.yaml` — auto-injected at runtime if absent (see below)

## Runtime Precondition: research-policy injection
Before running any round, check if `wiki/.schema/research-policy.yaml` exists.
If not:
1. Copy from global: `cp ~/.claude/skills/kg/schema/research-policy.yaml wiki/.schema/`
2. Create staging folder: `mkdir -p wiki/.research-queue/{approved,rejected}`
3. Log: `[YYYY-MM-DD] autoresearch | injected research-policy.yaml (v1.1 upgrade)`
This is idempotent — if the file already exists, skip silently.

## Flow

### Round 0: Decompose
1. Read `hot.md` for current context
2. Decompose topic into 3-5 research angles
3. Present angles to user for add/remove/modify
4. Lock angles

### Rounds 1-N (governed by `max_rounds`):
For each angle:
1. **Search**: `WebSearch` with the angle. Respect `source_preferences`.
2. **Fetch**: `WebFetch` each URL. Track cumulative tokens.
3. **Extract**: Key claims with quotes, relevance, confidence, contradictions.
4. **Queue**: Write to `wiki/.research-queue/<round>-<angle-slug>-<N>.md` with queue-specific frontmatter (NOT ontology types):
   ```yaml
   ---
   title: [Source Title]
   queue_status: pending
   date: YYYY-MM-DD
   url: [source URL]
   angle: [research angle]
   round: N
   confidence: medium
   claims: []
   ---
   ```
5. **Gap analysis**: Under-covered angles? Emerging sub-angles?

### Final: Present & Approve
1. Show summary: N sources queued, K contradictions.
2. For each queued source:
   - **approve** → re-fetch original URL, run `/kg-ingest` on fetched content. Move queue file to `approved/`.
   - **reject** → move to `rejected/`
   - **defer** → leave in queue
3. Update `hot.md` and `log.md`.

## Safety
- `auto_ingest: false` by default.
- Token budget enforced per round AND cumulative.
- Source URLs logged for provenance.

## When NOT to use
- When the question is answerable from existing wiki (`/kg-query --depth deep` first)
- When the topic is internal/proprietary (autoresearch uses web)
- When the wiki itself is not bootstrapped (run `/kg-init` first)

## Output Contract

Always return:

```text
Research topic: <topic>

Angles locked:
- <angle 1>
- <angle 2>
- <angle 3-5>

Sources queued: <N>
Contradictions found: <K>

Queue files:
- wiki/.research-queue/<round>-<angle-slug>-<N>.md (×N)

Per-source summary:
- [<title>] <url> | confidence: high|medium|low | <one-line claim>

Approval needed:
For each queued source, user chooses:
- approve → re-fetch, run /kg-ingest, move queue file to approved/
- reject  → move queue file to rejected/
- defer   → leave in queue for next session

Nothing ingested yet: yes
```

The last line ("Nothing ingested yet: yes") is **mandatory**. It is the operational guarantee that no wiki content was written without explicit user approval per source.

## Examples

### Example 1 — fresh topic, internal coverage insufficient

User (after `/kg-query --depth deep "graph database for ontology"` returned "insufficient wiki coverage"):
```text
/kg-autoresearch "graph database choices for OWL/RDF + Python ergonomics"
```

Expected behavior:
1. Inject `research-policy.yaml` if absent.
2. Decompose into 3-5 angles (e.g., RDF/OWL native stores, property graph + RDF*, Python client maturity, license/cost).
3. Lock angles after user confirmation.
4. Run rounds: search → fetch → extract → queue.
5. Present per-source summary + ask approve/reject/defer.
6. Output result block ending with "Nothing ingested yet: yes".

### Example 2 — internal-coverage check redirects user

User (without prior `/kg-query`):
```text
/kg-autoresearch "WRF microphysics scheme comparison"
```

Expected behavior:
- Stop before research starts.
- Run a quick BM25 lookup or suggest `/kg-query "WRF microphysics scheme comparison" --depth deep` first.
- Only proceed to autoresearch if internal coverage is genuinely thin.
- Reason: research costs tokens; existing wiki may already answer.

## Exceptions and Escalation

- **Topic is internal/proprietary** → stop and warn that web research is inappropriate. Suggest `/kg-query` or `/kg-elicit` instead.
- **Internal coverage is sufficient** → suggest `/kg-query` result rather than starting research.
- **Sources are low quality** → queue with `confidence: low` and recommend rejection in summary.
- **Research-policy.yaml is missing AND global copy unavailable** → stop; cannot run without policy.
- **Token budget exceeded mid-round** → stop the round, queue what was found so far, report partial result.
- **Never auto-ingest.** Approval gate is non-negotiable.

## Quality Gates

Before final answer:
- [ ] Every queued source has URL, date, angle, confidence, ≥1 direct quote
- [ ] Contradictions across sources are explicitly listed
- [ ] No queue file lacks `queue_status: pending`
- [ ] Final summary explicitly states "Nothing ingested yet"
- [ ] User approval prompt is unambiguous (approve/reject/defer per source)
