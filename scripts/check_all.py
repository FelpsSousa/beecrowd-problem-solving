#!/usr/bin/env python3
"""Run every repository check in one command (the gate before any Git update).

Steps, in order:
    1. unit tests of the scripts themselves
    2. structure and metadata validation   (validate_structure.py)
    3. style and safety lint               (lint_solutions.py)
    4. build and run all test cases        (run_tests.py)

Scope:
    python scripts/check_all.py                      # whole repository
    python scripts/check_all.py --staged             # only problems with staged changes
    python scripts/check_all.py --since origin/main  # only problems changed since a ref

Strictness (used by the Git hooks and CI):
    --sanitize  ASan+UBSan for C/C++      --werror  warnings fail the build
    --strict    warnings fail validation and lint
    --require-toolchains  a missing compiler/interpreter is a failure
    --github    GitHub Actions annotations

Exit code: 0 = everything passed, 1 = at least one step failed.
"""

from __future__ import annotations

import argparse
import sys
import time
import unittest
from pathlib import Path

import lint_solutions
import run_tests
import validate_structure
from repo_lib import changed_files, find_problem_dirs, implementations, problem_dirs_for

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent


def run_unit_tests() -> int:
    suite = unittest.defaultTestLoader.discover(str(SCRIPTS_DIR / "tests"), top_level_dir=str(SCRIPTS_DIR / "tests"))
    result = unittest.TextTestRunner(verbosity=0, stream=sys.stdout).run(suite)
    return 0 if result.wasSuccessful() else 1


def select_scope(root: Path, staged: bool, since: str | None) -> tuple[list[Path] | None, bool, str]:
    """Return (problem dirs or None for all, scripts changed, human description)."""
    if not staged and not since:
        return None, True, "whole repository"

    files = changed_files(root, staged=staged, since=since)
    if files is None:
        return None, True, "whole repository (git could not tell what changed)"

    infra_changed = any(name.startswith(("scripts/", ".github/")) for name in files)
    dirs = problem_dirs_for(root, files)
    label = "staged changes" if staged else f"changes since {since}"
    return dirs, infra_changed, f"{label}: {len(dirs)} problem folder(s)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run all repository checks.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--staged", action="store_true", help="only problems with staged changes")
    parser.add_argument("--since", metavar="REF", help="only problems changed since REF (e.g. origin/main)")
    parser.add_argument("--all", action="store_true", help="whole repository (default)")
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--werror", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-toolchains", action="store_true")
    parser.add_argument("--github", action="store_true")
    parser.add_argument("--skip-unit-tests", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.all:
        dirs, infra_changed, scope = None, True, "whole repository"
    else:
        dirs, infra_changed, scope = select_scope(root, args.staged, args.since)
    print(f"Scope: {scope}")

    path_args = [str(d) for d in dirs] if dirs is not None else []
    nothing_to_check = dirs is not None and not dirs

    steps: list[tuple[str, int | None]] = []

    def step(name: str, runner) -> None:  # noqa: ANN001
        print(f"\n=== {name} ===")
        started = time.perf_counter()
        code = runner()
        print(f"--- {name}: {'ok' if code == 0 else 'FAILED'} ({time.perf_counter() - started:.1f}s)")
        steps.append((name, code))

    if args.skip_unit_tests or not infra_changed:
        steps.append(("script unit tests", None))
    else:
        step("script unit tests", run_unit_tests)

    if nothing_to_check:
        print("\nNo problem folders changed: structure, lint and tests skipped.")
        steps += [("structure validation", None), ("lint", None), ("solution tests", None)]
    else:
        common = ["--root", str(root)]
        flags = (["--strict"] if args.strict else []) + (["--github"] if args.github else [])
        step("structure validation", lambda: validate_structure.main([*common, *flags, *path_args]))

        files = [str(f) for d in (dirs if dirs is not None else find_problem_dirs(root)) for f in implementations(d).values()]
        step("lint", lambda: lint_solutions.main([*common, *flags, *files]) if files else 0)

        test_flags = [flag for flag, on in (
            ("--sanitize", args.sanitize),
            ("--werror", args.werror),
            ("--require-toolchains", args.require_toolchains),
        ) if on]
        step("solution tests", lambda: run_tests.main([*common, *test_flags, *path_args]))

    print("\n=== Summary ===")
    failed = False
    for name, code in steps:
        label = "skipped" if code is None else ("ok" if code == 0 else "FAILED")
        failed = failed or code not in (None, 0)
        print(f"{label:8} {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
