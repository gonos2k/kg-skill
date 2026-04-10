---
name: kg-connect
description: Cross-community bridge discovery — find missing connections between graph communities based on semantic similarity. Co-create knowledge that neither human nor LLM could produce alone.
trigger: /kg-connect
---

# /kg-connect — Cross-Community Bridge Discovery

Find *missing bridges* between graph communities — connections that should exist based on semantic content but don't appear structurally.

**Steps:**
1. Load communities from GRAPH_REPORT.md
2. For each pair with zero/few cross-edges, read representative nodes
3. Propose potential connections with rationale
4. If user confirms, add edge (INFERRED) to graph

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg connect`.
