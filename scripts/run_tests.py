#!/usr/bin/env python3
"""Build and run every solution against its test cases.

Each problem keeps its cases in `tests/<name>.in` and `tests/<name>.out`. The same
cases are used for every implementation of that problem.

Usage:
    python scripts/run_tests.py                       # all problems
    python scripts/run_tests.py problems/3400-3499/3484-divided-class
    python scripts/run_tests.py --lang cpp,python     # only some languages
    python scripts/run_tests.py --sanitize --werror   # strict local build (C, C++, Rust)

Nothing is ever written into the repository: binaries live in a temporary folder.

Exit code: 0 = every executed case passed, 1 = a failure (or, with
--require-toolchains, a missing compiler/interpreter).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from repo_lib import LANGUAGES, find_problem_dirs, implementations, test_cases

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPILE_TIMEOUT_SECONDS = 120

SANITIZE_FLAGS = ["-fsanitize=address,undefined", "-fno-sanitize-recover=undefined"]


@dataclass(frozen=True)
class Options:
    timeout: float = 5.0
    sanitize: bool = False
    werror: bool = False
    lenient: bool = False


@dataclass
class Prepared:
    """How to run one implementation, or why it cannot be run."""

    command: list[str] | None = None
    skip_reason: str | None = None
    missing_tool: bool = False
    error: str | None = None
    notes: str = ""


@dataclass
class Result:
    problem: str
    folder: str
    case: str
    status: str  # PASS | FAIL | SKIP
    detail: str = ""
    millis: int = 0
    missing_tool: bool = False


def _exe(workdir: Path) -> Path:
    return workdir / ("main.exe" if os.name == "nt" else "main")


def _compile(command: list[str], exe: Path) -> Prepared:
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return Prepared(error="compilation timed out")
    if done.returncode != 0:
        return Prepared(error="compilation failed:\n" + done.stderr.strip())
    return Prepared(command=[str(exe)], notes=done.stderr.strip())


def prepare(folder: str, source: Path, workdir: Path, options: Options) -> Prepared:
    """Compile (if needed) and return the command that runs the solution."""
    exe = _exe(workdir)

    if folder in ("cpp", "c"):
        compiler = os.environ.get("CXX", "g++") if folder == "cpp" else os.environ.get("CC", "gcc")
        if shutil.which(compiler) is None:
            return Prepared(skip_reason=f"{compiler} not found", missing_tool=True)
        standard = "-std=c++20" if folder == "cpp" else "-std=c17"
        flags = [standard, "-O2", "-Wall", "-Wextra", "-Wpedantic"]
        if folder == "cpp":
            flags.append("-Wshadow")
        if options.sanitize:
            flags += SANITIZE_FLAGS
        if options.werror:
            flags.append("-Werror")
        return _compile([compiler, *flags, str(source), "-o", str(exe)], exe)

    if folder == "rust":
        if shutil.which("rustc") is None:
            return Prepared(skip_reason="rustc not found", missing_tool=True)
        flags = ["--edition", "2021", "-O"]
        if options.werror:
            flags += ["-D", "warnings"]
        return _compile(["rustc", *flags, str(source), "-o", str(exe)], exe)

    if folder == "python":
        command = [sys.executable]
        if options.werror:
            command += ["-W", "error"]
        return Prepared(command=[*command, str(source)])

    if folder == "javascript":
        node = shutil.which("node") or shutil.which("nodejs")
        if node is None:
            return Prepared(skip_reason="node not found", missing_tool=True)
        return Prepared(command=[node, str(source)])

    if folder == "sql":
        return Prepared(skip_reason="no SQL runner yet")

    return Prepared(skip_reason=f"unsupported language folder '{folder}'")


def normalize(text: str, lenient: bool) -> list[str]:
    """Line list used for comparison.

    Always: CRLF -> LF and trailing blank lines at the very end are ignored.
    Lenient: trailing spaces on each line are ignored too. The default is strict,
    because judges such as Beecrowd report whitespace differences as errors.
    """
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    if lenient:
        lines = [line.rstrip() for line in lines]
    return lines


def first_difference(expected: list[str], got: list[str]) -> str:
    def clip(value: str) -> str:
        return repr(value if len(value) <= 80 else value[:77] + "...")

    for index in range(max(len(expected), len(got))):
        want = expected[index] if index < len(expected) else "<missing line>"
        have = got[index] if index < len(got) else "<missing line>"
        if want != have:
            return f"line {index + 1}: expected {clip(want)}, got {clip(have)}"
    return "outputs differ"


def run_case(command: list[str], input_file: Path, expected_file: Path, options: Options) -> tuple[str, str, int]:
    """Run one case. Returns (status, detail, milliseconds)."""
    if not expected_file.is_file():
        return "FAIL", f"missing expected output {expected_file.name}", 0

    started = time.perf_counter()
    try:
        with input_file.open("rb") as stdin:
            done = subprocess.run(command, stdin=stdin, capture_output=True, timeout=options.timeout)
    except subprocess.TimeoutExpired:
        return "FAIL", f"time limit exceeded ({options.timeout:g}s)", int(options.timeout * 1000)
    millis = int((time.perf_counter() - started) * 1000)

    if done.returncode != 0:
        tail = done.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
        return "FAIL", f"runtime error (exit code {done.returncode}) " + " | ".join(tail), millis

    got = normalize(done.stdout.decode("utf-8", "replace"), options.lenient)
    want = normalize(expected_file.read_text(encoding="utf-8"), options.lenient)
    if got != want:
        return "FAIL", first_difference(want, got), millis
    return "PASS", "", millis


def run_problem(problem_dir: Path, languages: set[str] | None, options: Options) -> list[Result]:
    problem = problem_dir.name
    cases = test_cases(problem_dir)
    results: list[Result] = []

    # ignore_cleanup_errors: on Windows, a just-run .exe can still be briefly
    # locked (commonly by antivirus scanning it) when cleanup tries to delete
    # it; best-effort cleanup avoids crashing the whole run over a temp file.
    with tempfile.TemporaryDirectory(prefix="beecrowd-tests-", ignore_cleanup_errors=True) as tmp:
        for folder, source in implementations(problem_dir).items():
            if languages is not None and folder not in languages:
                continue
            if not cases:
                results.append(Result(problem, folder, "-", "SKIP", "no test cases"))
                continue

            workdir = Path(tmp) / folder
            workdir.mkdir()
            prepared = prepare(folder, source, workdir, options)

            if prepared.error:
                results.append(Result(problem, folder, "build", "FAIL", prepared.error))
                continue
            if prepared.skip_reason or prepared.command is None:
                results.append(Result(problem, folder, "-", "SKIP", prepared.skip_reason or "", missing_tool=prepared.missing_tool))
                continue
            if prepared.notes:
                results.append(Result(problem, folder, "build", "PASS", "compiler output:\n" + prepared.notes))

            for name, input_file, expected_file in cases:
                status, detail, millis = run_case(prepared.command, input_file, expected_file, options)
                results.append(Result(problem, folder, name, status, detail, millis))
    return results


def print_results(results: list[Result]) -> None:
    for r in results:
        timing = f" ({r.millis} ms)" if r.status == "PASS" and r.millis else ""
        print(f"{r.status:5} {r.problem} {r.folder} {r.case}{timing}")
        if r.detail and r.status != "PASS":
            for line in r.detail.splitlines():
                print(f"        {line}")
        elif r.detail and r.case == "build":
            print(f"        {r.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and run solutions against tests/*.in|out.")
    parser.add_argument("paths", nargs="*", type=Path, help="problem folders (default: all)")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--lang", help="comma separated language folders (e.g. cpp,python)")
    parser.add_argument("--timeout", type=float, default=5.0, help="seconds per case (default 5)")
    parser.add_argument("--sanitize", action="store_true", help="ASan+UBSan for C and C++")
    parser.add_argument("--werror", action="store_true", help="treat compiler/interpreter warnings as errors")
    parser.add_argument("--lenient", action="store_true", help="ignore trailing spaces on each line")
    parser.add_argument("--require-toolchains", action="store_true", help="fail when a compiler/interpreter is missing")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    problem_dirs = [p.resolve() for p in args.paths] if args.paths else find_problem_dirs(root)

    languages: set[str] | None = None
    if args.lang:
        languages = {part.strip().lower() for part in args.lang.split(",") if part.strip()}
        known = {folder for folder, _ext in LANGUAGES.values()}
        unknown = languages - known
        if unknown:
            parser.error(f"unknown language(s): {', '.join(sorted(unknown))}")

    options = Options(args.timeout, args.sanitize, args.werror, args.lenient)
    results: list[Result] = []
    for problem_dir in problem_dirs:
        results += run_problem(problem_dir, languages, options)

    print_results(results)
    cases = [r for r in results if r.case not in ("build", "-")]
    passed = sum(1 for r in cases if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    skipped = sum(1 for r in results if r.status == "SKIP")
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped.")

    missing = any(r.missing_tool for r in results)
    return 1 if failed or (args.require_toolchains and missing) else 0


if __name__ == "__main__":
    sys.exit(main())
