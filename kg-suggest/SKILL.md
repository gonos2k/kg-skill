---
name: kg-suggest
description: Recommend what to read or ingest next based on knowledge gaps — orphan concepts, low-cohesion communities, unresolved wikilinks, stale topics.
trigger: /kg-suggest
---

# /kg-suggest — Next Source Recommendation

Based on current knowledge gaps, suggest what to ingest next.

**Steps:**
1. Identify orphan concepts (mentioned but no dedicated page)
2. Find communities with low cohesion scores
3. Check for unresolved `[[wikilinks]]`
4. Look for topics where most recent source is old
5. Propose 3-5 specific suggestions with rationale

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg suggest`.
