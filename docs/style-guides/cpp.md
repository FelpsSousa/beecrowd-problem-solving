# C++ Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to C++.

## Standard

Prefer modern C++ with clarity and restraint. Use C++17 or C++20 when appropriate, but avoid unnecessary complexity. The judge compiles with a C++20 option; local builds use:

```bash
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Wshadow -fsanitize=address,undefined main.cpp
```

A starting point is in `templates/solutions/main.cpp`.

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
- types: `PascalCase`

## The `std` namespace

Always write `std::`. Never write `using namespace std;`.

It saves a few characters and costs clarity: the standard library has many short names (`left`, `right`, `count`, `distance`, `size`, `rank`, `hash`, `next`) that collide with your own variables and functions, producing errors such as `reference to 'left' is ambiguous`. Explicit qualification also shows at a glance what comes from the library. If a type name is long, give it an alias:

```cpp
using Graph = std::vector<std::vector<int>>;
```

## Includes

- Include exactly what you use, in alphabetical order. Never rely on another header pulling it in: that works on one compiler and fails on another.
- Never use `<bits/stdc++.h>`. It is an internal GCC header, not standard C++, and it hides missing includes.
- Avoid oversized competitive programming templates when the problem does not justify them.

## Ownership and memory

- Own heap objects with `std::unique_ptr` and create them with `std::make_unique`. The destructor releases the memory, so leaks, double frees, and use-after-free through that pointer are impossible by construction.
- A raw pointer (`Node*`) is allowed only as a **non-owning cursor** used to walk a structure.
- No `new`/`delete`, `malloc`/`free`.
- Prefer `std::vector` to C arrays and variable-length arrays; `std::array` for fixed sizes.
- A recursively destroyed structure (a degenerate tree or list) can overflow the stack when it holds hundreds of thousands of nodes. Fine for small limits; mention it when it is not.

## Types and conversions

- Use `long long` (or `std::int64_t`) when a value can exceed `int`. Decide after computing the worst case.
- Use `std::size_t` for container sizes and mind signed/unsigned comparisons.
- Convert with `static_cast`, never with a C-style cast.
- Initialize every variable. Mark single-argument constructors `explicit`. Use `const` by default and `constexpr` for constants. Prefer `enum class`.

## Performance

- Pass large objects by `const&`; use `std::string_view` for read-only text.
- `reserve()` a vector when the size is known.
- Write `'\n'`, not `std::endl` (`endl` flushes on every call).
- For large inputs only: `std::ios::sync_with_stdio(false); std::cin.tie(nullptr);` with a comment explaining why. Afterwards, never mix `cin`/`cout` with `scanf`/`printf`.
- Prefer `std::sort`, `std::lower_bound`, `std::accumulate` and friends to hand-written loops when they read better.
- `std::unordered_map` can be driven to its worst case by adversarial input; use `std::map` when the input is not trusted.

## Comments

Use comments only when they add reasoning that is not obvious from the code. Do not comment every line.

## Preferred style

- clear control flow
- explicit logic
- minimal hidden behavior
- no cryptic one-letter variable abuse unless used in very local contexts

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `CPP001` | error | `using namespace std` |
| `CPP002` | error | `<bits/stdc++.h>` |
| `CPP003` | warning | `std::endl` |
| `CPP004` | error | raw `new`/`delete` |
| `CPP005` | warning | C-style cast |
| `CPP006` | warning | `malloc`/`calloc`/`realloc`/`free` |
| `CPP007` | warning | `#define` macro |
| `CPP008` | error | std symbol used without its `#include` |
