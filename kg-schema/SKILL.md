---
name: kg-schema
description: Evolve the kg ontology (온톨로지 진화/스키마 변경/분류 체계 수정). Sub-commands propose/approve/migrate/diff/list/pull-global. Changes are proposal-first; nothing is auto-applied. Per-wiki pin is default target; use --global to modify the shipped default.
trigger: /kg-schema
---

# /kg-schema — Evolve the Mini-Ontology

Schema has **two tiers**:
- **Global default** at `~/.claude/skills/kg/schema/` — what the skill ships. Touched only with `--global`.
- **Per-wiki pin** at `<project>/wiki/.schema/` — what this specific wiki uses. Default target for all sub-commands.

Every change is an explicit, logged, reversible event. The two tiers evolve independently.

## Sub-commands

### `/kg-schema list [--global]`
Show current schema version, classes, epistemic states, predicate count. Without `--global`, reads the per-wiki pin and shows delta from global if any.

### `/kg-schema propose <change-description>` or `propose --from-reflect <signal_id>`
When invoked with `--from-reflect`, pre-fills the proposal YAML from the reflect signal's evidence and suggested type. The user still reviews and confirms before the file is created.
Create a proposal file at `wiki/.schema-proposals/<YYYY-MM-DD>-<slug>.yaml`:
```yaml
proposal_id: 2026-04-11-promote-benchmark
date: 2026-04-11
target_version: 2
type: add_class   # or: add_relation, add_epistemic_state, deprecate_class, rename
description: ""
rationale: ""
evidence: []      # wikilinks to pages that motivated this
migration_plan: ""
status: pending
```
Proposals are never auto-applied.

### `/kg-schema approve <proposal-id> [--codex-review]`

Evidence-based approval with receipt collection. No approve without receipt.
Approve and Apply are **separate phases** — approve collects evidence and gates, apply modifies schema.

**Step 1: Approve phase** (receipt collection + gate judgment only — NO schema file modification)

1. Read proposal from `wiki/.schema-proposals/<id>.yaml`
2. **Collect receipt** — run sensors automatically:
   ```bash
   python3 ~/.claude/skills/kg/schema/tools/validate.py \
     --receipt --schema-dir wiki/.schema \
     --wiki-root wiki/ --proposal wiki/.schema-proposals/<id>.yaml \
     wiki/**/*.md
   ```
