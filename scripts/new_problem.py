#!/usr/bin/env python3
"""Scaffold a new problem folder with the right structure and metadata.

Usage:
    python scripts/new_problem.py 3485 "Some Title" \\
        --category "Data Structures and Libraries" --difficulty 3 \\
        --topics "binary search tree,recursion" --lang cpp

    python scripts/new_problem.py 2602 "Total Spent" --category SQL \\
        --difficulty 2 --topics aggregation --lang sql --slug total-spent

Creates problems/<range>/<id>-<slug>/ with a README.md built from the right
L1/L2 template (L3 also gets deep-dive.md), a solutions/<lang>/main.<ext>
skeleton copied from templates/solutions/, and an empty tests/ folder.

Only the mechanical metadata (id, title, link, category, difficulty, topics,
language, status) is filled in. The authorial sections (summary, approach,
what you learned...) are left as the template's own {placeholders} for you
to write after actually solving the problem.

Exit code: 0 = created, 1 = invalid input or the folder already exists.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from repo_lib import CATEGORIES, DOC_LEVELS, LANGUAGES, PRIORITIES, SLUG_RE, find_language

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "templates"


def slugify(title: str) -> str:
    """"Binary Search!" -> "binary-search". Non-English titles need --slug."""
    text = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return text.strip("-")


def resolve_slug(title: str, override: str | None) -> str:
    if override:
        slug = override.strip().lower()
    else:
        # A non-ASCII title (accents, other scripts) would have its special
        # characters silently dropped by slugify(), producing a mangled slug
        # instead of an error, so this case always needs an explicit --slug.
        if not title.isascii():
            raise ValueError(f"title '{title}' is not in English; pass --slug explicitly")
        slug = slugify(title)
    if not SLUG_RE.match(slug):
        raise ValueError(
            f"slug '{slug}' is not lowercase-english-hyphenated; pass --slug explicitly"
        )
    return slug


def range_folder(problem_id: int) -> str:
    start = problem_id // 100 * 100
    return f"{start:04d}-{start + 99:04d}"


def fill_metadata(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def fill_topics(text: str, topics: list[str]) -> str:
    return text.replace("{topic-1}, {topic-2}", ", ".join(topics))


def force_unsolved_status(text: str) -> str:
    """Scaffolding happens before the problem is solved, whatever the template's own example says."""
    text = re.sub(r"(?m)^- Status:.*$", "- Status: In Progress", text, count=1)
    return text.replace("- [x] Solved", "- [ ] Solved")


def build_readme(level: str, values: dict[str, str], topics: list[str]) -> str:
    template_name = "problem-readme-l1.md" if level == "L1" else "problem-readme-l2.md"
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    text = fill_topics(text, topics)
    text = fill_metadata(text, values)
    text = force_unsolved_status(text)
    if level != "L1" and level != "L2":
        text = text.replace("- Documentation Level: L2", f"- Documentation Level: {level}")
    return text


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a new problem folder.")
    parser.add_argument("id", type=int, help="Beecrowd problem id, e.g. 3485")
    parser.add_argument("title", help="problem title, used for the README heading")
    parser.add_argument("--category", required=True, choices=CATEGORIES)
    parser.add_argument("--difficulty", required=True, type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--topics", required=True, help="comma separated, e.g. 'binary search,recursion'")
    parser.add_argument("--lang", required=True, dest="language", help="primary language, e.g. cpp, C++, python")
    parser.add_argument("--slug", help="override the slug derived from the title (needed for non-English titles)")
    parser.add_argument("--level", default="L1", choices=DOC_LEVELS)
    parser.add_argument("--priority", default="Medium", choices=PRIORITIES)
    parser.add_argument("--link", help="defaults to the standard Beecrowd URL for this id")
    parser.add_argument("--notes", action="store_true", help="also scaffold notes.md")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root: Path = args.root.resolve()

    display = find_language(args.language)
    if display is None:
        print(f"error: unknown language '{args.language}' (known: {', '.join(LANGUAGES)})", file=sys.stderr)
        return 1
    folder, ext = LANGUAGES[display]

    category = args.category
    if (display == "SQL") != (category == "SQL"):
        print("error: SQL is reserved for the SQL category, and the SQL category must use SQL", file=sys.stderr)
        return 1

    try:
        slug = resolve_slug(args.title, args.slug)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    problem_dir = root / "problems" / range_folder(args.id) / f"{args.id}-{slug}"
    if problem_dir.exists():
        print(f"error: {problem_dir.relative_to(root)} already exists", file=sys.stderr)
        return 1

    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    link = args.link or f"https://judge.beecrowd.com/en/problems/view/{args.id}"
    values = {
        "id": str(args.id),
        "title": args.title,
        "problem-link": link,
        "category": category,
        "difficulty-level": str(args.difficulty),
        "primary-language": display,
        "low-medium-high": args.priority,
        "language-1": display,
        "language-folder": folder,
        "ext": ext,
    }

    readme = build_readme(args.level, values, topics)

    (problem_dir / "solutions" / folder).mkdir(parents=True)
    (problem_dir / "tests").mkdir()
    (problem_dir / "README.md").write_text(readme, encoding="utf-8")

    skeleton = (TEMPLATES / "solutions" / f"main.{ext}").read_text(encoding="utf-8")
    (problem_dir / "solutions" / folder / f"main.{ext}").write_text(skeleton, encoding="utf-8")

    if args.level == "L3":
        deep_dive = fill_metadata(
            (TEMPLATES / "problem-deep-dive-l3.md").read_text(encoding="utf-8"),
            {"id": values["id"], "title": values["title"]},
        )
        (problem_dir / "deep-dive.md").write_text(deep_dive, encoding="utf-8")

    if args.notes:
        (problem_dir / "notes.md").write_text(
            (TEMPLATES / "notes-template.md").read_text(encoding="utf-8"), encoding="utf-8"
        )

    rel = problem_dir.relative_to(root).as_posix()
    print(f"Created {rel}")
    print("  README.md:                    fill in the {...} sections after solving")
    print(f"  solutions/{folder}/main.{ext}: replace the skeleton with the real solution")
    print("  tests/:                        add sampleN.in/.out and edge-*.in/.out")
    print(f"\nValidate with: python scripts/validate_structure.py {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
