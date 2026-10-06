# Python Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to Python. The language follows PEP 8. A starting point is in `templates/solutions/main.py`.

## Principles

- clarity first
- concise but not compressed
- explicit over clever
- follow readable Python conventions

## Naming

- variables: `snake_case`
- functions: `snake_case`
- constants: `UPPER_CASE`

## Structure

- Put the logic in `main()` and call it under `if __name__ == "__main__":`. Local variables are also faster than globals.
- Add type hints to function signatures.
- Never use a mutable default argument (`def f(items=[])`).

## Input and output

- Read all input at once: `sys.stdin.read().split()`, or `sys.stdin.readline` when lines matter. A loop of `input()` calls is slow for large inputs.
- Build the output and print it once: `print("\n".join(lines))`. Never grow a string with `+=` in a loop.

## Standard library and complexity

- `collections.deque` for queues (`list.pop(0)` is O(n)); `set` and `dict` for membership; `heapq` for priority queues; `bisect` for sorted lists; `collections.Counter` for counting.
- `math.isqrt` and `math.gcd` instead of floating-point tricks.
- Avoid copying slices inside loops.

## Numbers and recursion

- Integers never overflow, but very large ones are slow, and converting integers with thousands of digits to or from `str` is limited by default in recent Python versions.
- `round()` uses banker's rounding. Format with `f"{value:.2f}"` when the output needs fixed decimals, and use `decimal.Decimal` when exact decimal arithmetic matters.
- Deep recursion is slow and limited. Prefer an iterative version; raising `sys.setrecursionlimit` can crash the interpreter.

## Implementation

- avoid unnecessary shortcuts
- keep logic easy to trace
- do not sacrifice readability for fewer lines

## Comments

Use comments sparingly and only where they improve understanding.

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `PY001` | error | `eval` / `exec` |
| `PY002` | error | wildcard import |
| `PY003` | warning | `list.pop(0)` |
| `PY004` | warning | mutable default argument |
| `PY005` | warning | `sys.setrecursionlimit` |

## Goal

Python solutions should feel elegant, clear, and trustworthy.
