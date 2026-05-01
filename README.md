# kg-skill

> **Language / 언어:** **English** | [한국어](README.ko.md)

A Knowledge Graph + LLM Wiki skill set for [Claude Code](https://claude.ai/claude-code).

Build a **persistent, compounding knowledge base** for any project. The LLM curates a structured wiki, [Graphify](https://github.com/safishamsi/graphify) extracts the structural graph, and you keep both layers in sync with **18 deterministic slash commands** that follow a single 5-formula contract.

Inspired by [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) and extended with a 7-class ontology, proposal-first schema evolution, receipt-based quality gates, and graphify v0.5.0+ MCP integration.

---

## Why this might help you

You probably already have many of the pieces:

- **A folder of papers/code/notes** — but you forget what's connected to what
- **A vague memory** — "I read something about this six months ago…"
- **A growing wiki** — but it drifts out of sync with the code or with your evolving understanding
- **Many AI sessions** — but each one starts from zero

`kg-skill` gives Claude a **single, structured way** to remember across sessions:

```text
You              kg-skill                    Claude across sessions
────────         ─────────────────           ──────────────────────
"ingest paper" → /kg-ingest paper.pdf  →    knows the paper, links to your concepts
"why X over Y?" → /kg-query --depth deep →  cites your past decisions with evidence
"review wiki"   → /kg-reflect          →    surfaces tensions you didn't see
"audit it"      → /kg-lint             →    finds dead links, stale claims, schema drift
```

Every operation is **deterministic where possible** (BM25 search, graph traversal, validator scripts) and **human-gated where authority matters** (schema changes, page deletion, source approval).

---

## Quick Start (5 minutes)

```bash
# 1. Install graphify (graph extraction backend)
pip install graphifyy

# 2. Install kg-skill into Claude
git clone https://github.com/gonos2k/kg-skill.git ~/kg-skill-source
cd ~/kg-skill-source
cp -r kg kg-* ~/.claude/skills/

# 3. In Claude Code, bootstrap a wiki
/kg-init

# 4. Drop a paper or code repo into raw/ and ingest
/kg-ingest raw/my-paper.pdf

# 5. Ask questions
/kg-query "what does my paper say about X?"

# 6. After a few ingests, surface insights
/kg-reflect
```

That's it. Every skill follows the same 5-formula structure (see below) and produces predictable Output Contracts.

## Compatibility

kg-skill releases track [graphifyy](https://pypi.org/project/graphifyy/) closely. Each kg-skill release lists the **minimum** graphifyy that ships every CLI surface it relies on:

| kg-skill | Minimum `graphifyy` | New behavior gated on this version |
|---|---|---|
| **v0.5.7** (current) | **`graphifyy>=0.5.7`** | `.graphify_root` scan-root memo (argument-less `graphify update`); kg-update wiki back-pointer maintenance |
| v0.5.4 – v0.5.6 | `graphifyy>=0.5.0` | Multi-corpus naming convention, MCP integration via `--mcp` slash form |
| v0.5.0 – v0.5.3 | `graphifyy>=0.5.0` | Initial 0.5.x line |

Older `graphifyy` versions still work for the kg-skill features that don't depend on the newer CLI behavior — the table above lists the floor required to unlock all features documented for that kg-skill release. To align:

```bash
pip install --upgrade 'graphifyy>=0.5.7'
```

---

## The 5-Formula Standard

Every `kg-*` skill is structured the same way, so Claude behaves consistently:

| Section | What it answers |
|---|---|
| **YAML Trigger** | When should this skill activate? (specific phrases, project state) |
| **Activate When / Do Not Activate When** | Explicit positive + negative triggers — prevents skill collision |
| **Workflow** | Step-by-step plan including a "stop condition" |
| **Output Contract** | A fenced `text` block with standard fields (`Confidence:`, `Caveats:`, `Next command:`) — see [`kg/references/output-contract-standard.md`](kg/references/output-contract-standard.md) |
| **Examples + Exceptions and Escalation** | Concrete usage + every escape hatch closed (e.g., "user 'yes' is not approval") |

This means the LLM **cannot improvise where authority matters**. Try it: invoke any `/kg-*` command and you'll get the same shape every time.

---

## Slash Commands (18)

### Data operations — accumulate knowledge

| Command | Purpose |
|---|---|
| `/kg-init` | Bootstrap a wiki (schema, folders, indexes). Idempotent. |
| `/kg-ingest` | Read a source, discuss takeaways, write source/entity/concept pages with [[wikilinks]]. |
| `/kg-update` | Refresh the structural graph (CLI: `graphify update <path>`; for doc/paper re-extract: slash form `/graphify <path> --update`). |
| `/kg-query` | BFS/DFS traversal + wiki lookup. `--depth quick\|standard\|deep`. |
| `/kg-lint` | Health check — orphan pages, dead links, stale claims, proposal debt. |
| `/kg-orient` | Read-only session start summary (hot.md, graph stats, freshness). |

### Dialogue operations — make the LLM a thinking partner

| Command | Purpose |
|---|---|
| `/kg-reflect` | Surface tensions, emerging patterns, blind spots, schema drift. Not a summary — only non-obvious insights. |
| `/kg-challenge` | Devil's advocate. Argues against a wiki claim **using only existing evidence**. |
| `/kg-connect` | Find missing bridges between graph communities. Never auto-adds edges. |
| `/kg-suggest` | Recommend next sources/actions based on real knowledge gaps. |
| `/kg-elicit` | Capture tacit knowledge from dialogue → Experience (always) + optional Heuristic. |
| `/kg-postmortem` | Stricter `/kg-elicit` for recent discrete failures (verbatim error preserved). |
| `/kg-autoresearch` | Supervised multi-round web research. Queues findings for explicit user approval — never auto-ingests. |

### Governance & integration

| Command | Purpose |
|---|---|
| `/kg-schema` | Evolve the ontology — `propose`, `approve`, `apply`, `migrate`, `diff`, `list`, `pull-global`. Receipt-gated. |
| `/kg-canvas` | Export wiki as Obsidian Canvas (`.canvas` JSON). Read-only. |
| `/kg-merge` | **NEW** — Cross-project KG via `graphify merge-graphs` (multiple repos → one merged graph). |
| `/kg-mcp` | **NEW** — Register `graphify --mcp` in `.mcp.json` so other skills query the graph as MCP tools (no graph.json reload). `--apply` Authority gate. |

### The router

| Command | Purpose |
|---|---|
| `/kg` | Router — explains the system or routes you to the right sub-command. Does not execute operations itself. |

---

## Ontology (v1) — 7 classes

Each wiki page is one class with structured frontmatter:

| Class | Purpose | Folder |
|---|---|---|
| **Artifact** | Code entities (functions, modules, kernels) | `wiki/entities/` |
| **Concept** | Domain concepts and theories | `wiki/concepts/` |
| **Source** | Paper / document / URL summaries | `wiki/sources/` |
| **Procedure** | Step-by-step processes | `wiki/procedures/` |
| **Experience** | Trial-and-error episodes (kept verbatim) | `wiki/experiences/` |
| **Heuristic** | Distilled rules of thumb | `wiki/heuristics/` |
| **Decision** | Design decisions with rationale | `wiki/decisions/` |

### Schema evolution (proposal-first)

```text
/kg-reflect (detect drift)
    → /kg-schema propose (file proposal)
        → /kg-schema approve (collect receipt + 6-sensor gate)
            → /kg-schema apply (only if Receipt passed)
                → /kg-schema migrate (update affected pages)
```

**Authority Matrix** (per [`kg/references/authority-matrix.md`](kg/references/authority-matrix.md))

| Action | Authority | Why |
|---|---|---|
| Schema change | **Human** | Ontology is the contract |
| Page reclassification / deletion | **Human** | Folder change = identity change |
| Source approve (autoresearch) | **Human** | Provenance integrity |
| Heuristic promotion from Experience | **Human** | Generalization is a judgment call |
| `hot.md` / `log.md` / `_index.md` updates | **LLM** | Bookkeeping, regenerable |
| `pull-global` compatible changes | **LLM (dry-run first)** | Always preview |

---

## Architecture

```text
project/
├── <source-dir>/             # Layer 1 — Raw sources (immutable)
│   └── (auto-detected: gMeso/vault/, raw/, docs/, or .)
├── wiki/                     # Layer 2 — LLM-maintained wiki
│   ├── .schema/              #   Per-wiki schema pin (copied on /kg-init)
│   ├── .schema-proposals/    #   Pending proposals + receipts
│   ├── .research-queue/      #   /kg-autoresearch staging (approved/rejected)
│   ├── index.md              #   Content catalog (last-resort read)
│   ├── hot.md                #   ~500-word session context cache
│   ├── overview.md           #   Stable global synthesis
│   ├── log.md                #   Append-only operation history
│   ├── entities/             #   Artifact pages
│   ├── concepts/             #   Concept pages
│   ├── procedures/           #   Procedure pages
│   ├── experiences/          #   Experience pages
│   ├── heuristics/           #   Heuristic pages
│   ├── decisions/            #   Decision pages
│   ├── sources/              #   Source summaries
│   └── queries/              #   Filed query results
└── graphify-out/             # Structural graph layer (graphify v0.5.0+)
    ├── graph.json            #   NetworkX node_link_data
    ├── GRAPH_REPORT.md       #   God nodes, communities, surprises
    ├── graph.html            #   Interactive HTML (default)
    ├── manifest.json         #   SHA256 manifest for incremental updates
    ├── memory/               #   Q&A feedback loop
    ├── merged-graph.json     #   Cross-repo merge output
    └── (optional: graph.svg, graph.graphml, cypher.txt)
```

### Verification chain

**Graph → Wiki → Raw Source** is the trust hierarchy. The wiki is **derived**; the raw source is **authoritative**. `/kg-query` cites raw sources for any decision-grade answer.

### Two operating modes

- **Graph-only**: only `graphify-out/` exists. `/kg-orient`, `/kg-query`, `/kg-update` work alone.
- **Graph + Wiki**: both exist. The wiki adds semantic depth to the structural graph.

---

## References library

`kg/references/` — load on demand by Claude (progressive disclosure):

| File | Topic |
|---|---|
| [`architecture.md`](kg/references/architecture.md) | Layout, source detection, page templates, technical notes |
| [`ontology.md`](kg/references/ontology.md) | 7 classes, page_kind, instance_of, schema-as-product, proposal/receipt |
| [`authority-matrix.md`](kg/references/authority-matrix.md) | Human vs LLM authority, hot.md priority, novelty test |
| [`context-compression.md`](kg/references/context-compression.md) | BM25 search, hot/overview/_index hierarchy, archive policy |
| [`schema-evolution.md`](kg/references/schema-evolution.md) | Migration policy, supersession, convergence tracking |
| [`codex-integration.md`](kg/references/codex-integration.md) | Bidirectional Codex pipeline (review filing, domain context injection) |
| [`output-contract-standard.md`](kg/references/output-contract-standard.md) | Standard Output Contract field names — `Next command:`, `Confidence:`, `Caveats:` |

---

## Helper tools

`kg/schema/tools/` — deterministic helpers offload work from LLM judgment:

| Script | Purpose |
|---|---|
| `validate.py` | Frontmatter validation, relation domain/range checks, receipt generation |
| `build_search_index.py` | BM25 search index builder (Korean+English CJK tokenizer) |
| `check_skill_frontmatter.py` | Validate every SKILL.md (YAML, required keys, trigger equality, body forbidden patterns) |
| `kg_lint.py` | Wiki sensor — orphan pages, missing wikilinks, deprecated-without-callout, supersession orphans |
| `extract_claims.py` | Parse `> [!claim]`, `> [!evidence]`, `> [!tension]` callouts → JSON for `/kg-query` and `/kg-challenge` |

---

## graphify integration (soft dependency)

11 sub-skills automatically use [graphify](https://github.com/safishamsi/graphify) v0.5.0+ when available, falling back gracefully when absent or stale.

**Freshness gate**: `graphify-out/graph.json` is treated as authoritative only when `mtime < 7 days`. Stale graphs degrade to wiki-only / BM25-only paths and note the staleness in `Caveats:`.

**MCP server tools** (via `graphify <path> --mcp`):

| Tool | Used by |
|---|---|
| `query_graph` | `/kg-query` (BFS/DFS with token budget) |
| `get_node` / `get_neighbors` | `/kg-challenge`, `/kg-elicit` |
| `get_community` | `/kg-connect`, `/kg-suggest` |
| `god_nodes` | `/kg-orient`, `/kg-suggest` |
| `graph_stats` | `/kg-orient`, `/kg-lint` |
| `shortest_path` | `/kg-ingest` (confirmation gate), `/kg-postmortem` (pattern detection), `/kg-connect` (objective distance) |

Register MCP server with `/kg-mcp register --scope project --apply`.

---

## Installation

### Requirements

- Python ≥ 3.10
- [graphify](https://github.com/safishamsi/graphify) v0.5.0+: `pip install graphifyy`
- [Obsidian](https://obsidian.md/) (optional, for browsing wiki with graph view)

### Install skills

```bash
git clone https://github.com/gonos2k/kg-skill.git
cd kg-skill
cp -r kg kg-* ~/.claude/skills/
```

### Add to `~/.claude/CLAUDE.md`

```markdown
## kg (knowledge-graph)
- **kg** (`~/.claude/skills/kg/SKILL.md`) — Knowledge graph + LLM wiki router.
  Sub-commands: /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest,
  /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest, /kg-elicit,
  /kg-postmortem, /kg-schema, /kg-autoresearch, /kg-canvas, /kg-merge, /kg-mcp.
When the user types /kg or any sub-command, invoke the Skill tool with the matching skill name.
When wiki/ or graphify-out/ exists in the project, the kg-orient skill auto-suggests at session start.
```

### Verify install

```bash
python3 ~/.claude/skills/kg/schema/tools/check_skill_frontmatter.py
# expected: PASS — 18 SKILL.md files OK
```

---

## Naming convention

- **`/kg-<verb>`** (hyphen) — canonical user-facing slash command. Always use this form.
- **`/kg <verb>`** (space) — never used; the hyphenated form is ground truth in every sub-skill's `trigger:` field.

---

## Interaction principles

1. **Asymmetric roles** — Human provides judgment and direction. LLM provides recall, cross-referencing, and pattern detection.
2. **Productive friction** — Agreement is cheap. Value comes when the LLM surfaces contradictions, gaps, or unexpected connections.
3. **Filed dialogue** — Insights from `/kg-reflect`, `/kg-challenge`, `/kg-connect` are filed back into the wiki. The dialogue itself compounds.
4. **Schema as product** — `core.yaml` + `relations.yaml` is not infrastructure — it IS the domain model. All changes proposal-first.
5. **Deterministic > LLM judgment** — When a check can be a script (BM25, graph distance, frontmatter validation), it should be. LLM judgment is reserved for content questions.

---

## Real-use patterns

The skill set is structured around four observations:

1. **Supersession over deletion** — When new evidence overturns a prior claim, the old page is preserved with a `[SUPERSEDED]` callout linking to its replacement. Git history is not the audit trail; the wiki is.

2. **Productive friction is the product** — `/kg-challenge` and `/kg-reflect` are designed to generate disagreement, not consensus. Tension callouts and evidence-cited claims keep corrections cleanly applicable.

3. **Adversarial review prefers small prompts, in parallel** — External-LLM critiques are more reliable as short, single-question, parallel reviews than as long synthesis prompts. See [`kg/references/codex-integration.md`](kg/references/codex-integration.md).

4. **`Caveats:` is non-negotiable** — Every Output Contract carries a `Caveats:` line. Findings that *cannot* be fixed live there; the field refuses the temptation to silently drop unfixable issues.

---

## License

MIT
