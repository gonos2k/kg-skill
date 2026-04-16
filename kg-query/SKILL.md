---
name: kg-query
description: Query accumulated knowledge — BFS/DFS graph traversal + wiki lookup. Supports --depth quick|standard|deep for token-efficient queries. Use when asking questions about the knowledge base, codebase relationships, or concept connections.
trigger: /kg-query
---

# /kg-query — Query Knowledge

Answer questions against accumulated knowledge. Strategy depends on available layers and requested depth.

## Query Depth Modes

`/kg-query [question] --depth [quick|standard|deep]`

Default: `standard`. User can override per query.

### Quick (~1.5K tokens read budget)
1. **BM25 lookup** (0 tokens): If `wiki/.search_index.json` exists and is fresh (<24h), load and search directly. Otherwise rebuild first with `python3 ~/.claude/skills/kg/schema/tools/build_search_index.py wiki`. Returns top-5 pages ranked by relevance.
2. Read `wiki/hot.md` (session context cache)
3. Read top-1 BM25 result page if high confidence (score > 50)
4. If insufficient: say so and suggest `--depth standard`

Best for: "What was I working on?", "Which heuristics exist for X?", status checks.

### Standard (~3K tokens read budget) — default
1. **BM25 lookup** (0 tokens): get top-10 results. Use scores to prioritize which pages to read.
2. Read `wiki/hot.md`
3. Read up to 5 pages from BM25 top results (prioritize: highest BM25 score, then most recently modified)
4. For structural questions, supplement with graphify query
5. Synthesize with `[[wikilink]]` citations
6. **`wiki/index.md` is a low-confidence fallback** — only if BM25 returns no results

Best for: factual questions, concept lookups, relationship queries.

### Deep (~8K+ tokens read budget)
1. All of Standard
2. Follow wikilinks to depth 2 (pages linked by the pages you read)
3. Read raw source files cited in provenance fields
4. If graph layer exists, run BFS traversal from relevant nodes
5. Cross-reference claims across sources; flag contradictions
6. If wiki is insufficient and topic is external: suggest `/kg-autoresearch`

Best for: "Why did we choose X over Y?", cross-cutting analysis, preparing for decisions.

### Token Budget Enforcement
Each mode has a soft budget. If exceeded before synthesis:
- Quick: truncate to hot.md only
- Standard: skip low-relevance pages
- Deep: skip depth-2 pages, keep raw source reads

## Operating Modes

**Graph-only** (no wiki/):
1. Read `graphify-out/GRAPH_REPORT.md` for structural context
2. Load graph.json via `json_graph.node_link_graph(data, edges='links')`
3. Match query terms to node labels, BFS traverse (depth 3)
4. Synthesize answer from graph structure with source citations

**Graph + Wiki** (depth modes apply):
1. Follow the depth mode flow above
2. File answer to `wiki/queries/` if worth keeping
3. Update `wiki/hot.md` with the query topic

**Verification chain:** Graph -> Wiki -> Raw Source. Never cite graph/wiki as primary evidence.

**Codex handoff**: Query results can be injected into Codex prompts as `<domain_context>` when the follow-up is a Codex review/rescue task. Selection: matched heuristics (`confidence: high`), related decisions (`decided_for`), hot.md tensions. Cap ~500 tokens. See SKILL.md § Codex Integration.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-query`.
