/* ============================================================
   TASK 3: SQL FOR DATA ANALYSIS
   Dataset: Ecommerce_SQL_Database (custom-built sample dataset)
   Tables: customers, categories, products, orders, order_items
   ============================================================ */

/* ------------------------------------------------------------
   0. SCHEMA (for reference — see schema.sql for full DDL)
   ------------------------------------------------------------
   customers(customer_id, name, email, city, signup_date)
   categories(category_id, category_name)
   products(product_id, product_name, category_id, price, stock_quantity)
   orders(order_id, customer_id, order_date, status)
   order_items(order_item_id, order_id, product_id, quantity, unit_price)
------------------------------------------------------------- */


/* ------------------------------------------------------------
   a. SELECT, WHERE, ORDER BY, GROUP BY
------------------------------------------------------------- */

-- a1: Basic SELECT with WHERE and ORDER BY
-- All completed orders placed in 2024, most recent first
SELECT order_id, customer_id, order_date, status
FROM orders
WHERE status = 'Completed' AND order_date >= '2024-01-01'
ORDER BY order_date DESC;

-- a2: GROUP BY with aggregate — number of orders per status
SELECT status, COUNT(*) AS total_orders
FROM orders
GROUP BY status
ORDER BY total_orders DESC;

-- a3: Products priced above the average price, cheapest first
SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products)
ORDER BY price ASC;


/* ------------------------------------------------------------
   b. JOINS (INNER, LEFT, RIGHT)
------------------------------------------------------------- */

-- b1: INNER JOIN — order line items with product & customer names
SELECT o.order_id, c.name AS customer_name, p.product_name,
       oi.quantity, oi.unit_price
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
ORDER BY o.order_id
LIMIT 20;

-- b2: LEFT JOIN — every customer, with order count (including customers with 0 orders)
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY order_count ASC;

-- b3: RIGHT JOIN — every product, with total quantity sold (including never-sold products)
-- NOTE: SQLite (3.39+) supports RIGHT JOIN. If unsupported, swap table order and use LEFT JOIN instead.
SELECT p.product_name, COALESCE(SUM(oi.quantity), 0) AS total_sold
FROM order_items oi
RIGHT JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_sold DESC;


/* ------------------------------------------------------------
   c. SUBQUERIES
------------------------------------------------------------- */

-- c1: Scalar subquery — customers who spent more than the average customer
SELECT c.name,
       (SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2)
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.customer_id = c.customer_id) AS total_spent
FROM customers c
WHERE (SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
       FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
       WHERE o.customer_id = c.customer_id)
      > (SELECT AVG(customer_total) FROM
           (SELECT SUM(oi.quantity * oi.unit_price) AS customer_total
            FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.customer_id))
ORDER BY total_spent DESC;

-- c2: Subquery in FROM clause — top 5 best-selling products by revenue
SELECT product_name, revenue
FROM (
    SELECT p.product_name, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.product_name
) AS product_revenue
ORDER BY revenue DESC
LIMIT 5;

-- c3: Correlated subquery — customers whose most recent order was 'Cancelled'
SELECT c.name, o.order_date, o.status
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_date = (
    SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = c.customer_id
)
AND o.status = 'Cancelled';


/* ------------------------------------------------------------
   d. AGGREGATE FUNCTIONS (SUM, AVG, etc.)
------------------------------------------------------------- */

-- d1: Total revenue, average order value, and order count (overall)
SELECT
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    ROUND(AVG(oi.quantity * oi.unit_price), 2) AS avg_line_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Completed';

-- d2: Average revenue per user (classic interview question — see Q3 below)
SELECT ROUND(SUM(oi.quantity * oi.unit_price) * 1.0 / COUNT(DISTINCT o.customer_id), 2) AS avg_revenue_per_user
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Completed';

-- d3: Revenue by category, sorted highest first
SELECT cat.category_name,
       SUM(oi.quantity * oi.unit_price) AS category_revenue,
       COUNT(DISTINCT oi.order_id) AS orders_containing_category
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY category_revenue DESC;

-- d4: Min, Max, Avg price per category (HAVING filter example)
SELECT cat.category_name,
       MIN(p.price) AS min_price,
       MAX(p.price) AS max_price,
       ROUND(AVG(p.price), 2) AS avg_price
FROM products p
JOIN categories cat ON p.category_id = cat.category_id
GROUP BY cat.category_name
HAVING AVG(p.price) > 800
ORDER BY avg_price DESC;


/* ------------------------------------------------------------
   e. VIEWS FOR ANALYSIS
------------------------------------------------------------- */

-- e1: View — customer lifetime value (only counts completed orders)
DROP VIEW IF EXISTS customer_lifetime_value;
CREATE VIEW customer_lifetime_value AS
SELECT c.customer_id, c.name,
       COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS lifetime_value,
       COUNT(DISTINCT o.order_id) AS completed_orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'Completed'
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.name;

-- Query the view
SELECT * FROM customer_lifetime_value
ORDER BY lifetime_value DESC
LIMIT 10;

-- e2: View — monthly sales summary
DROP VIEW IF EXISTS monthly_sales_summary;
CREATE VIEW monthly_sales_summary AS
SELECT strftime('%Y-%m', o.order_date) AS sales_month,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'Completed'
GROUP BY sales_month;

-- Query the view
SELECT * FROM monthly_sales_summary
ORDER BY sales_month;


/* ------------------------------------------------------------
   f. OPTIMIZE QUERIES WITH INDEXES
------------------------------------------------------------- */

-- f1: Index to speed up lookups/joins on orders by customer_id
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- f2: Index to speed up joins on order_items by order_id and product_id
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- f3: Index to speed up filtering orders by status/date (common WHERE clause)
CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, order_date);

-- f4: Verify the query planner uses the index (EXPLAIN QUERY PLAN)
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE customer_id = 10;

EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE status = 'Completed' AND order_date >= '2024-06-01';


/* ============================================================
   END OF FILE
   ============================================================ */
