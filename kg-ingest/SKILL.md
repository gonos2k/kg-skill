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

9. **Elicitation sweep** — scan the source text and recent conversation for trigger keywords: `실패`, `주의`, `반복`, `명심`, `비법`, `failed`, `gotcha`, `pitfall`, `lesson learned`.
   - If found: invoke `/kg-elicit` with the keyword context as the topic.
   - If not found but the source is a postmortem-style doc (headings like "What went wrong", "Root cause", "Lessons"): suggest `/kg-postmortem`.
   - **Codex review output** — if source is a Codex review with structured findings: file to `wiki/experiences/codex-review-<date>-<slug>.md` (Experience template). Recurring patterns (3+ reviews) → suggest Heuristic promotion via `/kg-elicit`. See SKILL.md § Codex Integration.
   - This step is skippable by the user; don't block the ingest on it.

10. **Update `wiki/hot.md`** — add the ingested source to Recent Activity. Increment reflect_debt in Maintenance Debt.
11. **Reflect reminder** — if this is the 3rd+ ingest since last `/kg-reflect`, append to output:
    "Reflect 권장 — 이번 세션에서 `/kg-reflect`를 실행하면 schema drift와 emerging pattern을 확인할 수 있습니다."
    This is a suggestion, not a gate. The user can ignore it.

**Batch mode:** If many files, ask "all at once or one by one?" Batch skips discussion and elicitation, uses parallel subagents.

For full reference, read `~/.claude/skills/kg/SKILL.md` section `/kg-ingest`.
