"""End-of-notebook projects for group B (PostGIS)."""

PSETUP = '''
from geotrain.projects import build_projects, PROJ_DIR, publish
build_projects()
'''


def p_b0(nb):
    nb.project(
        "Your PostGIS workspace for all projects",
        """Set up the database the way a GIS team would: one schema `projects` holding the project layers (streets, buildings,
        tracts, fire stations), each with a spatial index, checked in SQL, and **connected to QGIS**, saved as a QGIS project file
        that you will reuse in the next notebooks.""",
        [("streets.gpkg", "1 172 street segments: `kind` (main/local), `speed_kmh`, `bridge`"),
         ("buildings.gpkg", "~1 700 building footprints"), ("tracts.gpkg", "36 census tracts"), ("fire_stations.gpkg", "Riverton's fire station")],
        [("""**Load** the four layers into schema `projects` (use `publish()` or `to_postgis(..., schema="projects")`).""", """
          ```python
          layers = {name: gpd.read_file(PROJ_DIR / f"{name}.gpkg") for name in ["streets", "buildings", "tracts", "fire_stations"]}
          publish(layers)
          ```
          """),
         ("""**Check the catalogue.** For each table in `projects`: geometry type, SRID and row count.""", """
          ```python
          sql(\"\"\"SELECT f_table_name, type, srid,
                      (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I.%I', f_table_schema, f_table_name), false, true, '')))[1]::text::int AS rows
               FROM geometry_columns WHERE f_table_schema = 'projects' ORDER BY 1\"\"\")
          ```
          (The `query_to_xml` trick counts rows of each table in one query; a loop in Python works too.)
          """),
         ("""**Indexes.** Make sure each geometry column has a GIST index (create missing ones) and run `ANALYZE`.""", """
          ```python
          for t in ["streets", "buildings", "tracts", "fire_stations"]:
              sql(f"CREATE INDEX IF NOT EXISTS {t}_gix ON projects.{t} USING GIST (geometry)")
              sql(f"ANALYZE projects.{t}")
          sql("SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'projects' AND indexdef ILIKE '%gist%' ORDER BY 1")
          ```
          """),
         ("""**First spatial questions in SQL:** number of buildings and residents per tract (building centroid within tract). Save it as a view `projects.tract_buildings` with the tract geometry, for QGIS.""", """
          ```python
          sql(\"\"\"CREATE OR REPLACE VIEW projects.tract_buildings AS
               SELECT t.tract_id, t.geometry, count(b.*) AS buildings, coalesce(sum(b.residents), 0) AS residents
               FROM projects.tracts t LEFT JOIN projects.buildings b ON ST_Within(ST_Centroid(b.geometry), t.geometry)
               GROUP BY t.tract_id, t.geometry\"\"\")
          sql("SELECT tract_id, buildings, residents FROM projects.tract_buildings ORDER BY residents DESC LIMIT 5")
          ```
          """)],
        setup=PSETUP,
        qgis="""
        1. Create the PostGIS connection in QGIS (steps below) and load **streets, buildings, tracts, fire_stations** and the view **tract_buildings**.
        2. For the view, QGIS asks for a *feature id* column: choose `tract_id`.
        3. Style: streets by `kind` (main thicker), bridges in red (`"bridge" = true`), tract_buildings graduated by `residents`.
        4. **Save the project** as `riverton_projects.qgz` (*Project → Save As*) next to the notebooks. You will reopen it in B1–B4.
        5. Optional: *Project → Properties → Data Sources → Trust project when data source has no metadata* makes big PostGIS projects open faster.
        """,
        deliver=["Schema `projects` with 4 indexed layers", "View `tract_buildings`", "QGIS project `riverton_projects.qgz`"])


