# Repository Maintenance Guide

This file defines the operational maintenance rules for this repository.

## Purpose 

The goal is to keep the repository consistent, readable, scalable, and professionally maintainable over time.

This repository is not a raw archive of accepted submissions. It is a structured public knowledge base for problem solving, code quality, and technical growth.

## Main Branch Strategy

- `main` is the source of truth
- use short-lived branches for coherent changes
- avoid long-lived parallel branches
- prefer small and meaningful pull requests 

## Recommended Branch Naming

- `docs/<topic>`
- `feat/<topic>`
- `fix/<topic>`
- `refactor/<topic>`
- `migration/<batch-name>`
- `problem/<id>-<slug>`
- `chore/<topic>`

Examples:

- `docs/repository-bootstrap-v1`
- `problem/3484-divided-class`
- `migration/legacy-batch-01`

## Commit Standard

Use conventional commits in English

Format:

`type(scope): message`

Examples:

- `docs(repo): bootstrap repository structure and core documentation`
- `feat(problem-3484): add L2 documentation and C++/Python solutions`
- `chore(workflow): add pull request template and repository maintenance scripts`

## Pull Request Standard

Open a pull request when the change is coherent and reviewable.

Examples of changes that should usually go through a PR:

- repository structure updates
- documentation blocks
- problem-model additions 
- script additions 
- migration batches 
- refactors

Examples of changes that may go directly to `main` if very small:

- typo fixes
- minor link corrections 
- tiny formatting adjustments 

When in doubt, prefer a PR.

## Merge Strategy 

Prefer **Squash and Merge**.

This keeps `main` clean and turn each pull request into one clear historical unit.

## Language Standard 

All public-facing repository content must be in English, including:

- documentation
- templates
- problem notes
- code comments
- branch names
- commit messages
- pull request titles

## Problem Folder Standard

Each problem should follow the established repository conventions:

- physical organization by ID range 
- one main documentation file per problem 
- multiple implementations under `solutions/`
- optional `notes.md`
- optional `deep-dive.md`

## Index and Tracker Maintenance

Whenever relevant, update:

- `trackers/solved-problems.md`
- `docs/indexes/by-category.md`
- `docs/indexes/by-difficulty.md`
- `docs/indexes/by-language.md`
- `docs/indexes/by-topic.md`

## Sustainability Rule

Do not over-document everything.

Use the repository documentation levels correctly:

- `L1` for quick logs
- `L2` for standard documentation
- `L3` for deep dives

The goal is sustainable excellence, not bureaucratic excess.

## Legacy Migration Rule

Older repositories are sources of extraction, not sources of truth.

Only migrate material that is:

- correct
- valuable
- aligned with the current standards
- worth keeping in the long term

## Review Checklist Before Merge

Before merging a change, verify that:

- naming is correct 
- English is consistent 
- structure follows the repository conventions
- documentation level is appropriate
- trackers and indexes are updated when needed
- the change improves clarity, not noise