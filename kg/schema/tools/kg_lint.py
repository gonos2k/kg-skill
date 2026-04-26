#!/usr/bin/env python3
"""kg_lint — deterministic wiki health sensors.

Detects:
  - Orphan pages (no inbound [[wikilinks]])
  - Missing wikilinks (referenced but page doesn't exist)
  - Deprecated pages without > [!superseded] callout
  - Supersession orphans (supersedes target not deprecated)

Output:
  - Default: human-readable text
  - --json: machine-readable JSON

Exit codes:
  0 = PASS (no issues)
  1 = WARN (issues found)
  2 = ERROR (script could not run)

Used by /kg-lint sensor loop. Stdlib + PyYAML only.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)

# Files that are bookkeeping / meta — not content pages
META_FILENAMES = {"hot.md", "log.md", "overview.md", "graph-report.md", "index.md"}


def parse_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, text[m.end():]


def collect_pages(wiki_root: Path) -> dict[str, tuple[Path, dict, str]]:
    pages: dict[str, tuple[Path, dict, str]] = {}
    for path in wiki_root.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(wiki_root).parts):
            continue
        if path.name in META_FILENAMES or path.name.startswith("_index"):
            continue
        slug = path.stem
        fm, body = parse_page(path)
        pages[slug] = (path, fm, body)
    return pages


def find_wikilinks(body: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(body)]


def detect_orphans(pages) -> list[str]:
    inbound: dict[str, int] = defaultdict(int)
    for _slug, (_path, _fm, body) in pages.items():
        for target in find_wikilinks(body):
            inbound[target] += 1
    return sorted(slug for slug in pages if inbound.get(slug, 0) == 0)


def detect_missing(pages) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = defaultdict(list)
    for slug, (_path, _fm, body) in pages.items():
        for target in find_wikilinks(body):
            if target not in pages:
                missing[target].append(slug)
    return dict(missing)


def detect_deprecated_without_callout(pages) -> list[str]:
    issues = []
    for slug, (_path, fm, body) in pages.items():
        if fm.get("epistemic_status") == "deprecated" and "> [!superseded]" not in body:
            issues.append(slug)
    return sorted(issues)


def detect_supersession_orphans(pages) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    for slug, (_path, fm, _body) in pages.items():
        relations = fm.get("relations") or []
        if not isinstance(relations, list):
            continue
        for rel in relations:
            if not isinstance(rel, dict) or rel.get("predicate") != "supersedes":
                continue
            target = (rel.get("target") or "").strip("[]").strip()
            if target in pages:
                target_fm = pages[target][1]
                if target_fm.get("epistemic_status") != "deprecated":
                    issues.append((slug, target))
    return issues


def build_report(wiki_root: Path) -> dict:
    pages = collect_pages(wiki_root)
    return {
        "wiki_root": str(wiki_root),
        "page_count": len(pages),
        "orphans": detect_orphans(pages),
        "missing_pages": detect_missing(pages),
        "deprecated_without_callout": detect_deprecated_without_callout(pages),
        "supersession_orphans": detect_supersession_orphans(pages),
    }


def has_issues(report: dict) -> bool:
    return any(report[k] for k in (
        "orphans", "missing_pages", "deprecated_without_callout", "supersession_orphans"
    ))


def print_human(report: dict) -> None:
    print("# kg_lint report")
    print(f"Wiki: {report['wiki_root']}")
    print(f"Pages scanned: {report['page_count']}")
    print()

    print(f"Orphan pages: {len(report['orphans'])}")
    for slug in report["orphans"][:10]:
        print(f"  - {slug}")
    if len(report["orphans"]) > 10:
        print(f"  ... ({len(report['orphans']) - 10} more)")
    print()

    print(f"Missing wikilinks: {len(report['missing_pages'])}")
    for target, refs in list(report["missing_pages"].items())[:10]:
        print(f"  - [[{target}]] (referenced from {len(refs)} pages)")
    print()

    print(f"Deprecated without superseded callout: {len(report['deprecated_without_callout'])}")
    for slug in report["deprecated_without_callout"]:
        print(f"  - {slug}")
    print()

    print(f"Supersession orphans: {len(report['supersession_orphans'])}")
    for slug, target in report["supersession_orphans"]:
        print(f"  - {slug} → {target} (target not deprecated)")
    print()

    print(f"Verdict: {'WARN' if has_issues(report) else 'PASS'}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: kg_lint.py <wiki-root> [--json]", file=sys.stderr)
        return 2

    wiki_root = Path(sys.argv[1]).resolve()
    if not wiki_root.is_dir():
        print(f"error: wiki root not found or not a directory: {wiki_root}", file=sys.stderr)
        return 2

    report = build_report(wiki_root)
    json_mode = "--json" in sys.argv[2:]

    if json_mode:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)

    return 1 if has_issues(report) else 0


if __name__ == "__main__":
    sys.exit(main())
