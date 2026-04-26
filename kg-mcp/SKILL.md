---
name: kg-mcp
description: "This skill should be used when the user asks to expose the project graph as MCP tools, register graphify --mcp in Claude config, says 'graphify mcp 서버', 'MCP로 그래프 쿼리', or invokes /kg-mcp [register|status|unregister]. Configures Claude's .mcp.json so subsequent /kg-query and /kg-orient can call graphify MCP tools (query_graph, get_node, get_neighbors, get_community, god_nodes, graph_stats, shortest_path) instead of loading graph.json directly. Edits user config — requires explicit approval."
trigger: /kg-mcp
---

# /kg-mcp — Register graphify MCP Server in Claude Config

Expose the project's graph as 7 MCP tools so other kg skills can query the graph without loading `graph.json` into the LLM context. Hard-depends on graphify v0.5.0+ slash-command orchestrator (`/graphify <path> --mcp` launches the stdio MCP server). Note: the bare CLI `graphify --mcp` returns `error: unknown command '--mcp'` — `--mcp` is a slash-command-only flag, not a raw CLI flag.

## Activate When

- User asks "graphify mcp 서버", "MCP로 그래프 쿼리", "register graphify mcp"
- User invokes `/kg-mcp [register|status|unregister]`
- Before running many `/kg-query` operations on a large graph (MCP avoids reloading graph.json every time)
- After `/kg-update` produces a fresh graph and user wants subsequent queries to use it via MCP

## Do Not Activate When

- One-off graph query → `/kg-query` (loads graph.json directly, no MCP setup needed)
- graph.json doesn't exist → `/kg-update` first
- User wants Obsidian Canvas visualization → `/kg-canvas` (separate output, not MCP)
- User wants to merge multiple graphs → `/kg-merge`

## Preconditions

- `graphify` CLI v0.5.0+ installed (`which graphify`)
- Target project has `graphify-out/graph.json` (verify mtime per `~/.claude/skills/kg/references/architecture.md` freshness gate)
- `~/.claude.json` or project-local `.mcp.json` exists and is writable

## MCP tools exposed (by `/graphify <path> --mcp`)

Per graphify v0.5.0 `serve.py`. The MCP server is launched by the **graphify slash-command orchestrator**, which spawns a stdio process exposing the tools below. The launch command in `.mcp.json` (set up by `register --apply`) invokes graphify in MCP-server mode via the orchestrator's known entrypoint, not the bare CLI flag.

| Tool | Purpose |
|---|---|
| `query_graph` | BFS/DFS search with token budget (replaces in-context graph.json loading) |
| `get_node` | Full details for a node by label/ID |
| `get_neighbors` | Direct neighbors with edge details |
| `get_community` | All nodes in a community by ID |
| `god_nodes` | Most connected nodes (anchor concepts) |
| `graph_stats` | Summary stats (nodes/edges/communities/confidence breakdown) |
| `shortest_path` | Shortest path between two concepts (used by `/kg-ingest` Confirmation gate, `/kg-connect`, `/kg-postmortem` pattern detection) |

## Subcommands

### `/kg-mcp` (no subcommand) — defaults to `status`

Bare invocation `/kg-mcp` (without `register|status|unregister`) is treated as `/kg-mcp status` (read-only inspection). Rationale: status is the only read-only subcommand; defaulting to it lets users inspect current registration with minimal typing. Mutations are always blocked from bare invocation by the existing `--scope` + `--apply` Authority gate.

When defaulting to status, prepend this note to the output:
> Note: `/kg-mcp` (no subcommand) maps to `status` (read-only). Mutations require explicit `register --scope <user|project> --apply` or `unregister --scope <user|project> --apply`.

### `/kg-mcp register --scope <user|project> [--apply]`
1. Detect target `graph.json` (cwd or arg).
2. Print the proposed MCP server entry to add to `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "graphify-<project-slug>": {
         "command": "<absolute-path-to-python3.10-or-newer>",
         "args": ["-m", "graphify.serve", "<absolute-path-to-graph.json>"]
       }
     }
   }
   ```
   **NOTE (graphify v0.5.0)**: launch entry is the Python module `graphify.serve`, not the bare CLI. The form `graphify <path> --mcp` returns `error: unknown command '--mcp'` — `--mcp` exists only as a slash-command flag in the graphify orchestrator SKILL, NOT in the bare CLI binary. Always use `<python> -m graphify.serve <graph.json>`. The `mcp` Python package is required (`pip install 'mcp[cli]'`); verify with `<python> -c "import graphify.serve"` before writing config.
