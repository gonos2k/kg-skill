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
│   ├── .schema/            #   Per-wiki schema pin (copied from global on /kg init)
│   │   ├── core.yaml       #     Class definitions
│   │   ├── relations.yaml  #     Predicate vocabulary
│   │   ├── frontmatter.yaml#     Field spec
│   │   ├── pin.yaml        #     Version lock
│   │   └── migrations/     #     Schema history
│   ├── .schema-proposals/  #   Pending schema change proposals
│   ├── index.md            #   Content catalog — every page listed
│   ├── hot.md              #   Session context cache (~500 words)
│   ├── log.md              #   Chronological record of operations
│   ├── overview.md         #   High-level synthesis
│   ├── graph-report.md     #   Synced from graphify-out/GRAPH_REPORT.md
│   ├── entities/           #   Artifact pages (code, files, data)
│   │   └── _index.md       #     Folder-level index
│   ├── concepts/           #   Concept pages (abstract ideas)
│   │   └── _index.md
│   ├── procedures/         #   Procedure pages (how-to steps)
│   │   └── _index.md
│   ├── experiences/        #   Experience pages (case records)
│   │   └── _index.md
│   ├── heuristics/         #   Heuristic pages (rules of thumb, 비법)
│   │   └── _index.md
│   ├── decisions/          #   Decision pages (ADR style)
│   │   └── _index.md
│   ├── sources/            #   Source summaries (one per ingested file)
│   │   └── _index.md
│   └── queries/            #   Filed query results worth keeping
│       └── _index.md
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

## Evolving Mini-Ontology

kg v2 separates **page_kind** (document format) from **instance_of** (ontology class). The schema is minimal by design and grows with use.

### Core classes (7)
- **Artifact** — physical code/file/data (`entities/`)
- **Concept** — abstract idea (`concepts/`)
- **Procedure** — how-to steps (`procedures/`)
- **Experience** — episodic case (`experiences/`)
- **Heuristic** — rule of thumb / 비법 (`heuristics/`)
- **Decision** — judgment record (`decisions/`)
- **Source** — ingested source summary (`sources/`)

### Epistemic status
Pages carry one of: `observed`, `inferred`, `hypothesis`, `validated`, `deprecated`.
- Required on: Artifact, Concept, Procedure, Heuristic.
- Optional on: Experience, Decision (these use `date` as primary metadata instead).
- `hypothesis` is distinct from `inferred`: a working guess pending evidence vs. reasoned from existing sources.

### Confidence levels (optional)
Supplementary to epistemic status: `high`, `medium`, `low`. Required on Heuristic; optional elsewhere.

### Frontmatter spec
See `schema/frontmatter.yaml` for required/optional fields per page_kind. Minimum example:

```yaml
---
title: Page Title
instance_of: Artifact | Concept | Procedure | Experience | Heuristic | Decision
page_kind: entity-page | concept-page | procedure-page | ...
epistemic_status: observed | inferred | hypothesis | validated | deprecated
confidence: high | medium | low
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
provenance:
  sources: [source-file.pdf]
  code_refs: ["file.F:123"]
relations:
  - {predicate: implements, target: "[[concept]]", rationale: ""}
---
```

### Legacy page interpretation
Existing `wiki/entities/*.md` and `wiki/concepts/*.md` pages without the new frontmatter fields are valid. The validator applies `legacy_mode` rules from `core.yaml`: implicit `instance_of`, `page_kind`, and `schema_origin: legacy`. No rewrites without explicit user approval.

### Schema ownership (global default vs per-wiki pin)
- **Global default** at `~/.claude/skills/kg/schema/` — shipped with the skill.
- **Per-wiki pin** at `<project>/wiki/.schema/` — copied on `/kg init`. Records the exact schema version.
- All `/kg-schema` operations target the per-wiki pin by default. `--global` flag for default.
- Cross-project divergence is expected. `/kg-schema diff --global` shows drift.

### Hot cache (`wiki/hot.md`) — session context persistence
~500-word compressed context summary that survives between sessions.