3. **Gate check** — receipt `gate_result` must be `PASS`:
   - Required: `schema_diff`, `template_contract`, `frontmatter_valid`, `legacy_compat`, `evidence_pages`
   - Advisory: `predicate_utilization` (reported but doesn't block)
   - If FAIL: stop, report failures, do NOT proceed
4. If `--codex-review`: send proposal + receipt to Codex independent evaluator
5. **Write receipt** to `wiki/.schema-proposals/<id>-receipt.yaml`
6. Set proposal status to `approved`, link receipt file
7. Report: "Approved with receipt. Run `/kg-schema apply <id>` to modify schema."

**Step 2: Apply phase** (separate invocation — schema files modified)

Run `/kg-schema apply <proposal-id>`:
1. Verify receipt exists and `gate_result == PASS`
2. Bump `schema_version` in `core.yaml`
3. Write new migration file `schema/migrations/v<N>.yaml` with receipt summary
4. Update `core.yaml` / `relations.yaml` / `frontmatter.yaml` as needed
5. Report downstream work: suggest `/kg-schema migrate --dry-run`

### `/kg-schema apply <proposal-id>`
Separated from approve to enforce Phase Lock. Only runs after receipt gate passes.
See Step 2 above.

**Receipt YAML structure** (written to `.schema-proposals/<id>-receipt.yaml`):
```yaml
proposal_id: <id>
date: YYYY-MM-DD
checks:
  schema_diff:       {status: PASS|FAIL|SKIP, detail: "..."}
  template_contract: {status: PASS|FAIL, detail: "...", errors: []}
  frontmatter_valid: {status: PASS|FAIL, detail: "...", errors: []}
  legacy_compat:     {status: PASS, detail: "N legacy unaffected", tiers: {...}}
  evidence_pages:    {status: PASS|FAIL, detail: "N cited, M missing"}
  predicate_utilization: {status: PASS|ADVISORY, detail: "N/M in use"}
  codex_review:      {status: PASS|SKIP, verdict: "APPROVE|CONCERN|REQUEST_CHANGES"}
gate_result: PASS|FAIL
gate_failures: []     # list of failed Required checks
reviewer: auto|codex|human
```

### `/kg-schema migrate [--dry-run] [--reclassify]`
Check which pages need updates against current schema:
- Missing required fields
- References to deprecated classes
- Orphan predicates

With `--reclassify`: additionally scans `wiki/concepts/` for pages better classified as Procedure/Experience/Heuristic/Decision. Presents proposals one-by-one for user approval.

With `--dry-run`, report only. Without, fix interactively (one page at a time, user approves each).

### `/kg-schema diff <v-old> <v-new>` or `/kg-schema diff --global`
Show delta between schema versions, or between this wiki's pin and global default.

### `/kg-schema pull-global [--dry-run]`
Upgrade per-wiki pin to latest global default:
1. Compute diff between pin and global
2. Classify changes as compatible (additive), conflicting, or overridden
3. Auto-apply compatible changes; present conflicts for user decision
4. Write migration entry recording the pull
5. Bump `pin.yaml` version

## Phase Lock (Narrow)

Schema evolution follows a phase-locked workflow. Each phase restricts which files may be modified.

```
Draft → Approve → Apply → Migrate → Validate
```

| Phase | Allowed modifications | Blocked |
|-------|----------------------|---------|
| **Draft** | `.schema-proposals/*.yaml` create/edit | `.schema/`, wiki pages |
| **Approve** | Receipt collection only (read-only + receipt write) | `.schema/`, wiki pages, proposal body |
| **Apply** | `.schema/core.yaml`, `relations.yaml`, `frontmatter.yaml`, `migrations/` | wiki pages, proposals |
| **Migrate** | Wiki page frontmatter/body (one at a time, user approval) | `.schema/`, proposals |
| **Validate** | None (read-only: `validate.py --summary`) | Everything |

**Enforcement**: LLM tracks current phase and warns if an out-of-phase modification is attempted. No hook enforcement — this is a discipline contract, not a technical lock. The receipt records which phase each action occurred in.

## Sensor Loop

Automated check → fix → re-check cycle for schema operations.

### Available sensors
Names match `validate.py --receipt` output keys exactly.

| Sensor (receipt key) | Auto-fixable | Runs during | Limitation |
|--------|:---:|---|---|
| `schema_diff` | ❌ | approve | version check only |
| `template_contract` | ✅ | approve, lint | checks global templates (per-wiki templates not yet supported) |
| `frontmatter_valid` | ✅ | approve, migrate, lint | required keys + enum only; date format/wikilink structure not checked |
| `legacy_compat` | ❌ | approve | counts tiers only; does not diff pre/post impact |
| `evidence_pages` | ❌ | approve | existence check only; content relevance not verified — cited page existing is NOT an evidence quality signal |
| `predicate_utilization` | ❌ | approve, reflect | advisory only |

**Not yet implemented in validate.py** (tracked as SKIP in receipt):
| Sensor | Runs during | Status |
|--------|---|---|
| `signal_staleness` | reflect, lint | SKILL.md 규약만 (수동 검사) |
| `proposal_debt` | reflect, lint | SKILL.md 규약만 (수동 검사) |
| `migration_dry_run` | approve | 향후 구현 예정 |
| `supersession_integrity` | lint | 향후 구현 예정 |
| `convergence_delta` | approve | 향후 구현 예정 |

### Loop protocol
```
sensor_run → results
  → auto-fixable failures? → apply fix → re-run (max 3 rounds)
  → non-fixable failures? → report to user → human escalation
  → all pass? → proceed to next phase
```

### Quality Gate tiers
- **Required** (blocks phase transition): `schema_diff`, `template_contract`, `frontmatter_valid`, `legacy_compat`, `evidence_pages`
- **Advisory** (reported, doesn't block): `predicate_utilization`, `supersession_integrity`, `signal_staleness`, `proposal_debt`
- **Insight** (informational): `convergence_delta`, `community_bridge_impact`

Missing data is `SKIP`, not `FAIL`. The gate only blocks on explicit failures.

## Guarantees
- Schema only goes forward. `deprecate` marks dead but visible.
- Every migration has date and rationale.
- Every approve has a receipt with gate result.
- No page modifications without user naming the specific page.
- Per-wiki and global tiers are independent.
