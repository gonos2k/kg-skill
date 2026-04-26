---
name: kg-postmortem
description: "This skill should be used after a recent discrete failure, build error, unexpected result, debugging session, 삽질, or '이걸 기록해뒀어야 했는데' moment, or when the user invokes /kg-postmortem. Captures one trial-and-error event as Experience and optionally Heuristic only if user confirms generalization."
trigger: /kg-postmortem
---

# /kg-postmortem — Record a Trial-and-Error Case

This is `/kg-elicit` with a stricter, fixed template. Use when the event is discrete and recent (last session or today).

## Activate When

- Recent discrete failure (last session or today)
- Build error, unexpected result, debugging session ended
- Korean: `빌드 실패`, `삽질`, `이걸 기록해뒀어야 했는데`
- User explicitly invokes `/kg-postmortem`

## Do Not Activate When

- Tacit knowledge from older memory → use `/kg-elicit` (more flexible template)
- Multiple unrelated events → split and file each separately
- User wants to query past postmortems → `/kg-query`

## Preconditions

- Wiki must be bootstrapped (`/kg-init` has run)
- If wiki doesn't exist, tell user to run `/kg-init` first and stop

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

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- After Experience creation: call `shortest_path(<symptom_keyword>, <past_experience>)` to find related past Experience pages (potential pattern detection)
- If 2+ similar past Experiences exist (path ≤ 3 hops), suggest "this looks like a recurring pattern — promote to Heuristic?" prompt
- If graph stale (≥7d) or absent, skip the pattern detection (postmortem is primarily wiki-layer).

## Principles

- **One event = one Experience page.** If the user conflates two events, split them.
- **Keep the error text verbatim** in Outcome.
- **If Resolution is "unresolved"**, still file it.
- Do NOT rebuild the graph — postmortem knowledge is wiki-layer only.

## Output Contract

```text
Postmortem result: PASS | PARTIAL

Filed:
- Experience: [[experiences/<date>-<slug>]]
- Heuristic: [[heuristics/<slug>]] | none

Attempted: <one line>
Outcome: <one line, exact error preserved if available>
Root cause: <one line>
Resolution: fixed | unresolved | workaround
Lesson (if Heuristic): <one line>

Updated:
- experiences/_index.md
- heuristics/_index.md (if Heuristic created)
- index.md
- log.md
- hot.md

Confidence: high | medium | low (overall recall quality)

Caveats:
- <unresolved | similar past Experience exists | no Heuristic | graphify-stale (pattern detection skipped) | none>

Pattern signal (graphify-fresh only):
- <none | similar past Experience: [[<slug>]] — consider Heuristic promotion>

Next command:
- <none | /kg-elicit "<related>" | /kg-challenge "<lesson>" | /kg-reflect>
```

## Exceptions and Escalation

- **Wiki absent** → stop and suggest `/kg-init`.
- **User describes 2+ incidents** → split into separate postmortems (one event = one page).
- **Resolution is "unresolved"** → still file the Experience (open cases are valuable).
- **Error text provided** → preserve **exactly** in Outcome (no LLM paraphrasing).
- **Heuristic generalization requires explicit "yes"** per Authority Matrix.
- **Do not rebuild graph** — postmortem is wiki-layer only.

## Quality Gates

Before final answer:
- [ ] Experience filed (always, even if unresolved)
- [ ] Verbatim error text in Outcome
- [ ] Heuristic only created with explicit "yes" to step 5
- [ ] All 5 indexes updated
- [ ] log.md entry added with date
