# Git Workflow

## Branching model

This repository uses a lightweight trunk-based approach.

- `main` is the source of truth
- short-lived branches are used when needed
- long-lived parallel branches are avoided

## Permanent branch

- `main`

## Recommended temporary branch patterns

- `docs/<topic>`
- `feat/<topic>`
- `fix/<topic>`
- `refactor/<topic>`
- `migration/<batch-name>`
- `problem/<id>-<slug>`
- `chore/<topic>`

Examples:

- `docs/repository-bootstrap-v1`
- `migration/legacy-batch-01`
- `problem/3381-quantifier-evaluation`
- `refactor/cpp-style-normalization`

## Commit style

This repository uses conventional commits in English.

Format:

`type(scope): message`

Examples:

- `docs(repo): add repository philosophy and workflow`
- `feat(problem-1000): add C++ solution and L1 documentation`
- `feat(problem-3381): add C++ solution and deep dive`
- `refactor(cpp): normalize naming in migrated solutions`
- `chore(trackers): update solved problems index`

## Commit principles

- keep commits small and meaningful
- describe intent clearly
- avoid vague messages such as `update` or `fix stuff`

## Merge principle

Merge when the branch is coherent, reviewed, and aligned with the repository conventions.