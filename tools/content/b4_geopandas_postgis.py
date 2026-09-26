from nbbuild import NB, SETUP


def build():
    nb = NB("B4_geopandas_postgis", "B4 · GeoPandas ⇄ PostGIS — read_postgis and to_postgis")
    nb.md("""
    **What this is:** the bridge you will use most. Two commands:
    - `gpd.read_postgis(sql, engine)` → runs SQL in PostGIS and returns a **GeoDataFrame**.
    - `gdf.to_postgis(name, engine)` → writes a GeoDataFrame as a **table** in PostGIS.

    Underneath: SQLAlchemy (B3) manages the connection, Psycopg (B2) talks to the server, Shapely unpacks the WKB geometries (B2 3.4).

    **Daily picture:** PostGIS is a big warehouse, GeoPandas is your workbench. `read_postgis` is ordering exactly the parts you need
    (ideally already cut to size in the warehouse). `to_postgis` is sending your finished product back to the warehouse for others to use.

    **Key professional skill:** decide **where** each step happens. Heavy filtering and joins on big tables → SQL.
    Exploring, modelling, plotting → GeoPandas.

    ⚙️ The database from **B0** must be running.
    """)
    nb.code(SETUP)
    nb.code("""
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from sqlalchemy import text
    from geotrain.db import engine, sql
    eng = engine()
    """)

    nb.level(1, "Basics: read and write whole tables", "load a PostGIS table into a GeoDataFrame and write one back.",
             "Taking a box off the warehouse shelf, and putting a new box on it.")
    nb.ex("1.1", "Read a table", "gpd.read_postgis(sql, engine, geom_col='geometry')",
          purpose_a="Runs a SQL query and returns a GeoDataFrame; `geom_col` names the geometry column. The CRS is read from the SRID.",
          life_a="Start an analysis from the city's central database instead of from files on your laptop.",
          hint="`sql=\"SELECT * FROM neighbourhoods\"`, `con=eng`, `geom_col=\"geometry\"`.",
          starter="""
          nbh = gpd.____("SELECT * FROM neighbourhoods", eng, geom_col="____")
          print(nbh.crs, len(nbh))
          nbh.plot(column="population", legend=True); plt.show()
          """,
          solution="""
          nbh = gpd.read_postgis("SELECT * FROM neighbourhoods", eng, geom_col="geometry")
          print(nbh.crs, len(nbh))
          nbh.plot(column="population", legend=True); plt.show()
          """)
    nb.ex("1.2", "Write a new table", "gdf.to_postgis(name, engine, if_exists=...)",
          purpose_a="Writes the GeoDataFrame to a PostGIS table; `if_exists` decides what happens if it exists: 'fail' (default), 'replace', or 'append'.",
          life_a="Publishing the shops layer (built from a CSV in A3) so a colleague's web map can use it.",
          hint="Build shops from the CSV as in A3 1.4, `to_crs(32633)`, then `to_postgis(\"shops\", eng, if_exists=\"replace\", index=False)`.",
          starter="""
          df = pd.read_csv(DATA_DIR / "shops_wgs84.csv")
          shops = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(32633)
          shops.____("shops", eng, if_exists="____", index=False)
          sql("SELECT kind, count(*) FROM shops GROUP BY kind")
          """,
          solution="""
          df = pd.read_csv(DATA_DIR / "shops_wgs84.csv")
          shops = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326).to_crs(32633)
          shops.to_postgis("shops", eng, if_exists="replace", index=False)
          sql("SELECT kind, count(*) FROM shops GROUP BY kind")
          """)
    nb.ex("1.3", "Check what arrived", "geometry_columns + Find_SRID",
          purpose_q="What is the **purpose** of checking the table after `to_postgis`?",
          purpose_a="To verify that the geometry type and SRID were stored as expected (a wrong or missing SRID breaks every later spatial query).",
          life_a="Quality control before telling colleagues 'the layer is online'.",
          hint="`SELECT type, srid FROM geometry_columns WHERE f_table_name = 'shops'`.",
          starter="""
          sql("SELECT type, srid FROM geometry_columns WHERE f_table_name = '____'")
          """,
          solution="""
          sql("SELECT type, srid FROM geometry_columns WHERE f_table_name = 'shops'")
          """)

    nb.level(2, "Core tools: let the database do the cutting", "filter and compute in SQL, then read only the result.",
             "Asking the butcher to cut the meat for you instead of carrying home the whole animal.")
    nb.ex("2.1", "Filter in SQL with parameters", "read_postgis(text('... :p'), eng, params={...})",
          purpose_a="Reads only the rows you need, with a safe parameter; less data travels over the network.",
          life_a="Load only the accidents of one severity (or one year) from a table of millions.",
          hint="Wrap the query in `text()` and use `:sev`; pass `params={\"sev\": \"serious\"}`.",
          starter="""
          serious = gpd.read_postgis(text("SELECT * FROM accidents WHERE severity = ____"), eng, geom_col="geometry", params={"sev": "____"})
          print(len(serious))
          """,
          solution="""
          serious = gpd.read_postgis(text("SELECT * FROM accidents WHERE severity = :sev"), eng, geom_col="geometry", params={"sev": "serious"})
          print(len(serious))
          """)
    nb.ex("2.2", "Compute geometry in SQL, receive the result", "SELECT ST_Intersection(...) AS geom ...",
          purpose_a="PostGIS builds new geometries (here flooded parts of neighbourhoods) and GeoPandas receives them ready to map.",
          life_a="A server computes the heavy overlay once; many users just download the small result.",
          hint="Reuse B1 2.1 but return the geometry: `ST_Intersection(n.geometry, ST_Buffer(r.geometry, 150)) AS geom`, `geom_col=\"geom\"`.",
          starter="""
          q = \"\"\"
              SELECT n.name, ST_Intersection(n.geometry, ST_Buffer(r.geometry, 150)) AS geom
              FROM neighbourhoods n JOIN river r ON ST_Intersects(n.geometry, ST_Buffer(r.geometry, 150))
          \"\"\"
          flood_parts = gpd.read_postgis(q, eng, geom_col="____")
          ax = nbh.boundary.plot(color="grey"); flood_parts.plot(ax=ax, column="name", legend=True); plt.show()
          flood_parts.assign(ha=flood_parts.area / 1e4)[["name", "ha"]].round(1)
          """,
          solution="""
          q = \"\"\"
              SELECT n.name, ST_Intersection(n.geometry, ST_Buffer(r.geometry, 150)) AS geom
              FROM neighbourhoods n JOIN river r ON ST_Intersects(n.geometry, ST_Buffer(r.geometry, 150))
          \"\"\"
          flood_parts = gpd.read_postgis(q, eng, geom_col="geom")
          ax = nbh.boundary.plot(color="grey"); flood_parts.plot(ax=ax, column="name", legend=True); plt.show()
          flood_parts.assign(ha=flood_parts.area / 1e4)[["name", "ha"]].round(1)
          """)
    nb.ex("2.3", "Add rows to a table", "to_postgis(..., if_exists='append')",
          purpose_a="Adds the new rows at the end of an existing table (columns must match).",
          life_a="Monthly accident reports added to the same table (the pipeline from A4's test, now into PostGIS).",
          hint="Make 2 new shops as a GeoDataFrame with the same columns, then append and count again.",
          starter="""
          new = shops.head(2).copy()
          new["shop_id"] = [41, 42]
          new.to_postgis("shops", eng, if_exists="____", index=False)
          sql("SELECT count(*) FROM shops")
          """,
          solution="""
          new = shops.head(2).copy()
          new["shop_id"] = [41, 42]
          new.to_postgis("shops", eng, if_exists="append", index=False)
          sql("SELECT count(*) FROM shops")
          """)
    nb.ex("2.4", "Read in chunks", "read_postgis(..., chunksize=n)",
          purpose_a="Returns an iterator of GeoDataFrames of n rows each, instead of one huge GeoDataFrame.",
          life_a="Processing a national buildings table piece by piece on a normal laptop.",
          hint="Loop: `for part in gpd.read_postgis(..., chunksize=500):` and add up `part[\"residents\"].sum()`.",
          starter="""
          total = 0
          for part in gpd.read_postgis("SELECT * FROM houses", eng, geom_col="geometry", chunksize=____):
              total += part["residents"].sum()
          total
          """,
          solution="""
          total = 0
          for part in gpd.read_postgis("SELECT * FROM houses", eng, geom_col="geometry", chunksize=500):
              total += part["residents"].sum()
          total
          """)

    nb.level(3, "Combining: round trips between the two worlds", "compute in GeoPandas, store in PostGIS, query again in SQL — and use views.",
             "A relay race: each runner (tool) runs the part of the track they are best at.")
    nb.ex("3.1", "GeoPandas result → PostGIS → SQL question", "sjoin → to_postgis → SQL",
          purpose_q="What is the **purpose** of storing an analysis result in PostGIS instead of a file?",
          purpose_a="The result becomes a shared, queryable table: other people, apps or SQL queries can use it immediately.",
          life_a="Your 'accidents per 1000 residents' layer feeds the city's dashboard every morning.",
          hint="Compute the rate with `gpd.sjoin` as in A3, write `nbh_rates` to PostGIS, then query the top 3 in SQL.",
          starter="""
          acc = gpd.read_postgis("SELECT * FROM accidents", eng, geom_col="geometry")
          counts = gpd.sjoin(acc, nbh[["name", "geometry"]], predicate="within")["name"].value_counts()
          nbh["acc_per_1000"] = nbh["name"].map(counts).fillna(0) / nbh["population"] * 1000
          nbh[["name", "population", "acc_per_1000", "geometry"]].____("nbh_rates", eng, if_exists="replace", index=False)
          sql("SELECT name, round(acc_per_1000::numeric, 2) AS rate FROM nbh_rates ORDER BY rate DESC LIMIT 3")
          """,
          solution="""
          acc = gpd.read_postgis("SELECT * FROM accidents", eng, geom_col="geometry")
          counts = gpd.sjoin(acc, nbh[["name", "geometry"]], predicate="within")["name"].value_counts()
          nbh["acc_per_1000"] = nbh["name"].map(counts).fillna(0) / nbh["population"] * 1000
          nbh[["name", "population", "acc_per_1000", "geometry"]].to_postgis("nbh_rates", eng, if_exists="replace", index=False)
          sql("SELECT name, round(acc_per_1000::numeric, 2) AS rate FROM nbh_rates ORDER BY rate DESC LIMIT 3")
          """)
    nb.ex("3.2", "A view: a saved query that behaves like a table", "CREATE VIEW ... AS SELECT ...",
          purpose_a="Stores a query under a name; reading the view runs the query on the latest data.",
          life_a="'serious_accidents_by_neighbourhood' always up to date, without anybody re-running a script.",
          hint="Create the view with `sql(...)` (the helper commits). Then `read_postgis(\"SELECT * FROM v_serious\", ...)`.",
          starter="""
          sql(\"\"\"
              CREATE OR REPLACE ____ v_serious AS
              SELECT n.name, count(a.*) AS serious, n.geometry
              FROM neighbourhoods n LEFT JOIN accidents a
                   ON ST_Within(a.geometry, n.geometry) AND a.severity IN ('serious', 'fatal')
              GROUP BY n.name, n.geometry
          \"\"\")
          v = gpd.read_postgis("SELECT * FROM v_serious", eng, geom_col="geometry")
          v.plot(column="serious", legend=True, cmap="Reds"); plt.show()
          """,
          solution="""
          sql(\"\"\"
              CREATE OR REPLACE VIEW v_serious AS
              SELECT n.name, count(a.*) AS serious, n.geometry
              FROM neighbourhoods n LEFT JOIN accidents a
                   ON ST_Within(a.geometry, n.geometry) AND a.severity IN ('serious', 'fatal')
              GROUP BY n.name, n.geometry
          \"\"\")
          v = gpd.read_postgis("SELECT * FROM v_serious", eng, geom_col="geometry")
          v.plot(column="serious", legend=True, cmap="Reds"); plt.show()
          """)

    nb.level(4, "Professional: hybrid workflows", "split each question between SQL and GeoPandas on purpose, and explain the split.",
             "A kitchen team: the prep cook cuts (SQL), the chef finishes and plates (GeoPandas).")
    nb.pro("4.1", "School demand model — heavy part in SQL, model in GeoPandas", "Modelling (hybrid workflow)",
           scenario="Repeat A3 4.4 (nearest primary school, 5 % children) but let **PostGIS** assign every house to its nearest primary school with a KNN `LATERAL` join, and return only the **summed demand per school** with its geometry. Then compute the load and map it in GeoPandas.",
           plan_hint="SQL: `FROM houses h CROSS JOIN LATERAL (SELECT school FROM schools WHERE level='primary' ORDER BY geometry <-> h.geometry LIMIT 1) s`, `GROUP BY s.school`. Join back to schools for capacity and geometry.",
           starter="""
           q = \"\"\"
               WITH alloc AS (
                   SELECT s.school, sum(h.residents) * 0.05 AS demand
                   FROM houses h
                   CROSS JOIN LATERAL (SELECT school FROM schools WHERE level = 'primary'
                                       ORDER BY geometry ____ h.geometry LIMIT 1) s
                   GROUP BY s.school)
               SELECT sc.school, sc.capacity, a.demand, sc.geometry
               FROM schools sc JOIN alloc a USING (school)
           \"\"\"
           load = gpd.read_postgis(q, eng, geom_col="geometry")
           load["load"] = (load["demand"] / load["capacity"]).round(2)
           ax = nbh.boundary.plot(color="grey"); load.plot(ax=ax, column="load", cmap="RdYlGn_r", legend=True, markersize=200); plt.show()
           load.drop(columns="geometry")
           """,
           solution="""
           q = \"\"\"
               WITH alloc AS (
                   SELECT s.school, sum(h.residents) * 0.05 AS demand
                   FROM houses h
                   CROSS JOIN LATERAL (SELECT school FROM schools WHERE level = 'primary'
                                       ORDER BY geometry <-> h.geometry LIMIT 1) s
                   GROUP BY s.school)
               SELECT sc.school, sc.capacity, a.demand, sc.geometry
               FROM schools sc JOIN alloc a USING (school)
           \"\"\"
           load = gpd.read_postgis(q, eng, geom_col="geometry")
           load["load"] = (load["demand"] / load["capacity"]).round(2)
           ax = nbh.boundary.plot(color="grey"); load.plot(ax=ax, column="load", cmap="RdYlGn_r", legend=True, markersize=200); plt.show()
           load.drop(columns="geometry")
           """,
           answer="Same numbers as A3 4.4, but only **4 rows** travel from the database instead of 1 604 houses. With 20 million houses, this split is the difference between seconds and hours.")
    nb.pro("4.2", "Monte Carlo test with random points made in PostGIS", "Statistical (simulation in SQL)",
           scenario="Repeat A3 4.3: are accidents closer to primary roads than random points? Generate the random points **in PostGIS** with `ST_GeneratePoints` (99 sets of 260 points inside Riverton) and read back only the mean distance per set.",
           plan_hint="`generate_series(1, 99) AS sim` × `ST_Dump(ST_GeneratePoints(town, 260, sim))` (the third argument is a seed, so results repeat). Mean distance to the union of primary roads, grouped by `sim`.",
           starter="""
           q = \"\"\"
               WITH town AS (SELECT ST_Union(geometry) AS g FROM neighbourhoods),
                    prim AS (SELECT ST_Union(geometry) AS g FROM roads WHERE road_type = 'primary'),
                    pts AS (SELECT sim, (ST_Dump(____(town.g, 260, sim))).geom AS g
                            FROM town, generate_series(1, 99) AS sim)
               SELECT sim, avg(ST_Distance(pts.g, prim.g)) AS mean_d FROM pts, prim GROUP BY sim
           \"\"\"
           sims = sql(q)["mean_d"].astype(float)
           real = float(sql("SELECT avg(ST_Distance(a.geometry, p.g)) FROM accidents a, (SELECT ST_Union(geometry) g FROM roads WHERE road_type='primary') p").iloc[0, 0])
           p = ((sims <= real).sum() + 1) / (len(sims) + 1)
           print(f"real {real:.0f} m, random {sims.mean():.0f} m, p = {p:.2f}")
           """,
           solution="""
           q = \"\"\"
               WITH town AS (SELECT ST_Union(geometry) AS g FROM neighbourhoods),
                    prim AS (SELECT ST_Union(geometry) AS g FROM roads WHERE road_type = 'primary'),
                    pts AS (SELECT sim, (ST_Dump(ST_GeneratePoints(town.g, 260, sim))).geom AS g
                            FROM town, generate_series(1, 99) AS sim)
               SELECT sim, avg(ST_Distance(pts.g, prim.g)) AS mean_d FROM pts, prim GROUP BY sim
           \"\"\"
           sims = sql(q)["mean_d"].astype(float)
           real = float(sql("SELECT avg(ST_Distance(a.geometry, p.g)) FROM accidents a, (SELECT ST_Union(geometry) g FROM roads WHERE road_type='primary') p").iloc[0, 0])
           p = ((sims <= real).sum() + 1) / (len(sims) + 1)
           print(f"real {real:.0f} m, random {sims.mean():.0f} m, p = {p:.2f}")
           """,
           answer="Same conclusion as in GeoPandas (p = 0.01, the smallest possible with 99 runs). The heavy simulation ran on the server; Python only did the final comparison.")
    nb.pro("4.3", "Accidents per month and severity", "Temporal (aggregate in SQL, plot in pandas)",
           scenario="Count accidents per month and severity with SQL (`date_trunc`), read the small table, and draw a stacked bar chart.",
           plan_hint="`SELECT date_trunc('month', date) AS month, severity, count(*) ... GROUP BY 1, 2`, then `pivot` in pandas and `.plot(kind='bar', stacked=True)`.",
           starter="""
           t = sql("SELECT ____('month', date)::date AS month, severity, count(*) AS n FROM accidents GROUP BY 1, 2 ORDER BY 1")
           t.pivot(index="month", columns="severity", values="n").fillna(0).plot(kind="bar", stacked=True, figsize=(8, 3)); plt.show()
           """,
           solution="""
           t = sql("SELECT date_trunc('month', date)::date AS month, severity, count(*) AS n FROM accidents GROUP BY 1, 2 ORDER BY 1")
           t.pivot(index="month", columns="severity", values="n").fillna(0).plot(kind="bar", stacked=True, figsize=(8, 3)); plt.show()
           """,
           answer="Non-spatial aggregation is also best done where the data lives. Only 36 numbers come back instead of 260 rows (or 2.6 million in a real city).")

    nb.test("""
    For each: **question type → where does each step happen (SQL or GeoPandas) and why → code → interpretation.**
    """, [
        ("task", """
        **A.** Read the houses within **400 m of Station Avenue** as a GeoDataFrame (filter in SQL), and plot them over the neighbourhoods.
        """, """
        ```python
        near = gpd.read_postgis(text(\"\"\"
            SELECT h.* FROM houses h JOIN roads r ON ST_DWithin(h.geometry, r.geometry, :d)
            WHERE r.name = :road\"\"\"), eng, geom_col="geometry", params={"d": 400, "road": "Station Avenue"})
        ax = nbh.boundary.plot(color="grey"); near.plot(ax=ax, markersize=3); plt.show()
        print(len(near))
        ```
        Filter in SQL (index, fewer rows); plot in GeoPandas.
        """),
        ("task", """
        **B.** Compute, per neighbourhood, the **number of shops of each kind** in SQL and save the wide table (one column per kind) with geometry to PostGIS as `nbh_shops`.
        """, """
        ```python
        q = \"\"\"SELECT n.name, n.geometry,
                    count(*) FILTER (WHERE s.kind = 'bakery')   AS bakery,
                    count(*) FILTER (WHERE s.kind = 'grocery')  AS grocery,
                    count(*) FILTER (WHERE s.kind = 'pharmacy') AS pharmacy,
                    count(*) FILTER (WHERE s.kind = 'cafe')     AS cafe
               FROM neighbourhoods n LEFT JOIN shops s ON ST_Within(s.geometry, n.geometry)
               GROUP BY n.name, n.geometry\"\"\"
        wide = gpd.read_postgis(q, eng, geom_col="geometry")
        wide.to_postgis("nbh_shops", eng, if_exists="replace", index=False)
        wide.drop(columns="geometry")
        ```
        """),
        ("task", """
        **C.** Your GeoDataFrame of candidate clinic sites (A3 4.5) must go to the planning department's database, with the score, in EPSG:4326. Write the code.
        """, """
        ```python
        cand = gpd.GeoDataFrame({"score": [997.0, 850.0]}, geometry=gpd.points_from_xy([394_125, 391_625], [5_820_625, 5_822_125]), crs=32633)
        cand.to_crs(4326).to_postgis("clinic_candidates", eng, if_exists="replace", index=False)
        sql("SELECT srid, type FROM geometry_columns WHERE f_table_name = 'clinic_candidates'")
        ```
        """),
        ("model", """
        **D · Modelling the workflow.** Riverton wants a **weekly accessibility dashboard**: for each neighbourhood, % of residents within 800 m of a clinic, a school and a pharmacy.
        Design the workflow: which steps in PostGIS, which in GeoPandas, what is stored, and how is it refreshed?
        """, """
        1. **PostGIS** holds the source tables (houses, clinics, schools, shops) — updated by loading jobs (Psycopg COPY / `to_postgis(append)`).
        2. **PostGIS view or materialized view** `access_by_nbh`: per house `EXISTS(... ST_DWithin ...)` for each service, aggregated per neighbourhood (B1 4.2). `REFRESH MATERIALIZED VIEW` weekly (a scheduled job).
        3. **GeoPandas** `read_postgis("SELECT * FROM access_by_nbh")` → maps and charts for the report / dashboard.
        Why: heavy spatial work near the data, with indexes; only 9 rows travel to Python; everyone sees the same numbers.
        """),
    ])
    nb.reflect("""
    Draw (on paper) your own ideal workflow: where does your data live, where is it analysed, where is the result published? Which B-notebook skills does each arrow need?
    """)
    return nb
