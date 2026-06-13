---
name: kg
description: "Router for the Knowledge Graph + LLM Wiki system. Use when the user invokes /kg explicitly or asks 'which kg command should I use?'. Sub-commands — /kg-orient, /kg-update, /kg-query, /kg-lint, /kg-ingest (data ops) and /kg-reflect, /kg-challenge, /kg-connect, /kg-suggest (dialogue ops). Project-state auto-trigger (wiki/ or graphify-out/ presence) belongs to /kg-orient, not this router."
trigger: /kg
---

# kg — Knowledge Graph + LLM Wiki Router

A persistent, compounding knowledge base combining two layers:

- **Graphify** extracts structural relationships (god nodes, communities, surprising connections) from any corpus.
- **LLM Wiki** (Karpathy pattern) maintains a living Obsidian vault of entity pages, concept summaries, and cross-references.

The graph tells you what's connected. The wiki tells you what it means. Either layer works standalone — both together compound across sessions.

## Activate When

- User invokes `/kg`
- User asks "어떤 kg 명령을 써야 해?" or how the Knowledge Graph + LLM Wiki system works
- User asks about the overall KG/Wiki architecture, ontology, or authority rules

Project-state auto-trigger (`wiki/` or `graphify-out/` presence at session start) routes to `/kg-orient`, **not** this router. See `kg-orient/SKILL.md`.

## Do Not Activate When

This skill is a **router**, not an executor. Do not run an operation here — route to the corresponding sub-skill:

| User intent | Route to |
|---|---|
| 세션 시작 / 현재 상태 | `/kg-orient` |
| 지식 질의 | `/kg-query` |
| 새 문서 투입 | `/kg-ingest` |
| 그래프 갱신 | `/kg-update` |
| 위키 건강 점검 | `/kg-lint` |
| 패턴/긴장 발견 | `/kg-reflect` |
| 주장 반박 | `/kg-challenge` |
| 다음 자료 추천 | `/kg-suggest` |
| 암묵지 기록 | `/kg-elicit` |
| 시행착오 기록 | `/kg-postmortem` |
| 스키마 변경 | `/kg-schema` |
| 웹 조사 | `/kg-autoresearch` |
| Obsidian Canvas export | `/kg-canvas` |
| wiki 초기화 | `/kg-init` |
| 여러 프로젝트 통합 그래프 | `/kg-merge` |
| graphify MCP server 등록 | `/kg-mcp` |

## Naming Convention

- **`/kg-<verb>`** (hyphen) — canonical user-facing slash command. Always use this form.
- **`/kg <verb>`** (space) — never used. The hyphenated form is ground truth in every sub-skill's `trigger:` field.

## Common Rules (5)

1. **Raw sources are immutable.** The LLM reads but never modifies them. They are the source of truth.
2. **Wiki and graph are derived artifacts.** Both are regenerable views, never primary evidence.
3. **Verification chain: Graph → Wiki → Raw Source.** Never cite graph/wiki as primary evidence for a decision.
4. **Human approval is required** for: schema change, page reclassification, page deletion, source approval (autoresearch), heuristic promotion from Experience.
5. **Use hyphenated commands**: `/kg-query`, not `/kg query`.

## References

For deeper detail, read the relevant reference file:

| Topic | File |
|---|---|
| System layout, source detection, page templates, technical notes, graphify v0.8.x CLI/MCP surface, freshness gate | `references/architecture.md` |
| Fortran corpora (scientific/HPC code — libraries, solvers, legacy, earth-system incl. WRF) — `.F`/`.f90` extraction, cpp step, node/edge model, USE/CALL graph workflow | `references/fortran.md` |
| 7 classes, page_kind, instance_of, schema-as-product, proposal/receipt | `references/ontology.md` |
| Human vs LLM authority, hot.md priority, novelty test, usage rules | `references/authority-matrix.md` |
| BM25 search, hot/overview/_index hierarchy, archive policy | `references/context-compression.md` |
| Migration policy, supersession, convergence tracking, attractor test | `references/schema-evolution.md` |
| Codex ↔ kg bidirectional pipeline (review filing, domain context injection) | `references/codex-integration.md` |
| Output Contract standard fields (`Next command:`, `Confidence:`, `Caveats:`, etc.) | `references/output-contract-standard.md` |

Reference files are loaded only when needed (progressive disclosure). Sub-skills are self-contained and do not depend on this router for execution details.

## Document Authority

- **Sub-skills are the authoritative source** for each operation's detailed flow.
- **This router (`kg/SKILL.md`)** owns: routing table, common rules, references list.
- **Reference files** own: ontology, authority rules, compression hierarchy, schema evolution, integration patterns.
- When sub-skill text diverges from a reference, the sub-skill wins for execution details; the reference wins for ontology/authority rules.
