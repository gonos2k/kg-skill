#!/usr/bin/env python3
"""extract_claims — parse Obsidian callouts from wiki pages.

Recognized callout types (case-insensitive):
  claim, evidence, warning, tension, superseded, note

Output: JSON list of {page, type, content, line}.

Used by:
  - /kg-query --depth deep (find evidence supporting a claim)
  - /kg-challenge (find contradicting claims/evidence)
  - /kg-reflect (detect tension callouts in recent pages)

Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CALLOUT_RE = re.compile(
    r"^>\s*\[!(claim|evidence|warning|tension|superseded|note)\]\s*(.*)$",
    re.IGNORECASE,
)

META_FILENAMES = {"hot.md", "log.md", "overview.md", "graph-report.md", "index.md"}


def extract_callouts(path: Path):
    """Yield {type, content, start_line} for each callout in the file."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = CALLOUT_RE.match(lines[i])
        if not m:
            i += 1
            continue

        callout_type = m.group(1).lower()
        first_line = m.group(2).strip()
        body_lines = [first_line] if first_line else []
        start_line = i + 1  # 1-indexed for grep parity

        i += 1
        while i < len(lines) and lines[i].startswith(">"):
            stripped = lines[i].lstrip(">").lstrip(" ")
            body_lines.append(stripped)
            i += 1

        yield {
            "type": callout_type,
            "content": "\n".join(body_lines).strip(),
            "start_line": start_line,
        }


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(
            "usage: extract_claims.py <wiki-root> [--types=claim,evidence,...] [--page=<slug>]",
            file=sys.stderr,
        )
        return 2

    wiki_root = Path(sys.argv[1]).resolve()
    if not wiki_root.is_dir():
        print(f"error: wiki root not found or not a directory: {wiki_root}", file=sys.stderr)
        return 2

    type_filter: set[str] | None = None
    page_filter: str | None = None
    for arg in sys.argv[2:]:
        if arg.startswith("--types="):
            type_filter = {t.strip().lower() for t in arg.split("=", 1)[1].split(",") if t.strip()}
        elif arg.startswith("--page="):
            page_filter = arg.split("=", 1)[1].strip()

    results = []
    for path in wiki_root.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(wiki_root).parts):
            continue
        if path.name in META_FILENAMES or path.name.startswith("_index"):
            continue
        rel = str(path.relative_to(wiki_root))
        slug = rel[:-3] if rel.endswith(".md") else rel
        if page_filter and page_filter not in (slug, path.stem):
            continue
        for callout in extract_callouts(path):
            if type_filter and callout["type"] not in type_filter:
                continue
            results.append({
                "page": slug,
                "type": callout["type"],
                "content": callout["content"],
                "line": callout["start_line"],
            })

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
