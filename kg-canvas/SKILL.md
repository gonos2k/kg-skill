---
name: kg-canvas
description: Export wiki knowledge as Obsidian Canvas (.canvas) files (지식 시각화/마인드맵/다이어그램/knowledge map). Auto-positioned nodes, color-coded by page_kind, grouped by community or folder. 공간적 탐색용 시각 렌더링.
trigger: /kg-canvas
---

# /kg-canvas — Visual Knowledge Export

Produces `.canvas` JSON files that Obsidian renders natively. No plugins required.

## Preconditions
- Wiki must be bootstrapped (`wiki/` exists with content pages)
- For `community` mode: `graphify-out/GRAPH_REPORT.md` must exist. If absent, suggest `overview` or `[folder]` mode instead
- If wiki doesn't exist, tell user to run `/kg init` first

## Modes

### `/kg-canvas overview`
Full wiki overview. One node per page, grouped by folder/page_kind.

### `/kg-canvas [folder]`
Single folder deep-dive. Shows pages + their wikilink connections.

### `/kg-canvas community [N]`
Graph community N from GRAPH_REPORT.md. Nodes = community members, edges = graph edges.

## Canvas JSON Structure (JSON Canvas 1.0)
```json
{
  "nodes": [
    {
      "id": "unique-id",
      "type": "file",
      "file": "wiki/concepts/register-pressure.md",
      "x": 0, "y": 0,
      "width": 400, "height": 200,
      "color": "4"
    }
  ],
  "edges": [
    {
      "id": "edge-id",
      "fromNode": "source-id",
      "toNode": "target-id",
      "label": "implements"
    }
  ]
}
```

## Color Scheme (page_kind -> JSON Canvas 1.0 preset)
- entity-page: `"1"` (red)
- concept-page: `"4"` (green)
- procedure-page: `"5"` (cyan)
- experience-page: `"3"` (yellow)
- heuristic-page: `"6"` (purple)
- decision-page: `"2"` (orange)
- source-page: omit (Obsidian default)

## Auto-Layout
1. Group nodes by folder (or community)
2. Grid within group: `cols = ceil(sqrt(count))`
3. Node size: 400x200 default, scale up for high-degree nodes
4. Group spacing: 600px
5. Edges auto-routed by Obsidian

## Output
- Writes to `wiki/<name>.canvas`
- Overwrites existing (canvases are generated views)
- Reports: N nodes, M edges, K groups

## Limitations
- Static snapshot. Re-run to update.
- Large wikis (>200 nodes) may be slow to render. Use folder mode.
- Read-only export. Does not modify wiki pages.
