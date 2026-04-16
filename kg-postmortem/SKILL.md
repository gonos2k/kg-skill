---
name: kg-postmortem
description: Structured capture of a trial-and-error event (시행착오 기록). Fills attempted → outcome → root_cause → resolution → lesson. Use after 빌드 실패, unexpected result, 삽질, or "이걸 기록해뒀어야 했는데" moment. Produces Experience + optional Heuristic.
trigger: /kg-postmortem
---

# /kg-postmortem — Record a Trial-and-Error Case

This is `/kg-elicit` with a stricter, fixed template. Use when the event is discrete and recent (last session or today).

## Flow

Ask sequentially; do not batch. Wait for the user's answer before asking the next.

1. **Attempted:** what command/config/approach did you try?
2. **Outcome:** what happened? (include exact error text if possible)
3. **Root cause:** why, in your current understanding?
4. **Resolution:** what fixed it, or "unresolved"?
5. **Generalization:** does this deserve a Heuristic? If yes, phrase it as a rule.

### Write Experience

Write `wiki/experiences/<YYYY-MM-DD>-<slug>.md` from the experience template.
- Set `epistemic_status: observed` (the event happened).
- Keep error text **verbatim** in the Outcome section. LLM summaries lose the distinctive fingerprint that lets future searches find it.
- If Resolution is "unresolved", still file it. An open case is more valuable than a forgotten one.

### Optional Heuristic (only if step 5 was "yes")

Write `wiki/heuristics/<slug>.md` from the heuristic template:
- Set `distilled_from: [[experience-slug]]`
- Add `relations: - {predicate: learned_from, target: "[[experience-slug]]"}`
- Ask: "Confidence: high / medium / low?" — record answer.

### Update indexes

Update all of:
- `wiki/experiences/_index.md`
- `wiki/heuristics/_index.md` (if heuristic created)
- `wiki/index.md`
- `wiki/log.md`:
  ```
  ## [YYYY-MM-DD] postmortem | <one-line thesis>
  - Experience: [[experience-slug]]
  - Heuristic: [[heuristic-slug]] (or "none")
  ```
- `wiki/hot.md` — update Recent Activity

## Principles
- **One event = one Experience page.** If the user conflates two events, split them.
- **Keep the error text verbatim** in Outcome.
- **If Resolution is "unresolved"**, still file it.
- Do NOT rebuild the graph — postmortem knowledge is wiki-layer only.
