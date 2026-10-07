#!/usr/bin/env python3
"""Mechanical style and safety checks for solution files.

Only rules that a program can decide are checked here; the reasoning behind each
one lives in `docs/coding-standards.md` and the per-language style guides.

Usage:
    python scripts/lint_solutions.py                     # every solution
    python scripts/lint_solutions.py path/to/main.cpp    # specific files
    python scripts/lint_solutions.py --strict            # warnings fail too

Suppress one finding deliberately by writing `lint:allow RULE_ID` (comma separated
ids allowed) in a comment on the same line or on the line above, and say why:

    int* raw = new int[3];  // lint:allow CPP004 deliberate raw-pointer exercise

Exit code: 0 = clean, 1 = errors (or warnings with --strict).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from repo_lib import LANGUAGES, Issue, count_issues, find_problem_dirs, implementations, print_issues

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_LINE_LENGTH = 120
ALLOW_RE = re.compile(r"lint:allow\s+([A-Z0-9_,\s]+)")


# --------------------------------------------------------------------------- scanning


@dataclass(frozen=True)
class ScanConfig:
    line_comment: str
    block_comment: tuple[str, str] | None
    quotes: str
    triple_quotes: tuple[str, ...] = ()
    multiline_quotes: str = ""


SCAN: dict[str, ScanConfig] = {
    "cpp": ScanConfig("//", ("/*", "*/"), "\"'"),
    "c": ScanConfig("//", ("/*", "*/"), "\"'"),
    "javascript": ScanConfig("//", ("/*", "*/"), "\"'`", multiline_quotes="`"),
    "rust": ScanConfig("//", ("/*", "*/"), '"'),  # ' is ambiguous (lifetimes)
    "python": ScanConfig("#", None, "\"'", triple_quotes=('"""', "'''")),
    "sql": ScanConfig("--", ("/*", "*/"), "'"),
}


def _blank(segment: str) -> str:
    return re.sub(r"[^\n]", " ", segment)


def split_source(text: str, folder: str) -> tuple[str, str, str]:
    """Split a source file into three same-shaped strings (newlines are preserved).

    Returns (code without strings, code with strings, comments). In each one, the
    characters that belong elsewhere are replaced by spaces, so line and column
    numbers always line up with the original file.
    """
    cfg = SCAN[folder]
    code_plain: list[str] = []
    code_strings: list[str] = []
    comments: list[str] = []

    def put(kind: str, segment: str) -> None:
        blank = _blank(segment)
        if kind == "code":
            code_plain.append(segment)
            code_strings.append(segment)
            comments.append(blank)
        elif kind == "string":
            code_plain.append(blank)
            code_strings.append(segment)
            comments.append(blank)
        else:
            code_plain.append(blank)
            code_strings.append(blank)
            comments.append(segment)

    i, n = 0, len(text)
    while i < n:
        if cfg.block_comment and text.startswith(cfg.block_comment[0], i):
            end = text.find(cfg.block_comment[1], i + len(cfg.block_comment[0]))
            end = n if end == -1 else end + len(cfg.block_comment[1])
            put("comment", text[i:end])
            i = end
            continue
        if text.startswith(cfg.line_comment, i):
            end = text.find("\n", i)
            end = n if end == -1 else end
            put("comment", text[i:end])
            i = end
            continue
        triple = next((t for t in cfg.triple_quotes if text.startswith(t, i)), None)
        if triple:
            end = text.find(triple, i + 3)
            end = n if end == -1 else end + 3
            put("string", text[i:end])
            i = end
            continue
        ch = text[i]
        if ch in cfg.quotes:
            j = i + 1
            while j < n:
                if text[j] == "\\" and folder != "sql":
                    j += 2
                    continue
                if text[j] == ch:
                    j += 1
                    break
                if text[j] == "\n" and ch not in cfg.multiline_quotes:
                    break  # unterminated: stop at the end of the line
                j += 1
            put("string", text[i:j])
            i = j
            continue
        put("code", ch)
        i += 1

    return "".join(code_plain), "".join(code_strings), "".join(comments)


# --------------------------------------------------------------------------- rules


@dataclass(frozen=True)
class Rule:
    id: str
    level: str
    langs: tuple[str, ...]
    pattern: re.Pattern[str]
    message: str
    keep_strings: bool = False


def rule(id_: str, level: str, langs: str, pattern: str, message: str, *, flags: int = 0, keep_strings: bool = False) -> Rule:
    return Rule(id_, level, tuple(langs.split(",")), re.compile(pattern, flags), message, keep_strings)


