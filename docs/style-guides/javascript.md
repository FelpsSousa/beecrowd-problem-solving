# JavaScript Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to JavaScript (Node.js). A starting point is in `templates/solutions/main.js`.

## Principles

- write modern, readable JavaScript
- prioritize correctness and clarity
- avoid overengineering simple solutions

## Naming

- variables: `camelCase`
- functions: `camelCase`
- constants: `UPPER_CASE`

## Declarations

- Start the file with `"use strict";`.
- Use `const` by default and `let` only when reassignment is necessary. Never use `var`.
- Compare with `===` and `!==`, never `==` or `!=`.

## Input and output

- Read everything at once and split it: `require("fs").readFileSync(0, "utf8")`. Check the judge's own template for the accepted way to read standard input (some judges expect `/dev/stdin`).
- Collect the output in an array and print it once with `join("\n")`; one `console.log` per line is slow for large outputs.

## Numbers: the traps

- `Number` is a double: integers above `Number.MAX_SAFE_INTEGER` (2^53 - 1) lose precision. Use `BigInt` for them.
- Integer division is `Math.trunc(a / b)`.
- Bitwise operators work on 32 bits (`| 0`, `>>> 0`).
- `Array.prototype.sort()` without a comparator sorts as **text**. Always pass `(a, b) => a - b` for numbers.

## Performance and data structures

- `Array.shift()` is O(n); implement a queue with a head index.
- Use typed arrays (`Int32Array`, `Float64Array`) for large numeric data.
- Use `Map` and `Set` as dictionaries. Plain objects inherit from `Object.prototype`, so keys such as `__proto__` can corrupt them (prototype pollution); if an object is needed, create it with `Object.create(null)`.
- Never use `eval` or `new Function`.

## Style

- avoid deeply nested logic when simpler structures exist

## Comments

Comment intent, not syntax.

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `JS001` | error | `var` |
| `JS002` | error | loose equality (`==`, `!=`) |
| `JS003` | error | `eval` / `new Function` |
| `JS004` | warning | `sort()` without a comparator |
| `JS005` | warning | `shift()` |
| `JS006` | warning | missing `"use strict"` |

## Goal

JavaScript solutions should reinforce professional consistency with a frontend engineering background while still fitting algorithmic problem-solving needs.
