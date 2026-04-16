---
name: kg-init
description: Bootstrap or upgrade a wiki directory to the evolving mini-ontology. Copies the global schema into <project>/wiki/.schema/, creates per-wiki pin.yaml, and ensures all folders required by v1 classes exist. Idempotent — safe to re-run. Invoke as /kg init [project-path] or let /kg init auto-detect cwd.
trigger: /kg-init
---

# /kg-init — Bootstrap a Wiki for the Evolving Mini-Ontology

This is the single source of "wiki is ready to use v1". Every other kg skill that writes to the wiki assumes this has run.

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

7. **Report**
   ```
   Initialized wiki at <path>
   Pin: v1 (copied from global)
   Folders: 10 created/verified
   Validator: OK
   Ready for /kg-ingest, /kg-elicit, /kg-postmortem, /kg-schema.
   ```

## Idempotency contract
- Running `/kg init` twice MUST NOT:
  - Overwrite an existing `pin.yaml`
  - Clobber `index.md`, `log.md`, `hot.md`, or any content page
  - Change migration files
- Running on a wiki whose pin is older than global prints a notice suggesting `/kg-schema pull-global` but does NOT pull automatically.
