# AI Assistance

This repository is built with the help of an AI assistant, and this page says exactly how. Transparency about tooling is part of the same standard as tests and code review: a reader should know what produced what.

## Tool

[Claude](https://www.anthropic.com/claude), by Anthropic, used through Claude Code inside the editor.

## What the assistant does

- Reviews solutions and documentation against [`coding-standards.md`](coding-standards.md), the [style guides](style-guides/) and the [documentation standard](documentation-standard.md), and explains every suggested change.
- Proposes solutions, refactors and alternative approaches, always with the reasoning and the trade-offs behind them.
- Writes and maintains the repository tooling in `scripts/` (validation, lint, test runner, index sync, the `flow` CLI), each script with its own unit tests.
- Audits the repository and plans the work (migration batches, priorities, security posture).

## What I do

- Decide what goes into the repository, review every line before it is committed, and reject what I cannot explain.
- Run every Git and GitHub command myself: branches, commits, pushes, pull requests and merges come from my account, after my review. Commit and PR text is drafted by [`scripts/flow.py`](../scripts/flow.py) from the repository metadata and edited by me before it is saved.
- Submit every solution to the Beecrowd judge myself. `Status: Solved` means I submitted that exact code and it was accepted.
- Write the reasoning sections of L2 and L3 problems ("My Interpretation", "Why This Works", "What I Learned") in my own words.

## Rules

1. No solution is committed unless I can explain its idea, its complexity and its edge cases without reading it.
2. No judge result is ever claimed without an accepted submission.
3. Problem statements are not copied into the repository; summaries are written in my own words.
4. If the assistant's suggestion is wrong, the fix and the lesson go to [`trackers/mistakes-log.md`](../trackers/mistakes-log.md) like any other mistake.
