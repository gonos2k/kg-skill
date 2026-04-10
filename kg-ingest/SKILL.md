---
name: kg-ingest
description: Ingest source files into the wiki — read, discuss key takeaways, write source/entity/concept pages with wikilinks. Requires wiki/ to be initialized (run /kg init first).
trigger: /kg-ingest
---

# /kg-ingest — Ingest Sources into Wiki

Requires `wiki/` to exist. If not, tell user to run `/kg init` first.

**Per source file:**
1. Read source completely
2. Discuss 3-5 key takeaways with user
3. Write `wiki/sources/<name>.md` (frontmatter + summary + `[[wikilinks]]`)
4. Update `wiki/entities/<entity>.md` (create or append)
5. Update `wiki/concepts/<concept>.md` (include rationale)
6. Update `wiki/overview.md`, `wiki/index.md`
7. Append to `wiki/log.md`
8. Run `/kg-update` to refresh graph

**Batch mode:** If many files, ask "all at once or one by one?" Batch skips discussion, uses parallel subagents.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg ingest`.
