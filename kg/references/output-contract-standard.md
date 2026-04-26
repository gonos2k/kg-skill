# Output Contract Standard (PR 3+)

Standard fields for the `## Output Contract` section in every kg-* sub-skill. Defined here to prevent the field-name divergence Codex flagged in PR 3 review (`Confidence` vs `per-source confidence`, `Suggested next step` vs `Follow-up` vs `Next command`, etc.).

## Purpose

When sub-skills produce structured final output (the fenced ```text``` block), they must use these field names so users and downstream skills can parse results consistently across all 16 sub-skills.

## Standard Fields

### Top-line outcome (always first)

```text
<Operation> result: PASS | FAIL | PARTIAL | REFUSED
```

Use the operation name (e.g., `Ingest result`, `Apply result`, `Lint result`). For read-only skills (kg-query, kg-orient), omit this line.

### Read-only skills (kg-query, kg-orient, kg-suggest)

```text
Answer: | Orientation: | Suggestion:
<content>

Evidence read:
- hot.md: yes | no
- overview.md: yes | no
- wiki pages: [[a]], [[b]]
- raw sources: <none | list>
- graph traversal: <none | depth-N from [[anchor]]>

Confidence: high | medium | low

Caveats:
- <missing evidence | stale data | contradictions | none>

Next command:
- <none | /kg-X "..." | read [[page]]>
```

### Write skills (kg-ingest, kg-elicit, kg-postmortem, kg-update)

```text
<Operation> result: PASS | PARTIAL | FAIL

Created pages:
- [[...]]
Updated pages:
- [[...]]
Indexes updated:
- index.md, <folder>/_index.md, log.md, hot.md

Caveats:
- <tensions | stale | none>

Next command:
- <none | /kg-update | /kg-reflect>
```

### Schema/governance skills (kg-schema)

Subcommand-specific contracts (already in kg-schema). Use `Next command:` for chained subcommands.

### Approval-gated skills (kg-autoresearch)

```text
<Operation> result: PASS | PARTIAL | FAIL

<Items queued: N | other counts>

Per-item summary:
- ...

Approval needed: yes | no
For each <item>, user chooses: approve | reject | defer

Caveats: ...

Nothing ingested yet: yes
```

The `Approval needed:` field is **separate from** `Next command:` — it represents a human-input gate, not a computational suggestion. Both can coexist in the same Output Contract.

## Field name table

| Field | Used by | Meaning |
|---|---|---|
| `<Op> result:` | write/governance skills | top-line outcome |
| `Answer:` / `Orientation:` / `Suggestion:` | read skills | primary content |
| `Confidence:` | all | overall result confidence (single value) |
| `Per-item confidence:` | list-output skills | inline per-item when listing multiple results |
| `Evidence read:` | read skills | what was consulted (transparency) |
| `Caveats:` | all | missing evidence, stale data, contradictions, or "none" |
| `Next command:` | all | exactly one suggested follow-up command, or "none" |
| `Approval needed:` | autoresearch + any human-gated skill | user input required before continuing |

## Deprecated field names (do not use)

| Old | Replace with |
|---|---|
| `Suggested next step:` | `Next command:` |
| `Follow-up:` | `Next command:` |
| `Recommended next:` | `Next command:` |

Sub-skills that previously used deprecated names must migrate. PR 3+ enforces this through `Next command:` only.

## Why this matters

- **Cross-skill chaining**: when kg-query suggests `/kg-autoresearch`, the user (or another skill) parses `Next command:` deterministically.
- **Cost of inconsistency**: 11 PR-4 sub-skills × 3 different field names = 33 surface-area variations. Standard collapses to 1.
- **Codex enforceability**: simple grep test — no skill body should contain the deprecated names.