def p_b1(nb):
    nb.project(
        "Flood exposure and street access, all in spatial SQL",
        """The planning office wants four answers from PostGIS alone: which buildings are close to the river, which stand on low ground
        (DEM raster), how far each building is from the nearest street, and a profile per tract. Deliver the answers as **views** that QGIS can show.""",
        [("projects.buildings / streets / tracts", "loaded in the B0 project (re-loaded here if missing)"),
         ("public.river, public.dem", "the river line (B0) and the DEM raster you loaded in B1 3.4")],
        [("""**Near the river.** Buildings (and residents) within 150 m of the river (`ST_DWithin`).""", """
          ```python
          sql(\"\"\"SELECT count(*) AS buildings, sum(b.residents) AS residents
               FROM projects.buildings b, public.river r WHERE ST_DWithin(b.geometry, r.geometry, 150)\"\"\")
          ```
          """),
         ("""**On low ground.** Elevation of each building (DEM value at its centroid). Create a view `projects.low_buildings` of buildings below 37.5 m, with geometry.""", """
          ```python
          sql(\"\"\"CREATE OR REPLACE VIEW projects.low_buildings AS
               SELECT b.bldg_id, b.use, b.residents, ST_Value(d.rast, ST_Centroid(b.geometry)) AS elev, b.geometry
               FROM projects.buildings b JOIN public.dem d ON ST_Intersects(d.rast, ST_Centroid(b.geometry))
               WHERE ST_Value(d.rast, ST_Centroid(b.geometry)) < 37.5\"\"\")
          sql("SELECT count(*), sum(residents) FROM projects.low_buildings")
          ```
          """),
         ("""**Street access.** For every building, the nearest street segment and its distance (KNN `<->` with LATERAL). Average and maximum distance?""", """
          ```python
          sql(\"\"\"SELECT round(avg(ns.d)::numeric, 1) AS avg_m, round(max(ns.d)::numeric, 1) AS max_m
               FROM projects.buildings b
               CROSS JOIN LATERAL (SELECT ST_Distance(b.geometry, s.geometry) AS d FROM projects.streets s
                                   ORDER BY b.geometry <-> s.geometry LIMIT 1) ns\"\"\")
          ```
          """),
         ("""**Tract profile view** `projects.tract_profile`: residents, asthma rate per 1 000, number of low buildings and residents in them, with the tract geometry.""", """
          ```python
          sql(\"\"\"CREATE OR REPLACE VIEW projects.tract_profile AS
               SELECT t.tract_id, t.population, round(t.asthma_cases * 1000.0 / t.population, 1) AS asthma_rate,
                      count(l.*) AS low_buildings, coalesce(sum(l.residents), 0) AS low_residents, t.geometry
               FROM projects.tracts t LEFT JOIN projects.low_buildings l ON ST_Within(ST_Centroid(l.geometry), t.geometry)
               GROUP BY t.tract_id, t.population, t.asthma_cases, t.geometry\"\"\")
          sql("SELECT tract_id, low_residents, asthma_rate FROM projects.tract_profile ORDER BY low_residents DESC LIMIT 5")
          ```
          """),
         ("""**For the web:** export the tract profile as GeoJSON in lon/lat (PROJ via `ST_Transform`) — one GeoJSON *FeatureCollection* built in SQL.""", """
          ```python
          gj = sql(\"\"\"SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json))
                      FROM (SELECT tract_id, asthma_rate, low_residents, ST_Transform(geometry, 4326) AS geometry FROM projects.tract_profile) t\"\"\").iloc[0, 0]
          import json; (PROJ_DIR / "b1_tract_profile.geojson").write_text(json.dumps(gj)); print(len(gj["features"]), "features written")
          ```
          """)],
        setup=PSETUP + '''
import geopandas as gpd
from geotrain.db import sql as _sql
if _sql("SELECT to_regclass('projects.buildings') IS NULL AS missing").iloc[0, 0]:
    publish({n: gpd.read_file(PROJ_DIR / f"{n}.gpkg") for n in ["streets", "buildings", "tracts"]})
''',
        qgis="""
        1. Open `riverton_projects.qgz` (B0) or connect again. Load the views **low_buildings** (id `bldg_id`) and **tract_profile** (id `tract_id`).
        2. **DB Manager → SQL Window:** paste your task 3 query but return `b.bldg_id, ns.d, b.geometry` and load it as a layer — style buildings by distance to street.
        3. Drag `b1_tract_profile.geojson` into QGIS: same tracts, now in EPSG:4326 — QGIS reprojects on the fly.
        4. Edit a building in QGIS (move it), then re-open the view: views always show the **current** data.
        """,
        deliver=["Answers to tasks 1 and 3", "Views `low_buildings` and `tract_profile` in PostGIS", "GeoJSON export + QGIS map"])


