# Schema Review Prompt — Codex Independent Evaluator

Use this template when `/kg-schema approve --codex-review` is invoked.
The prompt is sent to Codex via `codex:rescue` with the proposal and receipt attached.

## Prompt Template

```xml
<task>
Review this kg ontology schema proposal as an independent evaluator.
You have NOT seen the proposal creation process — evaluate it with fresh eyes.

Proposal:
{proposal_yaml}

Current schema (core.yaml):
{core_yaml}

Receipt from automated sensors:
{receipt_json}

Evaluate:
1. Is the change well-motivated? Does the rationale justify the schema evolution?
2. Is it backward-compatible? Will existing legacy/transitional pages break?
3. Is the evidence sufficient? Do cited pages actually support this change?
4. Is the migration path clear? Can affected pages be updated incrementally?
5. Are there unintended consequences? New predicate collisions, class overlaps, etc.
</task>

<structured_output_contract>
Return exactly:
1. verdict: APPROVE | CONCERN | REQUEST_CHANGES
2. confidence: high | medium | low
3. findings: [{severity: "required"|"advisory"|"insight", description: "..."}]
4. residual_risks: ["..."]
5. recommendation: one-sentence summary
</structured_output_contract>

<grounding_rules>
Ground every claim in the proposal YAML, receipt data, or current schema.
Do not invent failure modes not supported by the evidence.
If a check is inconclusive, say so — do not guess.
</grounding_rules>

<verification_loop>
Before finalizing, verify:
- Each finding is material and actionable
- The verdict matches the severity of findings
- No contradiction between findings and verdict
</verification_loop>
```

## How to use

1. Read the proposal YAML file
2. Read current `wiki/.schema/core.yaml`
3. Read the receipt (if already collected)
4. Interpolate into the template above
5. Send via `/codex:rescue` with `--write` disabled (read-only review)
6. Parse the structured output
7. Record verdict in receipt under `codex_review` key
