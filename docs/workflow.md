# Workflow

## Standard Flow

1. Read the problem carefully
2. Restate the problem in my own words
3. Identify inputs, outputs, and constraints
4. Think about the brute-force baseline
5. Search for the cleanest acceptable approach
6. Implement with clarity
7. Test with the samples, edge cases, and a brute-force cross-check (see `testing.md`), then run `python scripts/check_all.py`
8. Submit to the platform
9. Document the solution at the correct level
10. Register the problem in the trackers

## Documentation Decision

After solving a problem, choose one documentation level:

- **L1 &mdash; Quick Log**
  - easy or routine problem
  - direct implementation
  - no significant new insight

- **L2 &mdash; Standard**
  - medium problem
  - useful pattern
  - relevant mistake or learning point

- **L3 &mdash; Deep Dive**
  - hard problem
  - elegant solution
  - strong conceptual lesson
  - good candidate for future revision or teaching

## Multi-language Rule

A problem should have one main documentation file.

Each problem has one primary language, chosen for what it trains (see `language-policy.md`). Extra implementations exist only with a stated reason, and the conceptual explanation remains centralized.

`Status: Solved` is used only after the judge accepts the submission.

## Review Rule

Problems with strong learning value should be marked for future review.