def p_b2(nb):
    nb.project(
        "A live air-quality feed with Psycopg",
        """Riverton's 18 sensors now send **hourly PM2.5 readings**. Build the pipeline with Psycopg: a readings table with keys, a safe
        insert of a day of data, a fast bulk load of a week, a 'latest reading' layer for QGIS, and an alert query. Then watch QGIS update.""",
        [("public.sensors", "the 18 sensor locations with a typical PM2.5 level (loaded in B0)"),
         ("projects.pm_readings", "the table you create: one row per sensor per hour")],
        [("""**Create the table** `projects.pm_readings (sensor_id, ts, pm25)` with a primary key on (sensor_id, ts) and a CHECK (pm25 ≥ 0).""", """
          ```python
          with psycopg.connect(DSN) as conn:
              conn.execute("CREATE SCHEMA IF NOT EXISTS projects")
              conn.execute("DROP TABLE IF EXISTS projects.pm_readings CASCADE")
              conn.execute(\"\"\"CREATE TABLE projects.pm_readings (sensor_id text NOT NULL, ts timestamp NOT NULL,
                                pm25 real NOT NULL CHECK (pm25 >= 0), PRIMARY KEY (sensor_id, ts))\"\"\")
          ```
          """),
         ("""**One day, safely.** Simulate 24 hourly readings per sensor (typical level + rush-hour bump + noise) and insert with `executemany` and parameters.""", """
          ```python
          import numpy as np
          rng = np.random.default_rng(7)
          base = my_sql("SELECT sensor_id, pm25 FROM public.sensors")
          def readings(day, hours=24):
              rows = []
              for sid, lvl in zip(base.sensor_id, base.pm25):
                  for h in range(hours):
                      rush = 6 if h in (7, 8, 17, 18) else 0
                      rows.append((sid, day + pd.Timedelta(hours=h), float(max(0, lvl + rush + rng.normal(0, 2)))))
              return rows
          day1 = readings(pd.Timestamp("2025-09-01"))
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              cur.executemany("INSERT INTO projects.pm_readings VALUES (%s, %s, %s)", day1)
          my_sql("SELECT count(*) FROM projects.pm_readings")
          ```
          """),
         ("""**A week, fast.** Load the next 7 days with `COPY` and compare the row count. What happens if you run the day-1 insert again (primary key!)?""", """
          ```python
          week = [r for d in range(2, 9) for r in readings(pd.Timestamp(f"2025-09-{d:02d}"))]
          with psycopg.connect(DSN) as conn, conn.cursor() as cur:
              with cur.copy("COPY projects.pm_readings (sensor_id, ts, pm25) FROM STDIN") as cp:
                  for r in week:
                      cp.write_row(r)
          print(my_sql("SELECT count(*) FROM projects.pm_readings"))
          try:
              with psycopg.connect(DSN) as conn, conn.cursor() as cur:
                  cur.executemany("INSERT INTO projects.pm_readings VALUES (%s, %s, %s)", day1[:1])
          except psycopg.errors.UniqueViolation as e:
              print("refused duplicate:", e.diag.message_primary)
          ```
          """),
         ("""**Latest reading as a map layer.** A view `projects.pm_latest` with each sensor's most recent reading and its geometry (`DISTINCT ON`), and a view of daily means.""", """
          ```python
          with psycopg.connect(DSN) as conn:
              conn.execute(\"\"\"CREATE OR REPLACE VIEW projects.pm_latest AS
                  SELECT DISTINCT ON (r.sensor_id) r.sensor_id, r.ts, r.pm25, s.geometry
                  FROM projects.pm_readings r JOIN public.sensors s USING (sensor_id)
                  ORDER BY r.sensor_id, r.ts DESC\"\"\")
              conn.execute(\"\"\"CREATE OR REPLACE VIEW projects.pm_daily AS
                  SELECT sensor_id, ts::date AS day, round(avg(pm25)::numeric, 1) AS mean_pm25 FROM projects.pm_readings GROUP BY 1, 2\"\"\")
          my_sql("SELECT sensor_id, ts, round(pm25::numeric, 1) AS pm25 FROM projects.pm_latest ORDER BY pm25 DESC LIMIT 3")
          ```
          `DISTINCT ON (sensor_id) ... ORDER BY sensor_id, ts DESC` keeps the first (= newest) row per sensor — a PostgreSQL speciality.
          """),
         ("""**Alert function.** `alerts(limit)` returns the sensors whose **daily mean** exceeded the limit on any day, with the number of days (safe parameter). Try the WHO guideline, 15 µg/m³.""", """
          ```python
          def alerts(limit):
              return my_sql(\"\"\"SELECT sensor_id, count(*) AS days_over, max(mean_pm25) AS worst
                                FROM projects.pm_daily WHERE mean_pm25 > %s GROUP BY sensor_id ORDER BY days_over DESC\"\"\", (limit,))
          alerts(15)
          ```
          """)],
        setup=PSETUP + '''
import pandas as pd
''',
        qgis="""
        1. Load **pm_latest** (id `sensor_id`) and style it *Graduated* on `pm25` (green → red). Label with `round("pm25", 1)`.
        2. Run task 3 again with the next week (change the dates) in the notebook, then in QGIS press **F5 / refresh**: the map shows the new latest values. That is a *live* layer.
        3. Load **pm_daily** as a table and use the *Data Plotly* plugin (optional) to draw one sensor's daily means.
        4. Layer Properties → *Rendering → Refresh layer at interval* (e.g. 10 s) makes QGIS poll the view automatically.
        """,
        deliver=["Table `pm_readings` with keys and 8 days of data", "Views `pm_latest` and `pm_daily`", "Alert table for 15 µg/m³ + QGIS live map"])


