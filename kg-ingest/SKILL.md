---
name: kg-ingest
description: Ingest source files into the wiki — read, discuss key takeaways, write source/entity/concept pages with wikilinks. Requires wiki/ to be initialized (run /kg-init first).
trigger: /kg-ingest
---

# /kg-ingest — Ingest Sources into Wiki

Turn raw source material into wiki pages while preserving provenance and contradictions. This skill writes derived wiki content; it never modifies the raw source.

## Activate When

- User invokes `/kg-ingest <file>` or `/kg-ingest <folder>`
- User says "이 문서를 wiki에 넣어줘", "자료 인제스트", "README를 지식베이스에 반영"
- User pastes a long-form source and asks to summarize-and-file

## Do Not Activate When

- Source is external web content not yet downloaded → use `/kg-autoresearch` first
- User wants to query existing knowledge → `/kg-query`
- User wants to capture tacit knowledge from conversation → `/kg-elicit`

## Preconditions

- `wiki/` exists. If not, stop and suggest `/kg-init`.
- Source file/folder is readable.

## Workflow

### 1. Read source

Read the full source when feasible. For huge files, build a section map first and ingest section by section.

### 2. Extract & discuss

- 3-5 key takeaways
- Candidate entities (artifacts, modules, files)
- Candidate concepts (abstract ideas, principles)
- Explicit claims with evidence snippets

### 3. Plan writes

Present the planned writes before touching any file:

```
Plan:
  Create: <list of new pages with proposed instance_of class>
  Update: <list of pages and what will be added/appended>
  Possible tensions: <list of contradictions with existing claims, or "none">
```

**Confirmation gate (deterministic triggers — request user input when ANY is true):**

1. **Name collision**: title-string similarity ≥ 0.7 between proposed page name and any existing page filename. Use Python's `difflib.SequenceMatcher(None, new_title, existing_title).ratio()` (range [0,1], stdlib only — **not** BM25, which is for query-document relevance, not name comparison). Compare against every file in `wiki/<folder>/*.md`; flag if any pair scores ≥ 0.7.
2. **Class judgment**: proposed `instance_of` is one of multiple plausible classes (e.g., Concept vs Procedure, Artifact vs Concept) AND the source folder has no clear precedent.
3. **Contradiction**: source claim contradicts an existing page with `epistemic_status: validated` OR `confidence: high`.

**Optional graph-based trigger (graphify soft dependency):**
- If `graphify-out/graph.json` exists AND `mtime < 7 days` (freshness gate), additionally trigger when:
  - `graphify shortest_path "<new_entity>" "<best_difflib_match>" --max-hops 3` returns ≤ 2 hops (graph-distance proximity to the closest existing title found in Trigger 1).
- If graph is stale (≥ 7 days) or absent, skip this check and note "graph unavailable, name-similarity-only confirmation" in Caveats.

Otherwise proceed automatically. Default behavior matches Authority Matrix: page identity/classification = Human (when triggered), routine bookkeeping = LLM (see `~/.claude/skills/kg/references/authority-matrix.md`).

### 4. Write content pages

- `wiki/sources/<slug>.md` — source summary with provenance and frontmatter
- `wiki/entities/<entity>.md` — create or append (preserve existing claims)
- `wiki/concepts/<concept>.md` — create or append with rationale
- Use `[[wikilinks]]` for cross-references
- **Never erase contradictory older claims.** If contradiction exists, add a `> [!warning] Tension` callout citing both sources.

### 5. Update derived files

- `wiki/<folder>/_index.md` — folder index
- `wiki/index.md` — main catalog
- `wiki/overview.md` — keep under 500 words
- `wiki/log.md` — append entry

### 6. Refresh graph

- Run `/kg-update` (or suggest if a separate session manages the graph)

### 7. Elicitation sweep

Scan source text + recent conversation for trigger keywords: `실패`, `주의`, `반복`, `명심`, `비법`, `failed`, `gotcha`, `pitfall`, `lesson learned`.

