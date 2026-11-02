"""Tests for scripts/generate_views.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate_views as gv  # noqa: E402
from fixtures import quiet  # noqa: E402
from sync_index import collect_entries  # noqa: E402

README = """# {id}: {title}

## Link
https://example.invalid/{id}

## Metadata

- Problem ID: {id}
- Platform: Beecrowd
- Category: {category}
- Difficulty Level: {difficulty}
- Topics: {topics}
- Primary Language: {language}
- Other Implementations: {others}
- Documentation Level: {level}
- Status: {status}
- Review Priority: {priority}

## Status

- [{box}] Solved
- [ ] Revisit later
"""


class GenerateViewsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add_problem(
        self,
        problem_id: int,
        title: str = "Example",
        category: str = "Beginner",
        difficulty: int = 1,
        topics: str = "Input / Output",
        language: str = "C++",
        others: str = "None",
        level: str = "L1",
        status: str = "Solved",
        priority: str = "Medium",
        slug: str | None = None,
    ) -> None:
        slug = slug or title.lower().replace(" ", "-")
        start = problem_id // 100 * 100
        problem = self.root / "problems" / f"{start:04d}-{start + 99:04d}" / f"{problem_id}-{slug}"
        (problem / "solutions" / "cpp").mkdir(parents=True)
        (problem / "README.md").write_text(
            README.format(
                id=problem_id, title=title, category=category, difficulty=difficulty,
                topics=topics, language=language, others=others, level=level,
                status=status, priority=priority, box="x" if status == "Solved" else " ",
            ),
            encoding="utf-8",
        )

    def dashboard(self, markdown: bool = False) -> str:
        entries = collect_entries(self.root)
        total = len(list((self.root / "problems").rglob("README.md")))
        render = gv.render_markdown if markdown else gv.render_text
        return render(total, entries)

    def test_zero_solved_shows_total_folders(self) -> None:
        self.add_problem(1001, status="In Progress")
        text = self.dashboard()
        self.assertIn("Solved: 0 of 1 problem folder(s) tracked", text)

    def test_counts_reflect_a_solved_problem(self) -> None:
        self.add_problem(
            3485, title="Graph One", category="Graphs", difficulty=7,
            topics="Graphs, Simulation", language="C++", level="L3", priority="High",
        )
        text = self.dashboard()
        self.assertIn("Solved: 1 of 1 problem folder(s) tracked", text)
        self.assertIn("Graphs", text)
        self.assertIn("Level 7", text)
        self.assertIn("L3", text)
        self.assertIn("High", text)

    def test_zero_count_groups_are_still_listed(self) -> None:
        self.add_problem(1001)
        text = self.dashboard()
        self.assertIn("SQL", text)  # a category with zero entries, listed with count 0

    def test_other_implementations_counted_in_each_language(self) -> None:
        self.add_problem(3486, title="Dual", language="C", others="Rust")
        text = self.dashboard()
        lines = {line.strip() for line in text.splitlines()}
        self.assertTrue(any(line.startswith("C ") and line.endswith("1") for line in lines))
        self.assertTrue(any(line.startswith("Rust") and line.endswith("1") for line in lines))

    def test_markdown_output_is_a_table(self) -> None:
        self.add_problem(3487, title="Tabled")
        text = self.dashboard(markdown=True)
        self.assertIn("| Category | Count |", text)
        self.assertIn("|---|---|", text)

    def test_main_runs_without_writing_files(self) -> None:
        self.add_problem(3488, title="Cli")
        code = quiet(lambda: gv.main(["--root", str(self.root)]))
        self.assertEqual(code, 0)
        tracked_before = sorted(p.name for p in (self.root / "problems").rglob("*") if p.is_file())
        quiet(lambda: gv.main(["--root", str(self.root), "--markdown"]))
        tracked_after = sorted(p.name for p in (self.root / "problems").rglob("*") if p.is_file())
        self.assertEqual(tracked_before, tracked_after)


if __name__ == "__main__":
    unittest.main()
