"""Tests for scripts/sync_index.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sync_index as si  # noqa: E402

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
- Documentation Level: L1
- Status: {status}
- Review Priority: Medium

## Status

- [{box}] Solved
- [ ] Revisit later
"""


class SyncIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for name in ("trackers", "docs/indexes"):
            (self.root / name).mkdir(parents=True)

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
        status: str = "Solved",
        slug: str | None = None,
    ) -> None:
        slug = slug or title.lower().replace(" ", "-")
        start = problem_id // 100 * 100
        problem = self.root / "problems" / f"{start:04d}-{start + 99:04d}" / f"{problem_id}-{slug}"
        (problem / "solutions" / "cpp").mkdir(parents=True)
        (problem / "README.md").write_text(
            README.format(
                id=problem_id, title=title, category=category, difficulty=difficulty,
                topics=topics, language=language, others=others, status=status,
                box="x" if status == "Solved" else " ",
            ),
            encoding="utf-8",
        )

    def read(self, relative: str) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def test_no_solved_problems_is_the_empty_state(self) -> None:
        self.add_problem(1001, status="In Progress")
        si.main(["--root", str(self.root)])

        tracker = self.read("trackers/solved-problems.md")
        self.assertNotIn("1001", tracker)

        category = self.read("docs/indexes/by-category.md")
        self.assertIn("_No entries yet._", category)
        self.assertNotIn("1001", category)

    def test_solved_problem_appears_everywhere_it_should(self) -> None:
        self.add_problem(
            3485, title="Example Two", category="Graphs", difficulty=6,
            topics="Graphs, Simulation", language="C++",
        )
        si.main(["--root", str(self.root)])

        tracker = self.read("trackers/solved-problems.md")
        self.assertIn("| 3485 |", tracker)
        self.assertIn("[Example Two]", tracker)
        self.assertIn("Graphs, Simulation", tracker)

        category = self.read("docs/indexes/by-category.md")
        self.assertIn("## Graphs\n\n- [3485: Example Two]", category)

        difficulty = self.read("docs/indexes/by-difficulty.md")
        self.assertIn("## Level 6\n\n- [3485: Example Two]", difficulty)

        language = self.read("docs/indexes/by-language.md")
        self.assertIn("## C++\n\n- [3485: Example Two]", language)

        topic = self.read("docs/indexes/by-topic.md")
        self.assertIn("## Graphs\n\n- [3485: Example Two]", topic)
        self.assertIn("## Simulation\n\n- [3485: Example Two]", topic)

    def test_other_implementations_add_extra_language_entries(self) -> None:
        self.add_problem(3486, title="Dual", language="C", others="Rust")
        si.main(["--root", str(self.root)])

        language = self.read("docs/indexes/by-language.md")
        self.assertIn("## C\n\n- [3486: Dual]", language)
        self.assertIn("## Rust\n\n- [3486: Dual]", language)

    def test_links_resolve_relative_to_each_file(self) -> None:
        self.add_problem(3487, title="Linked")
        si.main(["--root", str(self.root)])

        tracker = self.read("trackers/solved-problems.md")
        self.assertIn("](../problems/3400-3499/3487-linked/README.md)", tracker)

        category = self.read("docs/indexes/by-category.md")
        self.assertIn("](../../problems/3400-3499/3487-linked/README.md)", category)

    def test_entries_sorted_by_id(self) -> None:
        self.add_problem(3490, title="Second")
        self.add_problem(1001, title="First")
        si.main(["--root", str(self.root)])
        tracker = self.read("trackers/solved-problems.md")
        self.assertLess(tracker.index("1001"), tracker.index("3490"))

    def test_check_mode_reports_drift_without_writing(self) -> None:
        self.add_problem(3491, title="Drift")
        code = si.main(["--root", str(self.root), "--check"])
        self.assertEqual(code, 1)
        self.assertFalse((self.root / "trackers" / "solved-problems.md").is_file())

    def test_check_mode_is_clean_after_a_real_run(self) -> None:
        self.add_problem(3492, title="Settled")
        si.main(["--root", str(self.root)])
        self.assertEqual(si.main(["--root", str(self.root), "--check"]), 0)

    def test_creates_missing_parent_directories(self) -> None:
        bare_tmp = tempfile.TemporaryDirectory()
        try:
            bare_root = Path(bare_tmp.name)
            start = 3494 // 100 * 100
            problem = bare_root / "problems" / f"{start:04d}-{start + 99:04d}" / "3494-bare"
            (problem / "solutions" / "cpp").mkdir(parents=True)
            (problem / "README.md").write_text(
                README.format(
                    id=3494, title="Bare", category="Beginner", difficulty=1,
                    topics="Input / Output", language="C++", others="None",
                    status="Solved", box="x",
                ),
                encoding="utf-8",
            )
            self.assertEqual(si.main(["--root", str(bare_root)]), 0)
            self.assertTrue((bare_root / "trackers" / "solved-problems.md").is_file())
        finally:
            bare_tmp.cleanup()

    def test_rerun_is_idempotent(self) -> None:
        self.add_problem(3493, title="Stable")
        si.main(["--root", str(self.root)])
        first = self.read("docs/indexes/by-topic.md")
        si.main(["--root", str(self.root)])
        second = self.read("docs/indexes/by-topic.md")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
