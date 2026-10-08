# Backlog

This file is the single prioritized TODO for the repository. Sections are ordered roughly by execution priority: finish quality gates and automation before scaling up migration volume.

## 1. Repository bootstrap

- [x] finalize root documentation
- [x] finalize style guides
- [x] finalize templates
- [x] create first problem-model folder (3484)
- [x] resolve the 3484 inconsistency: C++ solution written and verified locally, Python implementation dropped (one primary language per problem, see `docs/language-policy.md`), status set to `In Progress` until the judge accepts the submission
- [ ] register 3484 in `trackers/solved-problems.md` and the four `docs/indexes/*.md` files once it is genuinely solved

## 2. Automation scripts (empty stubs today, needed before scaling migration)

- [x] implement `scripts/new_problem.py`: scaffolds a problem folder (README from the right L1/L2 template, L3 also gets `deep-dive.md`, `solutions/<lang>/main.<ext>` from the language skeleton) from the problem ID, title, and category
- [x] implement `scripts/validate_structure.py`: fails if a `solutions/*/main.*` file is empty, a metadata field is missing, checkbox syntax is malformed, or a problem folder doesn't match `<id>-<slug>` naming
- [ ] implement `scripts/sync_index.py`: regenerates `trackers/solved-problems.md` and `docs/indexes/*.md` from each problem's metadata block, so indexes can never drift from reality again
- [ ] implement `scripts/generate_views.py`: optional dashboard/summary view (counts by language, category, difficulty)

## 2b. Test tooling and Git gates

- [x] `scripts/run_tests.py`: builds and runs every solution against `tests/*.in|out`
- [x] `scripts/lint_solutions.py`: mechanical style and safety rules from `docs/coding-standards.md`
- [x] `scripts/check_all.py` plus `scripts/hooks/pre-commit` and `pre-push`: one command before any Git update
- [ ] confirm Rust and SQL availability on the judge, then add Rust to the supported submission languages
- [ ] define the SQL engine and a SQL test runner

## 3. CI and repository security posture (AppSec-aligned, high signal for the portfolio goal)

- [x] add a GitHub Actions workflow that compiles every `main.cpp`/`main.c`/`main.rs` and runs every `main.py`/`main.js` on push/PR (`.github/workflows/ci.yml`)
- [x] decide and document a convention for sample input/output per problem: `tests/<name>.in` + `tests/<name>.out`, shared by every implementation (see `docs/testing.md`)
- [x] wire `scripts/validate_structure.py` into the same CI workflow as a required check (via `scripts/check_all.py`)
- [ ] enable branch protection on `main`: require PRs, require the CI check to pass before merge
- [ ] enable GitHub secret scanning + push protection (free on public repos)
- [ ] add a CodeQL analysis workflow (free on public repos, covers C/C++/Python/JS), directly reinforcing the AppSec specialization narrative
- [ ] add a short `SECURITY.md` (even a minimal one): a repo about problem-solving that also demonstrates a real security posture is a strong AppSec signal

## 4. Migration pipeline (for the existing solved Beecrowd problems)

- [ ] confirm rough volume and categories of already-solved problems to size the effort realistically
- [ ] do not bulk-import: each migrated problem goes through the full review: style-guide pass, correct L1/L2/L3 documentation level, metadata filled, indexes updated (per `docs/repository-philosophy.md` migration principle and `CONTRIBUTING.md`)
- [ ] use `scripts/new_problem.py` to scaffold each migrated problem consistently
- [ ] batch migrations under `migration/<batch-name>` branches, one PR per coherent batch (not one PR per problem, not one giant PR)
- [ ] prioritize breadth first: cover most Beecrowd categories at least once before grinding depth in a single category, since that's a better signal for a portfolio than volume in one topic
- [ ] follow `trackers/learning-path.md` as the concrete driver for problem selection order (category × difficulty tier spiral)

## 5. AppSec / robotics specialization alignment

- [ ] when a problem meaningfully touches memory, bit manipulation, parsing/input validation, or graph/network structure, consider tagging it explicitly (extend `docs/indexes/by-topic.md` with a tag such as "security-adjacent fundamentals"). This is optional, don't force it onto every problem.
- [ ] keep C/C++ as the primary implementation language for problems in that space, consistent with the existing style guides

## 6. Portfolio polish (later, once the above is stable)

- [ ] add a CI status badge and a "problems solved" counter to the root `README.md`
- [ ] add GitHub repo topics (e.g. `algorithms`, `cpp`, `appsec`, `competitive-programming`) for discoverability
- [ ] revisit `trackers/milestones.md` progress after the first migration batch lands
