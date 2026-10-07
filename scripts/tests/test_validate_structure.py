"""Tests for scripts/validate_structure.py (run: python -m unittest discover -s scripts/tests)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import validate_structure as vs  # noqa: E402
from fixtures import quiet  # noqa: E402

README = """# 1001 — Hello World

## Link
https://example.invalid/1001

## Metadata

- Problem ID: 1001
- Platform: Beecrowd
- Category: Beginner
- Difficulty Level: 1
- Topics: output
- Primary Language: C++
- Other Implementations: None
- Documentation Level: L1
- Status: Solved
- Review Priority: Low

## Status

- [x] Solved
- [ ] Revisit later
"""


class ValidateStructureTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.problem = self.root / "problems" / "1000-1099" / "1001-hello-world"
        (self.problem / "solutions" / "cpp").mkdir(parents=True)
        (self.problem / "README.md").write_text(README, encoding="utf-8")
        (self.problem / "solutions" / "cpp" / "main.cpp").write_text("int main() {}\n", encoding="utf-8")
        (self.problem / "tests").mkdir()
        (self.problem / "tests" / "sample.in").write_text("1\n", encoding="utf-8")
        (self.problem / "tests" / "sample.out").write_text("1\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def messages(self, level: str | None = None) -> list[str]:
        issues = vs.validate_repository(self.root)
        return [i.message for i in issues if level is None or i.level == level]

    def readme_replace(self, old: str, new: str) -> None:
        readme = self.problem / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def assert_error_contains(self, fragment: str) -> None:
        errors = self.messages("error")
        self.assertTrue(any(fragment in m for m in errors), f"no error containing {fragment!r} in {errors}")

    def test_valid_problem_is_clean(self) -> None:
        self.assertEqual(vs.validate_repository(self.root), [])

    def test_empty_solution_is_one_error(self) -> None:
        (self.problem / "solutions" / "cpp" / "main.cpp").write_text("  \n", encoding="utf-8")
        self.assertEqual(self.messages("error"), ["solution file is empty"])

    def test_status_must_match_checkbox(self) -> None:
        self.readme_replace("- [x] Solved", "- [ ] Solved")
        self.assert_error_contains("checkbox is unchecked")

    def test_in_progress_with_checked_box_fails(self) -> None:
        self.readme_replace("Status: Solved", "Status: In Progress")
        self.assert_error_contains("checkbox is checked")

    def test_missing_metadata_field(self) -> None:
        self.readme_replace("- Review Priority: Low\n", "")
        self.assert_error_contains("'Review Priority' is missing")

    def test_invalid_category_and_difficulty(self) -> None:
        self.readme_replace("Category: Beginner", "Category: Magic")
        self.readme_replace("Difficulty Level: 1", "Difficulty Level: 11")
        self.assert_error_contains("Category 'Magic'")
        self.assert_error_contains("Difficulty Level '11'")

    def test_malformed_checkbox(self) -> None:
        self.readme_replace("- [ ] Revisit later", "- [] Revisit later")
        self.assert_error_contains("malformed checkbox")

    def test_unknown_language_folder(self) -> None:
        (self.problem / "solutions" / "cobol").mkdir()
        self.assert_error_contains("unknown language folder")

    def test_undeclared_implementation_is_only_a_warning(self) -> None:
        (self.problem / "solutions" / "python").mkdir()
        (self.problem / "solutions" / "python" / "main.py").write_text("print(1)\n", encoding="utf-8")
        self.assertEqual(self.messages("error"), [])
        self.assertTrue(any("not declared" in m for m in self.messages("warning")))

    def test_declared_other_implementation_must_exist(self) -> None:
        self.readme_replace("Other Implementations: None", "Other Implementations: Rust")
        self.assert_error_contains("Rust is declared")

    def test_bad_slug_and_wrong_range(self) -> None:
        bad = self.root / "problems" / "1000-1099" / "1002-Bad_Slug"
        (bad / "solutions").mkdir(parents=True)
        wrong_range = self.root / "problems" / "2000-2099" / "1003-ok-slug"
        (wrong_range / "solutions").mkdir(parents=True)
        errors = self.messages("error")
        self.assertTrue(any("slug 'Bad_Slug'" in m for m in errors))
        self.assertTrue(any("does not belong in range" in m for m in errors))

    def test_problem_id_must_match_folder(self) -> None:
        self.readme_replace("Problem ID: 1001", "Problem ID: 1002")
        self.assert_error_contains("does not match folder id")

    def test_sql_is_reserved_for_sql_category(self) -> None:
        self.readme_replace("Primary Language: C++", "Primary Language: SQL")
        sql_dir = self.problem / "solutions" / "sql"
        sql_dir.mkdir()
        (sql_dir / "main.sql").write_text("SELECT 1;\n", encoding="utf-8")
        (self.problem / "solutions" / "cpp" / "main.cpp").unlink()
        (self.problem / "solutions" / "cpp").rmdir()
        self.assert_error_contains("SQL is reserved")

    def test_solved_problem_needs_test_cases(self) -> None:
        for leftover in (self.problem / "tests").iterdir():
            leftover.unlink()
        self.assert_error_contains("no test cases")

    def test_unsolved_problem_without_tests_is_only_a_warning(self) -> None:
        for leftover in (self.problem / "tests").iterdir():
            leftover.unlink()
        self.readme_replace("Status: Solved", "Status: In Progress")
        self.readme_replace("- [x] Solved", "- [ ] Solved")
        self.assertEqual(self.messages("error"), [])
        self.assertTrue(any("no test cases" in m for m in self.messages("warning")))

    def test_test_cases_must_come_in_pairs(self) -> None:
        (self.problem / "tests" / "lonely.in").write_text("1\n", encoding="utf-8")
        (self.problem / "tests" / "orphan.out").write_text("1\n", encoding="utf-8")
        self.assert_error_contains("lonely.in has no matching lonely.out")
        self.assert_error_contains("orphan.out has no matching orphan.in")

    def test_strict_mode_fails_on_warnings(self) -> None:
        (self.problem / "solutions" / "python").mkdir()
        (self.problem / "solutions" / "python" / "main.py").write_text("print(1)\n", encoding="utf-8")
        self.assertEqual(quiet(lambda: vs.main(["--root", str(self.root)])), 0)
        self.assertEqual(quiet(lambda: vs.main(["--root", str(self.root), "--strict"])), 1)


if __name__ == "__main__":
    unittest.main()
