# Testing and Verification

Nothing should reach Git without passing the same checks that CI runs. One command does it:

```bash
python scripts/check_all.py
```

Requirements: Python 3.9+ and, for the languages you use, `g++`, `gcc`, `node`, and `rustc`. A missing toolchain is reported as a skip, never silently ignored.

## What the gate runs

| Step | Script | What it verifies |
|------|--------|------------------|
| 1. Script unit tests | `scripts/tests/` | the tooling itself, the templates, and that every lint rule is documented |
| 2. Structure | `scripts/validate_structure.py` | folder naming, metadata fields and values, status coherence, language policy, test-case pairs |
| 3. Lint | `scripts/lint_solutions.py` | the mechanical rules of [Coding Standards](coding-standards.md) |
| 4. Solutions | `scripts/run_tests.py` | builds every implementation and runs it against its test cases |

## Test case convention

Test cases belong to the **problem**, not to a language, so every implementation runs the same ones:

```text
problems/3400-3499/3484-divided-class/
└── tests/
    ├── sample-1.in        input given to the program
    ├── sample-1.out       exact expected output
    ├── edge-single.in
    └── edge-single.out
```

- Every `.in` has a matching `.out`, and the other way around.
- A problem with `Status: Solved` needs at least one case (SQL excepted for now).
- Naming: `sample-N` for the examples shown by the judge, `edge-<what>` for boundaries (smallest and largest input, sorted, reversed, duplicates), `random-<seed>` for cross-checked generated cases.
- Keep cases small. The judge's examples are tiny and may be kept; prefer your own cases for everything else.
- Expected outputs for larger cases should come from an independent brute-force oracle, not from the solution under test. Keep the oracle outside the repository, unless it is a documented secondary implementation (see [Language Policy](language-policy.md)).

## Comparison rules

`run_tests.py` compares output the way a judge does:

- line endings are normalized and trailing blank lines at the very end are ignored;
- everything else is exact, including trailing spaces inside a line (`--lenient` relaxes only that);
- a non-zero exit code is a runtime error, and exceeding `--timeout` (5 s by default) is a time-limit failure.

Binaries are built in a temporary folder; nothing is written into the repository.

## Running parts of the gate

```bash
python scripts/check_all.py --staged              # only problems with staged changes
python scripts/check_all.py --since origin/main   # only problems changed on this branch
python scripts/check_all.py --all --strict        # everything, warnings fail too

python scripts/validate_structure.py [problem-folder]
python scripts/lint_solutions.py [file ...]
python scripts/run_tests.py [problem-folder] --lang cpp --sanitize --werror
```

`--sanitize` builds C and C++ with AddressSanitizer and UndefinedBehaviorSanitizer. `--werror` turns compiler and interpreter warnings into failures. `--require-toolchains` makes a missing compiler fail the run (CI uses it).

## Git hooks

Enable the hooks once per clone:

```bash
git config core.hooksPath scripts/hooks
```

- **pre-commit** runs the gate for the problems with staged changes (fast).
- **pre-push** runs it for everything changed since `origin/main`, with sanitizers and warnings-as-errors.

On Windows, mark the hooks executable in the index once: `git update-index --chmod=+x scripts/hooks/pre-commit scripts/hooks/pre-push`.

A hook can be bypassed with `--no-verify`, which is why CI repeats the full gate on every push and pull request (`.github/workflows/ci.yml`). Extra flags for one command: `CHECK_ARGS=--strict git commit`.

## Before opening a pull request

1. `python scripts/check_all.py` is green.
2. Trackers and indexes are updated (`trackers/solved-problems.md`, `docs/indexes/`).
3. The pull request follows the template and the commit messages follow the conventions in [Git Workflow](git-workflow.md).
