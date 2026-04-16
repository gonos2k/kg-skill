---
name: kg-challenge
description: Devil's advocate — argue against a claim or wiki belief using only evidence from the knowledge base. Stress-test knowledge before it calcifies.
trigger: /kg-challenge
---

# /kg-challenge — Devil's Advocate

Argue against a stated claim using only evidence from the knowledge base. The goal is not to be right — it's to stress-test a belief before it calcifies into received truth.

## When to invoke
- Before a major decision that depends on a wiki claim
- When a heuristic or decision page has not been challenged in 30+ days
- After 3+ ingests touching the same concept (claim has accumulated weight, deserves scrutiny)
- User explicitly asks for counter-argument

## Flow

1. **Pick target claim**:
   - If user provides claim text: use it verbatim
   - Otherwise auto-pick: highest-confidence `inferred` edge, OR most central concept (highest in-degree in graph), OR most-cited page in last 10 log entries
2. **Gather supporting evidence**: read the page itself + 3-5 pages that link to it. Note explicit `> [!claim]` callouts and `supported_by` relations.
3. **Gather contradicting evidence**: search wiki for terms that would weaken the claim (negations, alternatives, tradeoff discussions). Check for `> [!warning] Tension` callouts and `contradicted_by` relations.
4. **Present counter-argument**: structured as: (a) the claim restated, (b) strongest single piece of contradicting evidence with citation, (c) 1-2 weaker contradictions, (d) the residual support that survives.
5. **Ask the operative question**: "Does this change anything, or does the original claim still hold?"

## Output format

```
Claim under challenge: <verbatim or paraphrase>
Supporting (current): <N> citations — strongest: [[page#section]]
Contradicting (found): <M> citations — strongest: [[page#section]]
Verdict (you decide): claim survives | claim weakened | claim should be revised
```

## Quality bar (must pass before reporting)
- Counter-argument cites at least 1 wiki page (no fabricated counter-claims)
- If no contradicting evidence found, say so explicitly — do NOT manufacture doubt
- "Devil's advocate ≠ contrarian": only argue against what evidence allows

## Filing rule
If the challenge surfaces material contradiction (verdict = weakened or revise), file the exchange to `wiki/queries/challenge-<date>-<slug>.md`. If claim survives unchanged, do not file (no signal worth keeping).

## Distinction from related ops
- `/kg-reflect` surfaces tensions across many pages (broad scan)
- `/kg-challenge` stress-tests a single specific claim (narrow drill)
- If reflect finds a tension, follow up with challenge on the most central claim involved

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-challenge`.
