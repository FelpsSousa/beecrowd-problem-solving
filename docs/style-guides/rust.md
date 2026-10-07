# Rust Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to Rust. Rust is chosen when ownership, lifetimes, and memory safety are the point of the exercise, often as the counterpart of a C solution (see [Language Policy](../language-policy.md)).

Judge support for Rust is not confirmed yet, so Rust solutions are local study material until it is. A starting point is in `templates/solutions/main.rs`.

Local build and checks:

```bash
rustc --edition 2021 -O -D warnings main.rs
rustfmt --check main.rs
```

When a Cargo project is used for study, also run `cargo clippy -- -D warnings`.

## Principles

- let the type system carry the invariants
- prefer clarity to cleverness; iterators when they read better than indexes
- standard library only: no external crates

## Naming

- functions, variables, modules: `snake_case`
- types and traits: `PascalCase`
- constants: `UPPER_CASE`

Formatting is whatever `rustfmt` produces (4 spaces).

## Input and output

- Read all input with `read_to_string` and parse with `split_ascii_whitespace()`.
- Write through a `BufWriter` on a locked stdout and `writeln!`. A `println!` per line locks and flushes repeatedly in a hot loop.

## Errors

- Do not leave a bare `unwrap()`. Use `expect("reason")`, the `?` operator, or an explicit `match`. When the judge guarantees the input, an `expect` with a message is acceptable.
- Model absence with `Option` and failure with `Result`.

## Numbers

- Arithmetic overflow panics in debug builds and **wraps silently in release builds**. Choose deliberately: `checked_*`, `wrapping_*`, `saturating_*`.
- `as` casts truncate silently. Prefer `From`/`TryFrom` when the range is not obviously safe.
- Use `usize` for indexes and `i64`/`u64` for values that can be large.

## Ownership and performance

- Borrow (`&[T]`, `&str`) instead of cloning; clone only with a reason.
- `Vec::with_capacity` when the size is known; `sort_unstable` when stability is not needed.
- `HashMap` uses a randomly keyed, DoS-resistant hasher by default and is slower than a plain one; `BTreeMap` is a good ordered alternative.

## `unsafe`

`unsafe` is allowed only with a `// SAFETY:` comment, on the line above or the same line, explaining why the operation is sound. Prefer a safe design when one exists.

## Comments

Comment the reason, not the syntax.

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `RS001` | warning | `unwrap()` |
| `RS002` | error | `unsafe` without a `// SAFETY:` comment |

`rustfmt` and `clippy` complement these checks and are run manually.

## Goal

Rust solutions should show how ownership and types make a whole class of memory bugs impossible.
