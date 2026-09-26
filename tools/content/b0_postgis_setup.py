from nbbuild import NB, SETUP


def build():
    nb = NB("B0_postgis_setup", "B0 · PostGIS setup — start the database and load Riverton")
    nb.md("""
    **What PostgreSQL and PostGIS are:** PostgreSQL is a database server: it stores tables safely, lets many people use them at once,
    and answers questions written in **SQL**. **PostGIS** is an extension that adds a `geometry` column type and hundreds of
    spatial functions (`ST_Buffer`, `ST_Intersects`, `ST_Transform`…).

    **Daily picture:** files (GeoPackage, Shapefile) are like books on your desk: fine for one person.
    A database is like a public library with a librarian: many people read at the same time, the catalogue (index) finds
    things fast, and nobody loses a page.

    **The two groups of libraries in part B:**

    | Group | Library | Role | Notebook |
    |---|---|---|---|
    | Internal (inside PostGIS) | **GEOS** | geometry operations (buffer, intersection, union…) | B1 |
    | | **PROJ** | coordinate transformations (`ST_Transform`) | B1 |
    | | **GDAL** | raster reading/writing (`ST_FromGDALRaster`…) | B1 |
    | External (your Python side) | **Psycopg** | connect and send SQL | B2 |
    | | **SQLAlchemy / GeoAlchemy2** | connections and tables as Python objects | B3 |
    | | **GeoPandas** | `read_postgis()` / `to_postgis()` | B4 |
    """)
    nb.md("""
    ## Step 1 · Start a PostGIS database (choose one option)

    **Option A — Docker (recommended: same on Windows, Mac, Linux; easy to delete and restart):**
    ```bash
    docker run --name geotrain-db -e POSTGRES_USER=geo -e POSTGRES_PASSWORD=geo -e POSTGRES_DB=geotrain \\
               -p 5432:5432 -d postgis/postgis:16-3.4
    ```
    **Option B — Installers:** Windows: PostgreSQL installer from EDB + *StackBuilder → PostGIS*. Mac: *Postgres.app* (PostGIS included).
    Linux (Ubuntu): `sudo apt install postgresql postgis`. Then create a user `geo` (password `geo`) and a database `geotrain`.

    **Option C — Cloud notebook (e.g. Google Colab):** `!apt-get install -y postgresql postgis` then start the service; slower, but no install on your computer.

    The notebooks connect with this address (a *DSN*, like a postal address for the database):
    `postgresql://geo:geo@localhost:5432/geotrain` → user `geo`, password `geo`, computer `localhost`, port `5432`, database `geotrain`.
    If yours is different, set the environment variable `GEOTRAIN_DSN` before starting Jupyter.
    """)
    nb.code(SETUP)
    nb.code("""
    import psycopg
    import geopandas as gpd
    from geotrain.db import DSN, connect, engine, sql
    print("Connecting to:", DSN)
    """)

    nb.level(1, "Connect, enable PostGIS, meet the internal libraries", "open a connection, switch PostGIS on, and see which GEOS, PROJ and GDAL versions are inside.",
             "Getting a library card, and reading the sign that tells you which departments the library has.")
    nb.ex("1.1", "Open a connection and ask a first question", "psycopg.connect(DSN)",
          purpose_a="Opens a connection (a phone line) to the database; a cursor sends SQL through it and brings back rows.",
          life_a="Every Python script that reads or writes the city's database starts with a connection.",
          hint="`with psycopg.connect(DSN) as conn:` then `conn.execute(\"SELECT version()\").fetchone()`.",
          starter="""
          with psycopg.____(DSN) as conn:
              print(conn.execute("SELECT ____()").fetchone()[0])
          """,
          solution="""
          with psycopg.connect(DSN) as conn:
              print(conn.execute("SELECT version()").fetchone()[0])
          """)
    nb.ex("1.2", "Switch PostGIS on", "CREATE EXTENSION IF NOT EXISTS postgis",
          purpose_a="Installs PostGIS into this one database (adds the geometry type and the ST_ functions). `postgis_raster` adds rasters.",
          life_a="Done once per new database, like installing an app once on a phone.",
          hint="Run both statements, then `conn.commit()` to save. `IF NOT EXISTS` makes it safe to run twice.",
          starter="""
          with connect() as conn:
              conn.execute("CREATE EXTENSION IF NOT EXISTS ____")
              conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster")
              conn.____()
          """,
          solution="""
          with connect() as conn:
              conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
              conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster")
              conn.commit()
          """)
    nb.ex("1.3", "Find GEOS, PROJ and GDAL inside PostGIS", "SELECT postgis_full_version()",
          purpose_a="Reports the PostGIS version and the versions of the libraries it uses internally: GEOS, PROJ, GDAL…",
          life_a="When a function behaves differently on two servers, the GEOS or PROJ version is often the reason.",
          hint="Use the helper `sql(\"SELECT postgis_full_version()\")` — it returns a table. Look for `GEOS=`, `PROJ=`, `GDAL=` in the text.",
          starter="""
          import re
          txt = sql("SELECT ____()").iloc[0, 0]
          for name, version in re.findall(r'(POSTGIS|GEOS|PROJ|GDAL)="([^"]+)"', txt):
              print(f"{name:8s} {version}")
          """,
          solution="""
          import re
          txt = sql("SELECT postgis_full_version()").iloc[0, 0]
          for name, version in re.findall(r'(POSTGIS|GEOS|PROJ|GDAL)="([^"]+)"', txt):
              print(f"{name:8s} {version}")
          """,
          note="Compare with Shapely: `import shapely; shapely.geos_version_string`. Same engine, maybe a different version.")

    nb.level(2, "Load Riverton into the database", "copy every Riverton layer into PostGIS tables and check them.",
             "Moving your books from your desk into the library, and checking they appear in the catalogue.")
    nb.ex("2.1", "Upload all layers", "gdf.to_postgis(name, engine, if_exists='replace')",
          purpose_a="Writes a GeoDataFrame as a table with a geometry column into PostGIS (you study it in detail in B4).",
          life_a="Publishing your cleaned layers so colleagues and web apps can query them.",
          hint="Loop over the layers of the GeoPackage. `engine()` is a SQLAlchemy connection maker from the helper module. The `DROP TABLE ... CASCADE` line makes the cell safe to run again later (training database only!).",
          starter="""
          import pyogrio
          eng = engine()
          for name, _ in pyogrio.list_layers(GPKG):
              gdf = gpd.read_file(GPKG, layer=name)
              sql(f"DROP TABLE IF EXISTS {name} CASCADE")   # CASCADE also drops views built on it (e.g. from B4)
              gdf.____(name, eng, if_exists="____", index=False)
              print("loaded", name, len(gdf))
          """,
          solution="""
          import pyogrio
          eng = engine()
          for name, _ in pyogrio.list_layers(GPKG):
              gdf = gpd.read_file(GPKG, layer=name)
              sql(f"DROP TABLE IF EXISTS {name} CASCADE")   # CASCADE also drops views built on it (e.g. from B4)
              gdf.to_postgis(name, eng, if_exists="replace", index=False)
              print("loaded", name, len(gdf))
          """)
    nb.ex("2.2", "The catalogue of spatial tables", "SELECT * FROM geometry_columns",
          purpose_a="`geometry_columns` is a view that lists every table with a geometry column, its geometry type and SRID (CRS code).",
          life_a="Discovering what spatial data exists in a database you have just been given access to.",
          hint="Select the columns `f_table_name, f_geometry_column, type, srid`.",
          starter="""
          sql("SELECT f_table_name, f_geometry_column, type, srid FROM ____ ORDER BY 1")
          """,
          solution="""
          sql("SELECT f_table_name, f_geometry_column, type, srid FROM geometry_columns ORDER BY 1")
          """)
    nb.ex("2.3", "Add spatial indexes", "CREATE INDEX ... USING GIST (geometry)",
          purpose_a="Builds a spatial index (GIST) so spatial searches check only nearby shapes (like the STRtree in A1).",
          life_a="Without an index, 'houses near this road' reads every house in the country; with it, only the nearby ones.",
          hint="`to_postgis` usually creates one already. `IF NOT EXISTS` avoids an error. Then `ANALYZE` updates the statistics the database uses to plan queries.",
          starter="""
          for t in ["neighbourhoods", "houses", "accidents", "roads", "schools", "clinics", "parks", "river", "sensors"]:
              sql(f"CREATE INDEX IF NOT EXISTS {t}_geom_idx ON {t} USING ____ (geometry)")
              sql(f"ANALYZE {t}")
          sql("SELECT tablename, indexname FROM pg_indexes WHERE indexname LIKE '%geom%' ORDER BY 1")
          """,
          solution="""
          for t in ["neighbourhoods", "houses", "accidents", "roads", "schools", "clinics", "parks", "river", "sensors"]:
              sql(f"CREATE INDEX IF NOT EXISTS {t}_geom_idx ON {t} USING GIST (geometry)")
              sql(f"ANALYZE {t}")
          sql("SELECT tablename, indexname FROM pg_indexes WHERE indexname LIKE '%geom%' ORDER BY 1")
          """)
    nb.ex("2.4", "Your first spatial SQL question", "ST_Within(a.geometry, b.geometry)",
          purpose_a="A yes/no test in SQL: is geometry a inside b? Used in a JOIN it links rows by location (a spatial join).",
          life_a="Counting accidents per neighbourhood — the same as `gpd.sjoin` in A3, but done by the database.",
          hint="`FROM accidents a JOIN neighbourhoods n ON ST_Within(a.geometry, n.geometry)`, then `GROUP BY n.name`.",
          starter="""
          sql(\"\"\"
              SELECT n.name, count(*) AS accidents
              FROM accidents a JOIN neighbourhoods n ON ____(a.geometry, n.geometry)
              GROUP BY n.name
              ORDER BY accidents DESC
          \"\"\")
          """,
          solution="""
          sql(\"\"\"
              SELECT n.name, count(*) AS accidents
              FROM accidents a JOIN neighbourhoods n ON ST_Within(a.geometry, n.geometry)
              GROUP BY n.name
              ORDER BY accidents DESC
          \"\"\")
          """,
          note="Compare with A3 exercise 3.1: same numbers. Now you have one question answered in two worlds.")
    nb.md("""
    ### ✅ Setup check

    If all cells ran, your database holds Riverton. Go on with **B1** (the internal libraries). Keep the database running.
    """)
    return nb