RULES: tuple[Rule, ...] = (
    # C++
    rule("CPP001", "error", "cpp", r"\busing\s+namespace\s+std\b", "do not use 'using namespace std'; write std:: explicitly"),
    rule("CPP002", "error", "cpp", r"#\s*include\s*<bits/stdc\+\+\.h>", "<bits/stdc++.h> is not standard; include what you use"),
    rule("CPP003", "warning", "cpp", r"\bstd::endl\b", "prefer '\\n' over std::endl (endl flushes the stream)"),
    rule("CPP004", "error", "cpp", r"\bnew\s+[\w:<]|\bdelete\b\s*(?:\[\s*\]\s*)?[\w(*]", "avoid raw new/delete; use std::unique_ptr, std::make_unique or std::vector"),
    rule("CPP005", "warning", "cpp", r"\(\s*(?:unsigned\s+)?(?:int|long|long\s+long|short|double|float|char|size_t)\s*\)\s*[\w(]", "use static_cast instead of a C-style cast"),
    rule("CPP006", "warning", "cpp", r"\b(?:malloc|calloc|realloc|free)\s*\(", "avoid C memory management in C++; use containers and smart pointers"),
    rule("CPP007", "warning", "cpp", r"^\s*#\s*define\s+\w+", "avoid macros unless clearly justified; prefer constexpr"),
    # C
    rule("C001", "error", "c", r"\bgets\s*\(", "gets() cannot be used safely; use fgets()"),
    rule("C002", "error", "c", r"\b[fs]?scanf\s*\([^;]*%\*?[s\[]", "unbounded %s/%[ in scanf; give a width (e.g. %99s) or use fgets()", keep_strings=True),
    rule("C003", "error", "c", r"\b(?:strcpy|strcat|sprintf|vsprintf)\s*\(", "unbounded copy/format function; use snprintf or a bounded alternative"),
    rule("C004", "warning", "c", r"\b(?:atoi|atol|atoll|atof)\s*\(", "atoi-style functions cannot report errors; prefer strtol"),
    rule("C005", "warning", "c", r"^\s*#\s*define\s+[A-Z_0-9]+\s+\(?\d+", "prefer enum or static const over #define for numeric limits"),
    # Python
    rule("PY001", "error", "python", r"\b(?:eval|exec)\s*\(", "never evaluate dynamic code"),
    rule("PY002", "error", "python", r"^\s*from\s+\S+\s+import\s+\*", "wildcard imports hide where names come from"),
    rule("PY003", "warning", "python", r"\.pop\(\s*0\s*\)", "list.pop(0) is O(n); use collections.deque"),
    rule("PY004", "warning", "python", r"\bdef\s+\w+\([^)]*=\s*(?:\[\s*\]|\{\s*\}|set\(\s*\))", "mutable default argument"),
    rule("PY005", "warning", "python", r"\bsetrecursionlimit\s*\(", "deep recursion can crash the interpreter; consider an iterative version"),
    # JavaScript
    rule("JS001", "error", "javascript", r"\bvar\s+\w", "use const (or let when reassigning), never var"),
    rule("JS002", "error", "javascript", r"(?<![=!<>])==(?!=)|!=(?!=)", "use strict equality (=== / !==)"),
    rule("JS003", "error", "javascript", r"\beval\s*\(|\bnew\s+Function\s*\(", "never evaluate dynamic code"),
    rule("JS004", "warning", "javascript", r"\.sort\(\s*\)", "Array.sort() without a comparator sorts as text; pass (a, b) => a - b"),
    rule("JS005", "warning", "javascript", r"\.shift\(\s*\)", "Array.shift() is O(n); use a head index for queues"),
    # Rust
    rule("RS001", "warning", "rust", r"\.unwrap\(\s*\)", "prefer expect(\"reason\"), ? or an explicit match over unwrap()"),
    # SQL
    rule("SQL001", "error", "sql", r"\bSELECT\s+(?:DISTINCT\s+)?\*", "list the columns explicitly instead of SELECT *", flags=re.IGNORECASE),
    rule("SQL002", "error", "sql", r"\bFROM\s+\w+(?:\s+(?:AS\s+)?\w+)?\s*,\s*\w+", "use an explicit JOIN ... ON instead of a comma join", flags=re.IGNORECASE),
    rule("SQL003", "warning", "sql", r"\b(?:select|from|where|join|group\s+by|order\s+by|having|union)\b", "write SQL keywords in UPPERCASE"),
)

# C++: std symbol -> header that must be included explicitly (portability).
CPP_HEADERS: tuple[tuple[str, str], ...] = (
    (r"\bstd::(?:sort|stable_sort|reverse|max|min|min_element|max_element|lower_bound|upper_bound|binary_search|unique|fill|next_permutation|rotate|count_if|any_of|all_of|none_of)\b", "algorithm"),
    (r"\bstd::(?:accumulate|iota|gcd|lcm|partial_sum)\b", "numeric"),
    (r"\bstd::(?:cin|cout|cerr|ios|ios_base)\b", "iostream"),
    (r"\bstd::(?:setw|setprecision|setfill)\b", "iomanip"),
    (r"\bstd::vector\b", "vector"),
    (r"\bstd::(?:string|getline|to_string|stoi|stoll)\b", "string"),
    (r"\bstd::string_view\b", "string_view"),
    (r"\bstd::(?:unique_ptr|make_unique|shared_ptr|make_shared)\b", "memory"),
    (r"\bstd::(?:map|multimap)\b", "map"),
    (r"\bstd::(?:set|multiset)\b", "set"),
    (r"\bstd::unordered_map\b", "unordered_map"),
    (r"\bstd::unordered_set\b", "unordered_set"),
    (r"\bstd::(?:queue|priority_queue)\b", "queue"),
    (r"\bstd::stack\b", "stack"),
    (r"\bstd::deque\b", "deque"),
    (r"\bstd::array\b", "array"),
    (r"\bstd::optional\b", "optional"),
    (r"\bstd::function\b", "functional"),
    (r"\bstd::(?:sqrt|pow|ceil|floor|fabs|log|log2|exp)\b", "cmath"),
    (r"\bstd::numeric_limits\b", "limits"),
    (r"\bstd::(?:stringstream|istringstream|ostringstream)\b", "sstream"),
    (r"\bstd::memset\b", "cstring"),
    (r"\bstd::u?int(?:8|16|32|64)_t\b", "cstdint"),
)


