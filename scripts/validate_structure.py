#!/usr/bin/env python3
"""Validate the structure and metadata of every problem folder.

Usage:
    python scripts/validate_structure.py                  # whole repository
    python scripts/validate_structure.py problems/3400-3499/3484-divided-class
    python scripts/validate_structure.py --strict         # warnings fail too
    python scripts/validate_structure.py --github         # GitHub Actions annotations

Exit code: 0 = clean, 1 = errors found (or warnings with --strict).

Errors block a merge. Warnings are advice: things worth a look, but legitimate
in some cases.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_lib import (
    CATEGORIES,
    DOC_LEVELS,
    LANGUAGES,
    PRIORITIES,
    PROBLEM_DIR_RE,
    RANGE_DIR_RE,
    REQUIRED_FIELDS,
    SLUG_RE,
    STATUSES,
    Issue,
    count_issues,
    find_language,
    find_problem_dirs,
    parse_metadata,
    parse_other_implementations,
    parse_status_checkboxes,
    print_issues,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def check_location(problem_dir: Path, root: Path) -> list[Issue]:
    """Folder naming: problems/<NNNN-NNNN>/<id>-<english-slug>/."""
    issues: list[Issue] = []
    rel = _rel(problem_dir, root)

    range_match = RANGE_DIR_RE.match(problem_dir.parent.name)
    name_match = PROBLEM_DIR_RE.match(problem_dir.name)

    if not range_match:
        issues.append(Issue("error", rel, "range folder must look like 3400-3499"))
    else:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if start % 100 != 0 or end != start + 99:
            issues.append(Issue("error", rel, "range folder must cover exactly 100 ids (e.g. 3400-3499)"))

    if not name_match:
        issues.append(Issue("error", rel, "folder name must be <id>-<slug>"))
        return issues

    problem_id, slug = int(name_match.group(1)), name_match.group(2)
    if not SLUG_RE.match(slug):
        issues.append(Issue("error", rel, f"slug '{slug}' must be lowercase english words separated by hyphens"))
    if range_match and not int(range_match.group(1)) <= problem_id <= int(range_match.group(2)):
        issues.append(Issue("error", rel, f"id {problem_id} does not belong in range {problem_dir.parent.name}"))
    return issues


def check_metadata(problem_dir: Path, root: Path) -> tuple[list[Issue], dict[str, str]]:
    """README exists and its metadata block is complete and coherent."""
    readme = problem_dir / "README.md"
    rel = _rel(readme, root)
    issues: list[Issue] = []

    if not readme.is_file():
        return [Issue("error", rel, "README.md is missing")], {}

    text = readme.read_text(encoding="utf-8")
    meta = parse_metadata(text)

    for field in REQUIRED_FIELDS:
        if not meta.get(field):
            issues.append(Issue("error", rel, f"metadata field '{field}' is missing or empty"))

    name_match = PROBLEM_DIR_RE.match(problem_dir.name)
    if name_match and meta.get("Problem ID") and meta["Problem ID"] != name_match.group(1):
        issues.append(Issue("error", rel, f"Problem ID {meta['Problem ID']} does not match folder id {name_match.group(1)}"))

    def check_choice(field: str, allowed: tuple[str, ...]) -> None:
        value = meta.get(field)
        if value and value.lower() not in (item.lower() for item in allowed):
            issues.append(Issue("error", rel, f"{field} '{value}' must be one of: {', '.join(allowed)}"))

    check_choice("Category", CATEGORIES)
    check_choice("Documentation Level", DOC_LEVELS)
    check_choice("Review Priority", PRIORITIES)
    check_choice("Status", STATUSES)

    level = meta.get("Difficulty Level", "")
    if level and not (level.isdigit() and 1 <= int(level) <= 10):
        issues.append(Issue("error", rel, f"Difficulty Level '{level}' must be an integer from 1 to 10"))

    first_line = text.splitlines()[0] if text.strip() else ""
    if name_match and not first_line.startswith(f"# {name_match.group(1)}"):
        issues.append(Issue("warning", rel, f"first heading should start with '# {name_match.group(1)}'"))

    # Status field and the checklist at the bottom must tell the same story.
    boxes, malformed = parse_status_checkboxes(text)
    for line in malformed:
        issues.append(Issue("error", rel, f"malformed checkbox: '{line}' (use '- [ ] text' or '- [x] text')"))
    if "Solved" not in boxes:
        issues.append(Issue("error", rel, "## Status checklist must contain a 'Solved' checkbox"))
    elif meta.get("Status"):
        claims_solved = meta["Status"].lower() == "solved"
        if claims_solved != boxes["Solved"]:
            state = "checked" if boxes["Solved"] else "unchecked"
            issues.append(Issue("error", rel, f"Status is '{meta['Status']}' but the 'Solved' checkbox is {state}"))

    return issues, meta


def check_solutions(problem_dir: Path, root: Path, meta: dict[str, str]) -> list[Issue]:
    """Every declared implementation exists, is non-empty and is in a known language."""
    issues: list[Issue] = []
    solutions_dir = problem_dir / "solutions"
    rel_solutions = _rel(solutions_dir, root)

    if not solutions_dir.is_dir():
        return [Issue("error", rel_solutions, "solutions/ folder is missing")]

    folder_to_display = {folder: display for display, (folder, _ext) in LANGUAGES.items()}
    present: set[str] = set()
    reported: set[str] = set()  # languages that already got an error below

    for lang_dir in sorted(p for p in solutions_dir.iterdir() if p.is_dir()):
        display = folder_to_display.get(lang_dir.name)
        rel_dir = _rel(lang_dir, root)
        if display is None:
            allowed = ", ".join(sorted(folder_to_display))
            issues.append(Issue("error", rel_dir, f"unknown language folder (allowed: {allowed})"))
            continue

        _folder, ext = LANGUAGES[display]
        main_file = lang_dir / f"main.{ext}"
        rel_main = _rel(main_file, root)
        if not main_file.is_file():
            issues.append(Issue("error", rel_main, f"main.{ext} is missing"))
            reported.add(display)
        elif not main_file.read_text(encoding="utf-8").strip():
            issues.append(Issue("error", rel_main, "solution file is empty"))
            reported.add(display)
        else:
            present.add(display)

    rel_readme = _rel(problem_dir / "README.md", root)
    primary_raw = meta.get("Primary Language", "")
    primary = find_language(primary_raw) if primary_raw else None
    if primary_raw and primary is None:
        issues.append(Issue("error", rel_readme, f"Primary Language '{primary_raw}' is not supported"))
    elif primary and primary not in present and primary not in reported:
        issues.append(Issue("error", rel_readme, f"Primary Language {primary} has no valid solutions/{LANGUAGES[primary][0]}/main.{LANGUAGES[primary][1]}"))

    declared = {primary} if primary else set()
    for name in parse_other_implementations(meta.get("Other Implementations", "")):
        display = find_language(name)
        if display is None:
            issues.append(Issue("error", rel_readme, f"Other Implementations lists unsupported language '{name}'"))
            continue
        declared.add(display)
        if display not in present and display not in reported:
            issues.append(Issue("error", rel_readme, f"{display} is declared in Other Implementations but has no valid solution file"))

    for display in sorted(present - declared):
        issues.append(Issue("warning", rel_readme, f"{display} solution exists but is not declared in the metadata"))

    # Policy: SQL is only for the SQL category (and the SQL category only uses SQL).
    category = meta.get("Category", "")
    if primary == "SQL" and category and category != "SQL":
        issues.append(Issue("error", rel_readme, "SQL is reserved for the SQL category"))
    if category == "SQL" and primary and primary != "SQL":
        issues.append(Issue("error", rel_readme, "the SQL category must use SQL as Primary Language"))

    if meta.get("Documentation Level") == "L3" and not (problem_dir / "deep-dive.md").is_file():
        issues.append(Issue("warning", _rel(problem_dir, root), "Documentation Level L3 usually has a deep-dive.md"))

    return issues


def check_tests(problem_dir: Path, root: Path, meta: dict[str, str]) -> list[Issue]:
    """tests/<name>.in + tests/<name>.out pairs, shared by all implementations."""
    issues: list[Issue] = []
    rel = _rel(problem_dir / "tests", root)
    primary = find_language(meta.get("Primary Language", "")) or ""
    if primary == "SQL":
        return issues  # no SQL runner yet; nothing to execute

    tests_dir = problem_dir / "tests"
    inputs = {p.stem for p in tests_dir.glob("*.in")} if tests_dir.is_dir() else set()
    outputs = {p.stem for p in tests_dir.glob("*.out")} if tests_dir.is_dir() else set()

    if not inputs and not outputs:
        solved = meta.get("Status", "").lower() == "solved"
        level = "error" if solved else "warning"
        issues.append(Issue(level, rel, "no test cases (add tests/<name>.in and tests/<name>.out)"))
        return issues

    for stem in sorted(inputs - outputs):
        issues.append(Issue("error", rel, f"{stem}.in has no matching {stem}.out"))
    for stem in sorted(outputs - inputs):
        issues.append(Issue("error", rel, f"{stem}.out has no matching {stem}.in"))
    return issues


def validate_problem(problem_dir: Path, root: Path) -> list[Issue]:
    issues = check_location(problem_dir, root)
    meta_issues, meta = check_metadata(problem_dir, root)
    issues += meta_issues
    issues += check_solutions(problem_dir, root, meta)
    issues += check_tests(problem_dir, root, meta)
    return issues


def validate_repository(root: Path, only: list[Path] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    problems_root = root / "problems"

    if only is None:
        # Stray files/folders directly under problems/ that are not range folders.
        if problems_root.is_dir():
            for entry in sorted(problems_root.iterdir()):
                if entry.is_dir() and not RANGE_DIR_RE.match(entry.name):
                    issues.append(Issue("error", _rel(entry, root), "folders directly under problems/ must be id ranges like 3400-3499"))
        targets = find_problem_dirs(root)
    else:
        targets = only

    for problem_dir in targets:
        issues += validate_problem(problem_dir, root)
    return issues


def print_report(issues: list[Issue], checked: int, github: bool) -> None:
    print_issues(issues, github)
    errors, warnings = count_issues(issues)
    print(f"\nChecked {checked} problem folder(s): {errors} error(s), {warnings} warning(s).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate problem folder structure and metadata.")
    parser.add_argument("paths", nargs="*", type=Path, help="problem folders to check (default: all)")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--github", action="store_true", help="emit GitHub Actions annotations")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    only = [p.resolve() for p in args.paths] if args.paths else None
    issues = validate_repository(root, only)
    checked = len(only) if only is not None else len(find_problem_dirs(root))
    print_report(issues, checked, args.github)

    errors, warnings = count_issues(issues)
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