**Lifecycle:**
- **Session start (`/kg-orient`)**: read `hot.md` FIRST, before `index.md`.
- **After major write ops** (`/kg-ingest`, `/kg-elicit`, `/kg-postmortem`, `/kg-reflect`): overwrite with Current Focus, Recent Activity, Key Tensions.
- **Context compaction**: re-read `hot.md` to recover session state.
- The cache is a **view**, never a source of truth.

### Folder-level indexes (`<folder>/_index.md`)
Each content folder has a lightweight `_index.md` for query routing. Updated alongside the main index on ingest/elicit operations.

## Operations

### Naming convention
- **`/kg-<verb>`** (hyphen) — independent slash commands invoking each sub-skill directly. These are the canonical user-facing commands (e.g., `/kg-orient`, `/kg-query`, `/kg-schema`).
- **`/kg <verb>`** (space) — logical sub-command notation sometimes used in prose for readability. Section headers in this document use the canonical hyphenated form. Always use `/kg-<verb>` when invoking.
- Sub-skill frontmatter `trigger:` field always uses the hyphenated form (ground truth).

### `/kg-orient` — Session Start Orientation

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

### `/kg-init [path]` — Initialize

Set up the knowledge base structure. Adapts to what already exists.

1. Detect source directory (see detection order above)
2. If `graphify-out/graph.json` already exists, skip graph build
3. If sources exist but no graph, run `/graphify <source-dir>` to build initial graph
4. Create `wiki/` structure:
   - `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/queries/`
   - `wiki/index.md` — initial content:
     ```markdown
     ---
     title: Knowledge Base Index
     type: overview
     date_modified: YYYY-MM-DD
     ---
     # Index

     ## Entities
     (none yet)

     ## Concepts
     (none yet)

     ## Sources
     (none yet)

     ## Queries
     (none yet)
     ```
   - `wiki/log.md` — first entry:
     ```markdown
     # Knowledge Base Log

     ## [YYYY-MM-DD] init | Wiki initialized
     - Created: index.md, log.md, overview.md
     - Source directory: <detected-path>
     - Graph: <N nodes, M edges> (or "not yet built")
     ```
   - `wiki/overview.md` — seed from GRAPH_REPORT.md if it exists:
     ```markdown
     ---
     title: Overview
     type: overview
     date_modified: YYYY-MM-DD
     ---
     # Overview

     [High-level synthesis of the knowledge base. Updated on each ingest.
      If graph exists, seed with god nodes and community structure.]
     ```
   - `wiki/graph-report.md` — copy God Nodes + Communities + Surprising Connections from `GRAPH_REPORT.md`
5. If `.obsidian/` exists nearby, configure for wikilinks:
   ```json
   {"alwaysUpdateLinks": true, "newLinkFormat": "shortest", "useMarkdownLinks": false}
   ```
6. Run `/kg-orient` to present the initial state

### `/kg-update` — Incremental Graph Rebuild

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

### `/kg-ingest [file-or-folder]` — Ingest into Wiki

The core wiki-building operation. Requires wiki layer to be initialized.

**Flow per source:**

1. **Read** the source file completely
2. **Discuss** 3-5 key takeaways with the user
3. **Write source summary** → `wiki/sources/<source-name>.md`
   - YAML frontmatter: `title`, `date_ingested`, `source_type`, `tags`
   - Summary with key claims
   - `[[wikilinks]]` to entity/concept pages
4. **Update entity pages** → `wiki/entities/<entity>.md`
   - **New entity**: create page with Key Facts + Connections sections
   - **Existing entity**: add new facts under a `## From <source>` section. If new info contradicts existing claims, flag with `> [!warning] Tension: ...` and keep both versions
5. **Update concept pages** → `wiki/concepts/<concept>.md`
   - **New concept**: create with Why This Matters + Current Status sections
   - **Existing concept**: update Current Status, append to evidence. If the concept's framing has shifted, add `## Evolution` section tracking the change
   - Include rationale — WHY decisions were made, trade-offs chosen
