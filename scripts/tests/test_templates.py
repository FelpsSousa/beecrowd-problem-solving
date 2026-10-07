"""The solution templates must themselves satisfy the standards they teach."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lint_solutions as lint  # noqa: E402
import run_tests as rt  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent.parent.parent / "templates" / "solutions"
FOLDERS = {"cpp": "cpp", "c": "c", "py": "python", "js": "javascript", "rs": "rust", "sql": "sql"}


@unittest.skipUnless(TEMPLATES.is_dir(), "templates/solutions not found")
class TemplatesTest(unittest.TestCase):
    def test_every_language_has_a_template(self) -> None:
        self.assertEqual({p.suffix.lstrip(".") for p in TEMPLATES.glob("main.*")}, set(FOLDERS))

    def test_templates_are_lint_clean(self) -> None:
        for path in TEMPLATES.glob("main.*"):
            folder = FOLDERS[path.suffix.lstrip(".")]
            issues = lint.lint_text(path.read_text(encoding="utf-8"), folder, path.name)
            self.assertEqual(issues, [], f"{path.name}: {issues}")

    def test_templates_build_and_echo_their_input(self) -> None:
        options = rt.Options(sanitize=True, werror=True)
        for path in TEMPLATES.glob("main.*"):
            folder = FOLDERS[path.suffix.lstrip(".")]
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
                prepared = rt.prepare(folder, path, Path(tmp), options)
                if prepared.skip_reason:
                    continue  # toolchain not installed here, or no SQL runner
                self.assertIsNone(prepared.error, f"{path.name}: {prepared.error}")
                given, expected = Path(tmp) / "in", Path(tmp) / "out"
                given.write_text("42\n", encoding="utf-8")
                expected.write_text("42\n", encoding="utf-8")
                status, detail, _ = rt.run_case(prepared.command or [], given, expected, options)
                self.assertEqual((status, detail), ("PASS", ""), path.name)


if __name__ == "__main__":
    unittest.main()
