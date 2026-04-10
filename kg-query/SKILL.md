---
name: kg-query
description: Query accumulated knowledge — BFS/DFS graph traversal + wiki lookup. Use when asking questions about the knowledge base, codebase relationships, or concept connections.
trigger: /kg-query
---

# /kg-query — Query Knowledge

Answer questions against accumulated knowledge. Strategy depends on available layers.

**Graph-only mode** (no wiki/):
1. Read `graphify-out/GRAPH_REPORT.md` for structural context
2. Load graph.json via `json_graph.node_link_graph(data, edges='links')`
3. Match query terms to node labels, BFS traverse (depth 3)
4. Synthesize answer from graph structure with source citations

**Graph + Wiki mode:**
1. Read `wiki/index.md` to find relevant pages
2. Read relevant wiki pages (pre-synthesized)
3. Supplement with graph traversal for structural questions
4. File answer to `wiki/queries/` if worth keeping

**Verification chain:** Graph -> Wiki -> Raw Source. Never cite graph/wiki as primary evidence.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg query`.