6. **Update `wiki/index.md`** — add new pages under the correct category. Each entry: `- [[page-name]] — one-line summary`. Keep alphabetical within categories.
7. **Update `wiki/overview.md`** — revise the high-level synthesis to incorporate new source. The overview should answer: "What is this knowledge base about, and what are the key themes?" Keep under 500 words. Don't just append — rewrite to integrate.
8. **Append to `wiki/log.md`**:
   ```markdown
   ## [YYYY-MM-DD] ingest | Source Title
   - Added: sources/source-name.md
   - Updated: entities/module-x.md, concepts/openacc-porting.md
   - New pages: entities/new-entity.md
   - Tensions found: [list any contradictions discovered, or "none"]
   ```
9. **Rebuild graph** — run `/kg update` to refresh structural layer

**Batch ingest**: If many files, ask: "Process all at once or one by one?" Batch mode skips discussion, uses parallel subagents.

### Wiki Maintenance Rules

These rules govern how the wiki stays consistent as it grows.

**When to create a new page vs update existing:**
- An entity/concept mentioned 2+ times across different sources deserves its own page
- A single mention can be a `[[wikilink]]` to a not-yet-created page (Obsidian shows these as unresolved — natural TODO list)
- When creating, always add to `index.md` in the same operation

**Handling contradictions:**
- Never silently overwrite. When new source contradicts existing wiki content:
  1. Add `> [!warning] Tension` callout on the affected page with both claims and sources
  2. Log the tension in `wiki/log.md`
  3. The next `/kg-reflect` will surface this for user resolution
- The user decides which claim wins. Until then, both stay visible.

**Handling deletions:**
- If a source is removed from raw, its `wiki/sources/` page stays but gets `> [!note] Source removed from raw/` header
- Entity/concept pages that referenced only that source get flagged in next `/kg-lint`
- Never auto-delete wiki pages — always ask the user first

**Keeping overview.md current:**
- Rewrite (not append) on every ingest. It should read as a fresh synthesis, not a changelog.
- Structure: 1 paragraph on scope, 1 paragraph per major theme, 1 paragraph on open questions.
- Max 500 words. If it grows beyond this, split themes into their own concept pages and link.

**graph-report.md sync:**
- After every `/kg-update`, copy these sections from `GRAPH_REPORT.md` into `wiki/graph-report.md`: God Nodes (top 10), Communities (with labels), Surprising Connections, Hyperedges.
- Don't copy the full report — just the sections useful for wiki navigation.

### `/kg-query [question]` — Query Knowledge

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

### `/kg-lint` — Health Check

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

### `/kg-reflect` — Proactive Insight

After ingest or at session end, the LLM reviews recent activity and offers unprompted observations. Not a summary — a provocation.

**What to surface:**
- **Tensions** — "Source A claims X, but source B implies Y. Which is closer to your current understanding?"
- **Emerging patterns** — "The last 3 ingested sources all touch on [theme]. This might be becoming a central concern worth its own concept page."
- **Blind spots** — "Community C3 (KDM6 Phase 2b-4) has 15 nodes but zero inbound edges from C1 (RRTMG). Is this isolation intentional or a gap?"
- **Shifted ground** — "Your early sources assumed X. Recent sources assume not-X. The wiki still reflects the old framing in these pages: [list]."

The goal is to make the user think, not to inform. If reflect produces no genuine insight, say so — don't fabricate one.

**When to trigger:** Automatically after every 3rd ingest, or when the user explicitly asks. Log reflections in `wiki/log.md` as `## [date] reflect | [one-line thesis]`.

### `/kg-challenge [claim]` — Devil's Advocate

The user states a belief or the LLM picks one from the wiki. The LLM then argues against it using only evidence from the knowledge base.

**Flow:**
1. If no claim given, pick the highest-confidence INFERRED edge or the most central concept in the wiki
2. Find all evidence that supports the claim
3. Find all evidence that contradicts or weakens it
4. Present the counter-argument with citations
5. Ask: "Does this change anything, or does the original claim still hold?"

