# C Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to C. C is chosen for problems about memory layout, bits, and manual buffers (see [Language Policy](../language-policy.md)).

Local build:

```bash
gcc -std=c17 -O2 -Wall -Wextra -Wpedantic -fsanitize=address,undefined main.c
```

A starting point is in `templates/solutions/main.c`.

## Principles

- keep code simple and disciplined
- write explicit logic
- respect the low-level nature of the language
- avoid unnecessary abstraction

## Naming

- variables: `snake_case`
- functions: `snake_case`
- constants: `UPPER_CASE`

## Input: never read more than you can hold

- Never use `gets`. Use `fgets` with the buffer size, or `scanf` with a width: `scanf("%99s", buffer)` for a 100-byte buffer.
- Always check the return value of `scanf` (it is the number of fields read), and of `fgets`.
- Convert numbers with `strtol` and check `errno` and the end pointer. `atoi` cannot report errors.
- Store the result of `getchar` in an `int`, not a `char`, or end-of-file is lost.

## Memory and strings

- Avoid variable-length arrays: a large size overflows the stack. Use a static array sized by the problem's limits, or `malloc`/`calloc` and check for `NULL`.
- Every `malloc` has one owner and one `free`.
- Use `snprintf` instead of `sprintf`, and never `strcpy` or `strcat`. Make sure strings end with `'\0'`.
- Initialize arrays and variables (`int counts[26] = {0};`).

## Numbers

- Use `size_t` for sizes and indexes of objects, and take care with subtraction: a `size_t` never goes below zero. Count down with `for (size_t i = n; i-- > 0;)`.
- Use `<stdint.h>` and `long long` when values can exceed `int`. Signed overflow is undefined behavior.
- Use the right `printf` conversions: `%d`, `%lld`, `%zu`, `%f`.
- Prefer `enum` or `static const` to `#define` for numeric limits.

## Style

- be careful with indexes, memory, and boundaries
- keep input and output handling explicit
- prefer straightforward structure over trickery

## Comments

Use comments when they clarify reasoning, edge cases, or implementation choices. In C, explaining why an index or a buffer size is safe is expected.

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `C001` | error | `gets` |
| `C002` | error | `scanf` `%s` or `%[` without a width |
| `C003` | error | `strcpy`, `strcat`, `sprintf`, `vsprintf` |
| `C004` | warning | `atoi`, `atol`, `atoll`, `atof` |
| `C005` | warning | `#define` used for a numeric constant |

## Goal

C solutions should reflect solid fundamentals, precision, and disciplined implementation.
