"""Helpers shared by the script tests: build tiny throw-away problem folders."""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repo_lib import LANGUAGES  # noqa: E402

README = """# {id} — Fixture

## Link
https://example.invalid/{id}

## Metadata

- Problem ID: {id}
- Platform: Beecrowd
- Category: {category}
- Difficulty Level: 1
- Topics: fixture
- Primary Language: {language}
- Other Implementations: None
- Documentation Level: L1
- Status: {status}
- Review Priority: Low

## Status

- [{box}] Solved
- [ ] Revisit later
"""


def make_problem(
    root: Path,
    folder: str = "python",
    source: str = "print(input())\n",
    cases: dict[str, tuple[str, str]] | None = None,
    problem_id: int = 1001,
    slug: str = "fixture",
    status: str = "Solved",
    category: str = "Beginner",
) -> Path:
    """Create problems/<range>/<id>-<slug>/ with one implementation and its cases."""
    display = next(name for name, (f, _e) in LANGUAGES.items() if f == folder)
    ext = LANGUAGES[display][1]
    start = problem_id // 100 * 100
    problem = root / "problems" / f"{start}-{start + 99}" / f"{problem_id}-{slug}"
    (problem / "solutions" / folder).mkdir(parents=True)
    (problem / "solutions" / folder / f"main.{ext}").write_text(source, encoding="utf-8")
    (problem / "README.md").write_text(
        README.format(
            id=problem_id,
            category=category,
            language=display,
            status=status,
            box="x" if status == "Solved" else " ",
        ),
        encoding="utf-8",
    )
    for name, (given, expected) in (cases if cases is not None else {"sample": ("hello\n", "hello\n")}).items():
        (problem / "tests").mkdir(exist_ok=True)
        # newline="" disables universal-newline translation on write: `given`/`expected`
        # may already contain literal "\r\n" to simulate a CRLF file, and on Windows the
        # default write_text() would double it to "\r\r\n".
        (problem / "tests" / f"{name}.in").write_text(given, encoding="utf-8", newline="")
        (problem / "tests" / f"{name}.out").write_text(expected, encoding="utf-8", newline="")
    return problem


def quiet(function: Callable[[], int]) -> int:
    """Call a script's main() without letting its report clutter the test output."""
    with contextlib.redirect_stdout(io.StringIO()):
        return function()
