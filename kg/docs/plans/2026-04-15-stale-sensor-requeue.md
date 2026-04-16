# Stale Sensor Requeue — 2026-04-15

## Status
`signal_staleness` and `proposal_debt` remain SKIP in `validate.py --receipt`. The #6 "Stale 감지 자동화" work item is **re-queued**, not closed.

## Why this cycle did not implement the sensors
1. **No persistent cycle state.** `/kg-reflect` emits SIG-* IDs to stdout only; age / "cycles" counters are narrative strings in `wiki/log.md`, not machine-readable records. Same gap for proposals: `wiki/.schema-proposals/*.yaml` has `date` and `status` but no explicit cycle counter.
2. **Sensor execution path mismatch.** `build_receipt()` is invoked only on the approve phase (`validate.py --receipt`). But `proposal_debt` and `signal_staleness` are documented as `reflect, lint` sensors. Wiring them into the approve path would place them in the wrong phase.
3. **Stability constraint.** Memory item *Post Big-Change Stabilize* (do not stack large pattern changes). Several kg sub-skills were touched in the preceding 24–48 hours; Codex recommended a 3–5 day observation window before further structural work.

## What this cycle DID do (scope: documentation coherence only)
- `kg/SKILL.md:702`: `stale_signals` → `signal_staleness` (align with receipt-key exact-match rule in kg-schema/SKILL.md:134).
- `kg-schema/SKILL.md:164`: added `proposal_debt` to Advisory tier list so the tier taxonomy and the "Not yet implemented" table agree.
- `kg-lint/SKILL.md:62`: added legacy carve-out so approved proposals predating the receipt contract are reported as advisory debt, not Required-tier failure.
- This note.

## Prerequisites before implementation
Before re-opening #6, the following must be decided or designed:

1. **Cycle persistence model.** Pick one:
   - New artifact: `wiki/.signals/index.yaml` or per-signal files.
   - Derived from `wiki/log.md` reflect entries (requires structured log format).
   - Explicit cycle counter field in proposal YAML, ticked by a lifecycle command.
2. **Sensor execution surface.** Extend `validate.py` with a mode other than `--receipt` (e.g. `--reflect-mode`, `--lint-mode`) so reflect/lint sensors can be invoked without the approve-phase gate.
3. **Receipt coverage policy.** Decide whether existing legacy-approved proposals get retroactive receipts, explicit waivers, or a one-time migration pass. Currently two such proposals exist in `/Users/yhlee/GPU-KIM/wiki/.schema-proposals/` (sig001-body-drift, sig002-weak-backlink).
4. **Threshold source.** "2+ cycles" vs "N days" must be resolved with measurable intent — not proxied silently.

## When to re-open
Earliest: after the stabilization window passes AND at least one of the prerequisites above has a concrete proposal. Re-opening without cycle persistence will reintroduce the same blocker and should be refused.

## Non-goals of the re-open
- Do not extend `build_receipt()` to host reflect/lint sensors. Add a separate CLI entry point.
- Do not silently re-interpret "cycles" as "days". If the project settles on days, update `kg/SKILL.md:701-702` explicitly and remove this note's prerequisite #4.
