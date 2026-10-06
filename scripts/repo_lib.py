"""Shared helpers for the repository maintenance scripts.

Standard library only, so the scripts run anywhere (locally and in CI) without
installing anything.

The single source of truth for the repository vocabulary (languages,
categories, statuses...) lives here. If a convention changes, change it in
this file and every script follows.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Display name used in README metadata -> (folder name, file extension).
# Folder layout: problems/<range>/<id>-<slug>/solutions/<folder>/main.<ext>
LANGUAGES: dict[str, tuple[str, str]] = {
    "C++": ("cpp", "cpp"),
    "C": ("c", "c"),
    "Python": ("python", "py"),
    "JavaScript": ("javascript", "js"),
    "Rust": ("rust", "rs"),
    "SQL": ("sql", "sql"),
}

CATEGORIES: tuple[str, ...] = (
    "Beginner",
    "Ad-Hoc",
    "Strings",
    "Data Structures and Libraries",
    "Mathematics",
    "Paradigms",
    "Graphs",
    "Computational Geometry",
    "SQL",
)

DOC_LEVELS: tuple[str, ...] = ("L1", "L2", "L3")
PRIORITIES: tuple[str, ...] = ("Low", "Medium", "High")

# "Solved" must only be used for code that was really accepted by the judge.
STATUSES: tuple[str, ...] = ("Solved", "In Progress", "Improving", "To Review")

REQUIRED_FIELDS: tuple[str, ...] = (
    "Problem ID",
    "Platform",
    "Category",
    "Difficulty Level",
    "Topics",
    "Primary Language",
    "Documentation Level",
    "Status",
    "Review Priority",
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROBLEM_DIR_RE = re.compile(r"^(\d+)-(.+)$")
RANGE_DIR_RE = re.compile(r"^(\d{4})-(\d{4})$")
_FIELD_RE = re.compile(r"^-\s+([^:]+):\s*(.*)$")
_CHECKBOX_RE = re.compile(r"^-\s+\[([ xX])\]\s+(.+)$")


@dataclass(frozen=True)
class Issue:
    """One validation finding. `level` is either "error" or "warning"."""

    level: str
    path: str
    message: str


def find_language(value: str) -> str | None:
    """Map a metadata value ("C++", "cpp", "python"...) to its display name."""
    wanted = value.strip().lower()
    for display, (folder, _ext) in LANGUAGES.items():
        if wanted in (display.lower(), folder):
            return display
    return None


def read_section(text: str, heading: str) -> list[str]:
    """Return the lines under `## <heading>` up to the next `## ` heading."""
    lines = text.splitlines()
    collected: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            collected.append(line)
    return collected


def parse_metadata(readme_text: str) -> dict[str, str]:
    """Parse the `## Metadata` block (`- Key: value` lines) into a dict."""
    fields: dict[str, str] = {}
    for line in read_section(readme_text, "Metadata"):
        match = _FIELD_RE.match(line.strip())
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def parse_status_checkboxes(readme_text: str) -> tuple[dict[str, bool], list[str]]:
    """Parse the `## Status` checklist.

    Returns (label -> checked, malformed lines). A malformed line starts like a
    checklist item (`- [`) but does not follow the `- [ ] text` / `- [x] text`
    syntax.
    """
    boxes: dict[str, bool] = {}
    malformed: list[str] = []
    for line in read_section(readme_text, "Status"):
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        match = _CHECKBOX_RE.match(stripped)
        if match:
            boxes[match.group(2).strip()] = match.group(1).lower() == "x"
        else:
            malformed.append(stripped)
    return boxes, malformed


def parse_other_implementations(value: str) -> list[str]:
    """`Python, Rust` -> ["Python", "Rust"]; `None`, `-` or empty -> []."""
    cleaned = value.strip()
    if cleaned.lower() in ("", "none", "-", "n/a"):
        return []
    return [part.strip() for part in cleaned.split(",") if part.strip()]


def find_problem_dirs(root: Path) -> list[Path]:
    """List every `problems/<range>/<problem>/` directory, sorted."""
    problems_root = root / "problems"
    if not problems_root.is_dir():
        return []
    found: list[Path] = []
    for range_dir in sorted(p for p in problems_root.iterdir() if p.is_dir()):
        found.extend(sorted(p for p in range_dir.iterdir() if p.is_dir()))
    return found


def implementations(problem_dir: Path) -> dict[str, Path]:
    """Map language folder name -> main file, for every implementation that exists."""
    found: dict[str, Path] = {}
    solutions_dir = problem_dir / "solutions"
    if not solutions_dir.is_dir():
        return found
    for display, (folder, ext) in LANGUAGES.items():
        main_file = solutions_dir / folder / f"main.{ext}"
        if main_file.is_file():
            found[folder] = main_file
    return found


def test_cases(problem_dir: Path) -> list[tuple[str, Path, Path]]:
    """Return (name, input file, expected output file) for every tests/*.in."""
    tests_dir = problem_dir / "tests"
    if not tests_dir.is_dir():
        return []
    return [(p.stem, p, p.with_suffix(".out")) for p in sorted(tests_dir.glob("*.in"))]


def print_issues(issues: list[Issue], github: bool = False) -> None:
    """Print findings as plain text or as GitHub Actions annotations."""
    for issue in issues:
        if github:
            print(f"::{issue.level} file={issue.path}::{issue.message}")
        else:
            print(f"{issue.level.upper():7} {issue.path}: {issue.message}")


def count_issues(issues: list[Issue]) -> tuple[int, int]:
    """Return (errors, warnings)."""
    errors = sum(1 for issue in issues if issue.level == "error")
    return errors, len(issues) - errors


def _git_lines(root: Path, *args: str) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return [line for line in result.stdout.splitlines() if line]


def changed_files(root: Path, staged: bool = False, since: str | None = None) -> list[str] | None:
    """Files touched by the staged changes, or by commits since `since` (e.g. origin/main).

    Returns None when git cannot answer (not a repo, unknown ref...), so callers can
    fall back to checking everything.
    """
    if staged:
        return _git_lines(root, "diff", "--cached", "--name-only")
    if since:
        return _git_lines(root, "diff", "--name-only", f"{since}...HEAD")
    return None


def problem_dirs_for(root: Path, files: list[str]) -> list[Path]:
    """Map changed file paths to the problem folders (that still exist) they belong to."""
    found: set[Path] = set()
    for name in files:
        parts = Path(name).parts
        if len(parts) >= 3 and parts[0] == "problems":
            candidate = root / parts[0] / parts[1] / parts[2]
            if candidate.is_dir():
                found.add(candidate)
    return sorted(found)