This is not about being right. It's about stress-testing knowledge before it calcifies.

### `/kg-connect` — Cross-Community Bridge Discovery

Graphify finds communities. This operation finds the *missing bridges* between them — connections that should exist based on semantic content but don't appear structurally.

**Steps:**
1. Load graph communities from GRAPH_REPORT.md
2. For each pair of communities with zero or few cross-edges, read representative nodes from each
3. Propose potential connections: "Node A in C0 and Node B in C4 both deal with [shared concern], but they've never been linked. Is there a real relationship here?"
4. If the user confirms, add the edge to the graph (INFERRED, with rationale)

This is where the graph and the human co-create knowledge that neither could produce alone.

### `/kg-suggest` — Next Source Recommendation

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
instance_of: Artifact | Concept | Procedure | Experience | Heuristic | Decision
page_kind: entity-page | concept-page | procedure-page | experience-page | heuristic-page | decision-page
epistemic_status: observed | inferred | hypothesis | validated | deprecated
confidence: high | medium | low
date_created: YYYY-MM-DD
date_modified: YYYY-MM-DD
provenance:
  sources: [source-file-1.pdf]
  code_refs: ["file.F:123"]
relations:
  - {predicate: implements, target: "[[concept]]", rationale: ""}
---
```

Legacy pages (without `instance_of`) continue to work via `legacy_mode` in `core.yaml`.

### Wikilinks

Always use `[[wikilinks]]` for cross-references. This powers Obsidian's graph view and backlinks. Create links to pages that don't exist yet — Obsidian shows these as unresolved links (natural TODO list).

### Page Templates

Templates live at `~/.claude/skills/kg/templates/`. Each class has a template matching `core.yaml` contract. Examples:

**Artifact** (`wiki/entities/module-mp-kdm6.md`):
```markdown
---
title: module_mp_kdm6
instance_of: Artifact
page_kind: entity-page
epistemic_status: observed
provenance:
  code_refs: ["module_mp_kdm6.F"]
relations: []
---
# module_mp_kdm6

## Role
KDM6 microphysics module. Contains the main physics hotspot `kdm62D`.

## Key Facts
- Single live caller: [[module-microphysics-driver]] at line 2538
- ~2600 lines of Fortran, R8 precision

## Connections
- Called by: [[module-microphysics-driver]]
- Implements: [[register-pressure]]
```

**Heuristic** (`wiki/heuristics/item-nogradguard.md`):
```markdown
---
title: .item() 사용 시 반드시 NoGradGuard
instance_of: Heuristic
page_kind: heuristic-page
epistemic_status: validated
confidence: high
distilled_from: []
relations:
  - {predicate: prevents, target: "[[autograd-graph-break]]"}
---
# .item() 사용 시 반드시 NoGradGuard

## Rule
PyTorch 텐서에서 .item() 호출 시 반드시 torch.no_grad() 블록 안에서 수행.

## Why
.item()은 연산그래프를 끊어 자동미분이 불가능해짐. 반복된 실수 발생.

## Applies When
PyTorch autograd 컨텍스트에서 스칼라 값을 추출할 때.

## Does Not Apply When
추론 전용 코드(이미 no_grad 블록 내부).