- If found: invoke `/kg-elicit` with the keyword context as the topic.
- If not found but source is a postmortem-style doc (headings like "What went wrong", "Root cause", "Lessons"): suggest `/kg-postmortem`.
- **Codex review output** — if source is a Codex review with structured findings: file to `wiki/experiences/codex-review-<date>-<slug>.md`. Recurring patterns (3+ reviews) → suggest Heuristic promotion via `/kg-elicit`. See `~/.claude/skills/kg/references/codex-integration.md`.
- This step is skippable; don't block ingest on it.

### 8. Update `wiki/hot.md`

Add the ingested source to Recent Activity. Increment `reflect_debt` in Maintenance Debt.

### 9. Reflect reminder

If this is the 3rd+ ingest since last `/kg-reflect`, append:
> Reflect 권장 — 이번 세션에서 `/kg-reflect`를 실행하면 schema drift와 emerging pattern을 확인할 수 있습니다.

This is a suggestion, not a gate.

## Batch mode

If many files, ask "all at once or one by one?" Batch mode:

**Pre-scan (mandatory, before any write):**
1. Extract candidate entity names + proposed `instance_of` from all files
2. For each candidate, evaluate the 3 deterministic Confirmation gate triggers (name collision / class judgment / contradiction)
3. If graphify available and fresh, additionally evaluate the graph-distance trigger
4. Collect `(file, candidate, trigger_reason)` tuples where any trigger fires
5. Show consolidated **conflict list** to user
6. User decides: batch-approve all conflicts | per-file decision | cancel

**Auto-proceed for non-triggering writes** — these run via parallel subagents without per-file confirmation.

**Skipped in batch:** per-file discussion, elicitation sweep (suggest manual `/kg-elicit` after batch finishes).

**Rationale:** confirmation gate is preserved at the batch boundary, not bypassed. Single approval covers all conflicting files; clean files run automatically.

## Output Contract

Always end with:

```text
Ingest result: PASS | PARTIAL | FAIL
Source: <path>
Source page: [[sources/<slug>]]
Created pages:
- [[...]]
Updated pages:
- [[...]]
Tensions found:
- <none | list with citations>
Claims extracted:
- <N> claims, <M> with direct evidence
Indexes updated:
- index.md, <folder>/_index.md, overview.md, log.md, hot.md
Next command:
- /kg-update: <recommended | already run>
- /kg-reflect: <recommended if reflect_debt >= 3 | not needed>
```

## Examples

### Example 1 — single file, no ambiguity

User:
```text
/kg-ingest docs/architecture/auth-system.md
```

Expected behavior:
1. Read full file.
2. Discuss 3-5 takeaways with user.
3. Show plan (e.g., create `concepts/auth-flow.md`, update `entities/auth-service.md`). No ambiguity → proceed without confirmation.
4. Write all files with provenance.
5. Update indexes/log/hot.
6. Suggest `/kg-update`.
7. Output result block.

### Example 2 — contradiction found

User:
```text
/kg-ingest docs/perf-2026-q2.md
```

Expected behavior:
- During Plan writes, detect that source claims "Module X is the bottleneck" but existing `concepts/perf-bottleneck.md` (epistemic_status: validated) says "Module Y is the bottleneck".
- **Stop and ask**: "Source contradicts validated claim in [[perf-bottleneck]]. Options: (a) write as Tension callout citing both, (b) update existing page to mark old claim deprecated, (c) skip this claim."
- Apply chosen option. Never silently overwrite.

## Exceptions and Escalation

- **Source unreadable** → stop before writing; report file path.
- **Wiki absent** → stop and suggest `/kg-init`.
- **Source is web URL** → stop and suggest `/kg-autoresearch` (which queues for approval before ingest).
- **Conflict with high-confidence claim** → stop in Plan writes, request user resolution. Never auto-resolve.
- **Candidate Heuristic appears in source** → ask before invoking `/kg-elicit`. Do not auto-promote Experience to Heuristic.
- **Batch mode**: skip the per-file gates but produce a final consolidated write report and a list of items requiring user follow-up.

## Quality Gates

Before final answer:
- [ ] Every created page has provenance (`provenance.sources`)
- [ ] Every contradiction is preserved (Tension callout, not silent overwrite)
- [ ] Indexes (`index.md`, `<folder>/_index.md`) include the new pages
- [ ] `log.md` has the ingest entry
- [ ] `hot.md` Recent Activity reflects this ingest
