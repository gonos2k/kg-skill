---
name: kg-reflect
description: Proactive insight — surface tensions, emerging patterns, blind spots, and shifted ground in the knowledge base. Not a summary, a provocation. Triggers automatically after every 3rd ingest or on demand.
trigger: /kg-reflect
---

# /kg-reflect — Proactive Insight

Review recent activity and offer unprompted observations that make the user think.

**What to surface (pick what's genuinely present, not all):**
- **Tensions** — "Source A claims X, but source B implies Y. Which is closer to your current understanding?"
- **Emerging patterns** — "The last N sources all touch [theme]. Worth its own concept page?"
- **Blind spots** — "Community X has N nodes but zero inbound edges from Community Y. Intentional?"
- **Shifted ground** — "Early sources assumed X. Recent ones assume not-X. Wiki still reflects old framing."

**Steps (bounded sample, not full scan):**
1. Read `wiki/hot.md` + `wiki/overview.md` for current context
2. Read `wiki/log.md` tail (last 10 entries) for recent changes
3. Read up to 10 pages: 40% most recently modified, 40% anchor/high-link pages, 20% random from other folders
4. Compare for contradictions, shifts, emerging patterns
5. Present 2-3 genuine insights with citations (must pass novelty test)
6. If nothing non-obvious found, say so — don't fabricate
7. At 200+ pages: full sweep only every 10th reflect cycle or after schema change

## Schema Drift Detection

In addition to content reflection, scan recent pages for patterns that suggest the ontology should evolve.

### Signals to surface

Thresholds are debounced — a signal must clear BOTH a count and a breadth bar:

- **Class promotion candidate**: 3+ pages AND 2+ distinct ingests describe ordered steps → propose promoting to Procedure.
- **Relation promotion candidate**: same (subject, object) pair appears 3+ times across 2+ ingests with no typed predicate → propose a new predicate.
- **Class confusion**: pages whose content mismatches their `instance_of` → propose re-classification via `/kg-schema migrate --reclassify`.
- **Dead predicate**: predicate defined in `relations.yaml` but unused for >30 days AND never referenced by any ingest → propose deprecation.
- **Emerging domain class**: recurring concept that 5+ pages from 3+ ingests depend on → propose a new first-class class.
- **Possible supersession**: 2+ Decision pages share the same `decided_for` target, and the newer page's content implies the older is outdated → propose supersession link.

### What to do with signals

Do NOT modify the schema. Emit a structured report with actionable next commands:

```
Schema drift observations:

[SIG-001] CLASS_PROMOTION | confidence: high | age: 2 cycles
  3 concept pages ([[a]], [[b]], [[c]]) look like Procedures.
  → `/kg-schema propose "promote Procedure pattern in concepts" --evidence "[[a]],[[b]],[[c]]"`

[SIG-002] DEAD_PREDICATE | confidence: medium | age: 1 cycle
  Predicate `supersedes` used 0 times in 30 days.
  → `/kg-schema propose "deprecate supersedes predicate"`

[SIG-003] EMERGING_CLASS | confidence: medium | age: new
  5 pages track performance numbers inconsistently.
  → `/kg-schema propose "add Benchmark class" --evidence "[[p1]],[[p2]],[[p3]],[[p4]],[[p5]]"`
```

Each signal has: `signal_id`, `type`, `confidence`, `age` (how many cycles it's been surfaced), and a **prefilled command** the user can copy-paste or modify. If the same signal persists for 3+ cycles without propose/reject, escalate its confidence and mark as `STALE — action needed`.

**Signal → Proposal → Receipt chain**: Signals surfaced here feed into `/kg-schema propose`. Any subsequent `/kg-schema approve` requires a receipt from `validate.py --receipt` (Required-tier checks must PASS). Cited evidence must exist (`evidence_pages` sensor checks existence, not relevance — strengthen evidence anyway so reviewers see substance). See SKILL.md § Receipt-Based Evidence.

Let the user decide which (if any) to act on.

**Update `wiki/hot.md`** after reflecting:
- Reset reflect_debt to 0 in Maintenance Debt
- Add key observations to "Key Tensions / Open Questions"
- Update convergence metric if available

**Log:** `## [date] reflect | [one-line thesis]` in `wiki/log.md`

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-reflect`.
