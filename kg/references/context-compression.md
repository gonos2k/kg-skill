# kg Context Compression

As the wiki grows, reading cost must stay sub-linear. The compression hierarchy keeps token usage bounded regardless of wiki size.

## Compression Hierarchy

```
hot.md (250-400 tok) → overview.md (400-600) → _index.md (150-300) → individual page
```

## Reading Priority (all skills)

0. **BM25 lookup** (0 tokens) — `build_search_index.py` generates `wiki/.search_index.json`. Query returns top-k pages ranked by relevance. Run before any page reads.
1. `hot.md` — always first. If fresh (<24h), may skip further reads for quick tasks.
2. `overview.md` — stable global synthesis. Second read for cross-folder context.
3. `<folder>/_index.md` — folder-level routing with cluster map and anchor pages.
4. `index.md` — **last resort** canonical catalog. Not a default read past 200 pages.

## BM25 Search Index

- Builder: `~/.claude/skills/kg/schema/tools/build_search_index.py wiki`
- Output: `wiki/.search_index.json` (89 docs, 8670 terms, Korean+English CJK tokenizer)
- Section-level indexing: each `## Heading` is a separate posting
- Rebuild: after ingest, after reclassify, or manually
- Token cost: **0** (local keyword lookup, no LLM call)

## Adaptive Scaling

- **<120 pages (current)**: hot + overview + _index is sufficient for most operations
- **200+ pages**: add `.meta/communities/*.md` (topic cluster digest, ~200 tok each)
- **500+ pages**: split hot into global (300 tok) + per-cluster (120 tok each); demote index.md to registry-only

## Archive Policy

Pages are never deleted. Archive = frontmatter flag, not folder move.

- Add `archived: true`, `date_archived`, `archive_reason` to frontmatter
- **Candidate criteria**: 120+ days unmodified, not in recent 20 log entries, not in active frontier, inbound non-archived links <= 1
- **Excluded from archive**: Source and Decision pages (evidence/judgment records have higher preservation value)
- Archived pages are skipped by `/kg-query` and `/kg-reflect` by default; `--include-archived` to override
- Restore = remove flag + log entry. Human authority required.
