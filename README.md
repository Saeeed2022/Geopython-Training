# GeoPython & PostGIS training — step by step, easy to professional

A hands-on course in Jupyter notebooks for three groups of tools:

| Group | Libraries | Notebooks |
|---|---|---|
| **A · GeoPython** | Shapely, PyProj, GeoPandas, Pyogrio/Fiona, Rasterio, PySAL | `A1`–`A6` |
| **S · SQL and PostgreSQL** | SELECT, WHERE, GROUP BY, JOIN, subqueries, CTEs; tables, keys, indexes, views, transactions, users | `S1`, `S2` |
| **B · PostGIS, internal** (engines inside the database) | GEOS, PROJ, GDAL | `B1` |
| **B · PostGIS, external** (Python talks to the database) | Psycopg, SQLAlchemy/GeoAlchemy2, GeoPandas `read_postgis`/`to_postgis` | `B0`, `B2`–`B4` |
| **D · Desktop GIS engines** (QGIS Processing toolbox, run from Jupyter) | QGIS native, GDAL/OGR, GRASS GIS, SAGA GIS | `D0`–`D4` |
| **Capstone** | everything together | `C` |

The main focus is **GeoPandas and Shapely**, then **some PostGIS**.

## Recommended order

`00_START_HERE` → `A1_shapely` → `A2_pyproj` → **`A3_geopandas`** → `A4_pyogrio_fiona` → `A6_pysal` →
`S1_sql_foundations` → `S2_postgresql` → `B0_postgis_setup` →
`B1_postgis_internal` → `B2_psycopg` → `B3_sqlalchemy_geoalchemy2` → `B4_geopandas_postgis` → `A5_rasterio` →
`D0_desktop_gis_setup` → `D1_qgis_native` → `D2_gdal_ogr` → `D3_grass` → `D4_saga` → `C_capstone`

About 23 weeks at ~5 hours a week, projects included. `00_START_HERE` explains why this order is used.

## How each exercise works

1. **Purpose**: what does the command do?
2. **Real life**: where would you use it?
3. **Hint**: hidden, so open it only after you have tried.
4. **Code**: fill in the `____` blanks and run the cell.

Then open **✅ Solution** and compare your answer. Each notebook has four levels: Basics → Core tools → Combining → **Professional**.
At the Professional level you first name the **type of question** (descriptive, measurement, proximity, overlay, statistical,
modelling, decision, temporal), then plan, then code. Every notebook ends with a **🏁 Final test** that has task questions
("we want to do A, B, C, D in the region") and **modelling questions** ("how do we model X geographically?").

All notebooks use **Riverton**, a made-up 6 × 6 km town (EPSG:32633). Its data is generated on first run, so there is nothing to download.

## A project at the end of every notebook

After the final test, each notebook has a **🏗️ Project** with its **own data layer** (in `data/projects/`, generated on first run):

| Notebook | Project | Project data |
|---|---|---|
| A1 Shapely | Tram line A or B? | `tram.gpkg` |
| A2 PyProj | Cyclists' GPS tracks: real distances and speeds | `gps_tracks.csv` |
| A3 GeoPandas | Green-space access audit | `buildings.gpkg`, `tracts.gpkg` |
| A4 Pyogrio/Fiona | Clean a messy data delivery | `delivery/` (4 broken files) |
| A6 PySAL | Asthma clusters and their causes | `tracts.gpkg` |
| S1 SQL | What do the bike-share trips tell us? | `bike_*.csv` |
| S2 PostgreSQL | Build the bike-share database properly | `bike_*.csv` + bad rows |
| B0 PostGIS setup | Your PostGIS workspace + QGIS project | streets, buildings, tracts, fire station |
| B1 PostGIS internals | Flood exposure and street access in spatial SQL | same + DEM raster |
| B2 Psycopg | A live air-quality feed | sensor readings you generate |
| B3 SQLAlchemy/GeoAlchemy2 | Backend of a "report a problem" app | reports you generate |
| B4 GeoPandas ⇄ PostGIS | Bike stations: performance and gaps | bike stations + buildings |
| A5 Rasterio | Urban heat: who suffers? | `lst.tif` |
| D1 QGIS native | Fire-engine response times on the street network | `streets.gpkg`, `fire_stations.gpkg` |
| D2 GDAL/OGR | An open-data release | rasters + vectors |
| D3 GRASS | Storm-water risk per building | DEM + buildings |
| D4 SAGA | Basement-flooding risk | DEM + buildings |

Every project publishes its result to the PostGIS schema `projects` and ends in **QGIS** (connect to the database, style, map).

## Setup

```bash
pip install -r requirements.txt
cd notebooks
jupyter lab
```

For part B you also need a PostGIS database. The easiest way is Docker:

```bash
docker run --name geotrain-db -e POSTGRES_USER=geo -e POSTGRES_PASSWORD=geo -e POSTGRES_DB=geotrain \
           -p 5432:5432 -d postgis/postgis:16-3.4
```

Start the database at the beginning (`00_START_HERE` shows how): the SQL notebooks, group B and every project use it.
If your database address is different, set `GEOTRAIN_DSN` (the default is `postgresql://geo:geo@localhost:5432/geotrain`).
`B0_postgis_setup` has more options (installers, Colab).

For group D you need QGIS (with its `qgis_process` command-line tool and the GRASS provider), the GDAL command-line tools, and SAGA.
`D0_desktop_gis_setup` shows how to install them on Windows, macOS, Linux or conda. The notebooks run QGIS tools through `qgis_process`,
so they work from any Jupyter, even when QGIS uses a different Python.

Track your progress in [`PROGRESS.md`](PROGRESS.md).

## For maintainers

The notebooks are generated from `tools/content/*.py`:

```bash
python tools/build_all.py        # rewrite notebooks/
python tools/check_solutions.py  # run every solution and model answer as a test (needs PostGIS for B*, QGIS/GRASS/SAGA/GDAL for D*)
```

## Sources that shaped the syllabus

- University of Helsinki, [Automating GIS Processes](https://autogis-site.readthedocs.io/)
- PostGIS, [Introduction to PostGIS workshop](https://postgis.net/workshops/postgis-intro/) and [training materials](https://postgis.net/documentation/training/)
- Rey, Arribas-Bel & Wolf, [Geographic Data Science with Python](https://geographicdata.science/book/) (structure of the PySAL notebook)
- QGIS documentation, [Using processing from the command line (`qgis_process`)](https://docs.qgis.org/latest/en/docs/user_manual/processing/standalone.html)
