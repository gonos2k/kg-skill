#!/usr/bin/env python3
"""Validate every SKILL.md frontmatter + body for kg-skill standards.

Checks:
- frontmatter parses as YAML (handles BOM, malformed markers)
- required keys present (name, description, trigger)
- values are non-empty strings (not null, not "")
- trigger == "/" + skill directory name (catches typos)
- body has no forbidden patterns: "/kg init " (space form), dead-link to kg/SKILL.md
"""
import re
import sys
from pathlib import Path
import yaml

REQUIRED = {"name", "description", "trigger"}
ROOT = Path(__file__).resolve().parents[3]  # ~/.claude/skills

FORBIDDEN_BODY = [
    (re.compile(r"/kg init\b"),
     "use /kg-init (hyphenated form)"),
    (re.compile(r"~/\.claude/skills/kg/SKILL\.md.{0,5}section.{0,5}/kg-"),
     "dead link — PR 2 collapses kg/SKILL.md into a router; use references/ or remove"),
    (re.compile(r"\bSKILL\.md\s*§"),
     "dead link — `SKILL.md § X` references former router sections; redirect to references/ paths"),
]


def extract(path: Path):
    text = path.read_text(encoding="utf-8-sig")  # strips BOM if present
    if not text.startswith("---\n"):
        return None, None, "missing opening --- marker"
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, None, "missing closing --- marker"
    try:
        fm = yaml.safe_load(text[4:end])
    except yaml.YAMLError as e:
        return None, None, f"YAML parse error: {e}"
    body = text[end + 5:]
    return fm, body, None


def validate(skill: Path) -> list[str]:
    errors: list[str] = []
    fm, body, err = extract(skill)
    rel = skill.relative_to(ROOT)
    if err:
        return [f"{rel}: {err}"]
    if not isinstance(fm, dict):
        return [f"{rel}: frontmatter is not a mapping"]

    missing = REQUIRED - set(fm)
    if missing:
        errors.append(f"{rel}: missing keys {sorted(missing)}")

    for key in REQUIRED & set(fm):
        v = fm[key]
        if not isinstance(v, str) or not v.strip():
            errors.append(f"{rel}: '{key}' is empty or non-string")

    expected = f"/{skill.parent.name}"
    if isinstance(fm.get("trigger"), str) and fm["trigger"] != expected:
        errors.append(f"{rel}: trigger '{fm['trigger']}' != expected '{expected}'")

    for i, line in enumerate(body.splitlines(), start=1):
        for pattern, hint in FORBIDDEN_BODY:
            if pattern.search(line):
                errors.append(f"{rel} body line ~{i}: forbidden — {hint}")
    return errors


def main() -> int:
    skills = sorted(ROOT.glob("kg*/SKILL.md"))
    all_errors: list[str] = []
    for s in skills:
        all_errors.extend(validate(s))
    if all_errors:
        for e in all_errors:
            print("FAIL", e)
        return 1
    print(f"PASS — {len(skills)} SKILL.md files OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
