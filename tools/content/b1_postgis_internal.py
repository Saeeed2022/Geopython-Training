from nbbuild import NB, SETUP


def build():
    nb = NB("B1_postgis_internal", "B1 · Inside PostGIS — GEOS, PROJ and GDAL at work")
    nb.md("""
    **The idea of this notebook:** PostGIS does not do the heavy maths itself. It hands the work to three libraries:

    | Internal library | Does | Example SQL functions | Its twin in Python (group A) |
    |---|---|---|---|
    | **GEOS** | geometry operations | `ST_Buffer`, `ST_Intersects`, `ST_Intersection`, `ST_Union`, `ST_Contains`, `ST_Simplify`, `ST_IsValid` | **Shapely** (same GEOS!) |
    | **PROJ** | coordinate transformations | `ST_Transform`, and the CRS catalogue `spatial_ref_sys` | **PyProj** (same PROJ) |
    | **GDAL** | raster formats | `ST_FromGDALRaster`, `ST_AsGDALRaster`, `ST_GDALDrivers` | **Rasterio** (same GDAL) |

    Note: simple measurements like `ST_Area`, `ST_Distance` or `ST_Length` on planar geometry are computed by PostGIS's own code;
    GEOS is used for the harder operations (overlay, buffer, predicates, validity).

    **Daily picture:** PostGIS is a restaurant. GEOS, PROJ and GDAL are three specialist cooks in the kitchen.
    You (SQL) talk to the waiter (PostGIS); the waiter passes your order to the right cook.

    **So what?** Everything you learned in Shapely, PyProj and Rasterio has a direct SQL twin. This notebook trains the translation.
    In every exercise, Step 1 also asks: **which internal library does the work?**

    ⚙️ You need the database from **B0** running (with Riverton loaded).
    """)
    nb.code(SETUP)
    nb.code("""
    import shapely
    import geopandas as gpd
    from geotrain.db import sql, connect
    sql("SELECT postgis_geos_version() AS geos, postgis_proj_version() AS proj, postgis_gdal_version() AS gdal")
    """)

    nb.level(1, "GEOS: geometry on single shapes", "write the Shapely exercises of A1 again in SQL and prove it is the same engine.",
             "The same recipe cooked in two kitchens tastes the same when the same cook makes it.")
    nb.ex("1.1", "Area from text", "ST_Area(ST_GeomFromText(wkt))",
          purpose_q="What is the **purpose** of `ST_GeomFromText` and `ST_Area`? Which Shapely commands are their twins?",
          purpose_a="`ST_GeomFromText` builds a geometry from WKT (twin: `shapely.from_wkt`), `ST_Area` measures it (twin: `.area`).",
          life_a="Quick checks in SQL of a shape copied from a report or from QGIS.",
          hint="The garden from A1: `'POLYGON((0 0, 20 0, 20 10, 0 10, 0 0))'` → 200.",
          starter="""
          sql("SELECT ____(ST_GeomFromText('POLYGON((0 0, 20 0, 20 10, 0 10, 0 0))')) AS area")
          """,
          solution="""
          sql("SELECT ST_Area(ST_GeomFromText('POLYGON((0 0, 20 0, 20 10, 0 10, 0 0))')) AS area")
          """)
    nb.ex("1.2", "Proof: same buffer in Shapely and PostGIS", "ST_Buffer(geom, d, 'quad_segs=8')",
          purpose_q="What is the **purpose** of `ST_Buffer`, and **which internal library** computes it?",
          purpose_a="Makes the zone within distance d of a geometry. **GEOS** computes it — the same code Shapely calls.",
          life_a="Catchments, noise zones, safety distances, done directly on database tables.",
          hint="Both use a circle made of straight segments. PostGIS uses 8 segments per quarter circle by default; Shapely uses 16. Set both to 8: Shapely `buffer(500, quad_segs=8)`.",
          starter="""
          pg = sql("SELECT ST_Area(ST_Buffer(ST_Point(0, 0), 500, 'quad_segs=8')) AS a").iloc[0, 0]
          py = shapely.Point(0, 0).buffer(500, quad_segs=____).area
          print(pg, py, "identical:", abs(pg - py) < 1e-6)
          """,
          solution="""
          pg = sql("SELECT ST_Area(ST_Buffer(ST_Point(0, 0), 500, 'quad_segs=8')) AS a").iloc[0, 0]
          py = shapely.Point(0, 0).buffer(500, quad_segs=8).area
          print(pg, py, "identical:", abs(pg - py) < 1e-6)
          """)
    nb.ex("1.3", "Yes/no relations", "ST_Intersects / ST_Touches / ST_Contains",
          purpose_q="What is the **purpose** of these three functions? Which library evaluates them?",
          purpose_a="They test spatial relations and return true/false (GEOS evaluates them, same as Shapely's `intersects`, `touches`, `contains`).",
          life_a="Which plots touch the road? Which trees are inside the park?",
          hint="Use the park and plot1 from A1: park = square 200..600; plot1 starts at x=600. Expected: intersects t, touches t, contains f.",
          starter="""
          sql(\"\"\"
              WITH g AS (SELECT ST_MakeEnvelope(200, 200, 600, 600) AS park,
                                ST_MakeEnvelope(600, 200, 800, 400) AS plot1)
              SELECT ____(park, plot1) AS intersects, ____(park, plot1) AS touches, ____(park, plot1) AS contains FROM g
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              WITH g AS (SELECT ST_MakeEnvelope(200, 200, 600, 600) AS park,
                                ST_MakeEnvelope(600, 200, 800, 400) AS plot1)
              SELECT ST_Intersects(park, plot1) AS intersects, ST_Touches(park, plot1) AS touches, ST_Contains(park, plot1) AS contains FROM g
          \"\"\")
          """)
    nb.ex("1.4", "Repair broken shapes", "ST_IsValid / ST_IsValidReason / ST_MakeValid",
          purpose_q="What is the **purpose** of these functions? Which library checks validity?",
          purpose_a="Check whether geometries follow the rules, explain why not, and repair them (GEOS; twins: `is_valid`, `is_valid_reason`, `make_valid`).",
          life_a="Cleaning a whole table of hand-digitised parcels before measuring areas.",
          hint="The bow-tie from A1: `'POLYGON((0 0, 10 10, 10 0, 0 10, 0 0))'`.",
          starter="""
          sql(\"\"\"
              WITH b AS (SELECT ST_GeomFromText('POLYGON((0 0, 10 10, 10 0, 0 10, 0 0))') AS g)
              SELECT ST_IsValid(g), ____(g), ST_Area(____(g)) AS fixed_area FROM b
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              WITH b AS (SELECT ST_GeomFromText('POLYGON((0 0, 10 10, 10 0, 0 10, 0 0))') AS g)
              SELECT ST_IsValid(g), ST_IsValidReason(g), ST_Area(ST_MakeValid(g)) AS fixed_area FROM b
          \"\"\")
          """)

    nb.level(2, "GEOS on tables: overlay and union in SQL", "run the A3 overlay questions inside the database.",
             "Instead of carrying all the books home to read, you ask the librarian to find the answer in the building.")
    nb.ex("2.1", "Flooded area per neighbourhood", "ST_Intersection + ST_Buffer + GROUP BY",
          purpose_q="What is the **purpose** of `ST_Intersection`? Which A3 GeoPandas command does the same job?",
          purpose_a="Returns the shared part of two geometries (GEOS). Twin of `gpd.overlay(..., how='intersection')` / Shapely `intersection`.",
          life_a="How many hectares of each district are in the flood zone — for an insurance or planning report.",
          hint="`ST_Intersection(n.geometry, ST_Buffer(r.geometry, 150))`, area ÷ 10 000 = hectares. Join `neighbourhoods n` with `river r` using `ST_Intersects(n.geometry, ST_Buffer(r.geometry, 150))`.",
          starter="""
          sql(\"\"\"
              SELECT n.name, round((ST_Area(____(n.geometry, ST_Buffer(r.geometry, 150))) / 10000)::numeric, 1) AS flood_ha
              FROM neighbourhoods n JOIN river r ON ST_Intersects(n.geometry, ST_Buffer(r.geometry, 150))
              ORDER BY flood_ha DESC
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT n.name, round((ST_Area(ST_Intersection(n.geometry, ST_Buffer(r.geometry, 150))) / 10000)::numeric, 1) AS flood_ha
              FROM neighbourhoods n JOIN river r ON ST_Intersects(n.geometry, ST_Buffer(r.geometry, 150))
              ORDER BY flood_ha DESC
          \"\"\")
          """,
          note="Compare with A3 3.3. Small differences come from the buffer's number of segments (8 vs 16).")
    nb.ex("2.2", "Dissolve in SQL", "ST_Union(geometry) ... GROUP BY",
          purpose_q="What is the **purpose** of `ST_Union` used with `GROUP BY`? Which GeoPandas command is its twin?",
          purpose_a="Merges all geometries of a group into one (GEOS), like `gdf.dissolve(by=...)`.",
          life_a="Build districts from neighbourhoods; merge all parcels of one owner.",
          hint="Make the district from `nb_id`: `CASE WHEN nb_id <= 3 THEN 'south' WHEN nb_id <= 6 THEN 'centre' ELSE 'north' END`.",
          starter="""
          sql(\"\"\"
              SELECT CASE WHEN nb_id <= 3 THEN 'south' WHEN nb_id <= 6 THEN 'centre' ELSE 'north' END AS district,
                     sum(population) AS population, ST_Area(____(geometry)) / 1e6 AS km2
              FROM neighbourhoods GROUP BY 1 ORDER BY 1
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT CASE WHEN nb_id <= 3 THEN 'south' WHEN nb_id <= 6 THEN 'centre' ELSE 'north' END AS district,
                     sum(population) AS population, ST_Area(ST_Union(geometry)) / 1e6 AS km2
              FROM neighbourhoods GROUP BY 1 ORDER BY 1
          \"\"\")
          """)
    nb.ex("2.3", "Nearest clinic for each school (KNN)", "ORDER BY a.geometry <-> b.geometry LIMIT 1",
          purpose_q="What is the **purpose** of the `<->` operator? Which GeoPandas command is its twin?",
          purpose_a="`<->` is the distance operator used for 'K nearest neighbours' searches with the spatial index. Twin: `gpd.sjoin_nearest`.",
          life_a="The nearest fire station for every address, fast, even with millions of addresses.",
          hint="Use a `LATERAL` sub-query: for each school, sort clinics by `s.geometry <-> c.geometry` and keep 1.",
          starter="""
          sql(\"\"\"
              SELECT s.school, nc.clinic, round(nc.dist::numeric) AS dist_m
              FROM schools s
              CROSS JOIN LATERAL (
                  SELECT c.clinic, ST_Distance(s.geometry, c.geometry) AS dist
                  FROM clinics c ORDER BY s.geometry ____ c.geometry LIMIT ____
              ) nc
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT s.school, nc.clinic, round(nc.dist::numeric) AS dist_m
              FROM schools s
              CROSS JOIN LATERAL (
                  SELECT c.clinic, ST_Distance(s.geometry, c.geometry) AS dist
                  FROM clinics c ORDER BY s.geometry <-> c.geometry LIMIT 1
              ) nc
          \"\"\")
          """)

    nb.level(3, "PROJ and GDAL: coordinates and rasters", "transform coordinates with PROJ, measure on the globe with `geography`, and load and query a raster with GDAL.",
             "PROJ is the translator between map languages; GDAL is the one who can open every type of image file.")
    nb.ex("3.1", "What CRS is my table in?", "ST_SRID(geom) + spatial_ref_sys",
          purpose_q="What is the **purpose** of `ST_SRID` and the table `spatial_ref_sys`? Which internal library uses that catalogue?",
          purpose_a="`ST_SRID` gives the CRS code of a geometry; `spatial_ref_sys` holds the definitions of thousands of CRSs that **PROJ** uses for transformations.",
          life_a="Checking that two tables share a CRS before joining them (PostGIS refuses to mix SRIDs).",
          hint="`SELECT DISTINCT ST_SRID(geometry) FROM houses`, then look up `srtext` in `spatial_ref_sys` where `srid = 32633`.",
          starter="""
          print(sql("SELECT DISTINCT ____(geometry) AS srid FROM houses"))
          print(sql("SELECT srid, auth_name, left(srtext, 60) AS definition FROM ____ WHERE srid = 32633"))
          """,
          solution="""
          print(sql("SELECT DISTINCT ST_SRID(geometry) AS srid FROM houses"))
          print(sql("SELECT srid, auth_name, left(srtext, 60) AS definition FROM spatial_ref_sys WHERE srid = 32633"))
          """)
    nb.ex("3.2", "Transform to GPS coordinates", "ST_Transform(geom, 4326)",
          purpose_q="What is the **purpose** of `ST_Transform`, and which internal library does the maths?",
          purpose_a="Converts geometries to another CRS; **PROJ** does the calculation (twin: PyProj `Transformer` / GeoPandas `to_crs`).",
          life_a="Serving clinic locations to a phone app that expects lon/lat.",
          hint="`ST_X(ST_Transform(geometry, 4326))` gives the longitude, `ST_Y(...)` the latitude.",
          starter="""
          sql("SELECT clinic, ST_X(____(geometry, 4326)) AS lon, ST_Y(ST_Transform(geometry, ____)) AS lat FROM clinics")
          """,
          solution="""
          sql("SELECT clinic, ST_X(ST_Transform(geometry, 4326)) AS lon, ST_Y(ST_Transform(geometry, 4326)) AS lat FROM clinics")
          """)
    nb.ex("3.3", "Measure on the globe: geography", "ST_Distance(a::geography, b::geography)",
          purpose_q="What is the **purpose** of the `geography` type? Which PyProj tool from A2 is its twin?",
          purpose_a="`geography` stores lon/lat and measures on the curved Earth, in metres (twin: `pyproj.Geod`).",
          life_a="Distances between cities or countries, where no single flat projection is accurate.",
          hint="Berlin (13.40, 52.52) → Paris (2.35, 48.86). `ST_Point(lon, lat, 4326)::geography`. Expect ≈ 879 km, like A2 3.1.",
          starter="""
          sql("SELECT ST_Distance(ST_Point(13.40, 52.52, 4326)::____, ST_Point(2.35, 48.86, 4326)::geography) / 1000 AS km")
          """,
          solution="""
          sql("SELECT ST_Distance(ST_Point(13.40, 52.52, 4326)::geography, ST_Point(2.35, 48.86, 4326)::geography) / 1000 AS km")
          """)
    nb.ex("3.4", "Load a raster through GDAL", "ST_FromGDALRaster(bytes)",
          purpose_q="What is the **purpose** of `ST_FromGDALRaster`, and why must a GDAL driver be enabled first?",
          purpose_a="It lets **GDAL** read raster file bytes (here a GeoTIFF) and turns them into a PostGIS raster. For security, PostGIS enables no GDAL drivers by default; you switch on only the ones you need.",
          life_a="Storing an elevation model in the database next to the vector tables, so SQL can combine both.",
          hint="First `SET postgis.gdal_enabled_drivers = 'GTiff'`, then insert the file bytes as a parameter `%s`. All in one connection.",
          starter="""
          with connect() as conn:
              conn.execute("SET postgis.gdal_enabled_drivers = '____'")
              conn.execute("DROP TABLE IF EXISTS dem")
              conn.execute("CREATE TABLE dem AS SELECT 1 AS rid, ____(%s) AS rast", [(DATA_DIR / "dem.tif").read_bytes()])
              conn.commit()
              print(conn.execute("SELECT ST_Width(rast), ST_Height(rast), ST_SRID(rast), ST_PixelWidth(rast) FROM dem").fetchone())
              print(conn.execute("SELECT short_name FROM ST_GDALDrivers()").fetchall())
          """,
          solution="""
          with connect() as conn:
              conn.execute("SET postgis.gdal_enabled_drivers = 'GTiff'")
              conn.execute("DROP TABLE IF EXISTS dem")
              conn.execute("CREATE TABLE dem AS SELECT 1 AS rid, ST_FromGDALRaster(%s) AS rast", [(DATA_DIR / "dem.tif").read_bytes()])
              conn.commit()
              print(conn.execute("SELECT ST_Width(rast), ST_Height(rast), ST_SRID(rast), ST_PixelWidth(rast) FROM dem").fetchone())
              print(conn.execute("SELECT short_name FROM ST_GDALDrivers()").fetchall())
          """,
          note="On the command line, the tool `raster2pgsql` (it ships with PostGIS and also uses GDAL) does the same for big rasters, cut into tiles.")
    nb.ex("3.5", "Raster value at each school", "ST_Value(rast, point)",
          purpose_q="What is the **purpose** of `ST_Value`? Which Rasterio method is its twin?",
          purpose_a="Reads the pixel value at a point (twin: `src.sample()` in A5).",
          life_a="Elevation of every school or house directly in SQL.",
          hint="Join `schools s` and `dem d` with `ST_Intersects(d.rast, s.geometry)`.",
          starter="""
          sql(\"\"\"
              SELECT s.school, round(____(d.rast, s.geometry)::numeric, 1) AS elev_m
              FROM schools s JOIN dem d ON ST_Intersects(d.rast, s.geometry)
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT s.school, round(ST_Value(d.rast, s.geometry)::numeric, 1) AS elev_m
              FROM schools s JOIN dem d ON ST_Intersects(d.rast, s.geometry)
          \"\"\")
          """)
    nb.ex("3.6", "Zonal statistics in SQL", "ST_SummaryStats(ST_Clip(rast, polygon))",
          purpose_q="What is the **purpose** of combining `ST_Clip` and `ST_SummaryStats`? Which A5 exercise is the twin?",
          purpose_a="Clips the raster to each polygon and summarises the pixel values (count, mean, min, max). Twin: A5 3.4 (mask + mean).",
          life_a="Mean elevation (or temperature, or greenness) per district, for a report table.",
          hint="`(ST_SummaryStats(ST_Clip(d.rast, n.geometry))).mean` — the brackets around the function are needed to read one field.",
          starter="""
          sql(\"\"\"
              SELECT n.name, round((ST_SummaryStats(____(d.rast, n.geometry))).____::numeric, 1) AS mean_elev
              FROM neighbourhoods n JOIN dem d ON ST_Intersects(d.rast, n.geometry)
              ORDER BY mean_elev DESC
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT n.name, round((ST_SummaryStats(ST_Clip(d.rast, n.geometry))).mean::numeric, 1) AS mean_elev
              FROM neighbourhoods n JOIN dem d ON ST_Intersects(d.rast, n.geometry)
              ORDER BY mean_elev DESC
          \"\"\")
          """)

    nb.level(4, "Professional: fast and correct spatial SQL", "use indexes on purpose, read query plans, and answer the question types in SQL.",
             "A good librarian knows *which* catalogue to use so you get your book in one minute, not one day.")
    nb.pro("4.1", "Why ST_DWithin and not ST_Distance < x?", "Performance (proximity at scale)",
           scenario="Count houses within 300 m of each clinic in two ways: `ST_Distance(...) < 300` and `ST_DWithin(..., 300)`. Compare the query plans with `EXPLAIN`.",
           plan_hint="Run `EXPLAIN SELECT ...` for both. Look for **'Index Scan'** or **'Index Cond'** (uses the GIST index) vs **'Seq Scan'** with only a Filter (reads every row). Daily picture: looking up a word in a dictionary by the alphabet vs reading from page one.",
           starter="""
           q_slow = "SELECT c.clinic, count(*) FROM clinics c JOIN houses h ON ST_Distance(c.geometry, h.geometry) < 300 GROUP BY 1"
           q_fast = "SELECT c.clinic, count(*) FROM clinics c JOIN houses h ON ____(c.geometry, h.geometry, 300) GROUP BY 1"
           print(sql(q_fast))
           for q in [q_slow, q_fast]:
               plan = "\\n".join(sql("EXPLAIN " + q).iloc[:, 0])
               print("uses index:", "Index" in plan)
           """,
           solution="""
           q_slow = "SELECT c.clinic, count(*) FROM clinics c JOIN houses h ON ST_Distance(c.geometry, h.geometry) < 300 GROUP BY 1"
           q_fast = "SELECT c.clinic, count(*) FROM clinics c JOIN houses h ON ST_DWithin(c.geometry, h.geometry, 300) GROUP BY 1"
           print(sql(q_fast))
           for q in [q_slow, q_fast]:
               plan = "\\n".join(sql("EXPLAIN " + q).iloc[:, 0])
               print("uses index:", "Index" in plan)
           """,
           answer="`ST_DWithin` first uses the index (boxes), then GEOS checks exact distances only for candidates. `ST_Distance < x` must compute every distance. Same answer, very different speed on big tables.")
    nb.pro("4.2", "Population within 800 m of a clinic, per neighbourhood", "Proximity / accessibility (in SQL)",
           scenario="Repeat A3 exercise 4.1 in SQL: share of residents in each neighbourhood that live within 800 m of any clinic.",
           plan_hint="For each house: `EXISTS (SELECT 1 FROM clinics c WHERE ST_DWithin(h.geometry, c.geometry, 800))`. Then `sum(residents) FILTER (WHERE served) / sum(residents)` per `nb_id`, and join the names.",
           starter="""
           sql(\"\"\"
               WITH h AS (
                   SELECT nb_id, residents,
                          EXISTS (SELECT 1 FROM clinics c WHERE ____(h.geometry, c.geometry, 800)) AS served
                   FROM houses h)
               SELECT n.name, round(sum(residents) FILTER (WHERE served)::numeric / sum(residents), 2) AS share
               FROM h JOIN neighbourhoods n USING (nb_id)
               GROUP BY n.name ORDER BY share
           \"\"\")
           """,
           solution="""
           sql(\"\"\"
               WITH h AS (
                   SELECT nb_id, residents,
                          EXISTS (SELECT 1 FROM clinics c WHERE ST_DWithin(h.geometry, c.geometry, 800)) AS served
                   FROM houses h)
               SELECT n.name, round(sum(residents) FILTER (WHERE served)::numeric / sum(residents), 2) AS share
               FROM h JOIN neighbourhoods n USING (nb_id)
               GROUP BY n.name ORDER BY share
           \"\"\")
           """,
           answer="Same result as GeoPandas. Where to compute is a **decision**: in SQL when data is big or shared on a server; in GeoPandas when you explore, plot and model.")
    nb.pro("4.3", "Houses in low land: vector + raster in one query", "Modelling (raster-vector overlay in SQL)",
           scenario="Using the `dem` raster: how many houses stand on land lower than **37.5 m**? Which neighbourhoods have most of them?",
           plan_hint="`ST_Value(d.rast, h.geometry) < 37.5` in the WHERE clause, join `neighbourhoods` via `nb_id`, `GROUP BY`.",
           starter="""
           sql(\"\"\"
               SELECT n.name, count(*) AS low_houses
               FROM houses h
               JOIN dem d ON ST_Intersects(d.rast, h.geometry)
               JOIN neighbourhoods n USING (nb_id)
               WHERE ____(d.rast, h.geometry) < ____
               GROUP BY n.name ORDER BY low_houses DESC
           \"\"\")
           """,
           solution="""
           sql(\"\"\"
               SELECT n.name, count(*) AS low_houses
               FROM houses h
               JOIN dem d ON ST_Intersects(d.rast, h.geometry)
               JOIN neighbourhoods n USING (nb_id)
               WHERE ST_Value(d.rast, h.geometry) < 37.5
               GROUP BY n.name ORDER BY low_houses DESC
           \"\"\")
           """,
           answer="GDAL-loaded raster + GEOS/PostGIS vector logic in one SQL statement. The same bathtub model as A5 4.1 (river level ≈ 35.6 m + 2 m ≈ 37.5 m).")

    nb.test("""
    Answer in SQL (run it with `sql(\"\"\"...\"\"\")`). For each: **question type → which internal library does the key work → SQL → interpretation.**
    """, [
        ("task", """
        **A.** List the roads with their length in km inside the 150 m flood zone.
        """, """
        Type: overlay + measurement. GEOS computes buffer and intersection.
        ```python
        sql(\"\"\"
            SELECT ro.name, round((sum(ST_Length(ST_Intersection(ro.geometry, ST_Buffer(ri.geometry, 150)))) / 1000)::numeric, 2) AS km
            FROM roads ro JOIN river ri ON ST_Intersects(ro.geometry, ST_Buffer(ri.geometry, 150))
            GROUP BY ro.name ORDER BY km DESC
        \"\"\")
        ```
        """),
        ("task", """
        **B.** Export all schools as GeoJSON text in lon/lat, ready for a web map.
        """, """
        PROJ transforms, PostGIS writes GeoJSON.
        ```python
        sql("SELECT school, ST_AsGeoJSON(ST_Transform(geometry, 4326), 6) AS geojson FROM schools")
        ```
        """),
        ("task", """
        **C.** What is the area of Riverton in km² computed (a) in UTM and (b) on the globe with `geography`?
        """, """
        ```python
        sql(\"\"\"
            SELECT ST_Area(ST_Union(geometry)) / 1e6 AS utm_km2,
                   ST_Area(ST_Transform(ST_Union(geometry), 4326)::geography) / 1e6 AS globe_km2
            FROM neighbourhoods
        \"\"\")
        ```
        Almost equal: UTM is very good locally (compare A2 3.3).
        """),
        ("task", """
        **D.** Maximum elevation in each park, from the raster.
        """, """
        GDAL loaded the raster; PostGIS raster functions clip and summarise.
        ```python
        sql(\"\"\"
            SELECT p.park, round((ST_SummaryStats(ST_Clip(d.rast, p.geometry))).max::numeric, 1) AS max_elev
            FROM parks p JOIN dem d ON ST_Intersects(d.rast, p.geometry)
        \"\"\")
        ```
        """),
        ("model", """
        **E · Modelling: where should the work happen?** Riverton's houses table grows to **20 million** buildings (the whole country). You must compute 'residents within 800 m of a clinic' every night.
        Do you do it in PostGIS or in GeoPandas? Explain with at least three reasons.
        """, """
        **Recommendation: PostGIS.**
        1. Data does not fit comfortably in memory; the database streams it.
        2. GIST indexes + `ST_DWithin` make the search fast.
        3. The result stays on the server, where apps and colleagues use it; it can be scheduled (a nightly job) and kept consistent.
        Use GeoPandas afterwards to read the **small result** (per neighbourhood) for maps and models.
        """),
    ])
    nb.reflect("""
    Make your own translation table with 5 rows: Shapely/PyProj/Rasterio command → PostGIS function → internal library.
    (Example: `buffer` → `ST_Buffer` → GEOS.) Keep it; you will use it in B4 and the capstone.
    """)
    return nb
