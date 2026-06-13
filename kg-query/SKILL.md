---
name: kg-query
description: "Query accumulated knowledge — BFS/DFS graph traversal + wiki lookup. Supports --depth quick|standard|deep for token-efficient queries. Use when asking questions ABOUT existing knowledge (relationships, evidence, decisions). For PROPOSING new connections between communities, use /kg-connect instead."
trigger: /kg-query
---

# /kg-query — Query Knowledge

Answer questions against accumulated knowledge. Strategy depends on available layers and requested depth.

## Activate When

- User asks a question about the kg wiki, codebase relationships, or concept connections
- User invokes `/kg-query <question> [--depth quick|standard|deep]`
- After `/kg-orient`, when user wants to dive into a specific topic
- Before deciding what to ingest next (deep mode = "do we have this already?")

## Do Not Activate When

- Question is about external (web) information not in wiki → `/kg-autoresearch`
- User wants pattern/tension surfacing → `/kg-reflect`
- User wants to test a single claim → `/kg-challenge`
- User wants suggestions for what to ingest → `/kg-suggest`

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
6. **Deterministic claim/evidence harvest**: run `python3 ~/.claude/skills/kg/schema/tools/extract_claims.py wiki/ --types=claim,evidence` to get a JSON list of all `> [!claim]` and `> [!evidence]` callouts before synthesizing the answer. Cite by `page:line`.
7. If wiki is insufficient and topic is external: suggest `/kg-autoresearch`

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

**Codex handoff**: Query results can be injected into Codex prompts as `<domain_context>` when the follow-up is a Codex review/rescue task. Selection: matched heuristics (`confidence: high`), related decisions (`decided_for`), hot.md tensions. Cap ~500 tokens. See `~/.claude/skills/kg/references/codex-integration.md`.

## Structural sub-queries (graphify CLI, when `graphify-out/` fresh)

For relationship/impact questions the bare graphify CLI answers from `graph.json` at **0 LLM tokens** — prefer it over loading the graph into context:

| Question shape | Command |
|---|---|
| "What connects A to B?" / topic neighborhood | `graphify query "<q>" --budget N` (BFS; `--dfs` for depth-first) |
| "…but only along USE / import / calls edges" | `graphify query "<q>" --context use` (repeatable edge-context filter) |
| "Shortest link between X and Y" | `graphify path "X" "Y"` |
| "Explain this node" | `graphify explain "X"` |
| **Impact / blast radius** — "what breaks if I change X?" | `graphify affected "X" --relation R --depth N` (reverse traversal) |

**Impact mode** is the v0.8.x addition most useful for refactoring and large-scale porting/modernization (e.g. Fortran→PyTorch): `graphify affected "<symbol>" --relation imports --depth 3` returns everything transitively depending on a node before you touch it. Match `--relation` to how the symbol is depended on — for a Fortran module use `imports` (USE), for a derived **type** use `references` (`--relation` is repeatable: `--relation imports --relation references` covers both); the wrong relation silently returns an empty set. Cite the returned nodes as `Evidence read → graph traversal`. For Fortran specifics (USE-only filters, partial CALL coverage) see `~/.claude/skills/kg/references/fortran.md`. (A dedicated `/kg-impact` split is intentionally avoided — impact is a query; this mode lives here.)

## Output Contract

Always return:

```text
Answer:
<direct answer to the question>

Evidence read:
- hot.md: yes | no
- overview.md: yes | no
- wiki pages: [[a]], [[b]], ...
- raw sources: <none | list>
- graph traversal: <none | depth-N from [[anchor]]>

Confidence:
high | medium | low

Caveats:
- <missing evidence | stale pages | contradictions | none>

Next command:
- <none | /kg-query --depth deep | /kg-autoresearch "<topic>" | read [[page]]>
```

## Examples

### Example 1 — quick status

User:
```text
/kg-query "최근에 내가 뭘 보고 있었지?" --depth quick
```

Expected behavior:
- Read `wiki/hot.md` only.
- Skip BM25 if hot.md fresh (<24h).
- Return compact answer + confidence + suggested next step.
- Do not scan raw sources.

### Example 2 — decision question, deep mode

User:
```text
/kg-query "왜 OntoGPT를 PoC 1순위로 봤지?" --depth deep
```

Expected behavior:
- BM25 for "OntoGPT" + "PoC" → top-10 pages.
- Read relevant Decision/Concept/Source pages.
- Follow wikilinks to depth 2.
- Read raw sources cited in Decision page provenance.
- Distinguish wiki summary from primary evidence.
- Return Answer with explicit "Evidence read" listing both wiki pages and raw sources.

## Exceptions and Escalation

- **BM25 index stale or missing** → rebuild via `python3 ~/.claude/skills/kg/schema/tools/build_search_index.py wiki` before reading multiple pages.
- **No relevant page found in standard mode** → do not hallucinate. Say so and suggest `--depth deep`.
- **Deep mode still insufficient** → suggest `/kg-autoresearch "<topic>"`.
- **For decisions** → never cite graph/wiki as primary evidence. Always trace to raw sources via provenance.
- **Token budget exceeded** → apply per-mode truncation (see § Token Budget Enforcement) and note the truncation in Caveats.
- **Wiki absent** → fall back to graph-only mode if `graphify-out/` exists. If neither, suggest `/kg-init` + ingest.

## Quality Gates

Before final answer:
- [ ] Every claim is cited with `[[wikilink]]` or raw source path
- [ ] Confidence label honestly reflects evidence quality
- [ ] Caveats list any missing evidence, not just success
- [ ] If filed to `wiki/queries/`, log entry added
