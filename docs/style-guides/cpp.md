# C++ Style Guide

## Standard

Prefer modern C++ with clarity and restraint.

Use C++17 or C++20 when appropriate, but avoid unnecessary complexity.

## Principles

- prioritize readability
- avoid macros unless clearly justified
- prefer standard library facilities over custom reinvention
- keep functions small and purposeful
- use meaningful names

## Naming

- variables: `camelCase`
- constants: `kConstantName` or `UPPER_CASE` when strongly justified
- functions: `camelCase`

## Includes

Include only what is needed.

Avoid oversized competitive programming templates when the problem does not justify them.

## Comments

Use comments only when they add reasoning that is not obvious from the code.

Do not comment every line.

## Preferred style

- clear control flow
- explicit logic
- minimal hidden behavior
- no cryptic one-letter variable abuse unless used in very local contexts