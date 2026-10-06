"""Tests for scripts/run_tests.py (toolchain-dependent cases are skipped when absent)."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import make_problem, quiet  # noqa: E402

import run_tests as rt  # noqa: E402


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


class RunTestsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_problem(self, problem: Path, **options: object) -> list[rt.Result]:
        return rt.run_problem(problem, None, rt.Options(**options))  # type: ignore[arg-type]

    def statuses(self, results: list[rt.Result]) -> list[str]:
        return [r.status for r in results if r.case != "build"]

    def test_python_pass(self) -> None:
        problem = make_problem(self.root)
        self.assertEqual(self.statuses(self.run_problem(problem)), ["PASS"])

    def test_wrong_answer_reports_first_difference(self) -> None:
        problem = make_problem(self.root, cases={"c": ("hello\n", "bye\n")})
        (result,) = self.run_problem(problem)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("line 1: expected 'bye', got 'hello'", result.detail)

    def test_runtime_error_is_a_failure(self) -> None:
        problem = make_problem(self.root, source="import sys\nsys.exit(3)\n")
        (result,) = self.run_problem(problem)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("exit code 3", result.detail)

    def test_timeout_is_a_failure(self) -> None:
        problem = make_problem(self.root, source="import time\ntime.sleep(5)\n")
        (result,) = self.run_problem(problem, timeout=0.5)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("time limit", result.detail)

    def test_trailing_space_is_strict_by_default_and_ignored_when_lenient(self) -> None:
        problem = make_problem(self.root, source="print('1 ')\n", cases={"c": ("", "1\n")})
        self.assertEqual(self.statuses(self.run_problem(problem)), ["FAIL"])
        self.assertEqual(self.statuses(self.run_problem(problem, lenient=True)), ["PASS"])

    def test_crlf_and_final_newlines_are_normalized(self) -> None:
        problem = make_problem(self.root, source="print('a')\nprint('b')\n", cases={"c": ("", "a\r\nb\r\n\r\n")})
        self.assertEqual(self.statuses(self.run_problem(problem)), ["PASS"])

    def test_missing_expected_output_fails(self) -> None:
        problem = make_problem(self.root)
        (problem / "tests" / "sample.out").unlink()
        (result,) = self.run_problem(problem)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("missing expected output", result.detail)

    def test_no_cases_is_a_skip(self) -> None:
        problem = make_problem(self.root, cases={})
        (result,) = self.run_problem(problem)
        self.assertEqual((result.status, result.detail), ("SKIP", "no test cases"))

    def test_sql_is_skipped_without_counting_as_missing_toolchain(self) -> None:
        problem = make_problem(self.root, folder="sql", source="SELECT 1;\n", category="SQL")
        (result,) = self.run_problem(problem)
        self.assertEqual(result.status, "SKIP")
        self.assertFalse(result.missing_tool)

    @unittest.skipUnless(have("g++"), "g++ not installed")
    def test_cpp_pass_compile_error_and_werror(self) -> None:
        echo = "#include <iostream>\nint main() { int x; std::cin >> x; std::cout << x << '\\n'; }\n"
        ok = make_problem(self.root, folder="cpp", source=echo, cases={"c": ("7\n", "7\n")}, problem_id=1001)
        self.assertEqual(self.statuses(self.run_problem(ok)), ["PASS"])

        broken = make_problem(self.root, folder="cpp", source="int main() { return }\n", problem_id=1002, slug="broken")
        (result,) = self.run_problem(broken)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("compilation failed", result.detail)

        noisy_source = "#include <iostream>\nint main() { int unused = 0; std::cout << 1 << '\\n'; }\n"
        noisy = make_problem(self.root, folder="cpp", source=noisy_source, cases={"c": ("", "1\n")}, problem_id=1003, slug="noisy")
        self.assertEqual(self.statuses(self.run_problem(noisy)), ["PASS"])
        (strict_result,) = self.run_problem(noisy, werror=True)
        self.assertEqual(strict_result.status, "FAIL")

    @unittest.skipUnless(have("g++"), "g++ not installed")
    def test_sanitizer_catches_out_of_bounds(self) -> None:
        source = "#include <iostream>\n#include <vector>\nint main() { std::vector<int> v(3); std::cout << v[std::cin.get() == 'x' ? 3 : 10] << '\\n'; }\n"
        problem = make_problem(self.root, folder="cpp", source=source, cases={"c": ("x", "0\n")})
        (result,) = self.run_problem(problem, sanitize=True)
        if result.missing_tool:
            self.skipTest("ASan/UBSan runtime not installed for this compiler")
        self.assertEqual(result.status, "FAIL")

    @unittest.skipUnless(have("gcc"), "gcc not installed")
    def test_c_pass(self) -> None:
        source = '#include <stdio.h>\nint main(void) { int x; if (scanf("%d", &x) == 1) printf("%d\\n", x); return 0; }\n'
        problem = make_problem(self.root, folder="c", source=source, cases={"c": ("5\n", "5\n")})
        self.assertEqual(self.statuses(self.run_problem(problem)), ["PASS"])

    @unittest.skipUnless(have("node"), "node not installed")
    def test_javascript_pass(self) -> None:
        source = '"use strict";\nconsole.log(require("fs").readFileSync(0, "utf8").trim());\n'
        problem = make_problem(self.root, folder="javascript", source=source)
        self.assertEqual(self.statuses(self.run_problem(problem)), ["PASS"])

    @unittest.skipUnless(have("rustc"), "rustc not installed")
    def test_rust_pass(self) -> None:
        source = "use std::io::Read;\nfn main() { let mut s = String::new(); std::io::stdin().read_to_string(&mut s).unwrap(); print!(\"{}\", s); }\n"
        problem = make_problem(self.root, folder="rust", source=source)
        self.assertEqual(self.statuses(self.run_problem(problem)), ["PASS"])

    def test_missing_toolchain_is_skipped_and_can_fail_the_run(self) -> None:
        problem = make_problem(self.root, folder="cpp", source="int main() {}\n")
        with mock.patch.dict(os.environ, {"CXX": "definitely-not-a-compiler"}):
            (result,) = self.run_problem(problem)
            self.assertEqual((result.status, result.missing_tool), ("SKIP", True))
            self.assertEqual(quiet(lambda: rt.main(["--root", str(self.root)])), 0)
            self.assertEqual(quiet(lambda: rt.main(["--root", str(self.root), "--require-toolchains"])), 1)

    def test_main_exit_codes(self) -> None:
        make_problem(self.root)
        self.assertEqual(quiet(lambda: rt.main(["--root", str(self.root)])), 0)
        make_problem(self.root, cases={"c": ("x\n", "y\n")}, problem_id=1002, slug="wrong")
        self.assertEqual(quiet(lambda: rt.main(["--root", str(self.root)])), 1)


if __name__ == "__main__":
    unittest.main()
