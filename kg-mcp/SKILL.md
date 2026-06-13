---
name: kg-mcp
description: "This skill should be used when the user asks to expose the project graph as MCP tools, register the graphify MCP server (python -m graphify.serve) in Claude config, says 'graphify mcp 서버', 'MCP로 그래프 쿼리', or invokes /kg-mcp [register|status|unregister]. Configures Claude's .mcp.json so subsequent /kg-query and /kg-orient can call graphify MCP tools instead of loading graph.json directly. Edits user config — requires explicit approval."
trigger: /kg-mcp
---

# /kg-mcp — Register graphify MCP Server in Claude Config

Expose the project's graph as MCP tools so other kg skills can query the graph without loading `graph.json` into the LLM context. The server is the Python module `python -m graphify.serve <graph.json>` (or the `graphify-mcp` console script in graphify v0.8.36+) — **not** a bare CLI flag; `--mcp` is not a graphify CLI verb. Target `graphifyy>=0.8.24` (recommended `0.8.39`); the `mcp` Python package is required — install the dedicated extra `uv tool install "graphifyy[mcp]"` (or `pip install "graphifyy[mcp]"`; `graphifyy[all]` also bundles it), matching graphify's own runtime error guidance.

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

- `graphify` CLI v0.8.x installed (`which graphify`; `uv tool install graphifyy`). The `graphify-mcp` console-script launch form needs `>=0.8.36`; the `python -m graphify.serve` form works on any 0.8.x (incl. the 0.8.24 floor).
- Target project has `graphify-out/graph.json` (verify mtime per `~/.claude/skills/kg/references/architecture.md` freshness gate)
- `~/.claude.json` or project-local `.mcp.json` exists and is writable

## MCP tools exposed (by `python -m graphify.serve`)

Per graphify v0.8.x `serve.py`. The launch command in `.mcp.json` (set up by `register --apply`) runs `<python> -m graphify.serve <graph.json>`, which exposes the tools below over stdio.

| Tool | Purpose |
|---|---|
| `query_graph` | BFS/DFS search with token budget (replaces in-context graph.json loading) |
| `get_node` | Full details for a node by label/ID |
| `get_neighbors` | Direct neighbors with edge details |
| `get_community` | All nodes in a community by ID |
| `god_nodes` | Most connected nodes (anchor concepts) |
| `graph_stats` | Summary stats (nodes/edges/communities/confidence breakdown) |
| `shortest_path` | Shortest path between two concepts (used by `/kg-ingest` Confirmation gate, `/kg-connect`, `/kg-postmortem` pattern detection) |
| `list_prs` / `get_pr_impact` / `triage_prs` | PR-dashboard tools (v0.8.x). Need a git/PR context — usually irrelevant to a kg corpus; ignore unless graphing a repo with open PRs. |

**Transport (v0.8.34+):** stdio is the default (one local process per developer). To share one graph across a team, serve over HTTP — `python -m graphify.serve <graph.json> --transport http --host 0.0.0.0 --port 8080 --api-key "$SECRET"` — and point each `.mcp.json` at `http://<host>:8080/mcp`. Set `--host 0.0.0.0` **and** `--api-key` together; the default `127.0.0.1` bind is loopback-only. Every `query_graph` call is logged to `~/.cache/graphify-queries.log` (disable with `GRAPHIFY_QUERY_LOG_DISABLE=1`). Note: `/kg-mcp register --apply` only emits the **stdio** `command`/`args` entry — the HTTP client entry needs a `url`/http-transport shape, so for HTTP you hand-edit `.mcp.json` to point at `http://<host>:8080/mcp` (the server side is real, but `register` does not wire it up).

## Subcommands

### `/kg-mcp` (no subcommand) — defaults to `status`

Bare invocation `/kg-mcp` (without `register|status|unregister`) is treated as `/kg-mcp status` (read-only inspection). Rationale: status is the only read-only subcommand; defaulting to it lets users inspect current registration with minimal typing. Mutations are always blocked from bare invocation by the existing `--scope` + `--apply` Authority gate.

When defaulting to status, prepend this note to the output:
> Note: `/kg-mcp` (no subcommand) maps to `status` (read-only). Mutations require explicit `register --scope <user|project> --apply` or `unregister --scope <user|project> --apply`.

### `/kg-mcp register --scope <user|project> [--apply]`
1. Detect target `graph.json` (cwd or arg).
2. Print the proposed MCP server entry to add to `.mcp.json`. **For a `uv tool install` of graphify (recommended), use the self-resolving `graphify-mcp` console script** (v0.8.36+) — its shebang carries the right venv interpreter, so you don't have to locate a `python` that can import graphify:
   ```json
   {
     "mcpServers": {
       "graphify-<project-slug>": {
         "command": "graphify-mcp",
         "args": ["<absolute-path-to-graph.json>"]
       }
     }
   }
   ```
   **NOTE (graphify v0.8.x)**: `graphify-mcp` launches `graphify.serve`; there is no bare `--mcp` CLI verb. **The `graphify-mcp` console script requires graphify `>=0.8.36`** — on the documented `>=0.8.24` floor up to `0.8.35` it does not exist, so on those versions (or any install where `graphify-mcp` is not on PATH) use the `<python> -m graphify.serve` form instead. That alternative form `{"command": "<python>", "args": ["-m", "graphify.serve", "<graph.json>"]}` works **only when `<python>` is the exact interpreter that can `import graphify`** — for a `uv tool install` that is NOT system python (graphify lives in a uv-managed venv; `system python3 -c "import graphify"` → `ModuleNotFoundError`). Find it via the `graphify-mcp` shebang or `uv tool dir`, or just prefer the console script. The `mcp` package is required: `uv tool install "graphifyy[mcp]"` (or `pip install "graphifyy[mcp]"`; `graphifyy[all]` bundles it). **Verify with `graphify-mcp --help`, or `<that-python> -c "import mcp.server.stdio"`** before writing config — NOT `import graphify.serve`, which succeeds even when `mcp` is absent (serve.py imports `mcp` lazily) and then the server dies at runtime with `ImportError: mcp not installed. Run: pip install "graphifyy[mcp]"`.
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

Proposed/current MCP servers entry — graphify >=0.8.36 with graphify-mcp on PATH -> command = graphify-mcp (as shown); graphify 0.8.24-0.8.35 or graphify-mcp not on PATH -> command = the interpreter that can import graphify, args = ["-m", "graphify.serve", "<graph.json>"]:
  { "graphify-<slug>": { "command": "graphify-mcp", "args": ["<abs-path-to-graph.json>"] } }

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

- **graphify CLI not found** → stop, suggest `uv tool install graphifyy` (recommended over `pip`).
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
