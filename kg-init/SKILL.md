---
name: kg-init
description: "This skill should be used when the user asks to initialize, bootstrap, reset, or prepare a kg-skill wiki, says 'kg-skill 처음 설정', 'wiki 초기화', '스키마 pin 만들기', or invokes /kg-init. Creates wiki/, copies schema, seeds index/log/hot, validates setup. Idempotent — never overwrites existing wiki content."
trigger: /kg-init
---

# /kg-init — Bootstrap a Wiki for the Evolving Mini-Ontology

This is the single source of "wiki is ready to use v1". Every other kg skill that writes to the wiki assumes this has run.

## Activate When

- User invokes `/kg-init` (with or without project path)
- User asks "kg-skill 처음 설정", "wiki 초기화", "스키마 pin 만들기"
- A new project needs the kg wiki layer
- Pin file is missing or schema upgrade requested

## Do Not Activate When

- Wiki already exists and contains content → use `/kg-orient` for status, `/kg-schema pull-global` for schema upgrade
- User wants to ingest content → `/kg-ingest`
- User wants to query → `/kg-query`

## Preconditions
- Global schema exists at `~/.claude/skills/kg/schema/`
- Templates exist at `~/.claude/skills/kg/templates/`
- A project directory where the wiki should live

## Flow

1. **Resolve project root**
   - If path argument given, use it. Otherwise cwd.
   - Wiki root := `<project>/wiki/` (create if missing)

2. **Create folder structure** (idempotent — `mkdir -p` semantics)
   ```
   <project>/wiki/
   ├── .schema/
   │   └── migrations/
   ├── .schema-proposals/
   ├── entities/
   ├── concepts/
   ├── procedures/
   ├── experiences/
   ├── heuristics/
   ├── decisions/
   ├── sources/
   └── queries/
   ```

3. **Copy global schema to per-wiki pin** (only if pin doesn't already exist)
   ```bash
   cp ~/.claude/skills/kg/schema/core.yaml         wiki/.schema/
   cp ~/.claude/skills/kg/schema/relations.yaml    wiki/.schema/
   cp ~/.claude/skills/kg/schema/frontmatter.yaml  wiki/.schema/
   cp ~/.claude/skills/kg/schema/migrations/*.yaml  wiki/.schema/migrations/
   ```

3b. **Copy research policy** (only if absent):
   ```bash
   cp ~/.claude/skills/kg/schema/research-policy.yaml wiki/.schema/research-policy.yaml
   ```
   Create the research queue staging folder:
   ```bash
   mkdir -p wiki/.research-queue/{approved,rejected}
   ```

4. **Write `wiki/.schema/pin.yaml`** (only if absent)
   ```yaml
   pinned_version: 1
   pinned_at: YYYY-MM-DD
   source: global
   source_version: 1
   notes: Initial bootstrap. Run /kg-schema pull-global to upgrade.
   ```

5. **Seed `wiki/index.md`, `wiki/log.md`, and `wiki/hot.md`** (only if absent)
   - `index.md`: empty category stubs for all 10 folders
   - `log.md`: first entry `[YYYY-MM-DD] init | bootstrapped to v1`
   - `hot.md`:
     ```markdown
     ---
     title: Hot Cache
     type: meta
     date_modified: YYYY-MM-DD
     ---
     # Hot Cache

     ## Current Focus
     (initialized — no operations yet)

     ## Recent Activity
     - [YYYY-MM-DD] wiki bootstrapped to schema v1

     ## Key Tensions / Open Questions
     (none yet)
     ```

5b. **Seed folder-level `_index.md` stubs** for each content folder
   Each folder gets a lightweight `_index.md`:
   ```markdown
   ---
   title: <Folder> Index
   type: folder-index
   date_modified: YYYY-MM-DD
   ---
   # <Folder>

   (empty — pages will be listed here as they are created)
   ```
   Main `index.md` links to these: `- [[<folder>/_index|<Folder>]] — N pages`.

6. **Run validator against the per-wiki pin**
   ```bash
   python3 ~/.claude/skills/kg/schema/tools/validate.py --schema-dir wiki/.schema
   ```
   Expected: exit 0 (contract check runs against templates, no page errors).

7. **Optional: install `/graphify` companion skill** (only on first-time setup, ask before running)
   ```bash
   graphify install --platform claude
   ```
   This adds `~/.claude/skills/graphify/SKILL.md` so `/kg-update` and other skills can soft-depend on graphify v0.5.0+ tools.

## Idempotency contract
- Running `/kg-init` twice MUST NOT:
  - Overwrite an existing `pin.yaml`
  - Clobber `index.md`, `log.md`, `hot.md`, or any content page
  - Change migration files
- Running on a wiki whose pin is older than global prints a notice suggesting `/kg-schema pull-global` but does NOT pull automatically.

## Output Contract

```text
Init result: PASS | PARTIAL | FAIL
Wiki root: <path>
Pin: v<N> (created | existing | missing-global)
Folders created: <N>
Folders verified existing: <N>
Schema files copied: <list | skipped (existing)>
Research policy: copied | skipped | missing-global
Seed files: index.md=<created|kept>, log.md=<created|kept>, hot.md=<created|kept>
Folder _index.md stubs: <N created, M kept>
Validator: PASS | FAIL (<details if fail>)
graphify companion: installed | skipped | not-asked

Caveats:
- <existing wiki preserved | global schema missing | none>

Next command:
- /kg-orient | /kg-ingest <file> | /kg-schema list
```

## Exceptions and Escalation

- **Global schema directory missing** (`~/.claude/skills/kg/schema/` absent) → stop and report exact missing path. Do not proceed.
- **`wiki/.schema/pin.yaml` already exists** → skip write (do not overwrite). Note in output as "Pin: existing".
- **`wiki/index.md`, `wiki/log.md`, or `wiki/hot.md` exists** → preserve. Note in output as "kept".
- **Validator fails** → report exact failing file path. Do not suggest `/kg-ingest` until fixed.
- **Migration files exist** → never modify. They are append-only history.

## Quality Gates

Before final answer:
- [ ] No existing wiki content was overwritten (idempotency)
- [ ] Pin records source version
- [ ] All 10 folders exist (create or verify)
- [ ] Validator passed against per-wiki pin
- [ ] log.md contains init entry with date
