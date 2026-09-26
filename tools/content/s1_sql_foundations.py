from nbbuild import NB, SETUP

SQLSETUP = '''
import pandas as pd
import geopandas as gpd
import psycopg
from geotrain.db import DSN

def q(query, params=None, schema="sqlcourse"):
    """Run one SQL statement in the given schema and return the result as a table (DataFrame)."""
    with psycopg.connect(DSN, options=f"-c search_path={schema},public") as conn, conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description is None:
            return None
        return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])

# --- copy Riverton's attribute tables (no geometry) into the schema `sqlcourse` ---
from sqlalchemy import create_engine, text
eng = create_engine(DSN.replace("postgresql://", "postgresql+psycopg://", 1))
L = {n: gpd.read_file(GPKG, layer=n) for n in ["neighbourhoods", "schools", "clinics", "accidents"]}
nbh = L["neighbourhoods"]
def with_nb(g):                                     # add the neighbourhood id of each point
    return gpd.sjoin(g, nbh[["nb_id", "geometry"]], predicate="within").drop(columns=["geometry", "index_right"])
tables = {
    "neighbourhoods": pd.DataFrame(nbh.drop(columns="geometry")),
    "schools": with_nb(L["schools"]),
    "clinics": with_nb(L["clinics"]),
    "accidents": with_nb(L["accidents"]).assign(date=lambda d: pd.to_datetime(d["date"]).dt.date),
}
with eng.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS sqlcourse"))
for name, df in tables.items():
    df.to_sql(name, eng, schema="sqlcourse", if_exists="replace", index=False)
print({k: len(v) for k, v in tables.items()})
'''