# Rules implemented as code (not in RULES) that are still documented by id.
EXTRA_RULE_IDS: tuple[str, ...] = ("CPP008", "JS006", "RS002", "GEN001", "GEN002")


def _allowed(comment_lines: list[str], index: int) -> set[str]:
    """Rule ids suppressed for line `index` (same line or the line above)."""
    allowed: set[str] = set()
    for i in (index - 1, index):
        if 0 <= i < len(comment_lines):
            match = ALLOW_RE.search(comment_lines[i])
            if match:
                allowed.update(part.strip() for part in re.split(r"[,\s]+", match.group(1)) if part.strip())
    return allowed


def lint_text(text: str, folder: str, rel: str) -> list[Issue]:
    """Lint one file's text. `folder` is the language folder name (cpp, c, ...)."""
    code_plain, code_strings, comments = split_source(text, folder)
    plain_lines = code_plain.splitlines()
    string_lines = code_strings.splitlines()
    comment_lines = comments.splitlines()
    raw_lines = text.splitlines()
    issues: list[Issue] = []

    def report(level: str, line_no: int, rule_id: str, message: str) -> None:
        if rule_id not in _allowed(comment_lines, line_no - 1):
            issues.append(Issue(level, f"{rel}:{line_no}", f"[{rule_id}] {message}"))

    for r in RULES:
        if folder not in r.langs:
            continue
        lines = string_lines if r.keep_strings else plain_lines
        for number, line in enumerate(lines, start=1):
            if r.pattern.search(line):
                report(r.level, number, r.id, r.message)

    # File-level and multi-line rules.
    if folder == "javascript" and not re.search(r"""["']use strict["']""", code_strings):
        report("warning", 1, "JS006", "add \"use strict\" at the top of the file")

    if folder == "rust":
        for number, line in enumerate(plain_lines, start=1):
            if re.search(r"\bunsafe\b", line):
                nearby = " ".join(comment_lines[max(0, number - 2):number])
                if "SAFETY:" not in nearby:
                    report("error", number, "RS002", "unsafe needs a '// SAFETY:' comment explaining why it is sound")

    if folder == "cpp":
        included = set(re.findall(r"#\s*include\s*<([^>]+)>", code_plain))
        for pattern, header in CPP_HEADERS:
            for number, line in enumerate(plain_lines, start=1):
                if re.search(pattern, line) and header not in included:
                    report("error", number, "CPP008", f"uses std symbols from <{header}> without including it")
                    break

    for number, line in enumerate(comment_lines, start=1):
        if re.search(r"\b(?:TODO|FIXME|XXX)\b", line):
            report("warning", number, "GEN001", "unfinished marker left in the code")
    for number, line in enumerate(raw_lines, start=1):
        if len(line) > MAX_LINE_LENGTH:
            report("warning", number, "GEN002", f"line longer than {MAX_LINE_LENGTH} characters")

    return issues


# --------------------------------------------------------------------------- cli


def lint_file(path: Path, root: Path) -> list[Issue]:
    folder = path.parent.name
    if folder not in {f for f, _ in LANGUAGES.values()}:
        return [Issue("error", path.as_posix(), "not inside a known solutions/<language>/ folder")]
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return lint_text(path.read_text(encoding="utf-8"), folder, rel)


def collect_files(root: Path, paths: list[Path]) -> list[Path]:
    if paths:
        return [p.resolve() for p in paths]
    files: list[Path] = []
    for problem_dir in find_problem_dirs(root):
        files += list(implementations(problem_dir).values())
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint solution files against the repository standards.")
    parser.add_argument("paths", nargs="*", type=Path, help="solution files (default: all)")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--github", action="store_true", help="emit GitHub Actions annotations")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    files = collect_files(root, args.paths)
    issues: list[Issue] = []
    for path in files:
        issues += lint_file(path, root)

    print_issues(issues, args.github)
    errors, warnings = count_issues(issues)
    print(f"\nLinted {len(files)} file(s): {errors} error(s), {warnings} warning(s).")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
