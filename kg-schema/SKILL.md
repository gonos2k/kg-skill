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

## Activate When

- User asks for "스키마 변경", "온톨로지 진화", "분류 체계 수정", "class 추가", "predicate 추가"
- `/kg-reflect` surfaced a SIG-* drift signal that the user wants to formalize
- User invokes `/kg-schema <subcommand>` (list/propose/approve/apply/migrate/diff/list/pull-global)
- Before adopting a new content pattern that would benefit from a typed predicate

## Do Not Activate When

- User wants to ingest content using existing schema → `/kg-ingest`
- User wants drift signals (not formal proposals) → `/kg-reflect`
- User wants to lint without changing schema → `/kg-lint`
- User wants to query existing schema-compliant pages → `/kg-query`

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
| `signal_staleness` | reflect, lint | references/ontology.md 규약만 (수동 검사) |
| `proposal_debt` | reflect, lint | references/ontology.md 규약만 (수동 검사) |
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

## Output Contract (per subcommand)

### `list`
```text
Schema target: per-wiki | global
Schema version: v<N>
Classes: <count> (<list>)
Predicates: <count> active, <count> deprecated
Epistemic states: <list>
Delta from global: <added | removed | renamed | none>
Pending proposals: <count> (<list>)
```

### `propose`
```text
Proposal created: yes | no
Proposal id: YYYY-MM-DD-<slug>
Type: add_class | add_relation | deprecate_class | rename | add_epistemic_state
Description: <verbatim>
Evidence:
- [[page-1]]
- [[page-2]]
Originating signal: SIG-NNN | none
Migration plan: <one-line>
Status: pending
Next command: /kg-schema approve <id>
```

### `approve`
```text
Receipt collected: yes | no
Gate result: PASS | FAIL | SKIP
Required checks:
- schema_diff:        PASS | FAIL | SKIP
- template_contract:  PASS | FAIL | SKIP
- frontmatter_valid:  PASS | FAIL | SKIP
- legacy_compat:      PASS | FAIL | SKIP
- evidence_pages:     PASS | FAIL | SKIP
Advisory checks:
- predicate_utilization: <%>
Receipt file: wiki/.schema-proposals/<id>-receipt.yaml
Proposal status: approved | rejected
Next command: /kg-schema apply <id> | (re-run after fix)
```

### `apply`
```text
Apply result: PASS | REFUSED | FAIL
Proposal id: <id>
Receipt verified: yes | no (REFUSED if no)
Old schema version: v<N>
New schema version: v<N+1>
Files changed:
- wiki/.schema/core.yaml | relations.yaml | frontmatter.yaml
Migration file: wiki/.schema/migrations/<N+1>-<slug>.yaml
Next command: /kg-schema migrate --dry-run <id>
```

**Receipt-missing policy:** apply is **REFUSED** when `wiki/.schema-proposals/<id>-receipt.yaml` is absent. Reason: receipt is the evidence gate that approve uses; bypassing it via apply would absorb the human-deliberation step into an automated path, violating Authority Matrix ("Schema change = Human"). Recovery: re-run `/kg-schema approve <id>` to regenerate receipt, then retry apply.

### `migrate`
```text
Migration mode: dry-run | apply
Proposal id: <id>
Affected pages: <count>
Pages to modify: <list with action per page>
Pages skipped: <count> (legacy carve-out | already compliant | other)
Human review needed: <list — pages where reclassification or identity change is proposed>
Next command: /kg-migrate apply | edit <page> manually
```

### `diff`
```text
Diff target: <v-old> vs <v-new> | per-wiki vs global
Added classes: <list>
Removed classes: <list>
Added predicates: <list>
Removed predicates: <list>
Renamed: <list with old → new>
Frontmatter field changes: <list>
```

### `pull-global`
```text
Pull mode: dry-run | apply
Global version: v<N>
Pinned version: v<M>
Gap: <N-M>
Compatible changes: <count> (auto-applied if --apply)
Conflicting changes: <list — require manual reconciliation>
Next command: /kg-schema pull-global --apply | reject | review
```

## Exceptions and Escalation

- **Global mutation** → require explicit `--global` flag. Never modify global schema implicitly.
- **Receipt missing on apply** → REFUSE. Suggest `/kg-schema approve <id>` to regenerate.
- **Receipt FAIL** (any Required-tier check failed) → REFUSE apply. Report specific failures.
- **Migration touches page identity or folder classification** → require user approval per affected page.
- **Pull-global has conflicting changes** → stop; do not auto-merge. Require user reconciliation.
- **Proposal age > 14 days without action** → flag as stale in next `/kg-lint`. Suggest reject if intent has shifted.
- **Subcommand unrecognized** → list valid subcommands, do not guess.

## Quality Gates

Before final answer for `apply` or `migrate`:
- [ ] Receipt file exists and Required tiers PASS or SKIP
- [ ] Migration plan lists every affected page (no silent edits)
- [ ] Human-authority changes (reclassification, deletion) are flagged separately
- [ ] `wiki/log.md` updated with proposal_id, receipt status, action taken

## Guarantees
- Schema only goes forward. `deprecate` marks dead but visible.
- Every migration has date and rationale.
- Every approve has a receipt with gate result.
- No page modifications without user naming the specific page.
- Per-wiki and global tiers are independent.
