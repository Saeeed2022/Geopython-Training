# GeoPython & PostGIS training — step by step, easy to professional

A hands-on course in Jupyter notebooks for two groups of libraries:

| Group | Libraries | Notebooks |
|---|---|---|
| **A · GeoPython** | Shapely, PyProj, GeoPandas, Pyogrio/Fiona, Rasterio | `A1`–`A5` |
| **B · PostGIS, internal** (engines inside the database) | GEOS, PROJ, GDAL | `B1` |
| **B · PostGIS, external** (Python talks to the database) | Psycopg, SQLAlchemy/GeoAlchemy2, GeoPandas `read_postgis`/`to_postgis` | `B0`, `B2`–`B4` |
| **Capstone** | everything together | `C` |

The main focus is **GeoPandas and Shapely**, then **some PostGIS**.

## Recommended order

`00_START_HERE` → `A1_shapely` → `A2_pyproj` → **`A3_geopandas`** → `A4_pyogrio_fiona` → `B0_postgis_setup` →
`B1_postgis_internal` → `B2_psycopg` → `B3_sqlalchemy_geoalchemy2` → `B4_geopandas_postgis` → `A5_rasterio` → `C_capstone`

About 14 weeks at ~5 hours a week. `00_START_HERE` explains why this order is used.

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

If your database address is different, set `GEOTRAIN_DSN` (the default is `postgresql://geo:geo@localhost:5432/geotrain`).
`B0_postgis_setup` has more options (installers, Colab).

Track your progress in [`PROGRESS.md`](PROGRESS.md).

## For maintainers

The notebooks are generated from `tools/content/*.py`:

```bash
python tools/build_all.py        # rewrite notebooks/
python tools/check_solutions.py  # run every solution and model answer as a test (needs PostGIS for B*)
```

## Sources that shaped the syllabus

- University of Helsinki, [Automating GIS Processes](https://autogis-site.readthedocs.io/)
- PostGIS, [Introduction to PostGIS workshop](https://postgis.net/workshops/postgis-intro/) and [training materials](https://postgis.net/documentation/training/)
