# Task 3: SQL for Data Analysis

**Internship:** Elevate Labs — Data Analyst Internship
**Objective:** Use SQL queries to extract and analyze data from a database.
**Tools used:** SQLite (via Python's built-in `sqlite3` module)

## Dataset

A custom-built `Ecommerce_SQL_Database` with 5 related tables:

| Table         | Description                                   |
|---------------|------------------------------------------------|
| `customers`   | 40 customers (name, email, city, signup date) |
| `categories`  | 5 product categories                          |
| `products`    | 22 products with price & stock                |
| `orders`      | 142 orders (Completed / Pending / Cancelled)  |
| `order_items` | 403 line items linking orders to products     |

Schema DDL: [`schema.sql`](schema.sql)
Database build script (Python): [`build_db.py`](build_db.py)
Database file: [`ecommerce.db`](ecommerce.db)

## Files in this repo

```
├── README.md                 -- this file
├── schema.sql                -- table definitions (DDL)
├── build_db.py                -- generates & populates ecommerce.db with sample data
├── task3_queries.sql         -- all SQL queries for the task (deliverable)
├── run_and_screenshot.py     -- runs every query and renders output screenshots
├── ecommerce.db              -- the SQLite database file
├── query_run_log.txt         -- text log confirming each query ran successfully
└── screenshots/              -- PNG "screenshots" of each query's output
```

## What was done

All items from the mini-guide were covered in [`task3_queries.sql`](task3_queries.sql):

- **(a) SELECT / WHERE / ORDER BY / GROUP BY** — filtering completed orders, counting orders by status, filtering products above average price.
- **(b) JOINS** — INNER JOIN (orders + customers + products), LEFT JOIN (all customers incl. those with zero orders), RIGHT JOIN (all products incl. those never sold).
- **(c) Subqueries** — scalar subquery (customers who spent above average), subquery in `FROM` (top 5 products by revenue), correlated subquery (customers whose latest order was cancelled).
- **(d) Aggregate functions** — `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, including average revenue per user and category revenue breakdown with `HAVING`.
- **(e) Views** — `customer_lifetime_value` and `monthly_sales_summary`, created with `CREATE VIEW` and queried directly.
- **(f) Indexes** — created indexes on foreign keys and frequently filtered columns, verified with `EXPLAIN QUERY PLAN`.

Every query was executed against the real database; results and query text were rendered as PNG screenshots in the [`screenshots/`](screenshots) folder (one per query group).

## How to reproduce

```bash
pip install matplotlib
python3 build_db.py            # builds ecommerce.db
python3 run_and_screenshot.py  # runs all queries, saves screenshots/
```

Or open `ecommerce.db` in any SQL client (DB Browser for SQLite, DBeaver, etc.) and run the statements in `task3_queries.sql` directly.

---

## Interview Questions

**1. What is the difference between WHERE and HAVING?**
`WHERE` filters individual rows *before* any grouping/aggregation happens, and it cannot reference aggregate functions (e.g. `SUM()`, `COUNT()`). `HAVING` filters *groups* after `GROUP BY` has produced aggregated results, so it's used to filter on aggregate values (e.g. `HAVING AVG(price) > 800`). If a query has no `GROUP BY`, `HAVING` still works but effectively filters the single overall group.

**2. What are the different types of joins?**
- `INNER JOIN` — returns only rows that have matching values in both tables.
- `LEFT (OUTER) JOIN` — returns all rows from the left table, plus matched rows from the right table (unmatched columns are `NULL`).
- `RIGHT (OUTER) JOIN` — the mirror of LEFT JOIN: all rows from the right table, plus matches from the left.
- `FULL (OUTER) JOIN` — all rows from both tables, matched where possible, `NULL` where not (not natively supported in SQLite/MySQL — usually simulated with `UNION` of LEFT and RIGHT joins).
- `CROSS JOIN` — the Cartesian product of two tables (every row of A paired with every row of B).
- `SELF JOIN` — a table joined to itself, useful for hierarchical or comparative data (e.g. employees and their managers).

**3. How do you calculate average revenue per user in SQL?**
Sum total revenue and divide by the count of distinct users who generated it:
```sql
SELECT SUM(oi.quantity * oi.unit_price) * 1.0 / COUNT(DISTINCT o.customer_id) AS avg_revenue_per_user
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Completed';
```
The `* 1.0` forces floating-point division instead of integer division. `COUNT(DISTINCT ...)` is important — otherwise a user with many orders would be counted multiple times and skew the average downward.

**4. What are subqueries?**
A subquery is a query nested inside another SQL statement (in the `SELECT`, `FROM`, `WHERE`, or `HAVING` clause). It's evaluated first (or per-row, if correlated) and its result is used by the outer query. Types include:
- **Scalar subqueries** — return a single value (e.g. comparing a row to an overall average).
- **Subqueries in `FROM`** (derived tables) — treated like a temporary table the outer query can select from.
- **Correlated subqueries** — reference a column from the outer query, so they re-run for every outer row (e.g. "find each customer's most recent order").

**5. How do you optimize a SQL query?**
- Add **indexes** on columns used in `JOIN`, `WHERE`, and `ORDER BY` clauses (especially foreign keys).
- Avoid `SELECT *` — only select the columns you actually need.
- Use `EXPLAIN` / `EXPLAIN QUERY PLAN` to see whether the database is doing a full table scan vs. using an index.
- Filter as early as possible (`WHERE` before `JOIN` where possible) to reduce the working row set.
- Avoid unnecessary subqueries/correlated subqueries when a `JOIN` would do the same job faster.
- Use appropriate data types and avoid functions on indexed columns in `WHERE` clauses (e.g. `WHERE YEAR(date_col) = 2024` prevents index use — filter on a date range instead).
- Denormalize or add summary/materialized views for expensive, frequently-run aggregate queries.

**6. What is a view in SQL?**
A view is a saved, named SQL query that behaves like a virtual table. It doesn't store data itself (unless it's a materialized view) — every time you query it, the underlying query re-runs. Views are useful for simplifying complex/repeated queries, restricting access to specific columns, and presenting a consistent, reusable interface for analysis (e.g. `customer_lifetime_value` and `monthly_sales_summary` in this task).

**7. How would you handle null values in SQL?**
- Use `IS NULL` / `IS NOT NULL` to test for nulls (never `= NULL`, which always evaluates to unknown/false).
- Use `COALESCE(column, default_value)` (or `IFNULL` in MySQL/SQLite) to substitute a default when a value is null.
- Be careful with aggregates: `COUNT(column)` skips nulls, but `COUNT(*)` counts all rows regardless.
- In joins, `LEFT`/`RIGHT` joins intentionally introduce nulls for unmatched rows — decide whether to filter them out or keep and handle them.
- Decide at the schema level whether a column should allow `NULL` at all (`NOT NULL` constraint) based on whether "missing" is a valid state for that field.
