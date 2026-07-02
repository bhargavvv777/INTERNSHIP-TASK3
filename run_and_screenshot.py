import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

DB_PATH = "ecommerce.db"
OUT_DIR = "screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

queries = [
    ("a1_select_where_orderby", "-- Completed orders in 2024, most recent first",
     """SELECT order_id, customer_id, order_date, status
        FROM orders
        WHERE status = 'Completed' AND order_date >= '2024-01-01'
        ORDER BY order_date DESC
        LIMIT 12;"""),

    ("a2_groupby_status", "-- Order count per status",
     """SELECT status, COUNT(*) AS total_orders
        FROM orders GROUP BY status ORDER BY total_orders DESC;"""),

    ("a3_where_subquery_avg", "-- Products priced above average price",
     """SELECT product_name, price FROM products
        WHERE price > (SELECT AVG(price) FROM products)
        ORDER BY price ASC;"""),

    ("b1_inner_join", "-- INNER JOIN: order line items with product & customer names",
     """SELECT o.order_id, c.name AS customer_name, p.product_name,
               oi.quantity, oi.unit_price
        FROM orders o
        INNER JOIN customers c ON o.customer_id = c.customer_id
        INNER JOIN order_items oi ON o.order_id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.product_id
        ORDER BY o.order_id LIMIT 12;"""),

    ("b2_left_join", "-- LEFT JOIN: all customers with their order counts",
     """SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.name
        ORDER BY order_count ASC LIMIT 12;"""),

    ("b3_right_join", "-- RIGHT JOIN: all products with total quantity sold",
     """SELECT p.product_name, COALESCE(SUM(oi.quantity), 0) AS total_sold
        FROM order_items oi
        RIGHT JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_sold DESC LIMIT 12;"""),

    ("c1_subquery_above_avg_spend", "-- Customers who spent more than the average customer",
     """SELECT c.name,
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
        ORDER BY total_spent DESC LIMIT 12;"""),

    ("c2_subquery_top5_products", "-- Top 5 best-selling products by revenue",
     """SELECT product_name, revenue FROM (
            SELECT p.product_name, SUM(oi.quantity * oi.unit_price) AS revenue
            FROM order_items oi JOIN products p ON oi.product_id = p.product_id
            GROUP BY p.product_name
        ) AS product_revenue
        ORDER BY revenue DESC LIMIT 5;"""),

    ("c3_correlated_subquery_last_order_cancelled", "-- Customers whose most recent order was Cancelled",
     """SELECT c.name, o.order_date, o.status
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        WHERE o.order_date = (
            SELECT MAX(o2.order_date) FROM orders o2 WHERE o2.customer_id = c.customer_id
        ) AND o.status = 'Cancelled';"""),

    ("d1_aggregate_overall", "-- Total revenue, avg order-line value, order count (completed orders)",
     """SELECT COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
               ROUND(AVG(oi.quantity * oi.unit_price), 2) AS avg_line_value
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'Completed';"""),

    ("d2_avg_revenue_per_user", "-- Average revenue per user",
     """SELECT ROUND(SUM(oi.quantity * oi.unit_price) * 1.0 / COUNT(DISTINCT o.customer_id), 2) AS avg_revenue_per_user
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'Completed';"""),

    ("d3_revenue_by_category", "-- Revenue by category",
     """SELECT cat.category_name,
               SUM(oi.quantity * oi.unit_price) AS category_revenue,
               COUNT(DISTINCT oi.order_id) AS orders_containing_category
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories cat ON p.category_id = cat.category_id
        GROUP BY cat.category_name
        ORDER BY category_revenue DESC;"""),

    ("d4_having_avg_price", "-- Categories where avg product price > 800 (HAVING)",
     """SELECT cat.category_name, MIN(p.price) AS min_price,
               MAX(p.price) AS max_price, ROUND(AVG(p.price),2) AS avg_price
        FROM products p JOIN categories cat ON p.category_id = cat.category_id
        GROUP BY cat.category_name
        HAVING AVG(p.price) > 800
        ORDER BY avg_price DESC;"""),

    ("e1_view_customer_ltv", "-- VIEW: customer_lifetime_value (top 10)",
     """DROP VIEW IF EXISTS customer_lifetime_value;
        CREATE VIEW customer_lifetime_value AS
        SELECT c.customer_id, c.name,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS lifetime_value,
               COUNT(DISTINCT o.order_id) AS completed_orders
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'Completed'
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY c.customer_id, c.name;
        SELECT * FROM customer_lifetime_value ORDER BY lifetime_value DESC LIMIT 10;"""),

    ("e2_view_monthly_sales", "-- VIEW: monthly_sales_summary",
     """DROP VIEW IF EXISTS monthly_sales_summary;
        CREATE VIEW monthly_sales_summary AS
        SELECT strftime('%Y-%m', o.order_date) AS sales_month,
               COUNT(DISTINCT o.order_id) AS orders,
               ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'Completed'
        GROUP BY sales_month;
        SELECT * FROM monthly_sales_summary ORDER BY sales_month;"""),

    ("f1_create_indexes", "-- Creating indexes for optimization",
     """CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, order_date);
        SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"""),

    ("f2_explain_query_plan", "-- EXPLAIN QUERY PLAN using the new indexes",
     """EXPLAIN QUERY PLAN
        SELECT * FROM orders WHERE status = 'Completed' AND order_date >= '2024-06-01';"""),
]


def run_multi(sql_text):
    """Run possibly multiple ; separated statements, return columns+rows of LAST statement that returns rows."""
    statements = [s.strip() for s in sql_text.strip().split(";") if s.strip()]
    cols, rows = None, None
    for stmt in statements:
        cur.execute(stmt)
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
    conn.commit()
    return cols, rows


def render_screenshot(name, comment, sql_text, cols, rows):
    fig_height = 0.6 + 0.35 * (len(rows) + 2)
    fig, ax = plt.subplots(figsize=(11, max(fig_height, 2.2)))
    ax.axis("off")

    sql_display = sql_text.strip()
    title = f"$ sqlite3 ecommerce.db\n{comment}\n\n{sql_display}"
    ax.text(0, 1, title, fontsize=9, family="monospace", va="top", ha="left",
             color="#1a3d1a", wrap=True)

    if rows:
        table = ax.table(cellText=rows, colLabels=cols, loc="bottom",
                          cellLoc="left", bbox=[0, 0, 1, 0.55])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        for (r, c), cell in table.get_celld().items():
            if r == 0:
                cell.set_facecolor("#2d5f2d")
                cell.set_text_props(color="white", weight="bold")
            else:
                cell.set_facecolor("#f4f4f4" if r % 2 == 0 else "white")
    else:
        ax.text(0, 0.4, "(no rows returned)", fontsize=9, family="monospace")

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, f"{name}.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#eaf5ea")
    plt.close(fig)
    return out_path


log_lines = []
for name, comment, sql_text in queries:
    cols, rows = run_multi(sql_text)
    render_screenshot(name, comment, sql_text, cols, rows)
    log_lines.append(f"=== {name} ===\n{comment}\nColumns: {cols}\nRows returned: {len(rows) if rows else 0}\n")

with open("query_run_log.txt", "w") as f:
    f.write("\n".join(log_lines))

conn.close()
print("Done. Screenshots in", OUT_DIR)
print("\n".join(log_lines))
