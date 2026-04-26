#!/usr/bin/env python3
"""check_skill_examples — verify SKILL-documented CLI invocations actually exist.

Background (v0.5.x dogfooding pattern):
  v0.5.2 had 9 SKILLs documenting `graphify <path> --<flag>` Bash forms that
  graphify v0.5.0 CLI rejects with `error: unknown command`. v0.5.3 had
  `graphify --mcp` which doesn't exist either (--mcp is slash-command only).

  Both bugs would have been caught in seconds by parsing every backtick-quoted
  shell command in SKILL.md and verifying the verb is recognized.

Scope (intentionally narrow per Codex review v0.5.5):
  - Only check `graphify <subcommand>` and `python -m <module>` forms
  - Verb-only check: confirm `graphify --help` lists the subcommand, OR
    confirm the python module is importable
  - Do NOT execute the full command (no side effects, no file creation)
  - Allowlist: known forms that don't appear in graphify --help
    (e.g., `graphify install --platform claude` is valid but `install` may not
    be a top-level verb in some versions — explicit allowlist handles this)

Usage:
  python3 check_skill_examples.py <skills-root>
  python3 check_skill_examples.py ~/.claude/skills

Exit codes:
  0 = PASS (all examples verifiable)
  1 = FAIL (some examples reference non-existent CLI verbs)
  2 = ERROR (script could not run — graphify missing, etc.)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Patterns to detect potentially-executable shell commands inside SKILL.md.
#   INLINE_BACKTICK_RE: single-line backtick-quoted text (does NOT span newlines)
#   FENCED_BLOCK_RE:    fenced block with EXPLICIT language tag — bash, sh,
#                       console, shell (REQUIRED). Bare ``` without language is
#                       treated as not-a-shell-block to avoid false positives
#                       on json/text blocks. v0.5.5 tightening.
INLINE_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
FENCED_BLOCK_RE = re.compile(r"```(?:bash|sh|console|shell)\n(.+?)\n```", re.DOTALL)

# Words/phrases in the surrounding line that indicate a NEGATIVE example
# (i.e., the SKILL is showing the form to warn it doesn't work). v0.5.5.
NEGATIVE_CONTEXT_RE = re.compile(
    r"(returns?\s+`error|unknown\s+command|does\s+NOT|doesn'?t\s+(work|exist)|"
    r"fail(s|ed)?|broken|bug|invalid|incorrect|deprecated|warns?\s+about|"
    r"slash[-\s]command[-\s]?only|not\s+a\s+raw\s+CLI|NOT\s+in\s+the\s+CLI)",
    re.IGNORECASE,
)

# Python interpreters to try (in order) when checking `python -m graphify.X`.
# The system `python3` may be too old to have `mcp` installed; try modern
# versions before declaring a failure. v0.5.5.
PYTHON_FALLBACK_INTERPRETERS = ["python3.12", "python3.11", "python3.10", "python3"]

# Verbs we know about in graphify v0.5.0 CLI's `--help` output.
# Sourced from graphify --help; kept in code for offline verification.
GRAPHIFY_KNOWN_VERBS = {
    "install", "uninstall", "path", "explain", "clone", "merge-graphs",
    "add", "watch", "update", "cluster-only", "query", "save-result",
    "check-update", "benchmark", "hook",
    # Per-platform installers
    "gemini", "cursor", "claude", "codex", "opencode", "aider", "copilot",
    "vscode", "claw", "droid", "trae", "trae-cn", "antigravity", "hermes",
    "kiro",
}

# Forms that LOOK like CLI but are intentional slash-command notation.
# These are documented in SKILLs as `/graphify <path> --<flag>` but we accept
# them only when prefixed by `/`. Any UNPREFIXED occurrence inside backticks
# is a bug (Bash will fail on these).
SLASH_ONLY_FLAGS = {
    "--update", "--mcp", "--svg", "--graphml", "--neo4j", "--wiki",
    "--mode", "--directed", "--watch", "--html", "--neo4j-push",
}

# Allowlist: verb-flag combos to skip (known doc shorthand, never executed)
ALLOWLIST_PREFIXES = {
    "graphify --help",      # the meta query itself
    "graphify-out/",        # path reference, not a command
    "graphify v",           # version string in prose ("graphify v0.5.0")
    "graphifyy",            # PyPI package name in prose
    "graphify",             # bare without subcommand (covered separately)
}


def graphify_help_verbs() -> set[str]:
    """Try to query the live `graphify --help` for ground truth.

    Falls back to GRAPHIFY_KNOWN_VERBS if graphify isn't installed.
    """
    try:
        out = subprocess.run(
            ["graphify", "--help"],
            capture_output=True, text=True, timeout=5,
        )
        text = out.stdout + out.stderr
        # Lines like "  update <path>           re-extract code files..."
        live_verbs = set(re.findall(r"^\s{2}([a-z-]+)\b", text, re.MULTILINE))
        if live_verbs:
            return live_verbs
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return GRAPHIFY_KNOWN_VERBS


def line_text_around(text: str, char_pos: int, window: int = 200) -> str:
    """Return ~`window` chars of context around `char_pos` for negative-context detection."""
    start = max(0, char_pos - window)
    end = min(len(text), char_pos + window)
    return text[start:end]


def extract_shell_commands(skill_md: Path) -> list[tuple[int, str, str]]:
    """Extract candidate shell-form commands as (line_number, command_string, context)."""
    text = skill_md.read_text(encoding="utf-8-sig")
    out: list[tuple[int, str, str]] = []

    # Inline backtick — single line (cannot span newlines per regex)
    for m in INLINE_BACKTICK_RE.finditer(text):
        cmd = m.group(1).strip()
        line = text.count("\n", 0, m.start()) + 1
        ctx = line_text_around(text, m.start())
        out.append((line, cmd, ctx))

    # Fenced code blocks (require explicit shell language tag; bare ``` skipped)
    for m in FENCED_BLOCK_RE.finditer(text):
        block = m.group(1)
        block_start_line = text.count("\n", 0, m.start()) + 2  # +1 for ``` line
        for i, line_content in enumerate(block.split("\n")):
            stripped = line_content.strip()
            if not stripped or stripped.startswith("#"):
                continue
            out.append((block_start_line + i, stripped, ""))  # no surrounding prose

    return out


def is_allowed(cmd: str) -> bool:
    """Skip allowlisted phrases (path refs, version strings, etc.)."""
    return any(cmd.startswith(p) for p in ALLOWLIST_PREFIXES)


def check_command(cmd: str, known_verbs: set[str], context: str = "") -> tuple[str, str]:
    """Return (status, reason). status ∈ {OK, FAIL, SKIP}.

    `context` is surrounding prose (~200 chars before+after); used to detect
    negative examples (SKILL warns the form doesn't work) and skip them.
    """
    cmd = cmd.strip()

    # 0. Negative-context detection (v0.5.5) — SKILL is documenting a BROKEN form
    #    explicitly. Skip to avoid flagging "we warn this doesn't work" as a bug.
    if context and NEGATIVE_CONTEXT_RE.search(context):
        return "SKIP", "negative-example context (SKILL explicitly warns this form doesn't work)"

    # 1. Slash commands: skip — those are Claude-Code orchestrator forms
    if cmd.startswith("/"):
        return "SKIP", "slash-command form (orchestrator-only)"

    # 2. Allowlisted prose
    if is_allowed(cmd) and not cmd.startswith("graphify "):
        return "SKIP", "allowlisted (path/version/package)"

    # 3. graphify <verb> — verify verb is real
    if cmd.startswith("graphify "):
        rest = cmd[len("graphify "):].strip()
        # Special cases: "graphify <abs-path>" is invalid (caught by v0.5.2 patches)
        first_token = rest.split()[0] if rest.split() else ""

        # SLASH_ONLY_FLAGS appearing as Bash form is a bug
        if first_token in SLASH_ONLY_FLAGS:
            return "FAIL", f"slash-only flag {first_token!r} used in Bash position (use `/graphify ... {first_token}` instead)"

        # Any token starting with `--` in first position is a bug
        if first_token.startswith("--") and first_token != "--help":
            return "FAIL", f"flag {first_token!r} used as subcommand (graphify CLI requires <verb> first)"

        # Path-form (`graphify <path>` no subcommand) — typically a documentation
        # placeholder like `graphify <path>` itself; skip
        if first_token in {"<path>", "<file>", "<repo>", "<dir>", "."}:
            return "SKIP", f"placeholder path argument {first_token!r}"

        # Real subcommand check
        if first_token in known_verbs:
            return "OK", f"verb {first_token!r} verified in graphify --help"
        else:
            # Could be a typo or new verb not yet in our snapshot
            return "FAIL", f"verb {first_token!r} not in graphify --help (known: {sorted(known_verbs)[:8]}...)"

    # 4. python -m graphify.X — verify module exists
    #    Try multiple python interpreters since `mcp` package needs python ≥ 3.10
    #    and the system `python3` may be older. v0.5.5.
    if cmd.startswith("python") and " -m graphify" in cmd:
        m = re.search(r"-m\s+(graphify\.\w+)", cmd)
        if m:
            module = m.group(1)
            for interp in PYTHON_FALLBACK_INTERPRETERS:
                try:
                    check = subprocess.run(
                        [interp, "-c", f"import {module}"],
                        capture_output=True, text=True, timeout=3,
                    )
                    if check.returncode == 0:
                        return "OK", f"module {module!r} importable via {interp}"
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            return "FAIL", f"module {module!r} not importable in any of {PYTHON_FALLBACK_INTERPRETERS}"

    # 5. Anything else — out of scope for this checker
    return "SKIP", "not a graphify or python -m graphify form"


def main() -> int:
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <skills-root>", file=sys.stderr)
        return 2

    skills_root = Path(sys.argv[1]).expanduser().resolve()
    if not skills_root.is_dir():
        print(f"error: not a directory: {skills_root}", file=sys.stderr)
        return 2

    # Find all SKILL.md
    skill_files = list(skills_root.rglob("SKILL.md"))
    if not skill_files:
        print(f"warning: no SKILL.md found under {skills_root}", file=sys.stderr)
        return 0

    known_verbs = graphify_help_verbs()
    print(f"# check_skill_examples report")
    print(f"# Skills root: {skills_root}")
    print(f"# graphify verbs source: live --help" if "update" in known_verbs and "path" in known_verbs else "# graphify verbs source: hardcoded fallback")
    print(f"# SKILL.md files: {len(skill_files)}")
    print()

    total_fails = 0
    total_oks = 0
    total_skips = 0
    for skill_md in sorted(skill_files):
        rel = skill_md.relative_to(skills_root)
        commands = extract_shell_commands(skill_md)
        if not commands:
            continue
        file_fails: list[tuple[int, str, str]] = []
        for line, cmd, ctx in commands:
            status, reason = check_command(cmd, known_verbs, ctx)
            if status == "FAIL":
                file_fails.append((line, cmd, reason))
                total_fails += 1
            elif status == "OK":
                total_oks += 1
            else:
                total_skips += 1
        if file_fails:
            print(f"## {rel}")
            for line, cmd, reason in file_fails:
                print(f"  L{line}  FAIL: `{cmd}`")
                print(f"        reason: {reason}")
            print()

    print(f"Summary: {total_oks} OK, {total_fails} FAIL, {total_skips} SKIPPED")
    return 1 if total_fails > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
