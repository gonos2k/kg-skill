# kg Ontology — Mini-Ontology Spec

The 7-class evolving mini-ontology that distinguishes `page_kind` (document format) from `instance_of` (ontology class). Schema is minimal by design and grows with use through proposal-first evolution.

## Core Classes (7)

- **Artifact** — physical code/file/data (`entities/`)
- **Concept** — abstract idea (`concepts/`)
- **Procedure** — how-to steps (`procedures/`)
- **Experience** — episodic case (`experiences/`)
- **Heuristic** — rule of thumb / 비법 (`heuristics/`)
- **Decision** — judgment record (`decisions/`)
- **Source** — ingested source summary (`sources/`)

## Epistemic Status

Pages carry one of: `observed`, `inferred`, `hypothesis`, `validated`, `deprecated`.

- Required on: Artifact, Concept, Procedure, Heuristic.
- Optional on: Experience, Decision (these use `date` as primary metadata instead).
- `hypothesis` is distinct from `inferred`: a working guess pending evidence vs. reasoned from existing sources.

## Confidence Levels (optional)

Supplementary to epistemic status: `high`, `medium`, `low`. Required on Heuristic; optional elsewhere.

## Frontmatter Spec

See `schema/frontmatter.yaml` for required/optional fields per page_kind. Minimum example:

```yaml
---
title: Page Title
instance_of: Artifact | Concept | Procedure | Experience | Heuristic | Decision
page_kind: entity-page | concept-page | procedure-page | ...
epistemic_status: observed | inferred | hypothesis | validated | deprecated
confidence: high | medium | low
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
provenance:
  sources: [source-file.pdf]
  code_refs: ["file.F:123"]
relations:
  - {predicate: implements, target: "[[concept]]", rationale: ""}
---
```

## Legacy Page Interpretation

Existing `wiki/entities/*.md` and `wiki/concepts/*.md` pages without the new frontmatter fields are valid. The validator applies `legacy_mode` rules from `core.yaml`: implicit `instance_of`, `page_kind`, and `schema_origin: legacy`. No rewrites without explicit user approval.

## Schema Ownership (Global vs Per-Wiki Pin)

- **Global default** at `~/.claude/skills/kg/schema/` — shipped with the skill.
- **Per-wiki pin** at `<project>/wiki/.schema/` — copied on `/kg-init`. Records the exact schema version.
- All `/kg-schema` operations target the per-wiki pin by default. `--global` flag for default.
- Cross-project divergence is expected. `/kg-schema diff --global` shows drift.

## Hot Cache (`wiki/hot.md`)

~500-word compressed context summary that survives between sessions.

**Lifecycle:**
- **Session start (`/kg-orient`)**: read `hot.md` FIRST, before `index.md`.
- **After major write ops** (`/kg-ingest`, `/kg-elicit`, `/kg-postmortem`, `/kg-reflect`): overwrite with Current Focus, Recent Activity, Key Tensions.
- **Context compaction**: re-read `hot.md` to recover session state.
- The cache is a **view**, never a source of truth.

## Folder-level Indexes (`<folder>/_index.md`)

Each content folder has a lightweight `_index.md` for query routing. Updated alongside the main index on ingest/elicit operations.

## Schema as Core Product

The schema (`core.yaml` + `relations.yaml` + `frontmatter.yaml`) is not just infrastructure — it IS the domain model. Treat it as a first-class product.

### Signal-to-Proposal Contract

When `/kg-reflect` emits a drift signal (SIG-*), it must follow this lifecycle:

```
SIG detected → surfaced in reflect report → user decides:
  → `/kg-schema propose` (formalize as proposal) → approve/reject
  → explicit reject (signal marked "rejected, rationale: ...")
  → defer (signal stays, age increments)
  → 3 cycles without action → STALE escalation
```

No signal should remain unaddressed indefinitely. Reflect tracks signal age; lint flags STALE signals.

### Proposal Minimum Fields

```yaml
proposal_id: YYYY-MM-DD-<slug>
date: YYYY-MM-DD
type: add_class | add_relation | deprecate_class | rename | add_epistemic_state
description: ""
rationale: ""
evidence: []        # wikilinks to pages that motivated this
originating_signal: SIG-NNN  # link back to reflect signal
status: pending | approved | rejected
rejection_reason: ""  # if rejected, why
```

### Receipt-Based Evidence (Deep Suite Pattern)

Every schema approve collects a structured receipt before proceeding. The receipt is the gate — no approve without evidence.

**Receipt collection**: `validate.py --receipt` runs all sensors and outputs JSON:
```bash
python3 ~/.claude/skills/kg/schema/tools/validate.py \
  --receipt --schema-dir wiki/.schema \
  --wiki-root wiki/ --proposal wiki/.schema-proposals/<id>.yaml \
  wiki/**/*.md
```

**Receipt checks** (6 sensors):
| Check | Tier | Auto-fixable | What it validates |
|-------|------|:---:|---|
| `schema_diff` | Required | ❌ | target_version = current + 1 |
| `template_contract` | Required | ✅ | templates match core.yaml class definitions |
| `frontmatter_valid` | Required | ✅ | all pages pass frontmatter validation |
| `legacy_compat` | Required | ❌ | legacy/transitional pages unaffected |
| `evidence_pages` | Required | ❌ | cited evidence pages exist |
| `predicate_utilization` | Advisory | ❌ | % of predicates in active use |

**Gate rule**: All Required checks must be PASS or SKIP. Advisory is reported but doesn't block. Missing data = SKIP, not FAIL.

**Sensor loop**: auto-fixable failures (template, frontmatter) trigger fix → re-run, max 3 rounds. Non-fixable failures → human escalation.

**Receipt file**: written to `.schema-proposals/<id>-receipt.yaml` alongside the proposal.

### Schema Health Indicators (tracked in hot.md Maintenance Debt)

- `proposal_debt`: pending proposals not acted on for 2+ cycles
- `signal_staleness`: SIG-* surfaced 3+ times without propose/reject
- `predicate_utilization`: % of defined predicates used at least once in wiki
- `receipt_coverage`: % of approved proposals with receipt (target: 100%)

## How the Ontology Grows (Meta-Process)

The schema is a living artifact. Growth follows a bounded loop:

1. **Observe** — `/kg-reflect` continuously watches for pattern drift.
2. **Propose** — drift becomes a `/kg-schema propose` entry, never an auto-change.
3. **Deliberate** — user reviews proposal. Rejection is valid and expected.
4. **Apply** — approved proposal bumps `schema_version`, writes a migration file.
5. **Migrate** — `/kg-schema migrate` walks affected pages, proposing fixes one-by-one.
6. **Record** — every change is logged with rationale, so the schema history itself becomes a knowledge artifact about how our understanding evolved.

**What we are not doing:**
- No formal reasoner. This is a mini-ontology — a typed vocabulary, not OWL.
- No auto-classification. Humans judge class membership.
- No schema rollback. We only move forward via `deprecate`.

**Why this shape:** fixed ontologies calcify; free-form wikis lose structure. The proposal loop is the narrow seam where structure and evolution meet without fighting.
