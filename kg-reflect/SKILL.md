---
name: kg-reflect
description: "This skill should be used after multiple ingests, at session end, when the user asks for hidden tensions, emerging patterns, blind spots, schema drift, or invokes /kg-reflect. Surfaces only non-obvious insights supported by multiple wiki/graph signals — explicitly says 'no novel insights' if none."
trigger: /kg-reflect
---

# /kg-reflect — Proactive Insight

Review recent activity and offer unprompted observations that make the user think.

## Activate When

- After 3+ ingests since last reflect (auto-suggested by `/kg-ingest` reflect reminder)
- User asks for "tensions", "emerging patterns", "blind spots", "shifted ground", "schema drift"
- User invokes `/kg-reflect`
- Session end before context compaction
- Before major decisions to surface unconsidered angles

## Do Not Activate When

- User asks a specific question → `/kg-query`
- User wants a recent activity summary → just read `wiki/log.md` tail (not reflect's job)
- User wants to test a single claim → `/kg-challenge`
- This is **not** a summary skill — it must produce non-obvious insights or say none

## What to surface (pick what's genuinely present, not all):

- **Tensions** — "Source A claims X, but source B implies Y. Which is closer to your current understanding?"
- **Emerging patterns** — "The last N sources all touch [theme]. Worth its own concept page?"
- **Blind spots** — "Community X has N nodes but zero inbound edges from Community Y. Intentional?"
- **Shifted ground** — "Early sources assumed X. Recent ones assume not-X. Wiki still reflects old framing."

## Steps (bounded sample, not full scan)

1. Read `wiki/hot.md` + `wiki/overview.md` for current context
2. Read `wiki/log.md` tail (last 10 entries) for recent changes
3. Read up to 10 pages: 40% most recently modified, 40% anchor/high-link pages, 20% random from other folders
4. Compare for contradictions, shifts, emerging patterns
5. Present 2-3 genuine insights with citations (must pass novelty test)
6. If nothing non-obvious found, say so — don't fabricate
7. At 200+ pages: full sweep only every 10th reflect cycle or after schema change

## Novelty test (required before surfacing)

Before listing an insight, it must pass at least one (per `~/.claude/skills/kg/references/authority-matrix.md` § /kg-reflect Novelty Test):
- **Cross-reference**: cites 2+ wiki pages that contradict or tension each other
- **Anomaly**: graph structure (community isolation, missing bridge) + wiki content mismatch
- **Temporal**: early sources assumed X, recent sources assume not-X
- **Blind spot**: a concept is referenced 3+ times but has no page

If none pass, output: "No novel insights this cycle." Do not fabricate.

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

**Signal → Proposal → Receipt chain**: Signals surfaced here feed into `/kg-schema propose`. Any subsequent `/kg-schema approve` requires a receipt from `validate.py --receipt` (Required-tier checks must PASS). Cited evidence must exist (`evidence_pages` sensor checks existence, not relevance — strengthen evidence anyway so reviewers see substance). See `~/.claude/skills/kg/references/ontology.md` § Receipt-Based Evidence.

Let the user decide which (if any) to act on.

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- **Via MCP** (preferred when `/kg-mcp` server is registered): call MCP tools `shortest_path(a, b)` between top-3 god nodes from each community → cross-community emerging cluster detection; call `god_nodes(top_n=10)` for richer "anchor pages" sample (vs reading GRAPH_REPORT.md alone).
- **Via CLI** (fallback when MCP not registered): only `graphify path "A" "B"` (shortest_path equivalent) is exposed. `god_nodes` is MCP-only — read GRAPH_REPORT.md instead.
- If graph stale (≥7d) or absent, fall back to wiki-only sampling and note in Caveats.

## Update side effects (allowed by Authority Matrix)

After reflecting, update `wiki/hot.md`:
- Reset reflect_debt to 0 in Maintenance Debt
- Add key observations to "Key Tensions / Open Questions"
- Update convergence metric if available

Append to `wiki/log.md`:
```
## [date] reflect | [one-line thesis]
```

## Output Contract

```text
Reflection result: <N> insights | no novel insights this cycle

Insight #1: <one-line thesis>
Type: tension | emerging_pattern | blind_spot | shifted_ground | schema_drift
Novelty test passed: cross-reference | anomaly | temporal | blind_spot
Evidence:
- [[page-a]]
- [[page-b]]
Why this matters:
<1-2 sentences>
Suggested action:
<one concrete next command or wiki update>

(Insight #2 ... if applicable, max 3)

Schema drift observations:
- <none | SIG list with prefilled commands>

hot.md updated: yes (reflect_debt → 0)
log.md updated: yes

Confidence: high | medium | low

Caveats:
- <graph stale | small wiki | none>

Next command:
- <none | /kg-schema propose <SIG> | /kg-challenge "<claim>" | /kg-ingest <gap>>
```

## Exceptions and Escalation

- **No insight passes novelty test** → output "No novel insights this cycle." Do not fabricate.
- **Do not summarize recent activity** unless it directly supports an insight (recent activity is for `/kg-orient`).
- **Do not modify schema** — only emit signals.
- **Do not create new content pages** — only update hot.md and log.md (bookkeeping per Authority Matrix).
- **Wiki absent** → graph-only reflect (drift signals still possible from graph community changes).
- **Both absent** → suggest `/kg-init` + ingest first.

## Quality Gates

Before final answer:
- [ ] Every insight cites ≥2 wiki pages or 1 graph signal
- [ ] At least one novelty test passed per insight
- [ ] If 0 insights, "No novel insights this cycle" stated explicitly
- [ ] hot.md reflect_debt reset
- [ ] log.md entry added