## Evidence
CLAUDE.md Command Memories에 3회 이상 반복 경고 기록.
```

## Skill Routing Guide

When the agent isn't sure which skill to invoke, use this map:

| 사용자 의도 | 추천 스킬 | 참고 |
|---|---|---|
| 세션 시작 | `/kg-orient` | 항상 첫 번째 |
| 질문/조회 | `/kg-query --depth` | quick/standard/deep |
| 새 소스 투입 | `/kg-ingest` | → 자동으로 elicit/postmortem 권장 |
| 암묵지/경험 기록 | `/kg-elicit` 또는 `/kg-postmortem` | elicit=일반, postmortem=최근 사건 |
| 위키 건강 점검 | `/kg-lint` | orphan, dead links, stale claims |
| 패턴/긴장 발견 | `/kg-reflect` | drift signal + novelty test |
| 다음에 뭘 읽을지 | `/kg-suggest` | knowledge gap 기반 추천 |
| 커뮤니티 간 연결 | `/kg-connect` | cross-community bridge |
| 주장 반박 테스트 | `/kg-challenge` | devil's advocate |
| 스키마 변경 | `/kg-schema` | propose → approve → migrate |
| 판단 대체 기록 | 수동 `supersedes` relation + `/kg-reflect` 후보 감지 | Decision/Heuristic 대상 |
| 웹 조사 | `/kg-autoresearch` | source queue + user approval |
| 시각화 | `/kg-canvas` | .canvas JSON export |
| 그래프 재빌드 | `/kg-update` | graphify incremental |
| wiki 초기화 | `/kg-init` | 최초 1회 또는 재부트 |

## Usage Rules

1. **Raw sources are immutable** — The LLM reads from source files but never modifies them. They are the source of truth. The wiki and graph are derived artifacts.

2. **Don't Grep-first** — When wiki exists, read `wiki/index.md` first. When only graph exists, read `GRAPH_REPORT.md` first. Grep is for precise lookups after orientation.

3. **Graph supplements, never replaces** — The graph is structural (what connects to what). The wiki is semantic (what it means, why it matters). Neither replaces raw sources.

4. **Keep the wiki growing** — Every ingested source, answered query, lint fix makes it richer. Human curates sources and asks questions. LLM does the bookkeeping.

5. **Co-evolve the schema** — CLAUDE.md documents how the wiki is structured, what conventions apply, what workflows to follow. As you learn what works for your domain, update CLAUDE.md together with the LLM. The schema is what makes the LLM a disciplined wiki maintainer rather than a generic chatbot.

## Operation Authority Matrix

Who decides: **Human** (explicit approval required) vs **LLM** (autonomous, report only).

| Operation | Authority | Rationale |
|---|---|---|
| Schema change (propose/approve) | **Human** | Ontology is the contract — no auto-mutation |
| Page reclassification/move | **Human** | Folder change = identity change |
| Page deletion | **Human** | Irreversible |
| Source approve (autoresearch) | **Human** | Provenance integrity |
| Heuristic promotion from Experience | **Human** | Generalization = judgment call |
| Research angle lock | **Human** | Scope control |
| hot.md overwrite | **LLM** (report at session end) | Bookkeeping view, not truth |
| log.md append | **LLM** | Append-only audit trail |
| _index.md sync | **LLM** | Derived from actual files |
| Query filing to wiki/queries/ | **LLM** (if 3+ pages cross-referenced OR user says "save") | Low-stakes, reversible |
| pull-global compatible changes | **LLM** (dry-run first, show diff) | Always preview before apply |

**Principle:** "Schema/research처럼 비싼 변화는 사용자 승인. hot/log/index 같은 일상 bookkeeping은 LLM 재량."

## LLM Interaction Guidelines

### hot.md Compression Priority
When updating hot.md (~500 words max), prioritize in this order:
1. **Current Focus** (1-2 sentences: what the user is actively working on)
2. **Key Tensions / Open Questions** (top 3, most recent first)
3. **Recent Activity** (last 5 operations, most recent first)

If space is tight, drop old activity entries first.

### /kg-reflect Novelty Test
Before surfacing an insight, it must pass at least one:
- **Cross-reference test**: cites 2+ wiki pages that contradict or tension each other
- **Anomaly test**: graph structure (community isolation, missing bridge) + wiki content mismatch
- **Temporal test**: early sources assumed X, recent sources assume not-X
- **Blind spot test**: a concept is referenced 3+ times but has no page

If none pass, say "no novel insights this cycle" — don't fabricate.

### /kg-ingest Elicitation — Soft Transition
When keyword sweep detects trigger words (실패/주의/반복/명심/비법), don't jump into interrogation mode. Instead:
1. "이 문서에 [keyword] 관련 경험이 보입니다. 기록해둘까요?" (propose)
2. Wait for user response
3. Only then invoke `/kg-elicit` flow

### Document Authority
- **Sub-skills are the authoritative source** for each operation's detailed flow
- **This main SKILL.md is the hub**: architecture overview, ontology spec, authority matrix, interaction guidelines
- When sub-skill text diverges from this hub, the sub-skill wins for execution details; this hub wins for ontology/authority rules

## Migration Policy

**Legacy pages (68 files, `type:` only, no `instance_of`):**
- Officially supported long-term. Validator treats them as warnings, not errors.
- Upgrade is opt-in: when a page is actively edited, add `instance_of` and `page_kind`. No batch rewrite.

**Transitional pages (18 files, `instance_of` set, body sections not restructured):**
- Body restructuring happens when the page is next meaningfully updated.
- Validator tracks body drift as stderr warnings. `/kg-reflect` surfaces these as schema drift signals.
- Target: within 3 months, most frequently-edited pages should be full v1.

**New pages (created after bootstrap):**
- Must be full v1 from creation. Validator enforces strictly. Templates ensure compliance.

## Context Compression

As the wiki grows, reading cost must stay sub-linear. The compression hierarchy:

```
hot.md (250-400 tok) → overview.md (400-600) → _index.md (150-300) → individual page
```

### Reading Priority (all skills)
0. **BM25 lookup** (0 tokens) — `build_search_index.py` generates `wiki/.search_index.json`. Query returns top-k pages ranked by relevance. Run before any page reads.
1. `hot.md` — always first. If fresh (<24h), may skip further reads for quick tasks
2. `overview.md` — stable global synthesis. Second read for cross-folder context
3. `<folder>/_index.md` — folder-level routing with cluster map and anchor pages
4. `index.md` — **last resort** canonical catalog. Not a default read past 200 pages

### BM25 Search Index
- Builder: `~/.claude/skills/kg/schema/tools/build_search_index.py wiki`
- Output: `wiki/.search_index.json` (89 docs, 8670 terms, Korean+English CJK tokenizer)
- Section-level indexing: each `## Heading` is a separate posting
- Rebuild: after ingest, after reclassify, or manually
- Token cost: **0** (local keyword lookup, no LLM call)