3. **Without `--apply`**: print the proposal and STOP. Do **not** edit any file. Do **not** interpret a follow-up user "yes"/"go" as approval. The user must **re-issue the command with `--apply` explicitly added** to the same scope. This prevents an LLM-mediated escape hatch around the Authority gate.
4. **With `--apply`**: edit `.mcp.json` (user scope = `~/.claude.json`, project scope = `<cwd>/.mcp.json`).
5. **`--scope` is required, no default.** If the user omits `--scope`, stop and ask which scope; do not assume `project` or `user`. User-scope edits affect every Claude session, so silently defaulting either way is wrong.
6. Report which MCP tools are now available; instruct user to restart Claude Code session for MCP server to load.

### `/kg-mcp status`
1. Inspect both `~/.claude.json` and `<cwd>/.mcp.json` for `graphify-*` MCP server entries
2. Report:
   - Whether `graphify-*` MCP servers are registered
   - For each, the graph.json path they point to
   - Freshness of each pointed-to graph.json (mtime)
3. **Outdated-registration sensor (v0.5.5)** — scan project for graphs newer than the registered one:
   - Scan scope: cwd recursively, EXCLUDE these dirs: `node_modules/`, `.git/`, `__pycache__/`, `*.egg-info/`, `build/`, `dist/`, `vendor/`, `vendored/`, `tmp/`, `.tmp/`, `_archive/`, `_examples/`, `_fixtures/`
   - Priority order when multiple graphs exist:
     1. **`graphify-out/merged-graph.json`** at project root (cross-corpus union — most generally useful)
     2. Any `*/graphify-out/graph.json` (per-corpus graphs)
   - If a candidate graph has mtime newer than the currently-registered one by ≥ 5 minutes, emit warning:
     ```
     ⚠ Outdated registration:
       Registered: <path> (mtime: <ts>)
       Newer available: <newer-path> (mtime: <ts>) — type: merged | per-corpus
       Suggested: /kg-mcp register --scope <X> --apply (with new path)
     ```
   - 5-minute grace prevents false positives from filesystem time skew or routine re-runs.
4. Read-only — never edits.

### `/kg-mcp unregister [--scope user|project] [--apply]`
1. Show which `graphify-*` entries exist in target `.mcp.json`
2. **Without `--apply`**: stop and confirm.
3. **With `--apply`**: remove the entry, preserve other MCP servers.

## Output Contract

```text
MCP register result: PASS | REFUSED | FAIL  | (status: see status block)
Mode: register | status | unregister

Target config: ~/.claude.json | <cwd>/.mcp.json
Target graph: <absolute path to graph.json>
Graph freshness: FRESH | STALE (<N days>)

Proposed/current MCP servers entry:
```json
{ "graphify-<slug>": { "command": "graphify", "args": [...] } }
```

Tools that will be / are exposed:
- query_graph, get_node, get_neighbors, get_community, god_nodes, graph_stats, shortest_path

Action taken:
- Without --apply: nothing written; awaiting approval
- With --apply: <added | removed | already-present | not-present>

Restart required: yes | no
Approval needed: yes (without --apply) | no (status mode)

Confidence: high | medium | low

Caveats:
- <stale graph | other MCP servers in same config | none>

Next command:
- /kg-mcp register --apply (after reviewing proposal)
- /kg-query "<question>"  (after restart, will auto-use MCP if available)
```

## Exceptions and Escalation

- **graphify CLI not found** → stop, suggest `pip install graphifyy`.
- **Target `graph.json` missing** → suggest `/kg-update` first; do not register a non-existent path.
- **Target `graph.json` is stale (≥7d)** → warn and ask user; do not block, but Caveats must mention.
- **`.mcp.json` is malformed JSON** → stop, do not attempt repair. Report exact parse error and require user fix.
- **Without `--apply` flag** → never edit config; only print the proposal. A subsequent user "yes"/"approve"/"go" message is **not** a substitute for `--apply`. The user must re-issue the same `/kg-mcp` command with `--apply` explicitly present.
- **`--scope` omission** → stop and ask. There is no default scope; user-scope and project-scope have very different blast radii.
- **Editing user-scope `~/.claude.json`** affects all sessions → require both `--scope user` AND `--apply` explicit per Authority Matrix: user config edits = Human approval.
- **Never delete other MCP servers** when unregistering — only remove `graphify-*` entries.

## Authority

Per `~/.claude/skills/kg/references/authority-matrix.md`:
- `.mcp.json` edits = **Human** authority (explicit `--apply` flag required)
- `status` mode = **LLM** (read-only)
- This skill never edits `wiki/` or `graphify-out/`

## Quality Gates

Before final answer:
- [ ] graphify CLI verified installed
- [ ] Target graph.json verified to exist (register/unregister modes)
- [ ] Without --apply, no file modified
- [ ] With --apply, only `graphify-*` entries touched (other MCP servers preserved)
- [ ] Restart-required note when config changed
- [ ] Stale graph noted in Caveats
