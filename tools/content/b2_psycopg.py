from nbbuild import NB, SETUP
import projects_b


def build():
    nb = NB("B2_psycopg", "B2 · Psycopg — talking to PostGIS from Python")
    nb.md("""
    **What Psycopg is:** the standard Python driver for PostgreSQL (here version 3, imported as `psycopg`). It opens a connection,
    sends your SQL text, and brings the rows back as Python values. It knows nothing about geometry: to Psycopg, a geometry is
    just bytes or text. You add Shapely to turn those bytes into shapes.

    **Daily picture:** a telephone. `connect` dials the database, a `cursor` is the conversation, `execute` is what you say,
    `fetchall` is what you hear back, `commit` is "yes, please save that".

    **Where this fits in your plan:** GeoPandas and SQLAlchemy use a driver like this underneath. Knowing it helps you debug,
    write safe queries (no SQL injection), and load big data fast (COPY).

    ⚙️ The database from **B0** must be running.
    """)
    nb.code(SETUP)
    nb.code("""
    import psycopg
    import shapely
    import pandas as pd
    from geotrain.db import DSN
    print("psycopg", psycopg.__version__)
    """)

    nb.level(1, "Basics: connect, execute, fetch", "send a query and read the answer as Python values; build your own `sql()` helper.",
             "Calling a shop, asking a question, writing down the answer.")
    nb.ex("1.1", "Connection and cursor", "conn.cursor() / cur.execute() / cur.fetchone()",
          purpose_a="A cursor sends one SQL statement (`execute`) and reads the result rows (`fetchone`, `fetchall`).",
          life_a="Any script that reads numbers from the city database, e.g. a nightly report.",
          hint="`with psycopg.connect(DSN) as conn, conn.cursor() as cur:` then `cur.execute(\"SELECT count(*) FROM houses\")`.",
          starter="""
          with psycopg.connect(DSN) as conn, conn.____() as cur:
              cur.____("SELECT count(*) FROM houses")
              print(cur.____())
          """,
          solution="""
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.execute("SELECT count(*) FROM houses")
              print(cur.fetchone())
          """)
    nb.ex("1.2", "Many rows and their column names", "cur.fetchall() / cur.description",
          purpose_a="`fetchall` returns all rows as a list of tuples; `description` holds the column names and types.",
          life_a="Turning a query result into a table (DataFrame) for a report.",
          hint="Column names: `[c.name for c in cur.description]`.",
          starter="""
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.execute("SELECT school, capacity, students FROM schools")
              rows = cur.____()
              cols = [c.name for c in cur.____]
          pd.DataFrame(rows, columns=cols)
          """,
          solution="""
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.execute("SELECT school, capacity, students FROM schools")
              rows = cur.fetchall()
              cols = [c.name for c in cur.description]
          pd.DataFrame(rows, columns=cols)
          """)
    nb.ex("1.3", "Write your own helper", "def sql(query, params=None) -> DataFrame",
          purpose_q="What is the **purpose** of wrapping connect/execute/fetch into one function?",
          purpose_a="Reuse: one line per query instead of five, and the connection is always closed properly. (This is the `sql()` helper you used in B1.)",
          life_a="Every analyst builds small helpers like this so notebooks stay short and readable.",
          hint="Put 1.2 in a function; pass `params` to `cur.execute(query, params)`.",
          starter="""
          def my_sql(query, params=None):
              with psycopg.connect(DSN) as conn, conn.cursor() as cur:
                  cur.execute(query, ____)
                  return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
          my_sql("SELECT name, population FROM neighbourhoods ORDER BY population DESC LIMIT 3")
          """,
          solution="""
          def my_sql(query, params=None):
              with psycopg.connect(DSN) as conn, conn.cursor() as cur:
                  cur.execute(query, params)
                  return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])
          my_sql("SELECT name, population FROM neighbourhoods ORDER BY population DESC LIMIT 3")
          """)

    nb.level(2, "Core tools: parameters and transactions", "pass values safely and control when changes are saved.",
             "Filling in a form (safe) instead of letting a stranger write on your cheque (unsafe).")
    nb.ex("2.1", "Parameters: let the driver insert values", "cur.execute('... WHERE x > %s', (value,))",
          purpose_a="Sends the SQL and the values separately; the driver inserts them safely and with the right type.",
          life_a="A web map where users type a minimum capacity; their input goes into the query safely.",
          hint="Use `%s` as a placeholder (for any type) and pass a **tuple**: `(500,)` — note the comma.",
          starter="""
          my_sql("SELECT school, capacity FROM schools WHERE capacity > ____", (____,))
          """,
          solution="""
          my_sql("SELECT school, capacity FROM schools WHERE capacity > %s", (800,))
          """)
    nb.ex("2.2", "Why never build SQL with f-strings", "SQL injection",
          purpose_q="What is the **purpose** of this experiment? What goes wrong with the f-string version?",
          purpose_a="It shows that pasting user text into SQL lets that text change the query itself (SQL injection). With `%s` the text stays plain data.",
          life_a="A classic attack on websites: a user types `' OR '1'='1` into a search box and sees (or deletes) data they should not.",
          hint="Run both. The f-string version returns **every** school; the parameter version returns none, because no school is literally called that.",
          starter="""
          user_input = "x' OR '1'='1"
          print(len(my_sql(f"SELECT school FROM schools WHERE school = '{user_input}'")), "rows with f-string")
          print(len(my_sql("SELECT school FROM schools WHERE school = ____", (user_input,))), "rows with a parameter")
          """,
          solution="""
          user_input = "x' OR '1'='1"
          print(len(my_sql(f"SELECT school FROM schools WHERE school = '{user_input}'")), "rows with f-string")
          print(len(my_sql("SELECT school FROM schools WHERE school = %s", (user_input,))), "rows with a parameter")
          """,
          note="Table and column **names** cannot be parameters. For those use `psycopg.sql.Identifier` (see the psycopg docs).")
    nb.ex("2.3", "Transactions: commit or roll back", "conn.commit() / conn.rollback()",
          purpose_a="Changes are private until `commit()` saves them; `rollback()` cancels everything since the last commit.",
          life_a="Updating 1 000 parcels: if one update fails, roll back so the table is not left half-changed.",
          hint="Delete all accidents, count (0), then `rollback()` and count again (260). Nothing is lost!",
          starter="""
          with psycopg.connect(DSN) as conn:
              conn.execute("DELETE FROM accidents")
              print("inside the transaction:", conn.execute("SELECT count(*) FROM accidents").fetchone()[0])
              conn.____()
              print("after rollback:", conn.execute("SELECT count(*) FROM accidents").fetchone()[0])
          """,
          solution="""
          with psycopg.connect(DSN) as conn:
              conn.execute("DELETE FROM accidents")
              print("inside the transaction:", conn.execute("SELECT count(*) FROM accidents").fetchone()[0])
              conn.rollback()
              print("after rollback:", conn.execute("SELECT count(*) FROM accidents").fetchone()[0])
          """,
          note="The `with psycopg.connect(...)` block **commits** at the end if no error happened, and rolls back if there was an error.")
    nb.ex("2.4", "Named parameters", "%(name)s with a dict",
          purpose_a="Placeholders with names, filled from a dictionary — clearer when a value is used several times.",
          life_a="A query 'houses within {radius} m of point ({x}, {y})' where each value has a clear name.",
          hint="`%(x)s`, `%(y)s`, `%(r)s` and pass `{\"x\": ..., \"y\": ..., \"r\": ...}`.",
          starter="""
          my_sql(\"\"\"
              SELECT count(*) AS houses FROM houses
              WHERE ST_DWithin(geometry, ST_SetSRID(ST_Point(%(x)s, %(y)s), 32633), %(____)s)
          \"\"\", {"x": 393_000, "y": 5_821_000, "r": ____})
          """,
          solution="""
          my_sql(\"\"\"
              SELECT count(*) AS houses FROM houses
              WHERE ST_DWithin(geometry, ST_SetSRID(ST_Point(%(x)s, %(y)s), 32633), %(r)s)
          \"\"\", {"x": 393_000, "y": 5_821_000, "r": 500})
          """)

    nb.level(3, "Combining: geometries in and out", "create a spatial table, insert points, and move Shapely shapes in and out as WKB.",
             "Sending a parcel: pack it (Shapely → bytes), post it (Psycopg), unpack it on the other side (bytes → Shapely).")
    nb.ex("3.1", "Create a spatial table and insert one point", "CREATE TABLE ... geometry(Point, 32633)",
          purpose_a="Creates a table whose column only accepts points in EPSG:32633; `ST_SetSRID(ST_Point(x, y), 32633)` builds such a point.",
          life_a="A new layer for tree-planting requests collected by a web form.",
          hint="`geometry(Point, 32633)` = type + SRID. Insert with parameters for x and y.",
          starter="""
          with psycopg.connect(DSN) as conn:
              conn.execute("DROP TABLE IF EXISTS trees")
              conn.execute("CREATE TABLE trees (id serial PRIMARY KEY, species text, geom geometry(____, 32633))")
              conn.execute("INSERT INTO trees (species, geom) VALUES (%s, ST_SetSRID(ST_Point(%s, %s), ____))",
                           ("oak", 392_800, 5_821_400))
          my_sql("SELECT id, species, ST_AsText(geom) FROM trees")
          """,
          solution="""
          with psycopg.connect(DSN) as conn:
              conn.execute("DROP TABLE IF EXISTS trees")
              conn.execute("CREATE TABLE trees (id serial PRIMARY KEY, species text, geom geometry(Point, 32633))")
              conn.execute("INSERT INTO trees (species, geom) VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 32633))",
                           ("oak", 392_800, 5_821_400))
          my_sql("SELECT id, species, ST_AsText(geom) FROM trees")
          """)
    nb.ex("3.2", "Insert many rows at once", "cur.executemany(sql, list_of_tuples)",
          purpose_a="Runs the same statement for every tuple in a list (one round of talking instead of many separate calls).",
          life_a="Loading 200 tree-planting requests from a spreadsheet.",
          hint="Build a list of `(species, x, y)` tuples, then `cur.executemany(...)` with the same INSERT as 3.1.",
          starter="""
          import random
          random.seed(3)
          rows = [(random.choice(["oak", "lime", "birch"]), random.uniform(390_000, 396_000), random.uniform(5_818_000, 5_824_000)) for _ in range(200)]
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.____("INSERT INTO trees (species, geom) VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 32633))", rows)
          my_sql("SELECT species, count(*) FROM trees GROUP BY species")
          """,
          solution="""
          import random
          random.seed(3)
          rows = [(random.choice(["oak", "lime", "birch"]), random.uniform(390_000, 396_000), random.uniform(5_818_000, 5_824_000)) for _ in range(200)]
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.executemany("INSERT INTO trees (species, geom) VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 32633))", rows)
          my_sql("SELECT species, count(*) FROM trees GROUP BY species")
          """)
    nb.ex("3.3", "Send a Shapely shape (WKB)", "ST_GeomFromWKB(%s, 32633) with shapely.to_wkb(geom)",
          purpose_a="Packs a Shapely geometry into WKB bytes (a compact binary format) and lets PostGIS unpack it into a geometry.",
          life_a="You built a study area in Shapely and want PostGIS to count the trees inside it.",
          hint="`shapely.to_wkb(area)` gives bytes. Pass them as a parameter to `ST_GeomFromWKB(%s, 32633)`.",
          starter="""
          study = shapely.Point(393_000, 5_821_000).buffer(1000)
          my_sql("SELECT count(*) FROM trees WHERE ST_Within(geom, ST_GeomFromWKB(%s, 32633))", (shapely.____(study),))
          """,
          solution="""
          study = shapely.Point(393_000, 5_821_000).buffer(1000)
          my_sql("SELECT count(*) FROM trees WHERE ST_Within(geom, ST_GeomFromWKB(%s, 32633))", (shapely.to_wkb(study),))
          """)
    nb.ex("3.4", "Get shapes back into Shapely", "ST_AsBinary(geom) → shapely.from_wkb(bytes)",
          purpose_a="PostGIS packs geometries as WKB; Shapely unpacks them into shapes you can measure or plot.",
          life_a="Pulling the neighbourhood polygons out of the database for a custom calculation in Python.",
          hint="`SELECT name, ST_AsBinary(geometry) FROM neighbourhoods`, then `shapely.from_wkb(row[1])`.",
          starter="""
          df = my_sql("SELECT name, ST_AsBinary(geometry) AS wkb FROM neighbourhoods")
          df["geom"] = df["wkb"].apply(lambda b: shapely.____(bytes(b)))
          df["area_km2"] = df["geom"].apply(lambda g: g.area / 1e6)
          df[["name", "area_km2"]]
          """,
          solution="""
          df = my_sql("SELECT name, ST_AsBinary(geometry) AS wkb FROM neighbourhoods")
          df["geom"] = df["wkb"].apply(lambda b: shapely.from_wkb(bytes(b)))
          df["area_km2"] = df["geom"].apply(lambda g: g.area / 1e6)
          df[["name", "area_km2"]]
          """,
          note="GeoPandas `read_postgis` (B4) does exactly this for you, for all rows at once.")

    nb.level(4, "Professional: fast, safe and reusable", "load big data with COPY, stream big results, and build safe reusable query functions.",
             "Using a lorry instead of a bicycle when you move a whole house.")
    nb.pro("4.1", "Load 20 000 points fast with COPY", "Data engineering (bulk loading)",
           scenario="Load 20 000 random sensor readings into a new table `readings`. Compare `executemany` with PostgreSQL's `COPY`.",
           plan_hint="`with cur.copy(\"COPY readings (value, geom) FROM STDIN\") as cp: cp.write_row((v, 'SRID=32633;POINT(x y)'))`. COPY accepts geometry as EWKT text. Time both with `time.perf_counter()`.",
           starter="""
           import time
           pts = [(random.random() * 50, random.uniform(390_000, 396_000), random.uniform(5_818_000, 5_824_000)) for _ in range(20_000)]
           with psycopg.connect(DSN) as conn, conn.cursor() as cur:
               cur.execute("DROP TABLE IF EXISTS readings")
               cur.execute("CREATE TABLE readings (value float, geom geometry(Point, 32633))")
               t = time.perf_counter()
               cur.executemany("INSERT INTO readings VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 32633))", pts[:2000])
               t_many = (time.perf_counter() - t) / 2000 * 20_000          # scaled to 20 000 rows
               cur.execute("TRUNCATE readings")
               t = time.perf_counter()
               with cur.____("COPY readings (value, geom) FROM STDIN") as cp:
                   for v, x, y in pts:
                       cp.write_row((v, f"SRID=32633;POINT({x} {y})"))
               t_copy = time.perf_counter() - t
           print(f"executemany ≈ {t_many:.2f} s, COPY = {t_copy:.2f} s for 20 000 rows")
           my_sql("SELECT count(*) FROM readings")
           """,
           solution="""
           import time
           pts = [(random.random() * 50, random.uniform(390_000, 396_000), random.uniform(5_818_000, 5_824_000)) for _ in range(20_000)]
           with psycopg.connect(DSN) as conn, conn.cursor() as cur:
               cur.execute("DROP TABLE IF EXISTS readings")
               cur.execute("CREATE TABLE readings (value float, geom geometry(Point, 32633))")
               t = time.perf_counter()
               cur.executemany("INSERT INTO readings VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 32633))", pts[:2000])
               t_many = (time.perf_counter() - t) / 2000 * 20_000
               cur.execute("TRUNCATE readings")
               t = time.perf_counter()
               with cur.copy("COPY readings (value, geom) FROM STDIN") as cp:
                   for v, x, y in pts:
                       cp.write_row((v, f"SRID=32633;POINT({x} {y})"))
               t_copy = time.perf_counter() - t
           print(f"executemany ≈ {t_many:.2f} s, COPY = {t_copy:.2f} s for 20 000 rows")
           my_sql("SELECT count(*) FROM readings")
           """,
           answer="COPY streams rows in one go and is usually many times faster. For millions of rows, COPY (or `ogr2ogr`) is the professional choice.")
    nb.pro("4.2", "A safe, reusable question: nearest clinic to any address", "Proximity (reusable service)",
           scenario="Write `nearest_clinic(x, y)` that returns the name of the nearest clinic and the distance in metres, using parameters and the `<->` index operator. Test it for (391 000, 5 823 500).",
           plan_hint="One SQL query with `%s` placeholders; `ORDER BY geometry <-> ST_SetSRID(ST_Point(%s, %s), 32633) LIMIT 1`. Pass x, y twice (or use named parameters).",
           starter="""
           def nearest_clinic(x, y):
               q = \"\"\"
                   SELECT clinic, round(ST_Distance(geometry, p)::numeric) AS dist_m
                   FROM clinics, ST_SetSRID(ST_Point(%(x)s, %(y)s), 32633) AS p
                   ORDER BY geometry ____ p LIMIT 1
               \"\"\"
               return my_sql(q, {"x": x, "y": y}).iloc[0].to_dict()
           nearest_clinic(391_000, 5_823_500)
           """,
           solution="""
           def nearest_clinic(x, y):
               q = \"\"\"
                   SELECT clinic, round(ST_Distance(geometry, p)::numeric) AS dist_m
                   FROM clinics, ST_SetSRID(ST_Point(%(x)s, %(y)s), 32633) AS p
                   ORDER BY geometry <-> p LIMIT 1
               \"\"\"
               return my_sql(q, {"x": x, "y": y}).iloc[0].to_dict()
           nearest_clinic(391_000, 5_823_500)
           """,
           answer="This small function is the core of a real 'find my nearest service' web API: safe parameters + an index-backed KNN search.")
    nb.pro("4.3", "Stream a big result without filling memory", "Data engineering (server-side cursor)",
           scenario="Read all 20 000 readings in batches of 5 000 with a **server-side (named) cursor** and compute the mean value in Python.",
           plan_hint="`conn.cursor(name=\"stream\")` keeps the result on the server; `cur.fetchmany(5000)` brings one batch at a time. Keep a running sum and count.",
           starter="""
           total, n = 0.0, 0
           with psycopg.connect(DSN) as conn, conn.cursor(name="____") as cur:
               cur.execute("SELECT value FROM readings")
               while batch := cur.fetchmany(____):
                   total += sum(r[0] for r in batch)
                   n += len(batch)
           print(n, round(total / n, 2))
           """,
           solution="""
           total, n = 0.0, 0
           with psycopg.connect(DSN) as conn, conn.cursor(name="stream") as cur:
               cur.execute("SELECT value FROM readings")
               while batch := cur.fetchmany(5000):
                   total += sum(r[0] for r in batch)
                   n += len(batch)
           print(n, round(total / n, 2))
           """,
           answer="Same idea as chunked file reading in A4: process in pieces. (Of course, `SELECT avg(value)` in SQL is simpler — do the maths in the database when you can.)")

    nb.test("""
    Use Psycopg (and Shapely where needed). For each: **plan in words → code → interpretation.**
    """, [
        ("task", """
        **A.** Write a function `houses_near(x, y, r)` that returns the number of residents within `r` metres of a point. Make it injection-safe.
        """, """
        ```python
        def houses_near(x, y, r):
            return my_sql(\"\"\"SELECT coalesce(sum(residents), 0) AS residents FROM houses
                           WHERE ST_DWithin(geometry, ST_SetSRID(ST_Point(%s, %s), 32633), %s)\"\"\", (x, y, r)).iloc[0, 0]
        print(houses_near(393_000, 5_821_000, 500))
        ```
        """),
        ("task", """
        **B.** Insert a new clinic "Harbour Care" at (395 200, 5 823 300) with 5 doctors, check it, then **undo** it with a rollback.
        """, """
        ```python
        with psycopg.connect(DSN) as conn:
            conn.execute("INSERT INTO clinics (clinic, doctors, geometry) VALUES (%s, %s, ST_SetSRID(ST_Point(%s, %s), 32633))",
                         ("Harbour Care", 5, 395_200, 5_823_300))
            print(conn.execute("SELECT count(*) FROM clinics").fetchone())
            conn.rollback()
        print(my_sql("SELECT count(*) FROM clinics"))
        ```
        """),
        ("task", """
        **C.** Build a Shapely line from (390 500, 5 819 000) to (395 500, 5 823 000) (a planned tram line), send it to PostGIS, and count accidents within 100 m of it.
        """, """
        ```python
        tram = shapely.LineString([(390_500, 5_819_000), (395_500, 5_823_000)])
        print(my_sql("SELECT count(*) FROM accidents WHERE ST_DWithin(geometry, ST_GeomFromWKB(%s, 32633), 100)", (shapely.to_wkb(tram),)))
        ```
        """),
        ("decision", """
        **D.** Your colleague builds queries like `f\"... WHERE name = '{name}'\"` in a web app. What do you tell them, in two sentences?
        """, """
        "This allows SQL injection: a user can type text that changes your query and reads or deletes data. Always pass values as parameters (`%s`) and let psycopg insert them."
        """),
    ])
    projects_b.p_b2(nb)
    nb.reflect("""
    Will you mostly *read* from a database someone else runs, or *build* your own? Which Psycopg skills matter most for that (parameters, COPY, transactions)?
    """)
    return nb
