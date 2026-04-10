---
name: kg
description: Knowledge graph + LLM wiki — full reference. Sub-commands: /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest (data ops) and /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest (dialogue ops). Also triggers when wiki/ or graphify-out/ exist.
trigger: /kg
---

# Knowledge Graph + LLM Wiki

A persistent, compounding knowledge base combining two layers:

- **Graphify** extracts structural relationships (god nodes, communities, surprising connections) from any corpus.
- **LLM Wiki** (Karpathy pattern) maintains a living Obsidian vault of entity pages, concept summaries, and cross-references.

The graph tells you what's connected. The wiki tells you what it means. Either layer works standalone — both together compound across sessions.

## Architecture

```
project/
├── <source-dir>/           # Layer 1: Raw sources (immutable)
│   └── (auto-detected: gMeso/vault/, raw/, docs/, or user-specified)
│
├── wiki/                   # Layer 2: LLM-maintained wiki (optional)
│   ├── index.md            #   Content catalog — every page listed
│   ├── log.md              #   Chronological record of operations
│   ├── overview.md         #   High-level synthesis
│   ├── graph-report.md     #   Synced from graphify-out/GRAPH_REPORT.md
│   ├── entities/           #   Entity pages
│   ├── concepts/           #   Concept pages
│   ├── sources/            #   Source summaries (one per ingested file)
│   └── queries/            #   Filed query results worth keeping
│
├── graphify-out/           # Structural graph layer
│   ├── graph.json          #   Nodes, edges, communities
│   ├── GRAPH_REPORT.md     #   God nodes, communities, surprises
│   └── cache/              #   SHA256 extraction cache
│
└── CLAUDE.md               # Schema — conventions and workflows
```

**Source directory detection** (checked in order):
1. User-specified path (if given)
2. `gMeso/vault/` — KIM-meso project convention
3. `raw/` — Karpathy /raw pattern
4. `docs/` — common documentation folder
5. Current directory `.`

**Two operating modes:**
- **Graph-only** (default): Only `graphify-out/` exists. `/kg orient`, `/kg query`, `/kg update` all work against the graph alone.
- **Graph + Wiki**: Both `graphify-out/` and `wiki/` exist. Wiki provides semantic depth on top of structural graph.

## Operations

### `/kg orient` — Session Start Orientation

Run at the start of each session to understand accumulated knowledge. This is the most common entry point.

**Steps:**

1. Detect which layers exist:
   ```
   graphify-out/GRAPH_REPORT.md  → graph layer
   wiki/index.md                 → wiki layer
   ```

2. If graph layer exists, read `graphify-out/GRAPH_REPORT.md` (first 60 lines — god nodes + communities).

3. If wiki layer exists, read `wiki/index.md` and tail of `wiki/log.md` (last 20 lines).

4. Check freshness: compare `graph.json` mtime vs newest source file.

5. Present summary:
   ```
   Graph: X nodes · Y edges · Z communities
   Top god nodes: [top 3 by degree]
   Wiki: N pages (E entities, C concepts, S sources)  [or "not initialized"]
   Last activity: [date] — [last log entry]
   Freshness: FRESH | STALE (N files changed since last build)
   ```

### `/kg init [path]` — Initialize

Set up the knowledge base structure. Adapts to what already exists.

1. Detect source directory (see detection order above)
2. If `graphify-out/graph.json` already exists, skip to orientation
3. If sources exist but no graph, run `/graphify <source-dir>` to build initial graph
4. Create `wiki/` structure only if user explicitly requests wiki mode:
   - `wiki/index.md` — header template
   - `wiki/log.md` — first entry
   - `wiki/overview.md` — placeholder
   - `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/queries/`
5. If `.obsidian/` exists nearby, configure for wikilinks:
   ```json
   {"alwaysUpdateLinks": true, "newLinkFormat": "shortest", "useMarkdownLinks": false}
   ```

### `/kg update` — Incremental Graph Rebuild

Rebuild the structural graph layer without re-ingesting into wiki. Delegates to Graphify.

**Steps:**

1. Detect source directory
2. Run graphify `--update` pipeline on the source directory:
   - This uses SHA256 cache to find only new/changed files
   - Code-only changes skip semantic extraction (no LLM cost)
   - Re-clusters communities and regenerates GRAPH_REPORT.md
3. If wiki exists, sync: copy relevant sections of `GRAPH_REPORT.md` into `wiki/graph-report.md`
4. Report delta: new nodes, removed nodes, community changes

To run manually: invoke `/graphify <source-dir> --update`

### `/kg ingest [file-or-folder]` — Ingest into Wiki

The core wiki-building operation. Requires wiki layer to be initialized.

**Flow per source:**

1. **Read** the source file completely
2. **Discuss** 3-5 key takeaways with the user
3. **Write source summary** → `wiki/sources/<source-name>.md`
   - YAML frontmatter: `title`, `date_ingested`, `source_type`, `tags`
   - Summary with key claims
   - `[[wikilinks]]` to entity/concept pages