def build():
    nb = NB("S1_sql_foundations", "S1 · SQL foundations — SELECT, WHERE, GROUP BY, JOIN")
    nb.md("""
    **What SQL is:** *Structured Query Language*, the language for asking questions to a database. You describe **what**
    you want, and the database decides **how** to get it. PostGIS (group B) is SQL plus spatial functions, so this is the
    ground floor for everything in part B.

    **Daily picture:** a database table is a spreadsheet that many people share. SQL is a very precise way of saying:

    | SQL word | What it does | Daily picture |
    |---|---|---|
    | `SELECT` | choose the **columns** to show | "Show me only the name and the phone number columns." |
    | `FROM` | choose the **table** | "…from the customer list." |
    | `WHERE` | keep only some **rows** | a sieve: only customers from Berlin |
    | `ORDER BY` | sort | sort the list by surname |
    | `GROUP BY` | make **piles** and summarise each pile | sort receipts into piles by month, then total each pile |
    | `HAVING` | keep only some **piles** | only months where we spent more than €500 |
    | `JOIN` | combine two tables through a shared key | match the guest list with the seating plan by guest name |

    **The order in which the database reads a query** (not the order you write it):
    `FROM` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY` → `LIMIT`.
    This explains many errors: e.g. you cannot use a `SELECT` alias inside `WHERE`, because `WHERE` runs first.

    **Where you run it:** in the PostgreSQL database you started in `00_START_HERE` (Docker). The helper `q("SELECT ...")`
    sends one query and shows the answer as a table. The Riverton tables are copied into a *schema* (a folder inside the
    database) called `sqlcourse`, without geometry — pure SQL first, spatial later.
    """)
    nb.code(SETUP)
    nb.code(SQLSETUP)

    nb.level(1, "SELECT: choose columns, sort, limit", "read a table, choose columns, compute new ones, sort and limit.",
             "Opening a spreadsheet and hiding the columns you do not need.")
    nb.ex("1.1", "Everything from a table", "SELECT * FROM table",
          purpose_a="Returns all columns (`*`) and all rows of a table.",
          life_a="The first look at a new table.",
          hint="`SELECT * FROM neighbourhoods`. On big tables always add `LIMIT 10`.",
          starter="""
          q("SELECT ____ FROM neighbourhoods")
          """,
          solution="""
          q("SELECT * FROM neighbourhoods")
          """)
    nb.ex("1.2", "Only some columns, sorted", "SELECT a, b FROM t ORDER BY b DESC",
          purpose_a="Chooses columns and sorts the rows (`ASC` = small to large, `DESC` = large to small).",
          life_a="A ranking: neighbourhoods from most to least populated.",
          hint="`SELECT name, population FROM neighbourhoods ORDER BY population DESC`.",
          starter="""
          q("SELECT name, ____ FROM neighbourhoods ORDER BY population ____")
          """,
          solution="""
          q("SELECT name, population FROM neighbourhoods ORDER BY population DESC")
          """)
    nb.ex("1.3", "Computed columns and aliases", "SELECT a / b AS ratio",
          purpose_a="Calculates a new column from others; `AS` gives it a readable name (an alias).",
          life_a="How full is each school? students ÷ capacity.",
          hint="`round(students::numeric / capacity, 2) AS load`. `::numeric` turns whole numbers into decimals: in SQL, 7 / 2 with integers gives 3, not 3.5!",
          starter="""
          q("SELECT school, students, capacity, round(students::numeric / capacity, 2) ____ load FROM schools ORDER BY load DESC")
          """,
          solution="""
          q("SELECT school, students, capacity, round(students::numeric / capacity, 2) AS load FROM schools ORDER BY load DESC")
          """)
    nb.ex("1.4", "Top N and unique values", "LIMIT n / SELECT DISTINCT",
          purpose_a="`LIMIT` keeps the first n rows (after sorting); `DISTINCT` removes duplicate rows.",
          life_a="The 3 richest neighbourhoods; the list of different accident severities.",
          hint="Two queries: `... ORDER BY median_income DESC LIMIT 3` and `SELECT DISTINCT severity FROM accidents`.",
          starter="""
          print(q("SELECT name, median_income FROM neighbourhoods ORDER BY median_income DESC ____ 3"))
          q("SELECT ____ severity FROM accidents")
          """,
          solution="""
          print(q("SELECT name, median_income FROM neighbourhoods ORDER BY median_income DESC LIMIT 3"))
          q("SELECT DISTINCT severity FROM accidents")
          """)

    nb.level(2, "WHERE: filter rows", "keep only the rows that meet conditions — numbers, text, lists, ranges, dates, missing values.",
             "A sieve: only the flour passes, the lumps stay.")
    nb.ex("2.1", "Simple conditions", "WHERE col > value",
          purpose_a="Keeps only rows where the condition is true. Comparison signs: `=`, `<>` (not equal), `<`, `>`, `<=`, `>=`.",
          life_a="Neighbourhoods where more than 25 % of people are over 65 (for care services).",
          hint="`WHERE pct_over65 > 25`. Text values need single quotes: `WHERE name = 'Oldtown'`.",
          starter="""
          q("SELECT name, pct_over65 FROM neighbourhoods WHERE pct_over65 ____ 25")
          """,
          solution="""
          q("SELECT name, pct_over65 FROM neighbourhoods WHERE pct_over65 > 25")
          """)
    nb.ex("2.2", "Combine conditions", "AND / OR / NOT (with brackets)",
          purpose_a="`AND` = both must be true; `OR` = at least one; brackets decide what belongs together.",
          life_a="Serious **or** fatal accidents that happened **at night**.",
          hint="`WHERE (severity = 'serious' OR severity = 'fatal') AND (hour >= 20 OR hour < 6)`. Without brackets, AND is evaluated before OR — a classic mistake.",
          starter="""
          q(\"\"\"SELECT acc_id, date, hour, severity FROM accidents
               WHERE (severity = 'serious' ____ severity = 'fatal') AND (hour >= 20 OR hour < 6)
               ORDER BY date\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT acc_id, date, hour, severity FROM accidents
               WHERE (severity = 'serious' OR severity = 'fatal') AND (hour >= 20 OR hour < 6)
               ORDER BY date\"\"\")
          """)
    nb.ex("2.3", "Lists, ranges and patterns", "IN (...) / BETWEEN a AND b / LIKE 'x%'",
          purpose_a="`IN` = value is in a list; `BETWEEN` = inside a range (both ends included); `LIKE` = text pattern (`%` = any text).",
          life_a="Accidents in the rush hours 7–9; schools whose name contains 'Primary'.",
          hint="`WHERE hour BETWEEN 7 AND 9` and `WHERE school LIKE '%Primary%'` (use `ILIKE` to ignore upper/lower case).",
          starter="""
          print(q("SELECT count(*) FROM accidents WHERE hour ____ 7 AND 9"))
          print(q("SELECT school FROM schools WHERE school ____ '%Primary%'"))
          q("SELECT name FROM neighbourhoods WHERE name IN ('Oldtown', 'Harbour', 'Nowhere')")
          """,
          solution="""
          print(q("SELECT count(*) FROM accidents WHERE hour BETWEEN 7 AND 9"))
          print(q("SELECT school FROM schools WHERE school LIKE '%Primary%'"))
          q("SELECT name FROM neighbourhoods WHERE name IN ('Oldtown', 'Harbour', 'Nowhere')")
          """)
    nb.ex("2.4", "Dates", "WHERE date >= '2025-06-01' / EXTRACT(month FROM date)",
          purpose_a="Dates compare like numbers; `EXTRACT(part FROM date)` takes out the month, day of week, year…",
          life_a="Accidents in summer (June–August); accidents on weekends.",
          hint="Summer: `WHERE date BETWEEN '2025-06-01' AND '2025-08-31'`. Weekend: `EXTRACT(isodow FROM date) IN (6, 7)` (1 = Monday … 7 = Sunday).",
          starter="""
          print(q("SELECT count(*) AS summer FROM accidents WHERE date BETWEEN '2025-06-01' AND '____'"))
          q("SELECT count(*) AS weekend FROM accidents WHERE EXTRACT(____ FROM date) IN (6, 7)")
          """,
          solution="""
          print(q("SELECT count(*) AS summer FROM accidents WHERE date BETWEEN '2025-06-01' AND '2025-08-31'"))
          q("SELECT count(*) AS weekend FROM accidents WHERE EXTRACT(isodow FROM date) IN (6, 7)")
          """)
    nb.ex("2.5", "Categories with CASE WHEN", "CASE WHEN ... THEN ... ELSE ... END",
          purpose_a="Creates a value by rules, like IF … THEN … ELSE in a spreadsheet.",
          life_a="Label schools 'overcrowded' / 'nearly full' / 'ok' for a report.",
          hint="`CASE WHEN students > capacity THEN 'overcrowded' WHEN students > 0.9 * capacity THEN 'nearly full' ELSE 'ok' END AS status`.",
          starter="""
          q(\"\"\"SELECT school, students, capacity,
                      CASE WHEN students > capacity THEN 'overcrowded'
                           WHEN students > 0.9 * capacity THEN '____'
                           ELSE 'ok' END AS status
               FROM schools\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT school, students, capacity,
                      CASE WHEN students > capacity THEN 'overcrowded'
                           WHEN students > 0.9 * capacity THEN 'nearly full'
                           ELSE 'ok' END AS status
               FROM schools\"\"\")
          """)

    nb.level(3, "GROUP BY: summarise in piles", "count, sum and average per group, and filter groups with HAVING.",
             "Sorting a year of receipts into 12 piles (one per month) and adding up each pile.")
    nb.ex("3.1", "Aggregates over the whole table", "COUNT(*), SUM, AVG, MIN, MAX",
          purpose_a="Aggregate functions turn many rows into one number.",
          life_a="Total population of Riverton; average income; the smallest and largest neighbourhood.",
          hint="`SELECT count(*), sum(population), round(avg(median_income)), min(population), max(population) FROM neighbourhoods`.",
          starter="""
          q("SELECT count(*) AS n, ____(population) AS total_pop, round(avg(median_income)) AS avg_income, min(population), max(population) FROM neighbourhoods")
          """,
          solution="""
          q("SELECT count(*) AS n, sum(population) AS total_pop, round(avg(median_income)) AS avg_income, min(population), max(population) FROM neighbourhoods")
          """)
    nb.ex("3.2", "One row per group", "GROUP BY col",
          purpose_a="Makes one group per distinct value and computes the aggregates per group.",
          life_a="Number of accidents per severity; per hour of the day.",
          hint="`SELECT severity, count(*) FROM accidents GROUP BY severity`. Every column in SELECT must be either in GROUP BY or inside an aggregate.",
          starter="""
          print(q("SELECT severity, count(*) AS n FROM accidents GROUP BY ____ ORDER BY n DESC"))
          q("SELECT hour, count(*) AS n FROM accidents GROUP BY hour ORDER BY n DESC LIMIT 5")
          """,
          solution="""
          print(q("SELECT severity, count(*) AS n FROM accidents GROUP BY severity ORDER BY n DESC"))
          q("SELECT hour, count(*) AS n FROM accidents GROUP BY hour ORDER BY n DESC LIMIT 5")
          """)
    nb.ex("3.3", "Keep only some groups", "HAVING condition",
          purpose_a="Filters **groups** after aggregating (WHERE filters **rows** before). ",
          life_a="Only the months with more than 25 accidents.",
          hint="`SELECT EXTRACT(month FROM date) AS month, count(*) AS n FROM accidents GROUP BY 1 HAVING count(*) > 25`. `GROUP BY 1` = group by the first column of SELECT.",
          starter="""
          q(\"\"\"SELECT EXTRACT(month FROM date) AS month, count(*) AS n
               FROM accidents GROUP BY 1 ____ count(*) > 25 ORDER BY month\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT EXTRACT(month FROM date) AS month, count(*) AS n
               FROM accidents GROUP BY 1 HAVING count(*) > 25 ORDER BY month\"\"\")
          """)
    nb.ex("3.4", "Conditional counts", "count(*) FILTER (WHERE ...)",
          purpose_a="Counts only the rows that meet a condition, inside one GROUP BY — several counts side by side.",
          life_a="Per hour: all accidents and serious-or-fatal ones in one table.",
          hint="`count(*) FILTER (WHERE severity <> 'slight') AS severe`.",
          starter="""
          q(\"\"\"SELECT hour, count(*) AS all_acc, count(*) FILTER (WHERE severity ____ 'slight') AS severe
               FROM accidents GROUP BY hour ORDER BY hour\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT hour, count(*) AS all_acc, count(*) FILTER (WHERE severity <> 'slight') AS severe
               FROM accidents GROUP BY hour ORDER BY hour\"\"\")
          """)

    nb.level(4, "JOIN: combine tables", "link tables through a shared key, keep or drop unmatched rows, and join + group together.",
             "Matching the guest list (names) with the seating plan (names → table numbers).")
    nb.ex("4.1", "INNER JOIN", "FROM a JOIN b ON a.key = b.key",
          purpose_a="Combines rows of two tables where the key matches; rows without a partner are dropped.",
          life_a="Give each accident its neighbourhood name (the accidents table only has `nb_id`).",
          hint="Short table names (aliases) keep it readable: `FROM accidents a JOIN neighbourhoods n ON a.nb_id = n.nb_id`.",
          starter="""
          q(\"\"\"SELECT a.acc_id, a.date, a.severity, n.name
               FROM accidents a JOIN neighbourhoods n ON a.nb_id = ____
               LIMIT 5\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT a.acc_id, a.date, a.severity, n.name
               FROM accidents a JOIN neighbourhoods n ON a.nb_id = n.nb_id
               LIMIT 5\"\"\")
          """)
    nb.ex("4.2", "JOIN + GROUP BY: a rate per neighbourhood", "join, then group, then compute",
          purpose_a="The most common analysis pattern: attach the attributes, group, aggregate, compute a rate.",
          life_a="Accidents per 1 000 residents per neighbourhood (A3 3.6, now in SQL).",
          hint="`GROUP BY n.name, n.population`, then `round(count(*) * 1000.0 / n.population, 2)`.",
          starter="""
          q(\"\"\"SELECT n.name, count(*) AS accidents, round(count(*) * 1000.0 / n.population, 2) AS per_1000
               FROM accidents a JOIN neighbourhoods n ON a.nb_id = n.nb_id
               GROUP BY n.name, ____
               ORDER BY per_1000 DESC\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT n.name, count(*) AS accidents, round(count(*) * 1000.0 / n.population, 2) AS per_1000
               FROM accidents a JOIN neighbourhoods n ON a.nb_id = n.nb_id
               GROUP BY n.name, n.population
               ORDER BY per_1000 DESC\"\"\")
          """)
    nb.ex("4.3", "LEFT JOIN: keep everything on the left", "FROM a LEFT JOIN b ON ...",
          purpose_a="Keeps **all** rows of the left table; where there is no partner, the right columns are NULL (empty).",
          life_a="Which neighbourhoods have **no** clinic? (An inner join would silently drop them.)",
          hint="`FROM neighbourhoods n LEFT JOIN clinics c ON c.nb_id = n.nb_id`, then `WHERE c.clinic IS NULL`. Note: `= NULL` never works; use `IS NULL`.",
          starter="""
          q(\"\"\"SELECT n.name, n.population
               FROM neighbourhoods n ____ JOIN clinics c ON c.nb_id = n.nb_id
               WHERE c.clinic IS NULL
               ORDER BY n.population DESC\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT n.name, n.population
               FROM neighbourhoods n LEFT JOIN clinics c ON c.nb_id = n.nb_id
               WHERE c.clinic IS NULL
               ORDER BY n.population DESC\"\"\")
          """)
    nb.ex("4.4", "Several joins in one query", "a JOIN b ... LEFT JOIN c ...",
          purpose_a="Chains joins: each one adds columns from one more table.",
          life_a="One row per neighbourhood with its number of schools, school places and doctors.",
          hint="Join schools and clinics in **separate sub-results** first, or you will multiply rows (2 schools × 2 clinics = 4 rows!). Here we use two small grouped sub-queries and LEFT JOIN them.",
          starter="""
          q(\"\"\"SELECT n.name, coalesce(s.schools, 0) AS schools, coalesce(s.places, 0) AS places, coalesce(c.doctors, 0) AS doctors
               FROM neighbourhoods n
               LEFT JOIN (SELECT nb_id, count(*) AS schools, sum(capacity) AS places FROM schools GROUP BY nb_id) s ON s.nb_id = n.nb_id
               LEFT JOIN (SELECT nb_id, sum(____) AS doctors FROM clinics GROUP BY nb_id) c ON c.nb_id = n.nb_id
               ORDER BY n.name\"\"\")
          """,
          solution="""
          q(\"\"\"SELECT n.name, coalesce(s.schools, 0) AS schools, coalesce(s.places, 0) AS places, coalesce(c.doctors, 0) AS doctors
               FROM neighbourhoods n
               LEFT JOIN (SELECT nb_id, count(*) AS schools, sum(capacity) AS places FROM schools GROUP BY nb_id) s ON s.nb_id = n.nb_id
               LEFT JOIN (SELECT nb_id, sum(doctors) AS doctors FROM clinics GROUP BY nb_id) c ON c.nb_id = n.nb_id
               ORDER BY n.name\"\"\")
          """,
          note="`coalesce(x, 0)` replaces NULL by 0.")

    nb.level(5, "Professional: subqueries, CTEs, window functions, pitfalls", "write readable multi-step queries and avoid the classic mistakes.",
             "Writing a recipe in clear steps instead of one long sentence.")
    nb.pro("5.1", "Above-average schools (subquery)", "Descriptive (comparison with a total)",
           scenario="Which schools have more students than the average school?",
           plan_hint="A subquery computes the average first: `WHERE students > (SELECT avg(students) FROM schools)`.",
           starter="""
           q("SELECT school, students FROM schools WHERE students > (SELECT ____(students) FROM schools) ORDER BY students DESC")
           """,
           solution="""
           q("SELECT school, students FROM schools WHERE students > (SELECT avg(students) FROM schools) ORDER BY students DESC")
           """,
           answer="A subquery in brackets runs first and gives one value to compare with.")
    nb.pro("5.2", "A query in readable steps (CTE)", "Descriptive (multi-step)",
           scenario="Step 1: accidents per neighbourhood. Step 2: the town average. Step 3: neighbourhoods above the average, with how much above.",
           plan_hint="`WITH per_nb AS (...), avg_nb AS (SELECT avg(n) AS a FROM per_nb) SELECT ... FROM per_nb, avg_nb WHERE n > a`. A CTE (Common Table Expression) = a named temporary result.",
           starter="""
           q(\"\"\"WITH per_nb AS (SELECT nb_id, count(*) AS n FROM accidents GROUP BY nb_id),
                    avg_nb AS (SELECT avg(n) AS a FROM per_nb)
               SELECT nb.name, p.n, round(p.n - avg_nb.a, 1) AS above_avg
               FROM per_nb p JOIN neighbourhoods nb USING (nb_id), avg_nb
               WHERE p.n > ____
               ORDER BY above_avg DESC\"\"\")
           """,
           solution="""
           q(\"\"\"WITH per_nb AS (SELECT nb_id, count(*) AS n FROM accidents GROUP BY nb_id),
                    avg_nb AS (SELECT avg(n) AS a FROM per_nb)
               SELECT nb.name, p.n, round(p.n - avg_nb.a, 1) AS above_avg
               FROM per_nb p JOIN neighbourhoods nb USING (nb_id), avg_nb
               WHERE p.n > avg_nb.a
               ORDER BY above_avg DESC\"\"\")
           """,
           answer="CTEs make long queries readable, like naming intermediate results in Python. `USING (nb_id)` is short for `ON p.nb_id = nb.nb_id`.")
    nb.pro("5.3", "Rankings and running totals (window functions)", "Descriptive / temporal",
           scenario="(a) Rank neighbourhoods by income. (b) Monthly accidents with a running total over the year.",
           plan_hint="`RANK() OVER (ORDER BY median_income DESC)`; running total: `sum(n) OVER (ORDER BY month)`. A window function computes over a group of rows **without** collapsing them into one row.",
           starter="""
           print(q("SELECT name, median_income, RANK() ____ (ORDER BY median_income DESC) AS rnk FROM neighbourhoods"))
           q(\"\"\"SELECT month, n, sum(n) OVER (ORDER BY month) AS running_total
               FROM (SELECT EXTRACT(month FROM date) AS month, count(*) AS n FROM accidents GROUP BY 1) m
               ORDER BY month\"\"\")
           """,
           solution="""
           print(q("SELECT name, median_income, RANK() OVER (ORDER BY median_income DESC) AS rnk FROM neighbourhoods"))
           q(\"\"\"SELECT month, n, sum(n) OVER (ORDER BY month) AS running_total
               FROM (SELECT EXTRACT(month FROM date) AS month, count(*) AS n FROM accidents GROUP BY 1) m
               ORDER BY month\"\"\")
           """,
           answer="Window functions answer 'where does this row stand among the others?' — rankings, running totals, differences to the previous month (`lag(n) OVER (ORDER BY month)`).")
    nb.pro("5.4", "The join trap: counting twice", "Data quality (pitfall)",
           scenario="Someone joined neighbourhoods to accidents **and** to schools in one go and summed population. Show why the total population is wrong, and fix it.",
           plan_hint="Each neighbourhood row is repeated once per accident × school. Compare `sum(population)` from the bad join with the true sum. Fix: aggregate each table first (like 4.4), or use `DISTINCT` carefully.",
           starter="""
           bad = q(\"\"\"SELECT sum(n.population) AS total FROM neighbourhoods n
                      JOIN accidents a ON a.nb_id = n.nb_id JOIN schools s ON s.nb_id = n.nb_id\"\"\")
           good = q("SELECT sum(population) AS total FROM ____")
           print("wrong:", bad.iloc[0, 0], "| right:", good.iloc[0, 0])
           """,
           solution="""
           bad = q(\"\"\"SELECT sum(n.population) AS total FROM neighbourhoods n
                      JOIN accidents a ON a.nb_id = n.nb_id JOIN schools s ON s.nb_id = n.nb_id\"\"\")
           good = q("SELECT sum(population) AS total FROM neighbourhoods")
           print("wrong:", bad.iloc[0, 0], "| right:", good.iloc[0, 0])
           """,
           answer="Joins multiply rows (one-to-many). Rule: check the row count after every join (`count(*)`), and aggregate the 'many' side before joining.")

    nb.test("""
    Write the SQL yourself. For each: **plan in words (which tables, which filter, which groups) → SQL → one sentence result.**
    """, [
        ("task", """
        **A.** Which **hour** has the most **fatal** accidents? Show the top 3 hours.
        """, """
        ```python
        q("SELECT hour, count(*) AS n FROM accidents WHERE severity = 'fatal' GROUP BY hour ORDER BY n DESC LIMIT 3")
        ```
        """),
        ("task", """
        **B.** For each neighbourhood: number of **school places per 100 residents**. Include neighbourhoods with no school (as 0).
        """, """
        ```python
        q(\"\"\"SELECT n.name, round(coalesce(sum(s.capacity), 0) * 100.0 / n.population, 2) AS places_per_100
             FROM neighbourhoods n LEFT JOIN schools s ON s.nb_id = n.nb_id
             GROUP BY n.name, n.population ORDER BY places_per_100\"\"\")
        ```
        """),
        ("task", """
        **C.** Which neighbourhoods have **more serious+fatal accidents than slight ones per 10**? (i.e. share of severe accidents above 20 %). Use HAVING.
        """, """
        ```python
        q(\"\"\"SELECT n.name, count(*) AS n, round(avg((a.severity <> 'slight')::int), 2) AS severe_share
             FROM accidents a JOIN neighbourhoods n USING (nb_id)
             GROUP BY n.name HAVING avg((a.severity <> 'slight')::int) > 0.2 ORDER BY severe_share DESC\"\"\")
        ```
        `(condition)::int` turns true/false into 1/0, so its average is a share.
        """),
        ("model", """
        **D · Modelling with tables.** The city wants a table that can answer "how many accidents happened near each school, per month?".
        Which tables and columns do you need, and what would the query look like (in words)?
        """, """
        Tables: `schools(school_id, …)`, `accidents(acc_id, date, …)`, and a **link table** `accident_school(acc_id, school_id)` saying which accident is 'near' which school
        (made with a spatial rule, e.g. within 300 m — that is what PostGIS does in part B with `ST_DWithin`).
        Query: JOIN accidents → link table → schools, `GROUP BY school, date_trunc('month', date)`, `count(*)`.
        Lesson: SQL joins on keys; spatial SQL (B1) joins on **location**, which creates these links on the fly.
        """),
    ])

    nb.project(
        "Riverton Bike Share: what do the trips tell us?",
        """The bike-share company gives you three tables (stations, members, trips, April–September 2025). The city asks:
        which stations are busiest, when do people ride, who rides (members or casual riders), and which station pairs are most popular?
        You answer **only with SQL**, then put the busiest stations on a map in QGIS.""",
        [("bike_stations.csv", "24 stations: id, name, capacity, lon, lat, opening date"),
         ("bike_members.csv", "800 members: id, age group, plan (annual, monthly, pay-as-you-go), join date"),
         ("bike_trips.csv", "6 000 trips: start/end station, start time, duration (min), member id (empty = casual rider)")],
        [("""**Load and check.** How many rows does each table have? What is the date range of the trips?""", """
          ```python
          print(q("SELECT (SELECT count(*) FROM stations) AS stations, (SELECT count(*) FROM members) AS members, (SELECT count(*) FROM trips) AS trips", schema="bike"))
          q("SELECT min(start_time), max(start_time) FROM trips", schema="bike")
          ```
          """),
         ("""**Busiest stations.** Top 5 start stations by number of trips, with their names (JOIN).""", """
          ```python
          q(\"\"\"SELECT s.name, count(*) AS trips FROM trips t JOIN stations s ON s.station_id = t.start_station
               GROUP BY s.name ORDER BY trips DESC LIMIT 5\"\"\", schema="bike")
          ```
          """),
         ("""**When do people ride?** Trips per hour of the day, and the two peak hours.""", """
          ```python
          q("SELECT EXTRACT(hour FROM start_time) AS hour, count(*) AS trips FROM trips GROUP BY 1 ORDER BY trips DESC LIMIT 2", schema="bike")
          ```
          Two peaks (morning and evening) = commuting.
          """),
         ("""**Who rides?** Share of casual trips (no member id), and the average trip duration per **age group** of members (LEFT JOIN vs JOIN: which one and why?).""", """
          ```python
          print(q("SELECT round(avg((member_id IS NULL)::int), 3) AS casual_share FROM trips", schema="bike"))
          q(\"\"\"SELECT m.age_group, count(*) AS trips, round(avg(t.duration_min)::numeric, 1) AS avg_min
               FROM trips t JOIN members m USING (member_id) GROUP BY m.age_group ORDER BY m.age_group\"\"\", schema="bike")
          ```
          An inner JOIN is right here: casual trips have no age group, so they cannot be in an age-group average.
          """),
         ("""**Popular routes.** Top 5 start → end station pairs (not round trips), with both station names (join the stations table twice).""", """
          ```python
          q(\"\"\"SELECT a.name AS from_station, b.name AS to_station, count(*) AS trips
               FROM trips t JOIN stations a ON a.station_id = t.start_station JOIN stations b ON b.station_id = t.end_station
               WHERE t.start_station <> t.end_station
               GROUP BY a.name, b.name ORDER BY trips DESC LIMIT 5\"\"\", schema="bike")
          ```
          Joining the same table twice with two aliases (`a`, `b`) is a common trick.
          """),
         ("""**Map it.** Create a view `bike.station_usage` with station name, capacity, number of starts and a point geometry
          (`ST_SetSRID(ST_Point(lon, lat), 4326)`), so QGIS can show it. (This uses PostGIS — a first taste of part B.)""", """
          ```python
          q("CREATE EXTENSION IF NOT EXISTS postgis", schema="public")
          q(\"\"\"CREATE OR REPLACE VIEW bike.station_usage AS
               SELECT s.station_id, s.name, s.capacity, count(t.trip_id) AS starts,
                      ST_SetSRID(ST_Point(s.lon, s.lat), 4326)::geometry(Point, 4326) AS geom
               FROM bike.stations s LEFT JOIN bike.trips t ON t.start_station = s.station_id
               GROUP BY s.station_id, s.name, s.capacity, s.lon, s.lat\"\"\", schema="bike")
          q("SELECT name, starts FROM station_usage ORDER BY starts DESC LIMIT 3", schema="bike")
          ```
          Every non-aggregated column must be in GROUP BY. (If `station_id` were a PRIMARY KEY, `GROUP BY s.station_id` alone would be enough — you add keys in S2.)
          """)],
        setup="""
        from geotrain.projects import build_projects, PROJ_DIR
        build_projects()
        with eng.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS bike CASCADE"))
            conn.execute(text("CREATE SCHEMA bike"))
        for name in ["stations", "members", "trips"]:
            df = pd.read_csv(PROJ_DIR / f"bike_{name}.csv", parse_dates=[c for c in ["opened", "joined", "start_time"]
                                                                          if c in pd.read_csv(PROJ_DIR / f"bike_{name}.csv", nrows=1).columns])
            if "member_id" in df:
                df["member_id"] = df["member_id"].astype("Int64")
            df.to_sql(name, eng, schema="bike", if_exists="replace", index=False)
        print("loaded schema bike: stations, members, trips")
        """,
        qgis="""
        1. Connect QGIS to the database (steps below), expand **geotrain → bike**, and drag **station_usage** onto the map.
        2. Style it: *Layer Properties → Symbology → Graduated*, value = `starts`, method = *Size*. Big circles = busy stations.
        3. Add a background: *Browser → XYZ Tiles → OpenStreetMap* (only as decoration — Riverton is fictional!).
        4. Open **DB Manager → SQL Window** and run your task 5 query; load it as a table and look at it next to the map.
        """,
        deliver=["SQL for tasks 1–5 with one-sentence answers", "View `bike.station_usage` in the database",
                 "QGIS map of stations sized by starts (export: *Project → Import/Export → Export Map to Image*)"])
    nb.reflect("""
    Which SQL word was hardest (JOIN? GROUP BY? HAVING?) Write one question about your own data that needs a JOIN **and** a GROUP BY.
    """)
    return nb
