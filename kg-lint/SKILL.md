---
name: kg-lint
description: "This skill should be used when the user asks to audit, validate, health-check, repair, or lint the kg wiki/graph, says '위키 건강 점검', '깨진 링크 찾아줘', 'orphan page 확인', or invokes /kg-lint. Reports graph integrity, freshness, missing links, stale claims, schema proposal debt. With --fix applies only safe bookkeeping changes."
trigger: /kg-lint
---

# /kg-lint — Health Check

## Activate When

- User invokes `/kg-lint` or `/kg-lint --fix`
- User asks "위키 건강 점검", "깨진 링크 찾아줘", "orphan page 확인", "schema proposal receipt 확인"
- After major ingest spree (5+ files in one session)
- Periodic health check (weekly+)
- Before committing wiki changes to git

## Do Not Activate When

- User wants to add content → `/kg-ingest`
- User wants to refactor schema → `/kg-schema`
- User wants pattern/tension surfacing → `/kg-reflect` (lint is structural, reflect is semantic)

## Standard mode (default)

**Graph-only checks** (always):
- `graph.json` exists and parseable
- `GRAPH_REPORT.md` exists
- `manifest.json` exists (for incremental updates)
- Freshness: source files newer than `graph.json` (use 7-day threshold per `~/.claude/skills/kg/references/architecture.md`)

**Wiki checks** (when `wiki/` exists):
- Orphan pages — no inbound `[[wikilinks]]`
- Missing pages — referenced but don't exist
- Missing cross-references
- Graph drift — `graph-report.md` older than newest wiki page
- Stale claims — superseded by recent ingests
- Deprecated without callout — `epistemic_status: deprecated` pages missing `> [!superseded]` callout
- Supersession orphans — pages with `supersedes` relation pointing to non-deprecated target
- Stale signals — SIG-* surfaced 3+ cycles without propose/reject
- Proposal debt — pending proposals not acted on for 2+ cycles
- Receipt coverage — see § Receipt-aware lint below

**Deterministic sensor** (offload from LLM judgment):
```bash
python3 ~/.claude/skills/kg/schema/tools/kg_lint.py wiki/ [--json]
```
Returns orphans + missing wikilinks + deprecated-without-callout + supersession-orphans. Exit code 0=PASS, 1=WARN. Use this **before** LLM-side reasoning so the sensor catches structural issues deterministically; LLM only judges content questions (stale claim relevance, signal age).

Report findings, offer to fix. Log in `wiki/log.md` if wiki exists.

## Fix mode (`/kg-lint --fix`)

Sensor loop: automatically fix what can be fixed, report the rest.

**Auto-fixable** (applied without asking — bookkeeping only, no judgment changes):
| Issue | Fix |
|-------|-----|
| Deprecated page missing `> [!superseded]` callout | Add callout at top |
| Missing `date_modified` in frontmatter | Set to file mtime |

**Human escalation required** (reported, not auto-fixed — per Authority Matrix):
| Issue | Why human decides |
|-------|---|
| Supersession orphan (target not deprecated) | Status change = judgment call |
| Template missing required section | May require global template modification |

**Fix loop protocol**:
1. Run all sensors → collect findings
2. Apply auto-fixes for fixable items
3. Re-run sensors (max 3 rounds)
4. Report remaining non-fixable issues → user decides
5. Log all fixes in `wiki/log.md`

**Non-fixable** (reported for human decision):
- Orphan pages, missing pages, stale claims
- Signal staleness, proposal debt
- Content contradictions, class confusion

## Receipt-aware lint

When checking schema proposals, verify each `approved` proposal has a matching `<id>-receipt.yaml` in `wiki/.schema-proposals/`. Missing receipt = violation of Deep Suite evidence contract (see `~/.claude/skills/kg/references/ontology.md` § Receipt-Based Evidence). Report as Required-tier finding; do not auto-fix (requires re-running `/kg-schema approve`).

**Legacy carve-out**: proposals approved before the receipt contract was introduced (no `<id>-receipt.yaml` ever existed) are reported as **advisory** debt, not Required-tier failure. The retroactive-receipt policy is deferred until cycle persistence design lands (see `kg/docs/plans/2026-04-15-stale-sensor-requeue.md`).

## graphify integration (when available)

If `graphify-out/graph.json` exists AND `mtime < 7 days`:
- Call `graph_stats` MCP tool (or read GRAPH_REPORT.md) to validate node/edge counts match expected
- Call `get_neighbors` for each wiki page mentioned in dead-link findings to cross-validate (page may be missing from wiki but exist as graph node — different problem class)
- Note in Caveats if graph stale (≥7d) — fall back to wiki-only checks

## Output Contract

```text
Lint result: PASS | WARN | FAIL

Graph checks:
- graph.json: PASS | FAIL (<reason>)
- GRAPH_REPORT.md: PASS | FAIL
- manifest.json: PASS | FAIL
- Freshness: FRESH | STALE (<N days since rebuild>)

Wiki checks (if wiki/):
- Orphan pages: <N> ([[<sample>]], ...)
- Missing pages (referenced but absent): <N>
- Stale claims: <N>
- Deprecated without callout: <N>
- Supersession orphans: <N>
- Proposal debt: <N> proposals pending 2+ cycles
- Receipt coverage: <N>% (target 100%)

Auto-fixes applied (--fix mode only):
- <none | list with file paths>

Human decisions required:
- <none | list with one-line description per item>

Confidence: high | medium | low

Caveats:
- <graph stale | wiki absent | sensor X failed | none>

Next command:
- /kg-lint --fix | /kg-schema approve <id> | /kg-reflect | none
```

## Exceptions and Escalation

- **Never auto-delete pages** — even orphans. User decides.
- **Never auto-change `epistemic_status`** — that's judgment.
- **Never auto-resolve contradictions** — flag and escalate.
- **Never auto-approve schema proposals** — requires `/kg-schema approve` with receipt.
- **`--fix` may only update bookkeeping fields**: missing `date_modified`, generated `_index.md`, missing superseded callout placeholders.
- **If `wiki/` absent** → run graph-only checks; don't fail.
- **If `graphify-out/` absent** → run wiki-only checks; don't fail.
- **If both absent** → suggest `/kg-init` and stop.

## Quality Gates

Before final answer:
- [ ] Every finding cites a specific page or file
- [ ] Auto-fix list (if --fix) is bounded to bookkeeping items
- [ ] Receipt coverage reported as percentage
- [ ] log.md updated with lint entry (date + summary)