### Adaptive Scaling
- **<120 pages (current)**: hot + overview + _index is sufficient for most operations
- **200+ pages**: add `.meta/communities/*.md` (topic cluster digest, ~200 tok each)
- **500+ pages**: split hot into global (300 tok) + per-cluster (120 tok each); demote index.md to registry-only

### Archive Policy
Pages are never deleted. Archive = frontmatter flag, not folder move.
- Add `archived: true`, `date_archived`, `archive_reason` to frontmatter
- **Candidate criteria**: 120+ days unmodified, not in recent 20 log entries, not in active frontier, inbound non-archived links <= 1
- **Excluded from archive**: Source and Decision pages (evidence/judgment records have higher preservation value)
- Archived pages are skipped by `/kg-query` and `/kg-reflect` by default; `--include-archived` to override
- Restore = remove flag + log entry. Human authority required.

## Schema as Core Product

The schema (`core.yaml` + `relations.yaml` + `frontmatter.yaml`) is not just infrastructure — it IS the domain model. Treat it as a first-class product.

### Signal-to-Proposal Contract
When `/kg-reflect` emits a drift signal (SIG-*), it must follow this lifecycle:

```
SIG detected → surfaced in reflect report → user decides:
  → `/kg-schema propose` (formalize as proposal) → approve/reject
  → explicit reject (signal marked "rejected, rationale: ...")
  → defer (signal stays, age increments)
  → 3 cycles without action → STALE escalation
```

No signal should remain unaddressed indefinitely. Reflect tracks signal age; lint flags STALE signals.

