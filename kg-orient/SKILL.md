---
name: kg-orient
description: "This skill should be used at the start of a session when the project contains wiki/ or graphify-out/, when the user asks '현재 kg 상태 보여줘', '세션 시작 요약', 'what is the current wiki state?', or invokes /kg-orient. Reads hot.md, overview.md, graph reports, freshness — read-only, never modifies files."
trigger: /kg-orient
---

# /kg-orient — Session Start Orientation

Read-only status snapshot of the kg wiki and graphify-out layers.

## Activate When

- Session start when `wiki/` or `graphify-out/` exists
- User asks "현재 kg 상태 보여줘", "세션 시작 요약", "what is the current wiki state?"
- After a long break to recover context
- Before deciding what `/kg-*` operation to run next

## Do Not Activate When

- User wants to query a specific concept → `/kg-query`
- User wants to refresh the graph → `/kg-update`
- User wants to make schema changes → `/kg-schema`

## Quick steps

1. Detect layers: `graphify-out/GRAPH_REPORT.md` (graph), `wiki/index.md` (wiki)
2. **Read `wiki/hot.md` FIRST** (session context cache)
3. **Read `wiki/overview.md`** (stable global synthesis, ~500 words — this is the compression layer between hot.md and full index)
4. Read GRAPH_REPORT.md first 60 lines (god nodes + communities)
5. **Only if hot.md is stale (>24h) AND overview.md is insufficient for routing**, fall back to `wiki/index.md` + tail of `wiki/log.md`. As wiki grows past 200 pages, index.md becomes a last resort, not a default read.
6. Check freshness: `graph.json` mtime vs newest source file
7. Present summary (see Output Contract below)

## Maintenance Debt computation

Compute from `log.md` + `_index.md`:

```
Reflect debt: N ingests since last reflect (warn if >= 3)
Migration debt: N transitional pages with age > 21 days
Proposal debt: N drift signals surfaced but not proposed/rejected
Pin gap: global v{X} vs pinned v{Y} (suggest pull-global if gap > 0)
Convergence: full_v1 / active_frontier = N% (target: 80%+)
```

If reflect_debt >= 3, append: "Reflect 권장 — `/kg-reflect` 실행을 고려하세요."

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days` (freshness gate per `~/.claude/skills/kg/references/architecture.md`):
- Optional: invoke `graphify <path> --mcp` background server, then call `god_nodes(top_n=5)` and `graph_stats` MCP tools for richer orientation than reading GRAPH_REPORT.md alone.
- If graph stale (≥7d) or absent, fall back to GRAPH_REPORT.md only and note in Caveats.

## Source directory detection (checked in order)

1. User-specified path
2. `gMeso/vault/`
3. `raw/`
4. `docs/`
5. `.`

## Output Contract

```text
Orientation:
Hot cache: fresh | stale | absent
Mode: graph-only | graph+wiki | wiki-only | empty

Graph (if present):
- Nodes: <N>
- Edges: <M>
- Communities: <K>
- Top god nodes: [<top 3-5>]
- Freshness: FRESH | STALE (<N files changed since last build>)

Wiki (if present):
- Pages: <N> (E entities, C concepts, P procedures, X experiences, H heuristics, D decisions, S sources)
- Last activity: <date from log tail>
- Active focus: <from hot.md Current Focus>

Maintenance debt:
- Reflect debt: <N> ingests since last reflect
- Migration debt: <N> transitional pages
- Proposal debt: <N> open SIG signals
- Pin gap: global v<X> vs pinned v<Y>
- Convergence: <N>%

Confidence: high | medium | low

Caveats:
- <empty project | graph stale | hot.md missing | none>

Next command:
- <one suggested command based on state>
```

## Exceptions and Escalation

- **Neither `wiki/` nor `graphify-out/` exists** → suggest `/kg-init` and stop. Do not invent state.
- **`hot.md` missing but wiki exists** → read `overview.md`; report hot cache as "absent".
- **Graph is stale (≥7d)** → suggest `/kg-update` but do NOT run it automatically.
- **Validator output unavailable** → skip Maintenance debt section, note in Caveats.
- **NEVER modify** `hot.md`, `log.md`, `index.md`, or any content page during orient. This is a read-only skill.

## Quality Gates

Before final answer:
- [ ] No file was modified
- [ ] Every reported number has a source (which file it came from)
- [ ] Confidence reflects whether all expected files were readable
- [ ] At least one Next command suggestion provided