def p_b3(nb):
    nb.project(
        "Backend of a 'report a problem' app with SQLAlchemy",
        """Citizens will report potholes, broken lights and fallen trees in an app. Build the database side with the **ORM**:
        the table as a Python class, 60 test reports on real streets, queries the city needs, a status update, and a map in QGIS
        where staff can edit statuses.""",
        [("projects.streets", "the street network (B0 project)"), ("public.schools", "schools (B0)"),
         ("projects.reports", "the table you create")],
        [("""**The model.** Class `Report` → table `projects.reports`: id, category, status (default 'new'), created_at, description, `geom` POINT 32633. Create it.""", """
          ```python
          class PBase(DeclarativeBase):
              pass
          class Report(PBase):
              __tablename__ = "reports"
              __table_args__ = {"schema": "projects"}
              id: Mapped[int] = mapped_column(primary_key=True)
              category: Mapped[str]
              status: Mapped[str] = mapped_column(default="new")
              created_at: Mapped[datetime.datetime]
              description: Mapped[str]
              geom = mapped_column(Geometry("POINT", srid=32633))
          PBase.metadata.drop_all(engine); PBase.metadata.create_all(engine)
          print(sa.inspect(engine).get_columns("reports", schema="projects")[-1]["type"])
          ```
          """),
         ("""**Test data.** 60 reports at random points **on** streets (a random street segment, a random position along it), with random categories and times.""", """
          ```python
          import random
          random.seed(4)
          streets = gpd.read_postgis("SELECT street_id, kind, geometry FROM projects.streets", engine, geom_col="geometry")
          cats = ["pothole", "broken light", "fallen tree"]
          with Session(engine) as s:
              for i in range(60):
                  seg = streets.geometry.iloc[random.randrange(len(streets))]
                  p = seg.interpolate(random.random(), normalized=True)
                  s.add(Report(category=random.choice(cats), description=f"test report {i}",
                               created_at=datetime.datetime(2025, 9, 1) + datetime.timedelta(hours=random.randint(0, 24 * 20)),
                               geom=from_shape(p, srid=32633)))
              s.commit()
          with Session(engine) as s:
              print(s.execute(select(Report.category, func.count()).group_by(Report.category)).all())
          ```
          """),
         ("""**Queries the city needs:** (a) open reports per category; (b) reports within 300 m of a school (reflect `public.schools`).""", """
          ```python
          schools_t = sa.Table("schools", sa.MetaData(), autoload_with=engine, schema="public")
          with Session(engine) as s:
              print(s.execute(select(Report.category, func.count()).where(Report.status == "new").group_by(Report.category)).all())
              near = s.execute(select(Report.id, Report.category, schools_t.c.school)
                               .join(schools_t, func.ST_DWithin(Report.geom, schools_t.c.geometry, 300))).all()
          print(len(near), "reports near schools", near[:3])
          ```
          """),
         ("""**Update:** main streets are repaired first, so every report on a **main** street goes to 'in progress' (a report is 'on' a street if within 15 m). Commit and count statuses.""", """
          ```python
          streets_t = sa.Table("streets", sa.MetaData(), autoload_with=engine, schema="projects")
          on_main = select(Report.id).join(streets_t, func.ST_DWithin(Report.geom, streets_t.c.geometry, 15)).where(
              streets_t.c.kind == "main")
          with Session(engine) as s:
              for r in s.scalars(select(Report).where(Report.id.in_(on_main))):
                  r.status = "in progress"
              s.commit()
              print(s.execute(select(Report.status, func.count()).group_by(Report.status)).all())
          ```
          """),
         ("""**Reports per tract** for the monthly report: join reports to `projects.tracts` with `ST_Within` and read the result into pandas.""", """
          ```python
          per_tract = pd.read_sql(text(\"\"\"SELECT t.tract_id, count(r.id) AS reports
                                           FROM projects.tracts t LEFT JOIN projects.reports r ON ST_Within(r.geom, t.geometry)
                                           GROUP BY t.tract_id ORDER BY reports DESC\"\"\"), engine)
          per_tract.head()
          ```
          """)],
        setup=PSETUP + '''
import datetime
import pandas as pd
import geopandas as gpd
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
''',
        qgis="""
        1. Load **projects.reports** (it has a primary key, so QGIS can edit it). Style *Categorized* by `status`; use different symbols per `category` (*Rule-based*).
        2. *Toggle Editing* → select a report → change `status` to 'fixed' in the attribute table → *Save Edits*.
        3. Back in the notebook, re-run the status count of task 4: your QGIS edit is there. **QGIS and Python share one database.**
        4. Try to add a new point in QGIS with the *Add Point Feature* tool: this is how an office user would log a phone report.
        """,
        deliver=["ORM class and table `projects.reports`", "Answers to task 3 and the status table after task 4", "Reports per tract table + a QGIS edit round-trip"])


