# kg Authority Matrix

Who decides what — Human (explicit approval required) vs LLM (autonomous, report only).

## Operation Authority Matrix

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
- **The kg/SKILL.md router** is the hub: routing table, common rules, references list
- When sub-skill text diverges from a reference, the sub-skill wins for execution details; the reference wins for ontology/authority rules

## Usage Rules (5)

1. **Raw sources are immutable** — The LLM reads from source files but never modifies them. They are the source of truth. The wiki and graph are derived artifacts.

2. **Don't Grep-first** — When wiki exists, read `wiki/index.md` first. When only graph exists, read `GRAPH_REPORT.md` first. Grep is for precise lookups after orientation.

3. **Graph supplements, never replaces** — The graph is structural (what connects to what). The wiki is semantic (what it means, why it matters). Neither replaces raw sources.

4. **Keep the wiki growing** — Every ingested source, answered query, lint fix makes it richer. Human curates sources and asks questions. LLM does the bookkeeping.

5. **Co-evolve the schema** — CLAUDE.md documents how the wiki is structured, what conventions apply, what workflows to follow. As you learn what works for your domain, update CLAUDE.md together with the LLM. The schema is what makes the LLM a disciplined wiki maintainer rather than a generic chatbot.
