import sqlite3, os, random
from datetime import datetime, timedelta

DB_PATH = "ecommerce.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    city TEXT,
    signup_date DATE
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
""")

random.seed(42)

cities = ["Mumbai","Delhi","Bengaluru","Surat","Pune","Ahmedabad","Chennai","Kolkata","Hyderabad","Jaipur"]
first_names = ["Aarav","Vivaan","Aditya","Ananya","Diya","Ishaan","Kavya","Rohan","Meera","Sara",
               "Karan","Priya","Neha","Arjun","Riya","Sanjay","Pooja","Vikram","Anita","Rahul"]
last_names = ["Sharma","Verma","Patel","Gupta","Reddy","Iyer","Nair","Singh","Mehta","Joshi"]

customers = []
for i in range(1, 41):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    email = f"{name.lower().replace(' ', '.')}{i}@example.com"
    city = random.choice(cities)
    signup = (datetime(2024,1,1) + timedelta(days=random.randint(0, 500))).date()
    customers.append((i, name, email, city, signup.isoformat()))
cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

categories = [(1,"Electronics"),(2,"Clothing"),(3,"Home & Kitchen"),(4,"Books"),(5,"Sports & Fitness")]
cur.executemany("INSERT INTO categories VALUES (?,?)", categories)

product_catalog = [
    ("Wireless Mouse",1,699,150),("Bluetooth Headphones",1,1999,80),("Smartphone Stand",1,299,200),
    ("USB-C Cable",1,199,300),("4K Monitor",1,15999,25),("Laptop Backpack",1,1299,90),
    ("Men's T-Shirt",2,499,250),("Women's Kurti",2,899,180),("Denim Jeans",2,1499,120),
    ("Winter Jacket",2,2999,60),("Running Shoes",2,2499,100),
    ("Non-Stick Pan",3,899,140),("Mixer Grinder",3,2999,70),("LED Table Lamp",3,799,110),
    ("Bedsheet Set",3,999,130),
    ("Fiction Novel - The Journey",4,349,220),("Self-Help Book - Mindset",4,399,190),
    ("Cookbook - Indian Cuisine",4,599,95),
    ("Yoga Mat",5,699,160),("Dumbbell Set 10kg",5,1899,60),("Cricket Bat",5,1599,75),
    ("Badminton Racket",5,899,110),
]
products = [(i+1, p[0], p[1], p[2], p[3]) for i, p in enumerate(product_catalog)]
cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

statuses = ["Completed","Completed","Completed","Pending","Cancelled","Completed"]
orders = []
order_items = []
order_id = 1
item_id = 1
for cust in customers:
    n_orders = random.randint(0, 6)
    for _ in range(n_orders):
        odate = (datetime(2024,1,1) + timedelta(days=random.randint(0, 550))).date()
        status = random.choice(statuses)
        orders.append((order_id, cust[0], odate.isoformat(), status))
        n_items = random.randint(1, 4)
        chosen_products = random.sample(products, n_items)
        for prod in chosen_products:
            qty = random.randint(1, 5)
            # small price variance vs catalog price to simulate discounts
            unit_price = round(prod[3] * random.choice([1.0, 1.0, 0.9, 0.95]), 2)
            order_items.append((item_id, order_id, prod[0], qty, unit_price))
            item_id += 1
        order_id += 1

# Ensure some customers have NULL city (to demonstrate NULL handling)
cur.execute("UPDATE customers SET city = NULL WHERE customer_id IN (5, 17, 29)")

cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", order_items)

conn.commit()

print("Customers:", cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0])
print("Products:", cur.execute("SELECT COUNT(*) FROM products").fetchone()[0])
print("Orders:", cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("Order Items:", cur.execute("SELECT COUNT(*) FROM order_items").fetchone()[0])

conn.close()
