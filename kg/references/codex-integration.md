# kg ↔ Codex Integration (양방향 파이프라인)

Bidirectional pipeline between the kg wiki and Codex CLI reviews/rescues.

## Codex → kg: Review Result Structuring

When Codex performs code reviews (`/codex:review`, `/codex:rescue`), the findings can be filed into the wiki as structured knowledge.

**Workflow** (manual trigger, not automatic):

1. After Codex review completes, user says "kg에 기록" or LLM suggests filing
2. Parse Codex output: findings array with severity, description, location
3. Create `wiki/experiences/codex-review-<date>-<slug>.md` with Experience template:
   - Context: what was reviewed and why
   - Attempted: what the code tried to do
   - Outcome: Codex findings (severity-ordered)
   - Lesson: actionable takeaway
4. If the same pattern appears in 3+ Codex reviews → suggest Heuristic promotion via `/kg-elicit`
5. Update `wiki/log.md` and `wiki/hot.md`

**Pattern detection**: When filing a Codex review, check existing experiences for recurring themes:

- Same file/module flagged repeatedly → architectural issue
- Same error pattern across reviews → candidate Heuristic
- Contradicts an existing Heuristic → tension, surface in next reflect

## kg → Codex: Domain Context Injection

When invoking Codex for reviews or tasks, the LLM can enrich the prompt with kg context.

**`<domain_context>` block** (added to Codex prompts when relevant):

```xml
<domain_context>
Project heuristics (from wiki/heuristics/):
{relevant_heuristics — max 5, selected by topic match}

Active decisions (from wiki/decisions/):
{relevant_decisions — max 3, most recent first}

Known tensions (from wiki/hot.md):
{current_tensions — max 3}
</domain_context>
```

**Selection logic**:

1. Read `wiki/hot.md` for current focus
2. Match Codex task topic against heuristic `applies_when` fields
3. Match against decision `decided_for` targets
4. Include only items with `confidence: high` or `epistemic_status: validated`
5. Cap at ~500 tokens to keep Codex prompt lean

**When to inject**: automatically when `/codex:rescue` or `/codex:review` is invoked and `wiki/heuristics/` has content. Skip if `--no-kg-context` flag is set.
