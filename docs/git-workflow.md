# Git Workflow

## Branching model

This repository uses a lightweight trunk-based approach.

- `main` is the only permanent branch and the source of truth
- every change goes through a short-lived branch and a pull request
- pull requests are small and squash-merged, so each one becomes a single commit on `main`

## The cycle

`scripts/flow.py` runs the whole cycle with short commands. It only drafts text from facts the repository already holds (branch name, staged paths, each problem's metadata, test cases); every command can be previewed with `--dry-run`, and the final wording of each commit is always edited by me.

```bash
python scripts/flow.py start feat flow cli      # update main, create feat/flow-cli
git add <paths>                                 # stage exactly what belongs to this change
python scripts/flow.py commit "add the flow cli" # draft the message, open the editor
python scripts/flow.py pr                       # run the gate, push, open the PR
python scripts/flow.py merge 15                 # squash-merge, delete the branch, update main
```

| Command | What it does | Refuses when |
|---------|--------------|--------------|
| `start <type> <description...>` | `git switch main`, `git pull --ff-only`, `git switch -c <type>/<slug>` | tracked files have uncommitted changes, or the type is unknown |
| `commit [summary...]` | drafts a Conventional Commit from the staged changes and opens the editor (`--no-edit` skips it) | nothing is staged, or no subject can be derived and none was given |
| `pr [--draft]` | runs `scripts/check_all.py`, pushes, opens the PR with a generated title and body | the gate fails, or the branch is `main` |
| `merge <number>` | `gh pr merge --squash --delete-branch`, then returns to an updated `main` and prunes remote branches | `gh` fails (for example, checks still running) |
| `week --points P --rank R` | appends this week's Beecrowd points and world rank to `trackers/ranking-log.md` | invalid numbers |

When only problem folders changed, `commit` derives the subject by itself (`add 3484 divided class`, `migrate 11 problems (1000 to 1010) from the legacy repositories`). For scripts and documentation, pass the summary.

## Branch names

`<type>/<short-description>`, lowercase, words separated by hyphens. The type is a Conventional Commit type or one of two aliases:

| Branch | Commit type and scope |
|--------|----------------------|
| `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `ci/`, `chore/`, ... | the same type, scope taken from the changed area |
| `problem/<id>-<slug>` | `feat(problems)` |
| `migration/<first-id>-<last-id>` | `feat(migration)` |

Examples: `feat/flow-cli`, `problem/3484-divided-class`, `migration/1000-1010`, `docs/adr-rust-on-judge`.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) in English:

```text
type(scope): imperative summary in lowercase, at most 72 characters

Optional body: what changed and why, one fact per line.
```

- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`.
- **Scopes** follow the top-level folder: `problems`, `migration`, `scripts`, `docs`, `trackers`, `templates`, `ci`. Changes that span the whole repository have no scope.
- **Subjects** say what the commit does, not what was done to the code: `add 3484 divided class`, not `updated files`.

Examples:

- `feat(problems): add 3484 divided class`
- `feat(migration): migrate 1000 to 1010`
- `feat(scripts): add the flow cli`
- `fix(problems): handle equal heights in 3484`
- `docs: document the AI assistance policy`

## Pull requests

- The PR title is the commit that will land on `main`, so it follows the same format. `pr` reuses the single commit's subject, or derives one from the branch.
- The body lists the problems touched (ID, title, category, level, language, documentation level, tests, status), the gate result, and a review checklist. Migration branches add a migration checklist (resubmitted and accepted, accepted language kept, samples and edge cases, legacy headers removed, legacy mistakes logged).
- Merge only when CI is green and every checklist item is true.

## Rules

- Stage on purpose: `git add <paths>`, never `git add .` with unrelated files around.
- One coherent change per pull request. A migration batch is one PR, never one giant import.
- `Status: Solved` is committed only after the judge accepted that exact code. A code change after acceptance means submitting again.
- Never force-push to `main`.
