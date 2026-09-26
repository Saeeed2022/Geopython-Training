from nbbuild import NB, SETUP

PGSETUP = '''
import pandas as pd
import psycopg
from geotrain.db import DSN

def q(query, params=None, schema="shop"):
    """Run SQL (one or several statements) in `schema`; return the last result as a table, if any."""
    with psycopg.connect(DSN, options=f"-c search_path={schema},public") as conn, conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description is None:
            return None
        return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])

def try_sql(query, schema="shop"):
    """Run SQL and print the error instead of stopping (to see what the database refuses)."""
    try:
        r = q(query, schema=schema)
        print("✅ accepted")
        return r
    except psycopg.Error as e:
        print("❌ refused:", e.diag.message_primary)

q("CREATE SCHEMA IF NOT EXISTS shop", schema="public")
print(q("SELECT version()", schema="public").iloc[0, 0])
'''


def build():
    nb = NB("S2_postgresql", "S2 · PostgreSQL — building and running a real database")
    nb.md("""
    **What PostgreSQL is:** a database *server*: a program that stores tables safely, lets many users work at the same time,
    checks that data follows rules, and answers SQL. PostGIS is an extension that runs **inside** PostgreSQL.

    In S1 you **asked questions** (reading). Here you learn to **build and look after** a database (writing):

    | Topic | Daily picture |
    |---|---|
    | database → schema → table | a building → floors (folders) → filing cabinets |
    | data types (`integer`, `numeric`, `text`, `date`, `timestamp`, `boolean`) | forms where a date field only accepts dates |
    | constraints (`PRIMARY KEY`, `NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY`) | a bouncer who refuses wrong data at the door |
    | `INSERT`, `UPDATE`, `DELETE` | adding, correcting, removing cards in the cabinet |
    | transactions | "all or nothing": a bank transfer never takes money without delivering it |
    | indexes | the index at the back of a book |
    | views | a saved question that always shows fresh answers |
    | roles and `GRANT` | keys: some people may only read, others may also write |

    **The psql command line (optional):** PostgreSQL's own terminal client. With Docker: `docker exec -it geotrain-db psql -U geo -d geotrain`.
    Useful commands: `\\l` databases, `\\dn` schemas, `\\dt shop.*` tables, `\\d shop.customers` columns of a table, `\\q` quit.
    In this notebook we use SQL from Python; every psql command has an SQL equivalent (shown below).

    We build a small **Riverton bakery-shop** database in the schema `shop`: customers, products, orders.
    """)
    nb.code(SETUP)
    nb.code(PGSETUP)

    nb.level(1, "Basics: schemas, tables, data types, INSERT", "create tables with the right data types and fill them.",
             "Designing a paper form: which boxes, and what may be written in each box.")
    nb.ex("1.1", "What is in the database?", "information_schema.tables",
          purpose_a="`information_schema` is a set of views describing the database itself (tables, columns…); the SQL version of psql's `\\dt`.",
          life_a="Exploring a database someone gives you access to.",
          hint="`SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema')`.",
          starter="""
          q(\"\"\"SELECT table_schema, table_name, table_type FROM information_schema.____
               WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY 1, 2\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT table_schema, table_name, table_type FROM information_schema.tables
               WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY 1, 2\"\"\")
          """)
    nb.ex("1.2", "Create a table with data types", "CREATE TABLE name (column type, ...)",
          purpose_a="Creates an empty table; each column gets a data type that decides what it can hold.",
          life_a="Designing the customer list of a shop: name (text), birth date (date), newsletter (yes/no).",
          hint="Types: `serial` (auto-numbered integer), `text`, `date`, `boolean`, `numeric(6,2)` (money with 2 decimals). `DROP TABLE IF EXISTS` first, so you can re-run.",
          starter="""
          q(\"\"\"DROP TABLE IF EXISTS orders, products, customers CASCADE;
               CREATE TABLE customers (
                   customer_id serial,
                   name        text,
                   birth_date  ____,
                   newsletter  boolean
               );\"\"\")
          q("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'shop' AND table_name = 'customers'")
          """,
          solution="""
          q(\"\"\"DROP TABLE IF EXISTS orders, products, customers CASCADE;
               CREATE TABLE customers (
                   customer_id serial,
                   name        text,
                   birth_date  date,
                   newsletter  boolean
               );\"\"\")
          q("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'shop' AND table_name = 'customers'")
          """)
    nb.ex("1.3", "Add rows", "INSERT INTO t (cols) VALUES (...), (...)",
          purpose_a="Adds new rows; you list the columns and one bracket of values per row.",
          life_a="Registering new customers.",
          hint="Dates as text in ISO format: `'1985-03-12'`. `customer_id` fills itself (serial).",
          starter="""
          q(\"\"\"INSERT INTO customers (name, birth_date, newsletter) VALUES
               ('Amira', '1985-03-12', true),
               ('Ben',   '1999-11-02', false),
               ('Chen',  '1972-07-30', ____)\"\"\")
          q("SELECT * FROM customers")
          """,
          solution="""
          q(\"\"\"INSERT INTO customers (name, birth_date, newsletter) VALUES
               ('Amira', '1985-03-12', true),
               ('Ben',   '1999-11-02', false),
               ('Chen',  '1972-07-30', true)\"\"\")
          q("SELECT * FROM customers")
          """)
    nb.ex("1.4", "Types protect you", "inserting a wrong type",
          purpose_q="What is the **purpose** of this experiment? What does the database do with a date like `'2024-02-30'`?",
          purpose_a="It shows that data types reject impossible values (there is no 30 February), instead of silently storing rubbish like a spreadsheet would.",
          life_a="A spreadsheet happily stores 'next Tuesday' in a date column; a database refuses it, so later calculations stay correct.",
          hint="Use `try_sql(...)`, which prints the error message instead of stopping.",
          starter="""
          try_sql("INSERT INTO customers (name, birth_date) VALUES ('Dana', '2024-02-____')")
          try_sql("INSERT INTO customers (name, newsletter) VALUES ('Eli', 'maybe')")
          """,
          solution="""
          try_sql("INSERT INTO customers (name, birth_date) VALUES ('Dana', '2024-02-30')")
          try_sql("INSERT INTO customers (name, newsletter) VALUES ('Eli', 'maybe')")
          """)

    nb.level(2, "Core tools: constraints, UPDATE, DELETE", "make the database refuse bad data, and change data safely.",
             "A bouncer at the door checks every guest; a careful clerk corrects cards without throwing away the wrong ones.")
    nb.ex("2.1", "Keys and rules", "PRIMARY KEY, NOT NULL, UNIQUE, CHECK",
          purpose_a="Constraints are rules the database enforces: `PRIMARY KEY` = unique id of each row, `NOT NULL` = must be filled, `UNIQUE` = no duplicates, `CHECK` = custom rule.",
          life_a="No product without a name, no negative price, no two products with the same code.",
          hint="`price numeric(6,2) NOT NULL CHECK (price > 0)`. Recreate customers too, now with a primary key.",
          starter="""
          q(\"\"\"DROP TABLE IF EXISTS orders, products, customers CASCADE;
               CREATE TABLE customers (customer_id serial PRIMARY KEY, name text NOT NULL, birth_date date, newsletter boolean DEFAULT false);
               CREATE TABLE products (
                   product_id serial PRIMARY KEY,
                   code       text UNIQUE NOT NULL,
                   name       text NOT NULL,
                   price      numeric(6,2) NOT NULL CHECK (price ____ 0)
               );
               INSERT INTO customers (name, birth_date, newsletter) VALUES ('Amira', '1985-03-12', true), ('Ben', '1999-11-02', false), ('Chen', '1972-07-30', true);
               INSERT INTO products (code, name, price) VALUES ('BRD', 'Rye bread', 3.20), ('CRO', 'Croissant', 1.40), ('CAK', 'Cheesecake', 18.50);\"\"\")
          try_sql("INSERT INTO products (code, name, price) VALUES ('BRD', 'Another bread', 2.00)")
          try_sql("INSERT INTO products (code, name, price) VALUES ('FRE', 'Free cookie', 0)")
          try_sql("INSERT INTO products (code, price) VALUES ('XXX', 1.00)")
          """,
          solution="""
          q(\"\"\"DROP TABLE IF EXISTS orders, products, customers CASCADE;
               CREATE TABLE customers (customer_id serial PRIMARY KEY, name text NOT NULL, birth_date date, newsletter boolean DEFAULT false);
               CREATE TABLE products (
                   product_id serial PRIMARY KEY,
                   code       text UNIQUE NOT NULL,
                   name       text NOT NULL,
                   price      numeric(6,2) NOT NULL CHECK (price > 0)
               );
               INSERT INTO customers (name, birth_date, newsletter) VALUES ('Amira', '1985-03-12', true), ('Ben', '1999-11-02', false), ('Chen', '1972-07-30', true);
               INSERT INTO products (code, name, price) VALUES ('BRD', 'Rye bread', 3.20), ('CRO', 'Croissant', 1.40), ('CAK', 'Cheesecake', 18.50);\"\"\")
          try_sql("INSERT INTO products (code, name, price) VALUES ('BRD', 'Another bread', 2.00)")
          try_sql("INSERT INTO products (code, name, price) VALUES ('FRE', 'Free cookie', 0)")
          try_sql("INSERT INTO products (code, price) VALUES ('XXX', 1.00)")
          """)
    nb.ex("2.2", "Foreign keys: links that cannot break", "REFERENCES other_table(key)",
          purpose_a="A foreign key says: this value must exist in another table. It prevents orders for customers that do not exist.",
          life_a="Every order belongs to a real customer and a real product — the links JOIN uses in S1.",
          hint="`customer_id integer NOT NULL REFERENCES customers(customer_id)`. Then try an order for customer 99.",
          starter="""
          q(\"\"\"CREATE TABLE orders (
                   order_id    serial PRIMARY KEY,
                   customer_id integer NOT NULL REFERENCES customers(customer_id),
                   product_id  integer NOT NULL ____ products(product_id),
                   quantity    integer NOT NULL CHECK (quantity > 0),
                   ordered_at  timestamp NOT NULL DEFAULT now()
               );
               INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES
                   (1, 1, 2, '2025-05-01 08:10'), (1, 2, 4, '2025-05-01 08:10'), (2, 3, 1, '2025-05-02 16:30'),
                   (3, 2, 6, '2025-05-03 07:45'), (2, 2, 2, '2025-05-09 09:00'), (3, 1, 1, '2025-05-10 12:15');\"\"\")
          try_sql("INSERT INTO orders (customer_id, product_id, quantity) VALUES (99, 1, 1)")
          """,
          solution="""
          q(\"\"\"CREATE TABLE orders (
                   order_id    serial PRIMARY KEY,
                   customer_id integer NOT NULL REFERENCES customers(customer_id),
                   product_id  integer NOT NULL REFERENCES products(product_id),
                   quantity    integer NOT NULL CHECK (quantity > 0),
                   ordered_at  timestamp NOT NULL DEFAULT now()
               );
               INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES
                   (1, 1, 2, '2025-05-01 08:10'), (1, 2, 4, '2025-05-01 08:10'), (2, 3, 1, '2025-05-02 16:30'),
                   (3, 2, 6, '2025-05-03 07:45'), (2, 2, 2, '2025-05-09 09:00'), (3, 1, 1, '2025-05-10 12:15');\"\"\")
          try_sql("INSERT INTO orders (customer_id, product_id, quantity) VALUES (99, 1, 1)")
          """)
    nb.ex("2.3", "Correct data", "UPDATE t SET col = value WHERE ... RETURNING ...",
          purpose_a="Changes values in existing rows. **The WHERE decides which rows** — without it, every row changes!",
          life_a="Croissants get 10 % more expensive.",
          hint="`UPDATE products SET price = round(price * 1.10, 2) WHERE code = 'CRO' RETURNING code, price`. `RETURNING` shows the changed rows.",
          starter="""
          q("UPDATE products SET price = round(price * 1.10, 2) ____ code = 'CRO' RETURNING code, name, price")
          """,
          solution="""
          q("UPDATE products SET price = round(price * 1.10, 2) WHERE code = 'CRO' RETURNING code, name, price")
          """,
          note="Professional habit: first run the same WHERE as a `SELECT` to see which rows you will change.")
    nb.ex("2.4", "Remove data (and why the database protects links)", "DELETE FROM t WHERE ...",
          purpose_a="Removes rows. A foreign key stops you deleting a customer who still has orders (the orders would point to nobody).",
          life_a="GDPR request: remove a customer — first their orders, or anonymise them.",
          hint="Try to delete Ben (customer 2) → refused. Delete his orders first, then Ben.",
          starter="""
          try_sql("DELETE FROM customers WHERE customer_id = 2")
          q("DELETE FROM orders WHERE customer_id = ____")
          try_sql("DELETE FROM customers WHERE customer_id = 2")
          q("SELECT * FROM customers")
          """,
          solution="""
          try_sql("DELETE FROM customers WHERE customer_id = 2")
          q("DELETE FROM orders WHERE customer_id = 2")
          try_sql("DELETE FROM customers WHERE customer_id = 2")
          q("SELECT * FROM customers")
          """)

    nb.level(3, "Combining: transactions, COPY, indexes, views", "load data in bulk, keep changes safe, make queries fast, and save questions as views.",
             "Moving house: pack everything in one go (COPY), check nothing breaks on the way (transactions), and label the boxes (indexes).")
    nb.ex("3.1", "All or nothing: transactions", "BEGIN ... COMMIT / ROLLBACK",
          purpose_a="Groups several statements; either all are saved (`COMMIT`) or none (`ROLLBACK`, also automatic on error).",
          life_a="An order that reduces stock **and** creates an invoice: never one without the other.",
          hint="In psycopg, statements in one `with psycopg.connect(...)` block form one transaction. An error inside → nothing is saved. Here the second INSERT breaks a CHECK, so the first one is undone too.",
          starter="""
          before = q("SELECT count(*) FROM orders").iloc[0, 0]
          try:
              with psycopg.connect(DSN, options="-c search_path=shop") as conn:
                  conn.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (1, 3, 1)")
                  conn.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (1, 3, ____)")   # breaks CHECK
          except psycopg.Error as e:
              print("rolled back:", e.diag.message_primary)
          print(before, "->", q("SELECT count(*) FROM orders").iloc[0, 0])
          """,
          solution="""
          before = q("SELECT count(*) FROM orders").iloc[0, 0]
          try:
              with psycopg.connect(DSN, options="-c search_path=shop") as conn:
                  conn.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (1, 3, 1)")
                  conn.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (1, 3, -5)")
          except psycopg.Error as e:
              print("rolled back:", e.diag.message_primary)
          print(before, "->", q("SELECT count(*) FROM orders").iloc[0, 0])
          """)
    nb.ex("3.2", "Bulk load with COPY", "COPY table FROM STDIN (FORMAT csv)",
          purpose_a="Loads many rows at once from a file/stream — much faster than many INSERTs.",
          life_a="Importing a year of till receipts (hundreds of thousands of rows) from a CSV export.",
          hint="We generate 200 000 random orders as CSV text in memory and send it with psycopg's `cursor.copy`.",
          starter="""
          import io, numpy as np
          rng = np.random.default_rng(0)
          n = 200_000
          ts = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365 * 24 * 60, n), unit="m")
          csv = pd.DataFrame({"customer_id": rng.choice([1, 3], n), "product_id": rng.integers(1, 4, n),
                              "quantity": rng.integers(1, 6, n), "ordered_at": ts}).to_csv(index=False, header=False)
          with psycopg.connect(DSN, options="-c search_path=shop") as conn, conn.cursor() as cur:
              with cur.____("COPY orders (customer_id, product_id, quantity, ordered_at) FROM STDIN (FORMAT csv)") as cp:
                  cp.write(csv)
          q("SELECT count(*) FROM orders")
          """,
          solution="""
          import io, numpy as np
          rng = np.random.default_rng(0)
          n = 200_000
          ts = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365 * 24 * 60, n), unit="m")
          csv = pd.DataFrame({"customer_id": rng.choice([1, 3], n), "product_id": rng.integers(1, 4, n),
                              "quantity": rng.integers(1, 6, n), "ordered_at": ts}).to_csv(index=False, header=False)
          with psycopg.connect(DSN, options="-c search_path=shop") as conn, conn.cursor() as cur:
              with cur.copy("COPY orders (customer_id, product_id, quantity, ordered_at) FROM STDIN (FORMAT csv)") as cp:
                  cp.write(csv)
          q("SELECT count(*) FROM orders")
          """,
          note="From psql you would write `\\copy shop.orders FROM 'orders.csv' CSV HEADER`.")
    nb.ex("3.3", "Indexes and EXPLAIN ANALYZE", "CREATE INDEX ... ON t (col)",
          purpose_a="An index lets the database find rows without reading the whole table; `EXPLAIN ANALYZE` shows the plan and the real time.",
          life_a="'All orders of 3 May' must be fast even with millions of orders.",
          hint="Run the same query before and after `CREATE INDEX orders_time_idx ON orders (ordered_at)`. Look for **Seq Scan** (reads everything) vs **Index Scan** / **Bitmap Index Scan**.",
          starter="""
          query = "SELECT count(*) FROM orders WHERE ordered_at BETWEEN '2025-05-03' AND '2025-05-04'"
          def plan(sql):
              return "\\n".join(q("EXPLAIN ANALYZE " + sql).iloc[:, 0])
          print(plan(query).splitlines()[0:3])
          q("CREATE INDEX IF NOT EXISTS orders_time_idx ON orders (____); ANALYZE orders;")
          print(plan(query).splitlines()[0:3])
          """,
          solution="""
          query = "SELECT count(*) FROM orders WHERE ordered_at BETWEEN '2025-05-03' AND '2025-05-04'"
          def plan(sql):
              return "\\n".join(q("EXPLAIN ANALYZE " + sql).iloc[:, 0])
          print(plan(query).splitlines()[0:3])
          q("CREATE INDEX IF NOT EXISTS orders_time_idx ON orders (ordered_at); ANALYZE orders;")
          print(plan(query).splitlines()[0:3])
          """,
          note="Indexes cost disk space and slow down writing a little. Index the columns you filter or join on often. (Spatial indexes, GIST, work the same way — B0/B1.)")
    nb.ex("3.4", "Views: saved questions", "CREATE VIEW name AS SELECT ...",
          purpose_a="Stores a query under a name. Reading the view runs the query on the current data.",
          life_a="'Revenue per month' for the shop owner, always up to date, without knowing SQL.",
          hint="`date_trunc('month', ordered_at)` cuts a timestamp to the month. Join orders with products for the price.",
          starter="""
          q(\"\"\"CREATE OR REPLACE VIEW monthly_revenue AS
               SELECT date_trunc('month', o.ordered_at)::date AS month, sum(o.quantity * p.price) AS revenue
               FROM orders o JOIN products p USING (product_id)
               GROUP BY 1\"\"\")
          q("SELECT * FROM ____ ORDER BY month LIMIT 6")
          """,
          solution="""
          q(\"\"\"CREATE OR REPLACE VIEW monthly_revenue AS
               SELECT date_trunc('month', o.ordered_at)::date AS month, sum(o.quantity * p.price) AS revenue
               FROM orders o JOIN products p USING (product_id)
               GROUP BY 1\"\"\")
          q("SELECT * FROM monthly_revenue ORDER BY month LIMIT 6")
          """)

    nb.level(4, "Professional: upserts, roles, materialized views, maintenance", "run the database like a professional: safe re-loads, access rights, fast dashboards, backups.",
             "A building manager: who has which key, how the lift is maintained, and how to rebuild after a fire (backup).")
    nb.pro("4.1", "Insert or update: the 'upsert'", "Data engineering (idempotent loading)",
           scenario="The bakery gets a new price list every week. Some products are new, some have new prices. Load it so that running the load twice does not create duplicates.",
           plan_hint="`INSERT ... ON CONFLICT (code) DO UPDATE SET price = EXCLUDED.price`. `EXCLUDED` = the row you tried to insert. Needs the UNIQUE constraint on `code` (2.1).",
           starter="""
           upsert = \"\"\"INSERT INTO products (code, name, price) VALUES
                         ('BRD', 'Rye bread', 3.50), ('PRZ', 'Pretzel', 1.10)
                       ON CONFLICT (____) DO UPDATE SET price = EXCLUDED.price, name = EXCLUDED.name\"\"\"
           q(upsert); q(upsert)          # run twice on purpose
           q("SELECT code, name, price FROM products ORDER BY product_id")
           """,
           solution="""
           upsert = \"\"\"INSERT INTO products (code, name, price) VALUES
                         ('BRD', 'Rye bread', 3.50), ('PRZ', 'Pretzel', 1.10)
                       ON CONFLICT (code) DO UPDATE SET price = EXCLUDED.price, name = EXCLUDED.name\"\"\"
           q(upsert); q(upsert)
           q("SELECT code, name, price FROM products ORDER BY product_id")
           """,
           answer="An *idempotent* load gives the same result no matter how often it runs — essential for scheduled jobs that may be restarted.")
    nb.pro("4.2", "A read-only user for the city", "Security (roles and permissions)",
           scenario="Create a role `city_analyst` that may **read** the `shop` views and tables but not change anything. Prove it: as that role, SELECT works and DELETE is refused.",
           plan_hint="`CREATE ROLE city_analyst NOLOGIN; GRANT USAGE ON SCHEMA shop TO city_analyst; GRANT SELECT ON ALL TABLES IN SCHEMA shop TO city_analyst;` Test inside one transaction with `SET ROLE city_analyst`.",
           starter="""
           q(\"\"\"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'city_analyst') THEN CREATE ROLE city_analyst NOLOGIN; END IF; END $$;
                GRANT USAGE ON SCHEMA shop TO city_analyst;
                GRANT ____ ON ALL TABLES IN SCHEMA shop TO city_analyst;\"\"\")
           with psycopg.connect(DSN, options="-c search_path=shop") as conn:
               conn.execute("SET ROLE city_analyst")
               print("read:", conn.execute("SELECT count(*) FROM monthly_revenue").fetchone())
               try:
                   conn.execute("DELETE FROM orders")
               except psycopg.Error as e:
                   print("delete refused:", e.diag.message_primary)
           """,
           solution="""
           q(\"\"\"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'city_analyst') THEN CREATE ROLE city_analyst NOLOGIN; END IF; END $$;
                GRANT USAGE ON SCHEMA shop TO city_analyst;
                GRANT SELECT ON ALL TABLES IN SCHEMA shop TO city_analyst;\"\"\")
           with psycopg.connect(DSN, options="-c search_path=shop") as conn:
               conn.execute("SET ROLE city_analyst")
               print("read:", conn.execute("SELECT count(*) FROM monthly_revenue").fetchone())
               try:
                   conn.execute("DELETE FROM orders")
               except psycopg.Error as e:
                   print("delete refused:", e.diag.message_primary)
           """,
           answer="Give every user the smallest rights they need (the *least privilege* principle). In real life the role would have `LOGIN` and a password, and QGIS users would connect with it.")
    nb.pro("4.3", "A fast dashboard table: materialized view", "Performance (pre-computed results)",
           scenario="The revenue view (3.4) re-computes 200 000 rows every time. Make a **materialized view** that stores the result, compare the speed, and refresh it after new orders arrive.",
           plan_hint="`CREATE MATERIALIZED VIEW mv_revenue AS SELECT * FROM monthly_revenue;` then `REFRESH MATERIALIZED VIEW mv_revenue;`. Time both reads with `EXPLAIN ANALYZE` (look at 'Execution Time').",
           starter="""
           q("DROP MATERIALIZED VIEW IF EXISTS mv_revenue; CREATE ____ VIEW mv_revenue AS SELECT * FROM monthly_revenue;")
           for name in ["monthly_revenue", "mv_revenue"]:
               print(name, [l for l in q(f"EXPLAIN ANALYZE SELECT * FROM {name}").iloc[:, 0] if "Execution Time" in l])
           q("INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES (1, 3, 100, '2025-12-31 18:00')")
           q("REFRESH MATERIALIZED VIEW mv_revenue")
           q("SELECT * FROM mv_revenue ORDER BY month DESC LIMIT 1")
           """,
           solution="""
           q("DROP MATERIALIZED VIEW IF EXISTS mv_revenue; CREATE MATERIALIZED VIEW mv_revenue AS SELECT * FROM monthly_revenue;")
           for name in ["monthly_revenue", "mv_revenue"]:
               print(name, [l for l in q(f"EXPLAIN ANALYZE SELECT * FROM {name}").iloc[:, 0] if "Execution Time" in l])
           q("INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES (1, 3, 100, '2025-12-31 18:00')")
           q("REFRESH MATERIALIZED VIEW mv_revenue")
           q("SELECT * FROM mv_revenue ORDER BY month DESC LIMIT 1")
           """,
           answer="A view is always fresh but slow; a materialized view is fast but only as fresh as its last REFRESH. Dashboards usually use materialized views refreshed on a schedule.")
    nb.md("""
    ### Maintenance you should know (no code needed)

    - **Backup:** `docker exec geotrain-db pg_dump -U geo -d geotrain -Fc -f /tmp/geotrain.dump` (then copy it out);
      restore with `pg_restore -d geotrain geotrain.dump`. A backup you never tested restoring is not a backup.
    - **VACUUM / ANALYZE:** PostgreSQL cleans up and updates statistics automatically (*autovacuum*); run `ANALYZE table` after big loads.
    - **Size:** `SELECT pg_size_pretty(pg_total_relation_size('shop.orders'))`.
    """)

    nb.test("""
    For each: **plan in words → SQL → check → one sentence.**
    """, [
        ("task", """
        **A.** Add a column `vegan boolean DEFAULT false` to `products`, and mark the rye bread as vegan.
        """, """
        ```python
        q("ALTER TABLE products ADD COLUMN IF NOT EXISTS vegan boolean DEFAULT false")
        q("UPDATE products SET vegan = true WHERE code = 'BRD' RETURNING code, vegan")
        ```
        """),
        ("task", """
        **B.** Make sure no order can be placed in the future: add a CHECK constraint on `ordered_at`, and prove that it refuses a 2030 order.
        """, """
        ```python
        try_sql("ALTER TABLE orders ADD CONSTRAINT no_future CHECK (ordered_at <= now())")
        try_sql("INSERT INTO orders (customer_id, product_id, quantity, ordered_at) VALUES (1, 1, 1, '2030-01-01')")
        ```
        (Adding the constraint also fails if an existing row breaks it — then fix the data first.)
        """),
        ("task", """
        **C.** Which customer spent the most in 2025? (JOIN orders, products, customers; GROUP BY.)
        """, """
        ```python
        q(\"\"\"SELECT c.name, sum(o.quantity * p.price) AS spent
             FROM orders o JOIN products p USING (product_id) JOIN customers c USING (customer_id)
             WHERE o.ordered_at >= '2025-01-01' AND o.ordered_at < '2026-01-01'
             GROUP BY c.name ORDER BY spent DESC LIMIT 1\"\"\")
        ```
        """),
        ("model", """
        **D · Modelling a database.** Design the tables for Riverton's **tree register**: every street tree has a species, planting date, height,
        health checks over the years (date, inspector, result), and a location. Which tables, keys and constraints?
        """, """
        - `species(species_id PK, latin_name UNIQUE NOT NULL, common_name)`
        - `trees(tree_id PK, species_id FK → species, planted date CHECK (planted <= current_date), height_m numeric CHECK (height_m > 0), geom geometry(Point, 32633))`
        - `inspectors(inspector_id PK, name NOT NULL)`
        - `inspections(inspection_id PK, tree_id FK → trees, inspector_id FK → inspectors, inspected_on date NOT NULL, result text CHECK (result IN ('healthy','watch','remove')))`
        One tree has many inspections (one-to-many) → a separate table, not columns like `check_2021`, `check_2022`.
        Indexes on `inspections(tree_id)` and a GIST index on `trees(geom)`. That is **normalisation**: each fact stored once.
        """),
    ])

    nb.project(
        "Build the Riverton Bike Share database properly",
        """In S1 you queried loose tables with no rules. Now build the **real** database: schema `bikedb` with primary keys, foreign keys,
        CHECK rules and indexes; load the CSV files with COPY; find and handle the bad rows the company sent; create views for the city dashboard,
        a read-only role for the city, and a geometry column so the stations appear in QGIS.""",
        [("bike_stations.csv", "24 stations (id, name, capacity, lon, lat, opened)"),
         ("bike_members.csv", "800 members"),
         ("bike_trips_dirty.csv", "the trips again, **plus some bad rows** (unknown stations, negative durations) — your constraints must catch them")],
        [("""**Design and create the tables** with keys and rules: stations (PK, capacity > 0), members (PK, plan only
          'annual'/'monthly'/'pay-as-you-go'), trips (PK, FKs to stations for start and end, FK to members but allowed to be empty, duration > 0).""", """
          ```python
          q(\"\"\"DROP SCHEMA IF EXISTS bikedb CASCADE; CREATE SCHEMA bikedb; SET search_path = bikedb;
               CREATE TABLE stations (station_id integer PRIMARY KEY, name text NOT NULL, capacity integer CHECK (capacity > 0),
                                      lon double precision NOT NULL, lat double precision NOT NULL, opened date);
               CREATE TABLE members (member_id integer PRIMARY KEY, age_group text NOT NULL,
                                     plan text NOT NULL CHECK (plan IN ('annual', 'monthly', 'pay-as-you-go')), joined date);
               CREATE TABLE trips (trip_id integer PRIMARY KEY,
                                   member_id integer REFERENCES members(member_id),
                                   start_station integer NOT NULL REFERENCES stations(station_id),
                                   end_station integer NOT NULL REFERENCES stations(station_id),
                                   start_time timestamp NOT NULL, duration_min numeric CHECK (duration_min > 0));\"\"\", schema="bikedb")
          q("SELECT table_name FROM information_schema.tables WHERE table_schema = 'bikedb'")
          ```
          """),
         ("""**Load with COPY.** Load stations and members directly. For trips, COPY into a **staging table without rules** first
          (`trips_staging`), because one bad row would make a direct COPY fail completely.""", """
          ```python
          def copy_csv(table, path):
              with psycopg.connect(DSN, options="-c search_path=bikedb") as conn, conn.cursor() as cur:
                  with cur.copy(f"COPY {table} FROM STDIN (FORMAT csv, HEADER true)") as cp:
                      cp.write(open(path).read())
          copy_csv("stations", PROJ_DIR / "bike_stations.csv")
          copy_csv("members", PROJ_DIR / "bike_members.csv")
          q("CREATE TABLE trips_staging (LIKE trips INCLUDING DEFAULTS)", schema="bikedb")     # same columns, no keys or checks
          copy_csv("trips_staging", dirty)
          q("SELECT (SELECT count(*) FROM stations) st, (SELECT count(*) FROM members) mem, (SELECT count(*) FROM trips_staging) staged", schema="bikedb")
          ```
          """),
         ("""**Find the bad rows** in the staging table: trips with unknown start/end stations and trips with duration ≤ 0. How many of each?""", """
          ```python
          q(\"\"\"SELECT
                 count(*) FILTER (WHERE start_station NOT IN (SELECT station_id FROM stations)
                                   OR end_station NOT IN (SELECT station_id FROM stations)) AS unknown_station,
                 count(*) FILTER (WHERE duration_min <= 0) AS bad_duration
               FROM trips_staging\"\"\", schema="bikedb")
          ```
          """),
         ("""**Move only the good rows** into `trips` (INSERT … SELECT … WHERE), keep the bad ones in a `trips_rejected` table for the company, and check the counts add up.""", """
          ```python
          good = \"\"\"start_station IN (SELECT station_id FROM stations) AND end_station IN (SELECT station_id FROM stations) AND duration_min > 0\"\"\"
          q(f"INSERT INTO trips SELECT * FROM trips_staging WHERE {good}", schema="bikedb")
          q(f"CREATE TABLE trips_rejected AS SELECT * FROM trips_staging WHERE NOT ({good})", schema="bikedb")
          q("SELECT (SELECT count(*) FROM trips) ok, (SELECT count(*) FROM trips_rejected) rejected, (SELECT count(*) FROM trips_staging) total", schema="bikedb")
          ```
          """),
         ("""**Make it fast and useful:** indexes on the columns you join and filter on, a view `daily_trips` (trips per day), and a read-only role `city_viewer`.""", """
          ```python
          q(\"\"\"CREATE INDEX ON trips (start_station); CREATE INDEX ON trips (end_station); CREATE INDEX ON trips (start_time);
               CREATE OR REPLACE VIEW daily_trips AS SELECT start_time::date AS day, count(*) AS trips FROM trips GROUP BY 1;
               DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'city_viewer') THEN CREATE ROLE city_viewer NOLOGIN; END IF; END $$;
               GRANT USAGE ON SCHEMA bikedb TO city_viewer; GRANT SELECT ON ALL TABLES IN SCHEMA bikedb TO city_viewer;\"\"\", schema="bikedb")
          q("SELECT * FROM daily_trips ORDER BY trips DESC LIMIT 3", schema="bikedb")
          ```
          """),
         ("""**Put the stations on the map:** add a geometry column (PostGIS), fill it from lon/lat, add a spatial index. Then open the table in QGIS.""", """
          ```python
          q(\"\"\"CREATE EXTENSION IF NOT EXISTS postgis;
               ALTER TABLE bikedb.stations ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
               UPDATE bikedb.stations SET geom = ST_SetSRID(ST_Point(lon, lat), 4326);
               CREATE INDEX IF NOT EXISTS stations_geom_idx ON bikedb.stations USING GIST (geom);\"\"\", schema="public")
          q("SELECT count(*) FROM bikedb.stations WHERE geom IS NOT NULL", schema="public")
          ```
          """)],
        setup="""
        from geotrain.projects import build_projects, PROJ_DIR
        build_projects()
        trips = pd.read_csv(PROJ_DIR / "bike_trips.csv", dtype={"member_id": "Int64"})
        bad = pd.DataFrame({"trip_id": [90001, 90002, 90003, 90004, 90005], "member_id": [pd.NA] * 5,
                            "start_station": [99, 3, 5, 0, 7], "end_station": [4, 98, 5, 2, 7],
                            "start_time": ["2025-07-01 08:00:00"] * 5, "duration_min": [12.0, 8.5, -3.0, 5.0, 0.0]})
        dirty = PROJ_DIR / "bike_trips_dirty.csv"
        bad["member_id"] = bad["member_id"].astype("Int64")
        pd.concat([trips, bad]).to_csv(dirty, index=False)
        print("wrote", dirty.name, len(trips) + len(bad), "rows")
        """,
        qgis="""
        1. Connect QGIS to PostGIS (steps below). Expand **geotrain → bikedb** and drag **stations** onto the map (it now has a geometry).
        2. Drag **daily_trips** in too: it has no geometry, so QGIS adds it as a table. Open its attribute table.
        3. Join usage to the map: in **DB Manager → SQL Window** run
           `SELECT s.station_id, s.name, s.geom, count(t.*) AS starts FROM bikedb.stations s LEFT JOIN bikedb.trips t ON t.start_station = s.station_id GROUP BY s.station_id`
           → *Load as new layer* (geometry `geom`, id `station_id`) → style *Graduated* by `starts`.
        4. Try editing a station's capacity to `0` in QGIS (*Toggle Editing*): the database refuses it — your CHECK rule works in QGIS too.
        """,
        deliver=["Schema `bikedb` with keys, foreign keys, checks and indexes", "`trips_rejected` table with the bad rows and a note why each was rejected",
                 "View `daily_trips` and role `city_viewer`", "QGIS map of stations by number of starts"])
    nb.reflect("""
    Which rules (constraints) would protect the data in your own research? Write two CHECK or FOREIGN KEY rules for a table you use.
    """)
    return nb
