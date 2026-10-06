"""Tests for scripts/lint_solutions.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lint_solutions as lint  # noqa: E402


def ids(source: str, folder: str, level: str | None = None) -> list[str]:
    """Rule ids reported for `source` (e.g. ['CPP001'])."""
    found = lint.lint_text(source, folder, "x")
    return [i.message.split("]")[0].lstrip("[") for i in found if level is None or i.level == level]


class SplitSourceTest(unittest.TestCase):
    def test_strings_and_comments_are_separated(self) -> None:
        plain, with_strings, comments = lint.split_source('int a; // note\nchar* s = "gets(";\n', "c")
        self.assertNotIn("gets", plain)
        self.assertIn("gets", with_strings)
        self.assertIn("note", comments)
        self.assertEqual(len(plain), len('int a; // note\nchar* s = "gets(";\n'))

    def test_python_docstring_is_a_string(self) -> None:
        plain, _, _ = lint.split_source('"""eval(x)"""\nvalue = 1\n', "python")
        self.assertNotIn("eval", plain)

    def test_rust_lifetime_does_not_swallow_code(self) -> None:
        plain, _, _ = lint.split_source("fn f<'a>(x: &'a str) { x.unwrap(); }\n", "rust")
        self.assertIn("unwrap", plain)


class CppRulesTest(unittest.TestCase):
    GOOD = "#include <iostream>\nint main() {\n  std::cout << 1 << '\\n';\n}\n"

    def test_clean_file(self) -> None:
        self.assertEqual(ids(self.GOOD, "cpp"), [])

    def test_banned_constructs(self) -> None:
        source = "#include <bits/stdc++.h>\nusing namespace std;\nint main() { int* p = new int[2]; delete[] p; }\n"
        self.assertEqual(sorted(set(ids(source, "cpp", "error"))), ["CPP001", "CPP002", "CPP004"])

    def test_missing_include_is_caught(self) -> None:
        source = "#include <vector>\nint main() { std::vector<int> v; return std::max(1, 2); }\n"
        self.assertEqual(ids(source, "cpp", "error"), ["CPP008"])

    def test_include_present_is_fine(self) -> None:
        source = "#include <algorithm>\nint main() { return std::max(1, 2); }\n"
        self.assertEqual(ids(source, "cpp"), [])

    def test_mentions_in_comments_and_strings_are_ignored(self) -> None:
        source = '#include <iostream>\n// using namespace std; new int\nint main() { std::cout << "using namespace std"; }\n'
        self.assertEqual(ids(source, "cpp"), [])

    def test_deleted_function_is_not_raw_delete(self) -> None:
        self.assertEqual(ids("struct A { A(const A&) = delete; };\n", "cpp"), [])

    def test_allow_comment_suppresses_on_same_or_previous_line(self) -> None:
        same = "int main() { int* p = new int; }  // lint:allow CPP004 deliberate\n"
        above = "// lint:allow CPP004 deliberate exercise\nint main() { int* p = new int; }\n"
        self.assertEqual(ids(same, "cpp"), [])
        self.assertEqual(ids(above, "cpp"), [])

    def test_endl_cast_and_todo_are_warnings(self) -> None:
        source = "#include <iostream>\nint main() { std::cout << (int)2.5 << std::endl; }  // TODO\n"
        self.assertEqual(sorted(ids(source, "cpp", "warning")), ["CPP003", "CPP005", "GEN001"])


class OtherLanguagesTest(unittest.TestCase):
    def test_c_unbounded_input(self) -> None:
        self.assertEqual(ids('int main(void) { char b[8]; scanf("%s", b); gets(b); }\n', "c", "error"), ["C001", "C002"])
        self.assertEqual(ids('int main(void) { char b[8]; scanf("%7s", b); }\n', "c", "error"), [])

    def test_c_unsafe_copies(self) -> None:
        self.assertEqual(ids("void f(char* a, char* b) { strcpy(a, b); }\n", "c", "error"), ["C003"])

    def test_python(self) -> None:
        source = "from os import *\nx = eval('1')\nq.pop(0)\ndef f(a=[]):\n    pass\n"
        self.assertEqual(sorted(ids(source, "python")), ["PY001", "PY002", "PY003", "PY004"])

    def test_javascript(self) -> None:
        source = '"use strict";\nvar a = 1;\nif (a == 2) {}\nxs.sort();\nxs.shift();\n'
        self.assertEqual(sorted(ids(source, "javascript")), ["JS001", "JS002", "JS004", "JS005"])

    def test_javascript_needs_use_strict(self) -> None:
        self.assertEqual(ids("const a = 1;\n", "javascript"), ["JS006"])

    def test_javascript_strict_equality_is_fine(self) -> None:
        self.assertEqual(ids('"use strict";\nif (a === 1 && b !== 2 && c <= 3 && d >= 4) {}\n', "javascript"), [])

    def test_rust_unsafe_needs_safety_comment(self) -> None:
        self.assertEqual(ids("fn f() { unsafe { g() } }\n", "rust", "error"), ["RS002"])
        documented = "fn f() {\n    // SAFETY: g has no preconditions\n    unsafe { g() }\n}\n"
        self.assertEqual(ids(documented, "rust", "error"), [])

    def test_rust_unwrap_is_a_warning(self) -> None:
        self.assertEqual(ids("fn main() { let x: i32 = \"1\".parse().unwrap(); }\n", "rust"), ["RS001"])

    def test_sql(self) -> None:
        source = "select * from a, b where a.id = b.id;\n"
        self.assertEqual(sorted(set(ids(source, "sql"))), ["SQL001", "SQL002", "SQL003"])
        good = "SELECT a.id, b.name\nFROM a\nJOIN b ON b.a_id = a.id;\n"
        self.assertEqual(ids(good, "sql"), [])

    def test_sql_count_star_is_fine(self) -> None:
        self.assertEqual(ids("SELECT COUNT(*) FROM a;\n", "sql"), [])

    def test_long_lines_warn(self) -> None:
        self.assertEqual(ids("x = '" + "a" * 130 + "'\n", "python"), ["GEN002"])


class CliTest(unittest.TestCase):
    def test_exit_codes(self) -> None:
        import tempfile

        from fixtures import make_problem, quiet

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            problem = make_problem(root, folder="python", source="value = eval('1')\nprint(value)\n")
            self.assertEqual(quiet(lambda: lint.main(["--root", str(root)])), 1)
            (problem / "solutions" / "python" / "main.py").write_text("print(1)  # TODO\n", encoding="utf-8")
            self.assertEqual(quiet(lambda: lint.main(["--root", str(root)])), 0)
            self.assertEqual(quiet(lambda: lint.main(["--root", str(root), "--strict"])), 1)


if __name__ == "__main__":
    unittest.main()