4. **Update entity pages** → `wiki/entities/<entity>.md`
   - Create if new, append section if existing
   - What it is, where it appears, how it connects
5. **Update concept pages** → `wiki/concepts/<concept>.md`
   - Include rationale — WHY decisions were made
6. **Update** `wiki/overview.md`, `wiki/index.md`
7. **Append to `wiki/log.md`**:
   ```markdown
   ## [YYYY-MM-DD] ingest | Source Title
   - Added: sources/source-name.md
   - Updated: entities/module-x.md, concepts/openacc-porting.md
   - New pages: entities/new-entity.md
   ```
8. **Rebuild graph** — run `/kg update` to refresh structural layer

**Batch ingest**: If many files, ask: "Process all at once or one by one?" Batch mode skips discussion, uses parallel subagents.

### `/kg query [question]` — Query Knowledge

Answer questions against accumulated knowledge. Strategy depends on what layers exist.

**Graph-only mode** (no wiki):
1. Read `graphify-out/GRAPH_REPORT.md` for structural context
2. Use `/graphify query "question"` for graph traversal (BFS default, DFS for path-tracing)
3. Read source files cited in graph nodes for detail
4. Synthesize answer with source citations

**Graph + Wiki mode**:
1. Read `wiki/index.md` to find relevant pages
2. Read relevant wiki pages (pre-synthesized — faster than raw sources)
3. For structural questions, supplement with `/graphify query`
4. Synthesize answer with `[[wikilinks]]` citations
5. If answer is worth keeping: file to `wiki/queries/<question-slug>.md`

**Verification chain**: Graph → Wiki → Raw Source. The graph finds direction, the wiki provides context, the raw source verifies claims. Never cite graph or wiki as primary evidence in decisions.

### `/kg lint` — Health Check

Audit knowledge base health. Adapts to available layers.

**Graph-only checks** (always run):
- `graph.json` exists and is parseable
- `GRAPH_REPORT.md` exists
- `manifest.json` exists (needed for incremental updates)
- `.graphify_python` points to valid interpreter
- Freshness: source files newer than `graph.json`

**Wiki checks** (only when `wiki/` exists):
- **Orphan pages** — no inbound `[[wikilinks]]`
- **Missing pages** — referenced in `[[wikilinks]]` but don't exist
- **Missing cross-references** — pages that should link but don't
- **Graph drift** — `graph-report.md` older than newest wiki page
- **Stale claims** — superseded by recent ingests

Report findings, offer to fix. If wiki exists, log the lint pass in `wiki/log.md`.

## Dialogue Operations (상호작용)

Karpathy's pattern makes the LLM a diligent scribe. These operations make it a thinking partner — the LLM notices what the human might miss, challenges assumptions, and surfaces connections that cross the boundaries of what either could see alone.

### `/kg reflect` — Proactive Insight

After ingest or at session end, the LLM reviews recent activity and offers unprompted observations. Not a summary — a provocation.

**What to surface:**
- **Tensions** — "Source A claims X, but source B implies Y. Which is closer to your current understanding?"
- **Emerging patterns** — "The last 3 ingested sources all touch on [theme]. This might be becoming a central concern worth its own concept page."
- **Blind spots** — "Community C3 (KDM6 Phase 2b-4) has 15 nodes but zero inbound edges from C1 (RRTMG). Is this isolation intentional or a gap?"
- **Shifted ground** — "Your early sources assumed X. Recent sources assume not-X. The wiki still reflects the old framing in these pages: [list]."

The goal is to make the user think, not to inform. If reflect produces no genuine insight, say so — don't fabricate one.

**When to trigger:** Automatically after every 3rd ingest, or when the user explicitly asks. Log reflections in `wiki/log.md` as `## [date] reflect | [one-line thesis]`.

### `/kg challenge [claim]` — Devil's Advocate

The user states a belief or the LLM picks one from the wiki. The LLM then argues against it using only evidence from the knowledge base.

**Flow:**
1. If no claim given, pick the highest-confidence INFERRED edge or the most central concept in the wiki
2. Find all evidence that supports the claim
3. Find all evidence that contradicts or weakens it
4. Present the counter-argument with citations
5. Ask: "Does this change anything, or does the original claim still hold?"

This is not about being right. It's about stress-testing knowledge before it calcifies.

### `/kg connect` — Cross-Community Bridge Discovery

Graphify finds communities. This operation finds the *missing bridges* between them — connections that should exist based on semantic content but don't appear structurally.

**Steps:**
1. Load graph communities from GRAPH_REPORT.md
2. For each pair of communities with zero or few cross-edges, read representative nodes from each
3. Propose potential connections: "Node A in C0 and Node B in C4 both deal with [shared concern], but they've never been linked. Is there a real relationship here?"
4. If the user confirms, add the edge to the graph (INFERRED, with rationale)

This is where the graph and the human co-create knowledge that neither could produce alone.

### `/kg evolve [concept]` — Understanding Timeline

