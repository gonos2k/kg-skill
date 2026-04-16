---
name: kg-autoresearch
description: Autonomous multi-round web research loop (자율 웹 조사/자료조사/문헌 검토). Decomposes a topic into angles, searches, fetches, extracts findings, and queues results for user approval before filing into the wiki. Governed by research-policy.yaml. Use when /kg-query --depth deep says "insufficient wiki coverage" or 새로운 주제를 체계적으로 조사할 때.
trigger: /kg-autoresearch
---

# /kg-autoresearch — Supervised Autonomous Research

Autonomy with guardrails. The loop runs unsupervised, but nothing enters the wiki without user approval.

## Preconditions
- Wiki bootstrapped (`/kg init` has run)
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
- When the wiki itself is not bootstrapped (run `/kg init` first)
