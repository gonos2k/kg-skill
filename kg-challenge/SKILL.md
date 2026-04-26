---
name: kg-challenge
description: "This skill should be used when the user asks to stress-test, challenge, falsify, or argue against a wiki claim, decision, heuristic, or assumption, says '반박해줘', '이 주장 검증해줘', 'devil's advocate', or invokes /kg-challenge. Uses only evidence already in the knowledge base — never fabricates doubt."
trigger: /kg-challenge
---

# /kg-challenge — Devil's Advocate

Argue against a stated claim using only evidence from the knowledge base. The goal is not to be right — it's to stress-test a belief before it calcifies into received truth.

## Activate When

- User asks "반박해줘", "이 주장 검증해줘", "devil's advocate", "stress-test"
- Before a major decision that depends on a wiki claim
- When a heuristic or decision page has not been challenged in 30+ days
- After 3+ ingests touching the same concept (claim has accumulated weight, deserves scrutiny)
- User explicitly asks for counter-argument

## Do Not Activate When

- User wants broad pattern surfacing → `/kg-reflect` (challenge is narrow drill, reflect is broad scan)
- User wants to query → `/kg-query`
- User wants to find missing connections → `/kg-connect`
- The claim has no concrete target (vague like "maybe X is wrong") → ask for clarification first

## Flow

1. **Pick target claim**:
   - If user provides claim text: use it verbatim
   - Otherwise auto-pick: highest-confidence `inferred` edge, OR most central concept (highest in-degree in graph), OR most-cited page in last 10 log entries
2. **Gather supporting evidence**: read the page itself + 3-5 pages that link to it. Note explicit `> [!claim]` callouts and `supported_by` relations.
   - **Deterministic harvest**: run `python3 ~/.claude/skills/kg/schema/tools/extract_claims.py wiki/ --types=claim,evidence --page=<target>` to enumerate all callouts on the target page before LLM-side reading.
3. **Gather contradicting evidence**: search wiki for terms that would weaken the claim (negations, alternatives, tradeoff discussions). Check for `> [!warning] Tension` callouts and `contradicted_by` relations.
   - **Deterministic harvest**: `python3 ~/.claude/skills/kg/schema/tools/extract_claims.py wiki/ --types=tension,warning` to enumerate all tensions wiki-wide.
4. **Present counter-argument**: structured as: (a) the claim restated, (b) strongest single piece of contradicting evidence with citation, (c) 1-2 weaker contradictions, (d) the residual support that survives.
5. **Ask the operative question**: "Does this change anything, or does the original claim still hold?"

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- Call `get_neighbors(<claim_concept>)` to objectively enumerate adjacent nodes (potential supporting/contradicting evidence sources)
- Call `shortest_path(<claim>, <known_alternative>)` to verify the claim isn't trivially close to its alternative (which would weaken it)
- If graph stale (≥7d) or absent, fall back to wiki-only search and note in Caveats.

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

## Output Contract

```text
Claim under challenge:
<verbatim or paraphrase>

Current support:
- Strongest: [[page#section]]
- Other support: <N citations>

Contradicting evidence found:
- Strongest contradiction: [[page#section]] | none found
- Weaker signals: <list>

Counter-argument:
<short structured argument>

Residual support that survives:
<what holds despite contradictions>

Verdict (you decide): claim survives | claim weakened | claim should be revised | insufficient evidence

Confidence: high | medium | low

Caveats:
- <graph stale | small wiki | no contradicting evidence | none>

Filed to wiki: yes (wiki/queries/challenge-<date>-<slug>.md) | no (no material contradiction)

Next command:
- <none | /kg-schema propose <update> | edit [[page]] | /kg-reflect>
```

## Exceptions and Escalation

- **No contradicting evidence found** → say "No contradicting evidence found in the knowledge base." Do not invent doubt.
- **Claim too vague** → ask one clarification question OR auto-select a narrower claim from the wiki and report what was selected.
- **Challenge changes a Decision or Heuristic** → do NOT edit the page. File a challenge note and ask user (per Authority Matrix: page status change = Human).
- **Claim cites zero wiki pages** → flag as "claim has no documented support in wiki — challenge results would be from external opinion only".
- **Wiki absent** → suggest `/kg-init` + `/kg-ingest` first; cannot challenge without evidence base.

## Quality Gates

Before final answer:
- [ ] At least 1 wiki page cited per claim/contradiction
- [ ] Verdict explicitly states one of 4 options
- [ ] If filed, path noted in Output Contract
- [ ] No fabricated contradictions
