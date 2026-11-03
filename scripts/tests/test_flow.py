"""Tests for scripts/flow.py (message drafting only; git and gh are never called)."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flow  # noqa: E402
from fixtures import make_problem  # noqa: E402

README_PATH = "problems/1000-1099/{id}-fixture/README.md"
SOURCE_PATH = "problems/1000-1099/{id}-fixture/solutions/cpp/main.cpp"


class BranchTest(unittest.TestCase):
    def test_slug_and_type(self) -> None:
        self.assertEqual(flow.branch_name("feat", "Flow CLI, v1!"), "feat/flow-cli-v1")
        self.assertEqual(flow.branch_name("migration", "1000 1010"), "migration/1000-1010")

    def test_unknown_type_is_refused(self) -> None:
        with self.assertRaises(flow.FlowError):
            flow.branch_name("feature", "x")

    def test_empty_description_is_refused(self) -> None:
        with self.assertRaises(flow.FlowError):
            flow.branch_name("docs", "!!!")


class ParseTest(unittest.TestCase):
    def test_name_status(self) -> None:
        changes = flow.parse_name_status(["A\tnew.md", "M\told.md", "R100\ta.md\tb.md", "D\tgone.md"])
        self.assertEqual(
            [(c.status, c.path) for c in changes],
            [("added", "new.md"), ("modified", "old.md"), ("renamed", "b.md"), ("deleted", "gone.md")],
        )

    def test_type_and_scope(self) -> None:
        self.assertEqual(flow.type_and_scope("feat/flow-cli", ["scripts/flow.py", "scripts/tests/t.py"]), ("feat", "scripts"))
        self.assertEqual(flow.type_and_scope("docs/x", ["docs/a.md", "README.md"]), ("docs", ""))
        self.assertEqual(flow.type_and_scope("migration/1000-1010", ["scripts/a.py"]), ("feat", "migration"))
        self.assertEqual(flow.type_and_scope("ci/pin", [".github/workflows/ci.yml"]), ("ci", "ci"))
        self.assertEqual(flow.type_and_scope("wip", ["docs/a.md"]), ("chore", "docs"))


class ProblemTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def changes(self, *ids: int, status: str = "added") -> list[flow.Change]:
        found: list[flow.Change] = []
        for problem_id in ids:
            found.append(flow.Change(status, README_PATH.format(id=problem_id)))
            found.append(flow.Change(status, SOURCE_PATH.format(id=problem_id)))
        return found

    def test_new_problem_subject_and_body(self) -> None:
        make_problem(self.root, folder="cpp", source="int main() {}\n", problem_id=1001)
        changes = self.changes(1001)
        problems, new_ids = flow.problems_in(self.root, changes)
        subject = flow.derive_subject("problem/1001", problems, new_ids)
        self.assertEqual(subject, "add 1001 fixture")
        message = flow.commit_message(flow.format_header("feat", "problems", subject), problems, changes)
        self.assertTrue(message.startswith("feat(problems): add 1001 fixture\n\nFiles: 2 added."))
        self.assertIn("- 1001 Fixture: C++, Beginner, level 1, L1, 1 test case(s), status Solved", message)

    def test_modified_problem_says_update(self) -> None:
        make_problem(self.root, folder="cpp", source="int main() {}\n", problem_id=1001)
        problems, new_ids = flow.problems_in(self.root, self.changes(1001, status="modified"))
        self.assertEqual(flow.derive_subject("fix/1001", problems, new_ids), "update 1001 fixture")

    def test_migration_subject_lists_or_summarises_ids(self) -> None:
        for problem_id in (1001, 1002, 1003, 1004):
            make_problem(self.root, folder="cpp", source="int main() {}\n", problem_id=problem_id)
        problems, new_ids = flow.problems_in(self.root, self.changes(1001, 1002, 1003, 1004))
        self.assertEqual(
            flow.derive_subject("migration/1000-1010", problems, new_ids),
            "migrate 4 problems (1001 to 1004) from the legacy repositories",
        )
        self.assertEqual(
            flow.derive_subject("migration/1000-1010", problems[:2], new_ids),
            "migrate 1001, 1002 from the legacy repositories",
        )

    def test_removed_problem(self) -> None:
        problems, new_ids = flow.problems_in(self.root, self.changes(1001, status="deleted"))
        self.assertTrue(problems[0].removed)
        self.assertEqual(flow.derive_subject("chore/x", problems, new_ids), "remove 1001")

    def test_no_problem_means_no_subject(self) -> None:
        self.assertIsNone(flow.derive_subject("feat/x", [], set()))


class HeaderTest(unittest.TestCase):
    def test_lowercases_first_letter(self) -> None:
        self.assertEqual(flow.format_header("docs", "", "Fix typo"), "docs: fix typo")

    def test_too_long_is_refused(self) -> None:
        with self.assertRaises(flow.FlowError):
            flow.format_header("feat", "scripts", "x" * 80)


class PullRequestTest(unittest.TestCase):
    def test_title_from_single_commit(self) -> None:
        self.assertEqual(flow.pr_title("feat/flow", ["feat(scripts): add the flow cli"]), "feat(scripts): add the flow cli")

    def test_title_from_branch(self) -> None:
        self.assertEqual(flow.pr_title("docs/adr-rust-on-judge", ["a", "b"]), "docs: adr rust on judge")
        self.assertEqual(flow.pr_title("migration/1000-1010", ["a", "b"]), "feat(migration): migrate 1000 to 1010")

    def test_body_sections(self) -> None:
        problem = flow.ProblemInfo(1001, "Fixture", "Beginner", "1", "C++", "L1", "Solved", 2)
        changes = [flow.Change("added", README_PATH.format(id=1001))]
        body = flow.pr_body("migration/1000-1010", ["feat(migration): x"], [problem], changes, "passed")
        self.assertIn("| 1001 | Fixture | Beginner | 1 | C++ | L1 | 2 | Solved |", body)
        self.assertIn("## Migration checklist", body)
        self.assertIn("`python scripts/check_all.py`: passed", body)
        plain = flow.pr_body("feat/flow", ["feat(scripts): x"], [], changes, "passed")
        self.assertNotIn("## Problems", plain)
        self.assertNotIn("## Migration checklist", plain)


class RankingTest(unittest.TestCase):
    def test_line(self) -> None:
        self.assertEqual(flow.ranking_line(dt.date(2026, 11, 2), 367.7, 20195, 1), "| 2026-11-02 | 367.70 | 20195 | 1 |\n")


class CliTest(unittest.TestCase):
    def test_refusal_exits_with_one(self) -> None:
        import contextlib
        import io

        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(flow.main(["start", "feature", "x"]), 1)
        self.assertIn("unknown branch type", err.getvalue())


if __name__ == "__main__":
    unittest.main()
