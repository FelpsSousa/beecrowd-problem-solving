"""Tests for scripts/new_problem.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import new_problem as np  # noqa: E402
import validate_structure as vs  # noqa: E402


class NewProblemTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def create(self, *args: str) -> int:
        return np.main([*args, "--root", str(self.root)])

    def problem_dir(self, range_name: str, folder_name: str) -> Path:
        return self.root / "problems" / range_name / folder_name

    def test_creates_expected_structure(self) -> None:
        code = self.create(
            "3485", "Divided Class Two",
            "--category", "Data Structures and Libraries",
            "--difficulty", "3",
            "--topics", "binary search tree,recursion",
            "--lang", "cpp",
        )
        self.assertEqual(code, 0)

        problem = self.problem_dir("3400-3499", "3485-divided-class-two")
        readme = (problem / "README.md").read_text(encoding="utf-8")

        self.assertTrue((problem / "solutions" / "cpp" / "main.cpp").is_file())
        self.assertTrue((problem / "tests").is_dir())
        self.assertIn("# 3485: Divided Class Two", readme)
        self.assertIn("- Category: Data Structures and Libraries", readme)
        self.assertIn("- Difficulty Level: 3", readme)
        self.assertIn("- Topics: binary search tree, recursion", readme)
        self.assertIn("- Primary Language: C++", readme)
        self.assertIn("- Status: In Progress", readme)
        self.assertIn("- [ ] Solved", readme)
        self.assertNotIn("- [x] Solved", readme)
        self.assertIn("solutions/cpp/main.cpp", readme)

    def test_range_folder_computed_correctly(self) -> None:
        self.create(
            "1050", "Example", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "python",
        )
        self.assertTrue(self.problem_dir("1000-1099", "1050-example").is_dir())

    def test_refuses_to_overwrite_existing_folder(self) -> None:
        args = (
            "3485", "Divided Class Two", "--category", "Data Structures and Libraries",
            "--difficulty", "3", "--topics", "trees", "--lang", "cpp",
        )
        self.assertEqual(self.create(*args), 0)
        self.assertEqual(self.create(*args), 1)

    def test_sql_requires_sql_category(self) -> None:
        code = self.create(
            "2700", "Some Query", "--category", "Beginner", "--difficulty", "2",
            "--topics", "aggregation", "--lang", "sql",
        )
        self.assertEqual(code, 1)

    def test_sql_category_requires_sql_language(self) -> None:
        code = self.create(
            "2700", "Some Query", "--category", "SQL", "--difficulty", "2",
            "--topics", "aggregation", "--lang", "cpp",
        )
        self.assertEqual(code, 1)

    def test_sql_problem_created_correctly(self) -> None:
        code = self.create(
            "2700", "Some Query", "--category", "SQL", "--difficulty", "2",
            "--topics", "aggregation", "--lang", "sql",
        )
        self.assertEqual(code, 0)
        problem = self.problem_dir("2700-2799", "2700-some-query")
        self.assertTrue((problem / "solutions" / "sql" / "main.sql").is_file())

    def test_unknown_language_rejected(self) -> None:
        code = self.create(
            "3486", "Another One", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "cobol",
        )
        self.assertEqual(code, 1)

    def test_non_ascii_title_requires_explicit_slug(self) -> None:
        code = self.create(
            "3487", "Divisão de Turma", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "cpp",
        )
        self.assertEqual(code, 1)

    def test_explicit_slug_overrides_derivation(self) -> None:
        code = self.create(
            "3487", "Divisão de Turma", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "cpp", "--slug", "class-split",
        )
        self.assertEqual(code, 0)
        self.assertTrue(self.problem_dir("3400-3499", "3487-class-split").is_dir())

    def test_level_l3_also_creates_deep_dive(self) -> None:
        self.create(
            "3488", "Hard One", "--category", "Graphs", "--difficulty", "8",
            "--topics", "flood fill", "--lang", "cpp", "--level", "L3",
        )
        problem = self.problem_dir("3400-3499", "3488-hard-one")
        self.assertIn("- Documentation Level: L3", (problem / "README.md").read_text(encoding="utf-8"))
        deep_dive = (problem / "deep-dive.md").read_text(encoding="utf-8")
        self.assertIn("3488", deep_dive)
        self.assertIn("Hard One", deep_dive)

    def test_notes_flag_creates_notes_file(self) -> None:
        self.create(
            "3489", "Needs Notes", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "cpp", "--notes",
        )
        self.assertTrue(self.problem_dir("3400-3499", "3489-needs-notes").joinpath("notes.md").is_file())

    def test_output_validates_with_only_a_warning(self) -> None:
        self.create(
            "3490", "Fresh Scaffold", "--category", "Beginner", "--difficulty", "1",
            "--topics", "io", "--lang", "cpp",
        )
        issues = vs.validate_repository(self.root)
        errors = [i for i in issues if i.level == "error"]
        self.assertEqual(errors, [], errors)


if __name__ == "__main__":
    unittest.main()
