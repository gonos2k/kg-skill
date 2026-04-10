# kg-skill

Knowledge Graph + LLM Wiki skill for [Claude Code](https://claude.ai/claude-code).

An extension of [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — persistent, compounding knowledge base where the LLM writes and maintains a structured wiki while the human curates sources and asks questions.

## What this adds beyond Karpathy's pattern

- **Graphify structural graph** — automatic community detection, god nodes, surprising cross-document connections (Leiden clustering on extracted entities/relationships)
- **Graph-only mode** — works without wiki setup; orient/query/update against the graph alone
- **Incremental updates** — SHA256 cache detects changed files; code-only changes skip LLM extraction
- **Verification chain** — Graph -> Wiki -> Raw Source (3-layer trust hierarchy)
- **Dialogue operations** — the LLM is a thinking partner, not just a scribe

## Slash Commands

### Data Operations (knowledge accumulation)

| Command | Description |
|---------|-------------|
| `/kg` | Full reference + orientation |
| `/kg-orient` | Session start summary — graph/wiki status, god nodes, freshness |
| `/kg-update` | Incremental graph rebuild (delegates to Graphify `--update`) |
| `/kg-ingest` | Ingest source files into wiki with discussion |
| `/kg-query` | BFS/DFS graph traversal + wiki lookup |
| `/kg-lint` | Health check — graph integrity, manifest, freshness, orphan pages |

### Dialogue Operations (mutual interaction)

| Command | Description |
|---------|-------------|
| `/kg-reflect` | Surface tensions, emerging patterns, blind spots, shifted ground |
| `/kg-challenge` | Devil's advocate — argue against a wiki claim using only evidence |
| `/kg-connect` | Find missing bridges between graph communities |
| `/kg-suggest` | Recommend what to read/ingest next based on knowledge gaps |

## Installation

Copy skill directories into `~/.claude/skills/`:

```bash
cp -r kg kg-orient kg-update kg-query kg-lint kg-ingest \
      kg-reflect kg-challenge kg-connect kg-suggest \
      ~/.claude/skills/
```

Add to `~/.claude/CLAUDE.md`:

```markdown
# kg (knowledge-graph)
- **kg** (`~/.claude/skills/kg/SKILL.md`) - Knowledge graph + LLM wiki.
  Sub-commands: /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest,
  /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest
When the user types /kg or any sub-command, invoke the Skill tool with the matching skill name.
When wiki/ or graphify-out/ exists in the project, proactively orient at session start.
```

## Dependencies

- [graphify](https://github.com/safishamsi/graphify) (`pip install graphifyy`) — structural graph extraction
- [Obsidian](https://obsidian.md/) (optional) — browse the wiki with graph view and wikilinks

## Architecture

```
project/
├── <source-dir>/       # Layer 1: Raw sources (immutable)
├── wiki/               # Layer 2: LLM-maintained wiki (optional)
│   ├── index.md        #   Content catalog
│   ├── log.md          #   Chronological record
│   ├── entities/       #   Entity pages
│   ├── concepts/       #   Concept pages
│   └── sources/        #   Source summaries
├── graphify-out/       # Structural graph layer
│   ├── graph.json      #   Nodes, edges, communities
│   └── GRAPH_REPORT.md #   God nodes, surprises
└── CLAUDE.md           # Schema — conventions and workflows
```

## Interaction Principles

1. **Asymmetric roles** — Human provides judgment and direction. LLM provides recall, cross-referencing, and pattern detection across documents.
2. **Productive friction** — Agreement is cheap. The valuable interaction happens when the LLM surfaces contradictions, gaps, or unexpected connections.
3. **Filed dialogue** — Insights from reflect, challenge, and connect are filed back into the wiki. The dialogue itself compounds.

## License

MIT
