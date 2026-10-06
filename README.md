# beecrowd-problem-solving

A professional problem-solving repository focused on algorithmic thinking, clean code, and documented learning.

This repository is part of my long-term technical growth and public portfolio. It is not just a collection of accepted submissions &ndash; it is a structured knowledge base built to improve problem-solving, code quality, technical communication, and interview readiness.

## Goals

- Solve programming problems with consistency and clarity
- Build a documented study trail instead of a raw archive of submissions
- Create a public reference of how I approach algorithmic challenges
- Turn practice into reusable knowledge
- Strengthen foundations for software engineering and technical interviews

## Main Languages

Each problem has **one primary language**, chosen for what the problem trains (see `docs/language-policy.md`):

- C++17 / C++20 as the default problem-solving language
- C for memory, bits, and low-level reasoning
- Rust for ownership and memory safety, as the counterpart of C
- Python for clarity, strings, and quick prototypes
- JavaScript for parsing and text processing, aligned with my professional stack
- SQL for the SQL category

## Repository Structure

- `problems/` &rarr; problem-based documentation model;
- `docs/` &rarr; philosophy, workflow, standards, references, and language guides
- `trackers/` &rarr; progress tracking and reviews
- `templates/` &rarr; reusable documentation templates
- `scripts/` &rarr; automation helpers: validation, linting, test runner, Git hooks

## Documentation Levels

This repository uses a layered documentation model:

- **L1 &mdash; Quick Log**: short documentation for straightforward problems
- **L2 &mdash; Standard**: structured explanation for relevant problems
- **L3 &mdash; Deep Dive**: deeper analysis for hard, elegant, or high-value problems

Not every problem needs the same depth. The goal is not bureaucratic documentation &ndash; the goal is sustainable excellence.

## Core Principles

- Clarity over cleverness
- Consistency over intensity
- Explanation over raw acceptance
- Long-term maintainability over short-term volume
- Public visibility with intentional authorship

## Usage and Intellectual Property Notice

This repository is public for portfolio, study, and professional visibility purposes.

Unless explicitly stated otherwise, all code, notes, explanations, and repository structure in this project are authored and maintained by me and are not licensed for reuse, redistribution, modification, or commercial use.

The absence of a license file is intentional. Public visibility does not mean this repository open source.

Problem statements, titles, and platform references belong to their respective owners. This repository contains my own implementations, notes, and interpretations for educational and portfolio purposes.

## Quality Gate

Every change is verified before it reaches Git, locally and in CI:

```bash
python scripts/check_all.py
```

See `docs/testing.md` for what it checks and how to enable the Git hooks.

# Status

This repository is being built incrementally, with careful structure, documentation, and selective migration from older problem-solving repositories.