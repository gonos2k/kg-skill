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

**Steps:**
1. Read `wiki/log.md` tail (last 10 entries) or `GRAPH_REPORT.md` for recent state
2. Read the most recently modified wiki pages or graph nodes
3. Compare against older pages/nodes for contradictions or shifts
4. Present 2-3 genuine insights with citations
5. If nothing non-obvious found, say so — don't fabricate

**Log:** `## [date] reflect | [one-line thesis]` in `wiki/log.md`

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg reflect`.