### Proposal Minimum Fields
```yaml
proposal_id: YYYY-MM-DD-<slug>
date: YYYY-MM-DD
type: add_class | add_relation | deprecate_class | rename | add_epistemic_state
description: ""
rationale: ""
evidence: []        # wikilinks to pages that motivated this
originating_signal: SIG-NNN  # link back to reflect signal
status: pending | approved | rejected
rejection_reason: ""  # if rejected, why
```

### Receipt-Based Evidence (Deep Suite pattern)

Every schema approve collects a structured receipt before proceeding. The receipt is the gate — no approve without evidence.

**Receipt collection**: `validate.py --receipt` runs all sensors and outputs JSON:
```bash
python3 ~/.claude/skills/kg/schema/tools/validate.py \
  --receipt --schema-dir wiki/.schema \
  --wiki-root wiki/ --proposal wiki/.schema-proposals/<id>.yaml \
  wiki/**/*.md
```

**Receipt checks** (6 sensors):
| Check | Tier | Auto-fixable | What it validates |
|-------|------|:---:|---|
| `schema_diff` | Required | ❌ | target_version = current + 1 |
| `template_contract` | Required | ✅ | templates match core.yaml class definitions |
| `frontmatter_valid` | Required | ✅ | all pages pass frontmatter validation |
| `legacy_compat` | Required | ❌ | legacy/transitional pages unaffected |
| `evidence_pages` | Required | ❌ | cited evidence pages exist |
| `predicate_utilization` | Advisory | ❌ | % of predicates in active use |

**Gate rule**: All Required checks must be PASS or SKIP. Advisory is reported but doesn't block. Missing data = SKIP, not FAIL.

**Sensor loop**: auto-fixable failures (template, frontmatter) trigger fix → re-run, max 3 rounds. Non-fixable failures → human escalation.

**Receipt file**: written to `.schema-proposals/<id>-receipt.yaml` alongside the proposal.

### Schema Health Indicators (tracked in hot.md Maintenance Debt)
- `proposal_debt`: pending proposals not acted on for 2+ cycles
- `signal_staleness`: SIG-* surfaced 3+ times without propose/reject
- `predicate_utilization`: % of defined predicates used at least once in wiki
- `receipt_coverage`: % of approved proposals with receipt (target: 100%)

## Supersession (판단 대체 기록)

When a new Decision replaces an old one, use the `supersedes` predicate to preserve judgment history.

### Scope
- **Decision**: primary target. When a new design choice replaces a previous one.
- **Heuristic**: optional. When a rule is refined or overridden by a better rule.
- **Experience**: excluded. Episodes are not "replaced" — they are evidence.

### Workflow (manual + semi-auto)
1. **Author creates** new Decision with `relations: [{predicate: supersedes, target: "[[old-decision]]"}]`
2. **Old page** gets `epistemic_status: deprecated` + `> [!superseded] Replaced by [[new-decision]]` callout at top
3. **If author forgets**: `/kg-reflect` detects "same `decided_for` target, newer page exists" → emits `POSSIBLE_SUPERSESSION` signal with prefilled command
4. `/kg-lint` flags deprecated pages that lack a `superseded by` callout

### Authority
Supersession = page identity change → **Human approval required** (per Authority Matrix).

## Convergence Tracking

### Active Frontier
Not all pages need to be full v1. Convergence targets the **active frontier**: pages modified in last 30 days, pages referenced in hot.md Current Focus, pages cited in recent reflect signals.

### Metrics (computed by `validate.py --summary`)
- `convergence_ratio` = full_v1 / total_pages (target: frontier >= 0.8)
- `reflect_debt` = ingests since last reflect (warn >= 3)
- `transitional_age` = days since reclassification without body restructure

### Attractor Test (4 conditions = "converging")
1. Recent 5 maintenance cycles: reflect_debt <= 2 in 4+ cycles
2. Active frontier full_v1_ratio >= 0.8, no 2-week regression
3. Threshold drift signals closed by propose or explicit reject within 2 cycles
4. No transitional page in hot set older than 21 days

