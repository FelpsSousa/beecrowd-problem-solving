# SQL Style Guide

Read [Coding Standards](../coding-standards.md) first; this page adds what is specific to SQL. SQL is used only for problems in the SQL category (see [Language Policy](../language-policy.md)). A starting point is in `templates/solutions/main.sql`.

The database engine used by the judge is still to be confirmed. Until it is, stay with standard SQL and note any engine-specific feature in the problem `README.md`.

## Principles

- readable queries first, clever ones never
- the result must match the requested columns, names, and order exactly

## Formatting

- Keywords in `UPPERCASE`; table and column names in `snake_case`.
- One clause per line, indented consistently:

```sql
SELECT c.name,
       COUNT(*) AS orders
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.id
GROUP BY c.name
ORDER BY orders DESC, c.name;
```

## Correctness

- Always use explicit `JOIN ... ON`, never comma joins. Qualify columns with table aliases.
- Name the columns you select. Never use `SELECT *`: it breaks when the table changes and hides what the query returns.
- Order is only guaranteed by `ORDER BY`. Without it, the row order is undefined.
- `NULL` is not equal to anything, including itself: compare with `IS NULL` and handle it with `COALESCE`.
- `COUNT(*)` counts rows; `COUNT(column)` skips `NULL`s.
- `WHERE` filters rows before grouping; `HAVING` filters groups after it. Every selected column that is not aggregated belongs in `GROUP BY`.

## Readability and performance

- Prefer common table expressions (`WITH`) to deeply nested subqueries.
- Prefer a `JOIN` to a correlated subquery when both express the same thing.
- Use `UNION ALL` unless duplicates must be removed (`UNION` pays for deduplication).
- Do not wrap an indexed column in a function inside `WHERE`; it prevents the index from being used.

## Security

Outside this repository, never build SQL by concatenating strings with user input: use parameterized queries. That is what prevents SQL injection.

## Comments

Use `--` comments for the reason behind a non-obvious condition.

## Automated checks

| Rule | Level | Meaning |
|------|-------|---------|
| `SQL001` | error | `SELECT *` |
| `SQL002` | error | comma join |
| `SQL003` | warning | lowercase keywords |

SQL solutions are linted and structurally validated but not executed yet: there is no SQL test runner.

## Goal

SQL solutions should be precise, readable, and independent of accidental row order.
