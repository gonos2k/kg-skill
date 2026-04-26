# kg Schema Evolution

Migration policy, supersession of judgments, and convergence tracking. For the proposal/approve/receipt flow itself, see `ontology.md` § Schema as Core Product.

## Migration Policy

**Legacy pages (68 files, `type:` only, no `instance_of`):**
- Officially supported long-term. Validator treats them as warnings, not errors.
- Upgrade is opt-in: when a page is actively edited, add `instance_of` and `page_kind`. No batch rewrite.

**Transitional pages (18 files, `instance_of` set, body sections not restructured):**
- Body restructuring happens when the page is next meaningfully updated.
- Validator tracks body drift as stderr warnings. `/kg-reflect` surfaces these as schema drift signals.
- Target: within 3 months, most frequently-edited pages should be full v1.

**New pages (created after bootstrap):**
- Must be full v1 from creation. Validator enforces strictly. Templates ensure compliance.

## Supersession (판단 대체 기록)

When a new Decision replaces an old one, use the `supersedes` predicate to preserve judgment history.

### Scope

- **Decision**: primary target. When a new design choice replaces a previous one.
- **Heuristic**: optional. When a rule is refined or overridden by a better rule.
- **Experience**: excluded. Episodes are not "replaced" — they are evidence.

### Workflow (manual + semi-auto)

1. **Author creates** new Decision with `relations: [{predicate: supersedes, target: "[[old-decision]]"}]`
2. **Old page** gets `epistemic_status: deprecated` + `> [!superseded] Replaced by [[new-decision]]` callout at top
3. **If author forgets**: `/kg-reflect` detects "same `decided_for` target, newer page exists" → emits `POSSIBLE_SUPERSESSION` signal with prefilled command
4. `/kg-lint` flags deprecated pages that lack a `superseded by` callout

### Authority

Supersession = page identity change → **Human approval required** (per Authority Matrix).

## Convergence Tracking

### Active Frontier

Not all pages need to be full v1. Convergence targets the **active frontier**: pages modified in last 30 days, pages referenced in hot.md Current Focus, pages cited in recent reflect signals.

### Metrics (computed by `validate.py --summary`)

- `convergence_ratio` = full_v1 / total_pages (target: frontier >= 0.8)
- `reflect_debt` = ingests since last reflect (warn >= 3)
- `transitional_age` = days since reclassification without body restructure

### Attractor Test (4 conditions = "converging")

1. Recent 5 maintenance cycles: reflect_debt <= 2 in 4+ cycles
2. Active frontier full_v1_ratio >= 0.8, no 2-week regression
3. Threshold drift signals closed by propose or explicit reject within 2 cycles
4. No transitional page in hot set older than 21 days

### Fixpoint (operational definition)

Last 3 `/kg-reflect` runs produce no new drift signals above threshold, pending proposals = 0, active frontier new pages = 100% template-compliant. Cold legacy excluded from this judgment.
