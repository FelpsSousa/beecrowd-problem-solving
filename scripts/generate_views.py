#!/usr/bin/env python3
"""Print a progress dashboard: counts by category, difficulty, language, doc level.

Usage:
    python scripts/generate_views.py              # plain text, for a terminal
    python scripts/generate_views.py --markdown    # same content, as Markdown to paste elsewhere

This is a read-only summary view, nothing is written to the repository. It
reuses the same Status: Solved entries as trackers/solved-problems.md (see
sync_index.py), so the two never disagree about what counts as solved.

Exit code: always 0.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from repo_lib import CATEGORIES, DOC_LEVELS, PRIORITIES, TOPICS, find_problem_dirs
from sync_index import LANGUAGE_INDEX_ORDER, Entry, collect_entries

REPO_ROOT = Path(__file__).resolve().parent.parent


def count_by(entries: list[Entry], groups: tuple[str, ...], bucket_of) -> list[tuple[str, int]]:  # noqa: ANN001
    """One (group, count) pair per item in `groups`, in that order, zeros included."""
    counts: Counter[str] = Counter()
    for entry in entries:
        for group in bucket_of(entry):
            counts[group] += 1
    return [(g, counts[g]) for g in groups]


def render_text(total_problems: int, entries: list[Entry]) -> str:
    lines = [
        "Beecrowd Problem Solving: Progress Dashboard",
        "=" * 46,
        "",
        f"Solved: {len(entries)} of {total_problems} problem folder(s) tracked",
    ]

    sections: list[tuple[str, list[tuple[str, int]]]] = [
        ("By Category", count_by(entries, CATEGORIES, lambda e: [e.category] if e.category in CATEGORIES else [])),
        ("By Difficulty", count_by(entries, tuple(f"Level {n}" for n in range(1, 11)),
                                    lambda e: [f"Level {e.difficulty}"] if 1 <= e.difficulty <= 10 else [])),
        ("By Language", count_by(entries, LANGUAGE_INDEX_ORDER, lambda e: list(e.languages))),
        ("By Documentation Level", count_by(entries, DOC_LEVELS, lambda e: [e.doc_level] if e.doc_level in DOC_LEVELS else [])),
        ("By Review Priority", count_by(entries, PRIORITIES, lambda e: [e.review] if e.review in PRIORITIES else [])),
        ("By Topic", count_by(entries, TOPICS, lambda e: list(e.topics))),
    ]

    width = max((len(label) for section in sections for label, _ in section[1]), default=0)
    for title, rows in sections:
        lines += ["", title]
        for label, count in rows:
            lines.append(f"  {label:<{width}}  {count}")
    return "\n".join(lines) + "\n"


def render_markdown(total_problems: int, entries: list[Entry]) -> str:
    lines = [
        "## Progress Dashboard",
        "",
        f"Solved: **{len(entries)}** of **{total_problems}** problem folder(s) tracked",
    ]

    sections: list[tuple[str, list[tuple[str, int]]]] = [
        ("Category", count_by(entries, CATEGORIES, lambda e: [e.category] if e.category in CATEGORIES else [])),
        ("Difficulty", count_by(entries, tuple(f"Level {n}" for n in range(1, 11)),
                                 lambda e: [f"Level {e.difficulty}"] if 1 <= e.difficulty <= 10 else [])),
        ("Language", count_by(entries, LANGUAGE_INDEX_ORDER, lambda e: list(e.languages))),
        ("Documentation Level", count_by(entries, DOC_LEVELS, lambda e: [e.doc_level] if e.doc_level in DOC_LEVELS else [])),
        ("Review Priority", count_by(entries, PRIORITIES, lambda e: [e.review] if e.review in PRIORITIES else [])),
        ("Topic", count_by(entries, TOPICS, lambda e: list(e.topics))),
    ]

    for title, rows in sections:
        lines += ["", f"| {title} | Count |", "|---|---|"]
        lines += [f"| {label} | {count} |" for label, count in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a progress dashboard (read-only).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--markdown", action="store_true", help="emit Markdown instead of plain text")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    entries = collect_entries(root)
    total_problems = len(find_problem_dirs(root))

    output = render_markdown(total_problems, entries) if args.markdown else render_text(total_problems, entries)
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
