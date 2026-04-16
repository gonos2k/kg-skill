# kg-skill

> **Language / 언어:** **English** | [한국어](README.ko.md)

Knowledge Graph + LLM Wiki skill for [Claude Code](https://claude.ai/claude-code).

An extension of [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — persistent, compounding knowledge base where the LLM writes and maintains a structured wiki while the human curates sources and asks questions.

## What this adds beyond Karpathy's pattern

- **Structural graph** — Leiden clustering-based community detection, god nodes, surprising cross-document connections via [Graphify](https://github.com/safishamsi/graphify)
- **Graph-only mode** — works without wiki setup; orient/query/update against the graph alone
- **Incremental updates** — SHA256 cache detects changed files; code-only changes skip LLM extraction
- **Verification chain** — Graph → Wiki → Raw Source (3-layer trust hierarchy)
- **Dialogue operations** — the LLM is a thinking partner, not just a scribe
- **Evolving ontology** — 7 knowledge classes (Artifact, Concept, Source, Procedure, Experience, Heuristic, Decision) with proposal-first schema evolution and receipt-based quality gates

## Slash Commands

### Data Operations

| Command | Description |
|---------|-------------|
| `/kg` | Full reference + orientation |
| `/kg-orient` | Session start summary — graph/wiki status, god nodes, freshness |
| `/kg-init` | Bootstrap wiki directory — copy schema, create folders, idempotent |
| `/kg-update` | Incremental graph rebuild (delegates to Graphify `--update`) |
| `/kg-ingest` | Ingest source files into wiki with discussion and key takeaways |
| `/kg-query` | BFS/DFS graph traversal + wiki lookup |
| `/kg-lint` | Health check — graph integrity, orphan pages, missing links, schema validation |

### Dialogue Operations

| Command | Description |
|---------|-------------|
| `/kg-reflect` | Surface tensions, emerging patterns, blind spots, shifted ground |
| `/kg-challenge` | Devil's advocate — argue against a wiki claim using only evidence |
| `/kg-connect` | Find missing bridges between graph communities |
| `/kg-suggest` | Recommend what to read/ingest next based on knowledge gaps |
| `/kg-elicit` | Surface tacit knowledge — create Experience and Heuristic pages via dialog |
| `/kg-autoresearch` | Autonomous multi-round web research loop |

### Schema Operations

| Command | Description |
|---------|-------------|
| `/kg-schema` | Evolve the ontology — propose/approve/migrate/diff/list |
| `/kg-canvas` | Export wiki knowledge as Obsidian Canvas for visualization |
| `/kg-postmortem` | Structured trial-and-error capture (attempted → outcome → lesson) |

## Ontology (v1)

Seven knowledge classes with structured frontmatter contracts.

| Class | Purpose | page_kind |
|-------|---------|-----------|
| **Artifact** | Code entities (functions, modules, kernels) | entity, kernel, module |
| **Concept** | Domain concepts and theories | concept, theory, overview |
| **Source** | Paper and document summaries | paper, manual, spec |
| **Procedure** | Step-by-step processes | procedure, workflow, recipe |
| **Experience** | Trial-and-error episodes | episode, session, incident |
| **Heuristic** | Rules of thumb and lessons | rule, guideline, pattern |
| **Decision** | Design decisions with rationale | decision, trade-off |

### Schema Evolution

All schema changes follow a proposal-first workflow:

```
/kg-reflect (detect drift)
  → /kg-schema propose (create proposal)
    → /kg-schema approve (collect receipt + gate check)
      → /kg-schema apply (modify schema files)
        → /kg-schema migrate (update affected pages)
```

**Receipt-based quality gate**: `validate.py --receipt` runs 6 sensors. All Required-tier checks (schema_diff, template_contract, frontmatter_valid, legacy_compat, evidence_pages) must PASS before approval proceeds.

## Installation

Copy skill directories into `~/.claude/skills/`:

```bash
cp -r kg kg-orient kg-update kg-query kg-lint kg-ingest \
      kg-reflect kg-challenge kg-connect kg-suggest \
      kg-init kg-schema kg-elicit kg-postmortem \
      kg-autoresearch kg-canvas \
      ~/.claude/skills/
```

Add to `~/.claude/CLAUDE.md`:

```markdown
## kg (knowledge-graph)
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
├── <source-dir>/            # Layer 1: Raw sources (immutable)
├── wiki/                    # Layer 2: LLM-maintained wiki
│   ├── .schema/             #   Per-wiki schema pin
│   ├── .schema-proposals/   #   Pending schema proposals
│   ├── index.md             #   Content catalog
│   ├── hot.md               #   Current focus + maintenance debt
│   ├── overview.md          #   Project overview
│   ├── log.md               #   Chronological record
│   ├── entities/            #   Artifact pages
│   ├── concepts/            #   Concept pages
│   ├── sources/             #   Source summaries
│   ├── procedures/          #   Step-by-step processes
│   ├── experiences/         #   Trial-and-error episodes
│   ├── heuristics/          #   Rules and lessons
│   ├── decisions/           #   Design decisions
│   └── queries/             #   Query result cache
├── graphify-out/            # Structural graph layer
│   ├── graph.json           #   Nodes, edges, communities
│   ├── manifest.json        #   Hashes for incremental updates
│   └── GRAPH_REPORT.md      #   God nodes, surprises
└── CLAUDE.md                # Schema conventions and workflows
```

### Naming Convention

- **`/kg-<verb>`** (hyphen) — canonical user-facing commands. Sub-skill `trigger:` fields use this form.
- **`/kg <verb>`** (space) — prose notation for readability. Always use the hyphenated form when invoking.

## Interaction Principles

1. **Asymmetric roles** — Human provides judgment and direction. LLM provides recall, cross-referencing, and pattern detection across documents.
2. **Productive friction** — Agreement is cheap. The valuable interaction happens when the LLM surfaces contradictions, gaps, or unexpected connections.
3. **Filed dialogue** — Insights from reflect, challenge, and connect are filed back into the wiki. The dialogue itself compounds.
4. **Schema as product** — The schema (`core.yaml` + `relations.yaml`) is not infrastructure — it IS the domain model. All changes are proposal-first.

## Tools

| File | Purpose |
|------|---------|
| `kg/schema/tools/validate.py` | Frontmatter validation, relation domain/range checks, receipt generation |
| `kg/schema/tools/build_search_index.py` | Build BM25 search index for wiki |
| `kg/schema/core.yaml` | Class definitions, epistemic states, confidence levels |
| `kg/schema/relations.yaml` | Predicate definitions with domain/range constraints |
| `kg/schema/frontmatter.yaml` | Field types and enumerations |
| `kg/templates/*.md` | Per-class page templates |

## License

MIT
