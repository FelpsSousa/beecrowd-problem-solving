# Coding Standards

These rules apply to **every language** in this repository. Each language adds its own details in `docs/style-guides/`:

[C++](style-guides/cpp.md) · [C](style-guides/c.md) · [Python](style-guides/python.md) · [JavaScript](style-guides/javascript.md) · [Rust](style-guides/rust.md) · [SQL](style-guides/sql.md)

The rules that a program can decide are checked automatically by `scripts/lint_solutions.py`. The rest is checked by review, using the checklist at the end of this page.

## 1. Think before typing

1. **Estimate complexity from the constraints before coding.** Choosing the right algorithm is the largest optimization there is. `N <= 250` allows `O(N^2)` or even `O(N^3)`; `N = 10^5` calls for `O(N log N)`.
2. **Correct first, fast second.** Optimize only after the samples pass and a measurement or a complexity estimate says it is necessary.
3. **Pick the data structure for the operations you need**, not for habit: lookups, ordered traversal, a queue, a priority queue.
4. **Prefer the simplest correct approach.** Clever code is a liability; clear code is an asset.

## 2. Input and output contract

1. Read **exactly** what the statement describes. Handle end-of-file when the statement says the input ends that way.
2. Never assume a particular whitespace layout; read tokens, not lines, unless lines matter.
3. Match the output format **character for character**: separators, decimals, trailing spaces, and the final newline. Judges report formatting differences as errors.
4. Read the whole input efficiently when it is large, and write the output in as few calls as practical.

## 3. Safety is the default

These rules are cheap in a puzzle and essential in real code, which is why they are practiced here.

1. **Every index needs an argument.** Either a bounds check, or a short comment that explains why it cannot go out of range.
2. **Know the largest value before choosing a numeric type.** Compute the worst case. Signed overflow is undefined behavior in C and C++, wraps silently in release Rust, and loses precision in JavaScript numbers above 2^53.
3. **Never trust sizes or counts from input** when allocating or indexing. Validate them against the statement's limits.
4. **Initialize everything.** No variable is read before it has a value.
5. **Ownership is explicit.** Prefer containers and smart pointers (or Rust's ownership) to manual memory management. A non-owning cursor is fine; a second owner is a bug.
6. **No dynamic code execution** (`eval`, `exec`, `new Function`) and no building queries by string concatenation.
7. **Treat compiler and linter warnings as defects.** Fix them or justify them.

## 4. Performance rules

1. Measure or estimate; do not guess.
2. Avoid work in the inner loop that can be done once outside it.
3. Prefer the standard library: it is tested, documented, and fast.
4. Fast input/output matters only when the input is large. Add it deliberately and say why in a comment.
5. Know the cost of the operations you call (`list.pop(0)`, `Array.shift()`, string concatenation in a loop, copying large values).
6. Beware of adversarial inputs for hash tables when the input is not trusted.

## 5. Structure, naming, and comments

1. One file per implementation: `solutions/<language>/main.<ext>`. Standard library only, no external dependencies.
2. Small functions with one clear purpose; `main` reads, calls, and prints.
3. Meaningful names. One-letter names only in very local scopes (`i`, `j`, `n`).
4. Comments explain **why**, never what. A good comment records a non-obvious reason: a bound, a trick, an invariant.
5. Follow the naming rules of each language (see the style guides) and `.editorconfig` (UTF-8, LF, spaces, 4-space indent for code).
6. English only for code, comments, and documentation.
7. No leftover `TODO`, debugging output, or commented-out code.

## 6. Testing expectations

Every solved problem has test cases in `tests/` (see [Testing](testing.md)): the public samples, the edge cases, and, when a faster solution replaced a simpler one, cases cross-checked against a brute-force oracle.

## 7. What is checked automatically

`scripts/lint_solutions.py` reports findings with a stable rule id. Errors block a commit; warnings are advice. The full list per language is in the style guides.

| Area | Examples of what it catches |
|------|-----------------------------|
| Portability | `<bits/stdc++.h>`, std symbols used without their `#include` |
| Memory safety | raw `new`/`delete`, `gets`, unbounded `%s`, `strcpy`, `unsafe` without a `SAFETY` note |
| Correctness traps | `var` and `==` in JavaScript, default `Array.sort()`, mutable default arguments |
| Security | `eval`/`exec`, wildcard imports, `SELECT *` and comma joins in SQL |
| Hygiene | leftover `TODO`/`FIXME` (`GEN001`), lines over 120 characters (`GEN002`) |

### Deliberate exceptions

A rule can be waived on purpose with a comment on the same line or the line above, naming the rule and giving the reason:

```cpp
int* raw = new int[3];  // lint:allow CPP004 deliberate raw-pointer exercise
```

An exception without a reason does not pass review.

## 8. Review checklist before submitting

- [ ] I can explain the algorithm and its complexity in my own words.
- [ ] Every index and every numeric range has an argument.
- [ ] The samples pass, plus edge cases (smallest and largest input, sorted, reversed, duplicates when allowed).
- [ ] The output format matches the statement exactly.
- [ ] No warnings, no leftover markers, no unused code.
- [ ] `python scripts/check_all.py` passes.