Track how the user's understanding of a concept has changed across sessions.

**Steps:**
1. Read `wiki/log.md` for all entries mentioning the concept
2. Read the concept page's revision history (git log, or frontmatter date_modified)
3. Read query results that touched this concept
4. Present a timeline: "Here's how your understanding of [concept] evolved:"
   - [date] First mention via [source] — initial framing was X
   - [date] Challenged by [source] — shifted to Y
   - [date] Your query revealed Z — current synthesis
5. Ask: "Is this trajectory still the right direction, or has something shifted again?"

### `/kg suggest` — Next Source Recommendation

Based on current knowledge gaps, suggest what to read/ingest next.

**Steps:**
1. Identify orphan concepts (mentioned but no dedicated page)
2. Find communities with low cohesion scores (weakly connected internally)
3. Check for unresolved `[[wikilinks]]` (pages that should exist but don't)
4. Look for topics where the most recent source is old
5. Propose 3-5 specific suggestions: "To strengthen the knowledge base, consider ingesting something about [topic] — it's referenced 4 times but never directly addressed."

### Interaction Principles

These dialogue operations follow three principles:

1. **Asymmetric roles** — The human provides judgment, direction, and domain intuition. The LLM provides recall, cross-referencing, and pattern detection across documents the human hasn't re-read in weeks. Neither can do the other's job.

2. **Productive friction** — Agreement is cheap. The valuable interaction happens when the LLM surfaces something the human didn't expect — a contradiction, a gap, a connection that crosses community boundaries. If every interaction confirms what the user already knows, the system is failing.

3. **Filed dialogue** — Insights from reflect, challenge, and connect are not chat ephemera. They get filed back into the wiki (`wiki/queries/` or as updates to concept pages). The dialogue itself compounds, just like ingested sources.

## Wiki Page Conventions

### Frontmatter

```yaml
---
title: Page Title
type: entity | concept | source | query | overview
tags: [relevant, tags]
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
sources: [source-file-1.pdf, source-file-2.md]
---
```

### Wikilinks

Always use `[[wikilinks]]` for cross-references. This powers Obsidian's graph view and backlinks. Create links to pages that don't exist yet — Obsidian shows these as unresolved links (natural TODO list).

### Page Templates

**Entity** (`wiki/entities/module-mp-kdm6.md`):
```markdown
---
title: module_mp_kdm6
type: entity
tags: [fortran, microphysics, kdm6]
---
# module_mp_kdm6

KDM6 microphysics module. Contains the main physics hotspot `kdm62D`.

## Key Facts
- Single live caller: [[module-microphysics-driver]] at line 2538
- ~2600 lines of Fortran, R8 precision

## Connections
- Called by: [[module-microphysics-driver]]
- Concepts: [[openacc-porting]], [[register-pressure]]
```

**Concept** (`wiki/concepts/register-pressure.md`):
```markdown
---
title: Register Pressure Risk (R1)
type: concept
tags: [gpu, risk, openacc]
---
# Register Pressure

Risk R1 in [[plan-kdm6-b200]]. kdm62D is ~2600 lines with hundreds
of local variables — likely occupancy collapse on GPU.

## Why This Matters
[rationale — extracted from source decisions]

## Current Status
Path C: monolithic refactor first, probe, split if spill > threshold.
```

## Usage Rules

1. **Raw sources are immutable** — The LLM reads from source files but never modifies them. They are the source of truth. The wiki and graph are derived artifacts.

2. **Don't Grep-first** — When wiki exists, read `wiki/index.md` first. When only graph exists, read `GRAPH_REPORT.md` first. Grep is for precise lookups after orientation.

3. **Graph supplements, never replaces** — The graph is structural (what connects to what). The wiki is semantic (what it means, why it matters). Neither replaces raw sources.

4. **Keep the wiki growing** — Every ingested source, answered query, lint fix makes it richer. Human curates sources and asks questions. LLM does the bookkeeping.

5. **Co-evolve the schema** — CLAUDE.md documents how the wiki is structured, what conventions apply, what workflows to follow. As you learn what works for your domain, update CLAUDE.md together with the LLM. The schema is what makes the LLM a disciplined wiki maintainer rather than a generic chatbot.

## Technical Notes

- **graph.json format**: Saved as NetworkX `node_link_data` — top-level keys are `nodes`, `links` (not `edges`). Load with `json_graph.node_link_graph(data, edges='links')`. For extraction format (with `edges` key), use `build_from_json()`.
- **Manifest location**: `graphify-out/manifest.json` (no `.graphify_` prefix). Used by `detect_incremental()` to identify changed files.
- **Graphify Python**: Interpreter path at `graphify-out/.graphify_python`. If missing, re-resolve via `which graphify`.
- **No git required** for Graphify (SHA256 cache). Wiki benefits from git for version history.
- **Cost**: Graph build ~ 1 API call per doc file. Wiki pages are part of the conversation (no extra cost). Incremental updates only process changed files.
