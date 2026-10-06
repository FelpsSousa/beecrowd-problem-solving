"""Tests for scripts/check_all.py and the git helpers in repo_lib."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import make_problem, quiet  # noqa: E402

import check_all  # noqa: E402
import repo_lib  # noqa: E402


class ProblemDirsForTest(unittest.TestCase):
    def test_maps_files_to_existing_problem_folders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            problem = make_problem(root)
            files = [
                "problems/1000-1099/1001-fixture/solutions/python/main.py",
                "problems/1000-1099/1001-fixture/README.md",
                "problems/1000-1099/1002-deleted/README.md",
                "docs/workflow.md",
                "problems/README.md",
            ]
            self.assertEqual(repo_lib.problem_dirs_for(root, files), [problem])


@unittest.skipUnless(shutil.which("git"), "git not installed")
class ScopeTest(unittest.TestCase):
    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        make_problem(self.root, problem_id=1001, slug="first")
        make_problem(self.root, problem_id=1002, slug="second")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_since_selects_only_changed_problems(self) -> None:
        main_file = self.root / "problems/1000-1099/1002-second/solutions/python/main.py"
        main_file.write_text("print(input())  # changed\n", encoding="utf-8")
        self.git("commit", "-q", "-am", "change second")
        dirs, infra, label = check_all.select_scope(self.root, staged=False, since="HEAD~1")
        self.assertEqual([d.name for d in dirs or []], ["1002-second"])
        self.assertFalse(infra)
        self.assertIn("1 problem folder", label)

    def test_staged_scope_and_infra_detection(self) -> None:
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "tool.py").write_text("x = 1\n", encoding="utf-8")
        self.git("add", "scripts/tool.py")
        dirs, infra, _ = check_all.select_scope(self.root, staged=True, since=None)
        self.assertEqual(dirs, [])
        self.assertTrue(infra)

    def test_unknown_ref_falls_back_to_everything(self) -> None:
        dirs, infra, label = check_all.select_scope(self.root, staged=False, since="no-such-ref")
        self.assertIsNone(dirs)
        self.assertTrue(infra)
        self.assertIn("whole repository", label)

    def test_end_to_end_pass_and_fail(self) -> None:
        self.assertEqual(quiet(lambda: check_all.main(["--root", str(self.root), "--skip-unit-tests"])), 0)
        (self.root / "problems/1000-1099/1001-first/solutions/python/main.py").write_text("print('wrong')\n", encoding="utf-8")
        self.assertEqual(quiet(lambda: check_all.main(["--root", str(self.root), "--skip-unit-tests"])), 1)

    def test_nothing_changed_means_nothing_to_check(self) -> None:
        self.assertEqual(quiet(lambda: check_all.main(["--root", str(self.root), "--since", "HEAD", "--skip-unit-tests"])), 0)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitignoreTest(unittest.TestCase):
    def test_expected_outputs_are_not_ignored(self) -> None:
        """`*.out` is ignored for compiler output; tests/*.out must stay trackable."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        gitignore = repo_root / ".gitignore"
        if not gitignore.is_file():
            self.skipTest(".gitignore not found")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
            shutil.copy(gitignore, root / ".gitignore")
            case = root / "problems" / "1000-1099" / "1001-x" / "tests"
            case.mkdir(parents=True)
            (case / "sample.out").write_text("1\n", encoding="utf-8")
            (root / "a.out").write_text("binary", encoding="utf-8")
            kept = subprocess.run(["git", "check-ignore", "-q", "problems/1000-1099/1001-x/tests/sample.out"], cwd=root)
            ignored = subprocess.run(["git", "check-ignore", "-q", "a.out"], cwd=root)
            self.assertEqual(kept.returncode, 1, "tests/*.out must not be ignored")
            self.assertEqual(ignored.returncode, 0, "a.out should stay ignored")


if __name__ == "__main__":
    unittest.main()