### Fixpoint (operational definition)
Last 3 `/kg-reflect` runs produce no new drift signals above threshold, pending proposals = 0, active frontier new pages = 100% template-compliant. Cold legacy excluded from this judgment.

## How the Ontology Grows (Meta-Process)

The schema is a living artifact. Growth follows a bounded loop:

1. **Observe** — `/kg-reflect` continuously watches for pattern drift.
2. **Propose** — drift becomes a `/kg-schema propose` entry, never an auto-change.
3. **Deliberate** — user reviews proposal. Rejection is valid and expected.
4. **Apply** — approved proposal bumps `schema_version`, writes a migration file.
5. **Migrate** — `/kg-schema migrate` walks affected pages, proposing fixes one-by-one.
6. **Record** — every change is logged with rationale, so the schema history itself becomes a knowledge artifact about how our understanding evolved.

**What we are not doing:**
- No formal reasoner. This is a mini-ontology — a typed vocabulary, not OWL.
- No auto-classification. Humans judge class membership.
- No schema rollback. We only move forward via `deprecate`.

**Why this shape:** fixed ontologies calcify; free-form wikis lose structure. The proposal loop is the narrow seam where structure and evolution meet without fighting.

## Codex Integration (양방향 파이프라인)

### Codex → kg: Review Result Structuring

When Codex performs code reviews (`/codex:review`, `/codex:rescue`), the findings can be filed into the wiki as structured knowledge.

**Workflow** (manual trigger, not automatic):
1. After Codex review completes, user says "kg에 기록" or LLM suggests filing
2. Parse Codex output: findings array with severity, description, location
3. Create `wiki/experiences/codex-review-<date>-<slug>.md` with Experience template:
   - Context: what was reviewed and why
   - Attempted: what the code tried to do
   - Outcome: Codex findings (severity-ordered)
   - Lesson: actionable takeaway
4. If the same pattern appears in 3+ Codex reviews → suggest Heuristic promotion via `/kg-elicit`
5. Update `wiki/log.md` and `wiki/hot.md`

**Pattern detection**: When filing a Codex review, check existing experiences for recurring themes:
- Same file/module flagged repeatedly → architectural issue
- Same error pattern across reviews → candidate Heuristic
- Contradicts an existing Heuristic → tension, surface in next reflect

### kg → Codex: Domain Context Injection

When invoking Codex for reviews or tasks, the LLM can enrich the prompt with kg context.

**`<domain_context>` block** (added to Codex prompts when relevant):
```xml
<domain_context>
Project heuristics (from wiki/heuristics/):
{relevant_heuristics — max 5, selected by topic match}

Active decisions (from wiki/decisions/):
{relevant_decisions — max 3, most recent first}

Known tensions (from wiki/hot.md):
{current_tensions — max 3}
</domain_context>
```

**Selection logic**:
1. Read `wiki/hot.md` for current focus
2. Match Codex task topic against heuristic `applies_when` fields
3. Match against decision `decided_for` targets
4. Include only items with `confidence: high` or `epistemic_status: validated`
5. Cap at ~500 tokens to keep Codex prompt lean

**When to inject**: automatically when `/codex:rescue` or `/codex:review` is invoked and `wiki/heuristics/` has content. Skip if `--no-kg-context` flag is set.

## Technical Notes

- **graph.json format**: Saved as NetworkX `node_link_data` — top-level keys are `nodes`, `links` (not `edges`). Load with `json_graph.node_link_graph(data, edges='links')`. For extraction format (with `edges` key), use `build_from_json()`.
- **Manifest location**: `graphify-out/manifest.json` (no `.graphify_` prefix). Used by `detect_incremental()` to identify changed files.
- **Graphify Python**: Interpreter path at `graphify-out/.graphify_python`. If missing, re-resolve via `which graphify`.
- **No git required** for Graphify (SHA256 cache). Wiki benefits from git for version history.
- **Cost**: Graph build ~ 1 API call per doc file. Wiki pages are part of the conversation (no extra cost). Incremental updates only process changed files.