def p_b4(nb):
    nb.project(
        "Bike share: which stations work, and where is the gap?",
        """Combine SQL and GeoPandas on purpose. The trip counting (6 000 trips) happens **in PostGIS**; the catchment analysis
        (residents around each station) happens **in GeoPandas**; the results go back to PostGIS for QGIS. Finally, find the tract where a
        new station would reach the most people who have none today.""",
        [("bike_stations.csv, bike_trips.csv", "stations (lon/lat) and trips"), ("projects.buildings, projects.tracts", "residents and tracts (B0 project)")],
        [("""**Load** the stations as points in EPSG:32633 into `projects.bike_stations` (GeoPandas) and the trips as a plain table `projects.bike_trips`.""", """
          ```python
          st = pd.read_csv(PROJ_DIR / "bike_stations.csv")
          st = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.lon, st.lat), crs=4326).to_crs(32633)
          st.to_postgis("bike_stations", eng, schema="projects", if_exists="replace", index=False)
          pd.read_csv(PROJ_DIR / "bike_trips.csv").to_sql("bike_trips", eng, schema="projects", if_exists="replace", index=False)
          sql("SELECT (SELECT count(*) FROM projects.bike_stations) st, (SELECT count(*) FROM projects.bike_trips) trips")
          ```
          """),
         ("""**Count in the database:** starts and ends per station, read back **with geometry** (`read_postgis`).""", """
          ```python
          use = gpd.read_postgis(\"\"\"
              SELECT s.station_id, s.name, s.capacity, s.geometry,
                     (SELECT count(*) FROM projects.bike_trips t WHERE t.start_station = s.station_id) AS starts,
                     (SELECT count(*) FROM projects.bike_trips t WHERE t.end_station = s.station_id) AS ends
              FROM projects.bike_stations s\"\"\", eng, geom_col="geometry")
          use.nlargest(3, "starts")[["name", "starts", "ends"]]
          ```
          """),
         ("""**Catchments in GeoPandas:** residents within 400 m of each station (building centroids), and trips per 100 residents. Which station performs best relative to its catchment?""", """
          ```python
          bld = gpd.read_postgis("SELECT residents, ST_Centroid(geometry) AS geometry FROM projects.buildings WHERE residents > 0", eng, geom_col="geometry")
          ring = use[["station_id", "geometry"]].assign(geometry=use.buffer(400))
          res = gpd.sjoin(bld, ring, predicate="within").groupby("station_id")["residents"].sum()
          use["residents_400m"] = use["station_id"].map(res).fillna(0)
          use["starts_per_100res"] = (use["starts"] / use["residents_400m"].replace(0, np.nan) * 100).round(1)
          use.sort_values("starts_per_100res", ascending=False)[["name", "starts", "residents_400m", "starts_per_100res"]].head()
          ```
          """),
         ("""**The gap (in SQL):** per tract, residents living **more than 500 m** from any station (`NOT EXISTS … ST_DWithin`). Which tract is the best candidate for a new station?""", """
          ```python
          gap = gpd.read_postgis(\"\"\"
              SELECT t.tract_id, t.geometry, coalesce(sum(b.residents), 0) AS unserved
              FROM projects.tracts t
              LEFT JOIN projects.buildings b ON ST_Within(ST_Centroid(b.geometry), t.geometry) AND b.residents > 0
                   AND NOT EXISTS (SELECT 1 FROM projects.bike_stations s WHERE ST_DWithin(s.geometry, b.geometry, 500))
              GROUP BY t.tract_id, t.geometry\"\"\", eng, geom_col="geometry")
          gap.nlargest(3, "unserved")[["tract_id", "unserved"]]
          ```
          """),
         ("""**Publish** `station_performance` (task 3) and `station_gap` (task 4) to PostGIS.""", """
          ```python
          use.to_postgis("station_performance", eng, schema="projects", if_exists="replace", index=False)
          gap.to_postgis("station_gap", eng, schema="projects", if_exists="replace", index=False)
          sql("SELECT f_table_name FROM geometry_columns WHERE f_table_schema = 'projects' AND f_table_name LIKE 'station%'")
          ```
          **Why this split:** counting 6 000 (or 6 million) trips is a database job; buffers, joins and ratios for 24 stations are quick and flexible in GeoPandas.
          """)],
        setup=PSETUP + '''
import numpy as np
''',
        qgis="""
        1. Open `riverton_projects.qgz`, add **station_performance** and **station_gap**.
        2. `station_gap`: *Graduated* on `unserved`; `station_performance`: circles sized by `starts`, labelled with `starts_per_100res`.
        3. With the *Add Point Feature* tool, digitise your proposed new station in a new *Temporary scratch layer*, and measure its distance to the nearest stations.
        4. Build a print layout: title, the two layers, legend, and a text box with your recommendation.
        """,
        deliver=["Station usage table (from SQL)", "Catchment and performance table (from GeoPandas)", "Gap map with the recommended tract + short justification"])
