# Repository Conventions

## Language

English is the default language for all public repository content, including:

- documentation
- file names
- folder names
- code comments
- commit messages
- branch names
- issue titles
- pull request titles

## Naming

### Files and folders

Use lowercase and hyphen-separated names.

Examples:

- `repository-philosophy.md`
- `problem-solving-framework.md`
- `deep-dive.md`

### Problem folders

Use the following format:

`<problem-id>-<slug-in-english>`

Example:

`3381-one-for-all-all-for-what-exists`

## Problem organization

The physical repository structure is organized by ID ranges.

Example:

- `problems/1000-1099/`
- `problems/3300-3399/`

This keeps the filesystem stable and scalable.

## Problem documentation

A problem has one main conceptual documentation file.

A problem has one primary language. Extra implementations may exist inside `solutions/` when there is a stated reason (see `language-policy.md`), but the explanation remains centralized.

## Problem folder layout

```text
<problem-id>-<slug>/
├── README.md              one explanation, with the metadata block
├── notes.md               optional
├── deep-dive.md           optional, for L3
├── solutions/<language>/main.<ext>
└── tests/<name>.in, <name>.out
```

Supported language folders: `cpp`, `c`, `python`, `javascript`, `rust`, `sql`. Test cases are shared by every implementation (see `testing.md`).

## Code standards

All code follows `coding-standards.md` and the style guide of its language. The rules are checked by `scripts/lint_solutions.py`.

## Statements

Do not copy the full original statement into the repository.

Use:

- the problem ID
- title
- link
- an authorial summary
- your own interpretation
- your own reasoning

## Documentation levels

- `L1` for quick logs
- `L2` for structured explanations
- `L3` for deep dives

## Repository principle

This repository should look like a professional technical knowledge base, not like an unstructured archive of accepted submissions.