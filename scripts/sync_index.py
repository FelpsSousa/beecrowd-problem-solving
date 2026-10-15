#!/usr/bin/env python3
"""Regenerate trackers/solved-problems.md and docs/indexes/*.md from problem metadata.

Usage:
    python scripts/sync_index.py            # rewrite every generated file
    python scripts/sync_index.py --check    # exit 1 if any file is out of date, write nothing

Only problems with Status: Solved are listed, so these files always reflect
what is genuinely accepted by the judge, not work in progress. The source of
truth is each problem's README.md metadata block; these five files are fully
generated and should never be hand-edited, any change would just be
overwritten on the next run.

Exit code: 0 = up to date (or rewritten), 1 = --check found drift.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from repo_lib import (
    CATEGORIES,
    TOPICS,
    find_language,
    find_problem_dirs,
    find_topic,
    parse_metadata,
    parse_other_implementations,
    parse_topics,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# docs/indexes/by-language.md lists languages in this order; distinct from
# repo_lib.LANGUAGES, whose dict order is about (folder, ext) convenience.
LANGUAGE_INDEX_ORDER = ("C++", "Python", "JavaScript", "C", "Rust", "SQL")

TITLE_RE = re.compile(r"^#\s*\d+:\s*(.+)$")


@dataclass(frozen=True)
class Entry:
    id: int
    title: str
    category: str
    difficulty: int
    doc_level: str
    languages: tuple[str, ...]
    topics: tuple[str, ...]
    review: str
    readme: Path


def read_title(readme_text: str) -> str:
    first_line = readme_text.splitlines()[0] if readme_text.strip() else ""
    match = TITLE_RE.match(first_line.strip())
    return match.group(1).strip() if match else "(untitled)"


def collect_entries(root: Path) -> list[Entry]:
    """Every Status: Solved problem, as a flat list sorted by id."""
    entries: list[Entry] = []
    for problem_dir in find_problem_dirs(root):
        readme = problem_dir / "README.md"
        if not readme.is_file():
            continue
        text = readme.read_text(encoding="utf-8")
        meta = parse_metadata(text)
        if meta.get("Status", "").strip().lower() != "solved":
            continue

        primary = find_language(meta.get("Primary Language", ""))
        others = (find_language(name) for name in parse_other_implementations(meta.get("Other Implementations", "")))
        languages = tuple(dict.fromkeys(lang for lang in (primary, *others) if lang))

        topics = tuple(dict.fromkeys(
            resolved for t in parse_topics(meta.get("Topics", "")) if (resolved := find_topic(t))
        ))

        try:
            difficulty = int(meta.get("Difficulty Level", ""))
        except ValueError:
            difficulty = 0

        problem_id_raw = meta.get("Problem ID") or problem_dir.name.split("-", 1)[0]
        try:
            problem_id = int(problem_id_raw)
        except ValueError:
            continue

        entries.append(Entry(
            id=problem_id,
            title=read_title(text),
            category=meta.get("Category", ""),
            difficulty=difficulty,
            doc_level=meta.get("Documentation Level", ""),
            languages=languages,
            topics=topics,
            review=meta.get("Review Priority", ""),
            readme=readme,
        ))
    return sorted(entries, key=lambda e: e.id)


def link(entry: Entry, from_dir: Path) -> str:
    return Path(os.path.relpath(entry.readme, start=from_dir)).as_posix()


def render_tracker(entries: list[Entry], out_path: Path) -> str:
    lines = [
        "# Solved Problems",
        "",
        "| ID | Title | Category | Difficulty | Doc Level | Languages | Topics | Review |",
        "|----|-------|----------|------------|-----------|-----------|--------|--------|",
    ]
    for e in entries:
        lines.append(
            f"| {e.id} | [{e.title}]({link(e, out_path.parent)}) | {e.category} | {e.difficulty} | "
            f"{e.doc_level} | {', '.join(e.languages)} | {', '.join(e.topics)} | {e.review} |"
        )
    return "\n".join(lines) + "\n"


def render_grouped(
    title: str,
    intro: str,
    groups: list[str],
    bucket_of: Callable[[Entry], list[str]],
    entries: list[Entry],
    out_path: Path,
) -> str:
    """One `## <group>` heading per item in `groups`, in that order."""
    by_group: dict[str, list[Entry]] = {g: [] for g in groups}
    for entry in entries:
        for g in bucket_of(entry):
            if g in by_group:
                by_group[g].append(entry)

    lines = [f"# {title}", "", intro]
    for g in groups:
        lines += ["", f"## {g}", ""]
        items = by_group[g]
        lines.append("_No entries yet._" if not items else "\n".join(
            f"- [{e.id}: {e.title}]({link(e, out_path.parent)})" for e in items
        ))
    return "\n".join(lines) + "\n"


def build_files(root: Path, entries: list[Entry]) -> dict[Path, str]:
    tracker_path = root / "trackers" / "solved-problems.md"
    category_path = root / "docs" / "indexes" / "by-category.md"
    difficulty_path = root / "docs" / "indexes" / "by-difficulty.md"
    language_path = root / "docs" / "indexes" / "by-language.md"
    topic_path = root / "docs" / "indexes" / "by-topic.md"

    return {
        tracker_path: render_tracker(entries, tracker_path),
        category_path: render_grouped(
            "Index by Category",
            "This file organizes solved problems by Beecrowd category.",
            list(CATEGORIES),
            lambda e: [e.category] if e.category in CATEGORIES else [],
            entries,
            category_path,
        ),
        difficulty_path: render_grouped(
            "Index by Difficulty",
            "This file organizes solved problems by Beecrowd difficulty level.",
            [f"Level {n}" for n in range(1, 11)],
            lambda e: [f"Level {e.difficulty}"] if 1 <= e.difficulty <= 10 else [],
            entries,
            difficulty_path,
        ),
        language_path: render_grouped(
            "Index by Language",
            "This file organizes solved problems by implementation language.",
            list(LANGUAGE_INDEX_ORDER),
            lambda e: list(e.languages),
            entries,
            language_path,
        ),
        topic_path: render_grouped(
            "Index by Topic",
            "This file organizes solved problems by reusable topics and patterns.",
            list(TOPICS),
            lambda e: list(e.topics),
            entries,
            topic_path,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the tracker and docs indexes from problem metadata.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true", help="exit 1 on drift instead of writing")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    entries = collect_entries(root)
    files = build_files(root, entries)

    drift: list[Path] = []
    for path, content in files.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current != content:
            drift.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    if args.check:
        for path in drift:
            print(f"out of date: {path.relative_to(root).as_posix()}")
        if drift:
            print(f"\n{len(drift)} file(s) out of date. Run: python scripts/sync_index.py")
            return 1
        print(f"Indexes up to date ({len(entries)} solved problem(s)).")
        return 0

    for path in drift:
        print(f"updated: {path.relative_to(root).as_posix()}")
    if not drift:
        print("Already up to date.")
    print(f"{len(entries)} solved problem(s) indexed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
