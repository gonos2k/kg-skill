---
name: kg-elicit
description: "This skill should be used when the user mentions tacit knowledge, repeated mistakes, gotchas, lessons learned, 비법, 주의사항, 실패 경험, or invokes /kg-elicit. Captures implicit knowledge as Experience first, optionally promotes to Heuristic only after explicit confirmation."
trigger: /kg-elicit
---

# /kg-elicit — Extract Tacit Knowledge

Goal: turn what's in the user's head into a wiki page before it's lost.

## Activate When

- User mentions tacit knowledge, repeated mistakes, gotchas, lessons learned
- Korean keywords: `비법`, `주의사항`, `실패`, `반복된 실수`, `명심`
- During `/kg-ingest`, after the main flow, if trigger keywords appear in source or recent conversation
- During `/kg-reflect`, when an Experience is referenced but no page exists
- User explicitly invokes `/kg-elicit [topic]`

## Do Not Activate When

- The event is concrete and recent (last session/today) → use `/kg-postmortem` (stricter template)
- User wants to query existing experiences → `/kg-query`
- User wants summary of tensions → `/kg-reflect`

## Preconditions

- Wiki must be bootstrapped (`/kg-init` has run, `wiki/` exists with `.schema/` and content folders)
- If wiki doesn't exist, tell user to run `/kg-init` first and stop

## When to run

- Explicitly: user types `/kg-elicit [topic]`
- Auto: during `/kg-ingest`, after the main flow, if trigger keywords appear in the source or recent conversation
- Auto: during `/kg-reflect`, when an Experience is referenced but no page exists

## Dialog (Experience-first routing)

Default outcome is always an Experience. Heuristic is a **second, separate step** that only runs when the user explicitly confirms the lesson generalizes.

### Pass 1 — File the Experience (always runs)

Ask sequentially (max 5 questions; skip any the user answers upfront):

1. **What did you try that didn't work?** — seeds body section Attempted
2. **What actually happened?** — seeds Outcome (keep verbatim error text if any)
3. **Why did it fail (your current theory)?** — seeds Root Cause
4. **How did you get past it, or is it still open?** — seeds Resolution
5. **One-line lesson?** — seeds Lesson

Write `wiki/experiences/<YYYY-MM-DD>-<slug>.md` from the experience template.
Set `epistemic_status`:
- `observed` if the event is concrete
- `inferred` if reconstructed from memory
- `hypothesis` if the user is still unsure about root cause

Update `wiki/experiences/_index.md`, `wiki/index.md`, `wiki/log.md`, and `wiki/hot.md`.

### Pass 2 — Optional Heuristic promotion (only after confirmation)

Ask: "Does this lesson apply beyond this one case? If yes, phrase it as a general rule. If unsure or 'maybe', we leave it as an Experience for now — you can always promote later."

Only if the user gives a phrased rule:

6. **Under what conditions would a newcomer hit this?** — Heuristic.applies_when
7. **Are there cases where the rule does NOT apply?** — Heuristic "Does Not Apply When"
8. **Confidence: high / medium / low?** — Heuristic.confidence

Then write `wiki/heuristics/<slug>.md` from the heuristic template:
- Set `distilled_from: [[experience-slug]]`
- Add `relations: - {predicate: learned_from, target: "[[experience-slug]]"}`

Update `wiki/heuristics/_index.md`, `wiki/index.md`, `wiki/log.md`, and `wiki/hot.md`.

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- After Heuristic creation: call `get_neighbors(<related_concept>)` to verify the new Heuristic links to existing concepts (auto-suggest 1-hop wikilinks)
- For Experience: optional `shortest_path(<symptom>, <root_cause>)` to verify the link makes structural sense
- If graph stale (≥7d) or absent, skip this enrichment (Heuristic creation is wiki-layer; graph isn't required).

## After writing

- Do NOT rebuild the graph — elicited knowledge is wiki-layer only
- Append to `wiki/log.md`:
  ```
  ## [YYYY-MM-DD] elicit | <one-line thesis>
  - Experience: [[experience-slug]]
  - Heuristic: [[heuristic-slug]] (or "none — deferred")
  ```

## Principles

- **Don't fabricate**. If the user is vague, ask one sharpening question. If still vague, file as `epistemic_status: inferred` with `confidence: low`.
- **No leading questions**. "What went wrong?" not "Was it X that went wrong?"
- **One page per lesson**. Don't pack multiple heuristics into one page.
- **Experience-first**. A single "specific or general?" gate over-files Heuristics. Routing through Experience first keeps the raw case intact and makes promotion an explicit, datable act.

## Output Contract

```text
Elicit result: PASS | PARTIAL

Captured:
- Experience: [[experiences/<slug>]]
- Heuristic: [[heuristics/<slug>]] | none (deferred or rejected)

Epistemic status: observed | inferred | hypothesis
Per-item confidence: high | medium | low (Heuristic only)

One-line lesson:
<lesson>

Updated:
- experiences/_index.md
- heuristics/_index.md (if Heuristic created)
- index.md
- log.md
- hot.md (Recent Activity)

Confidence: high | medium | low

Caveats:
- <vague answers | event still unresolved | no Heuristic | graphify-stale (enrichment skipped) | none>

Next command:
- <none | /kg-reflect (if 3rd+ elicit) | /kg-challenge "<lesson>" | /kg-update>
```

## Exceptions and Escalation

- **Wiki absent** → stop and suggest `/kg-init`.
- **User vague after one sharpening question** → file as `epistemic_status: inferred`, `confidence: low`. Do not invent details.
- **User says "maybe general"** → do NOT create Heuristic. Keep as Experience only.
- **Multiple lessons in one input** → split into multiple Experience pages (one event = one page).
- **Promotion to Heuristic requires explicit "yes" + phrased rule** per Authority Matrix.

## Quality Gates

Before final answer:
- [ ] Experience page created (always, even if vague)
- [ ] Heuristic only created with explicit confirmation + phrased rule
- [ ] Indexes updated
- [ ] log.md entry added
