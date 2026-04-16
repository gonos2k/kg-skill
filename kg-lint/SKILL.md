---
name: kg-lint
description: Health check — verify graph integrity, manifest, freshness. If wiki exists, also check orphan pages, missing links, stale claims. Use to audit knowledge base quality.
trigger: /kg-lint
---

# /kg-lint — Health Check

## Standard mode (default)

**Graph-only checks** (always):
- `graph.json` exists and parseable
- `GRAPH_REPORT.md` exists
- `manifest.json` exists (for incremental updates)
- `.graphify_python` points to valid interpreter
- Freshness: source files newer than `graph.json`

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

When checking schema proposals, verify each `approved` proposal has a matching `<id>-receipt.yaml` in `wiki/.schema-proposals/`. Missing receipt = violation of Deep Suite evidence contract (see SKILL.md § Receipt-Based Evidence). Report as Required-tier finding; do not auto-fix (requires re-running `/kg-schema approve`).

**Legacy carve-out**: proposals approved before the receipt contract was introduced (no `<id>-receipt.yaml` ever existed) are reported as **advisory** debt, not Required-tier failure. The retroactive-receipt policy is deferred until cycle persistence design lands (see `kg/docs/plans/2026-04-15-stale-sensor-requeue.md`).

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-lint`.
