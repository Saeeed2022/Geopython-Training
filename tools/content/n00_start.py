from nbbuild import NB, SETUP


def build():
    nb = NB("00_START_HERE", "00 · Start here — your map of the course")
    nb.md("""
    ## What this course is

    You learn **three groups of tools**, step by step, from easy to professional.

    | Group | Libraries / tools | What they do for you |
    |---|---|---|
    | **A · GeoPython** (you run them in Python) | Shapely, PyProj, GeoPandas, Pyogrio/Fiona, Rasterio, **PySAL** | Draw and measure shapes, fix coordinates, analyse layers, read/write files, work with images of the ground, test spatial patterns statistically |
    | **B1 · Inside PostGIS** (internal engines) | GEOS, PROJ, GDAL | The engines PostGIS calls when you write SQL like `ST_Buffer`, `ST_Transform`, raster functions |
    | **B2 · Talking to PostGIS** (external, from Python) | Psycopg, SQLAlchemy/GeoAlchemy2, GeoPandas `read_postgis`/`to_postgis` | Connect, send SQL, move tables in and out of the database |
    | **D · Desktop GIS engines** (QGIS Processing toolbox, from Jupyter) | QGIS native, GDAL/OGR, GRASS GIS, SAGA GIS | Buffers, overlays, repair, joins, networks (QGIS); convert, reproject, clip (GDAL/OGR); hydrology, terrain, environmental models (GRASS, SAGA) |

    **One key link:** Shapely, PostGIS and QGIS all use the **same engine, GEOS**, for geometry. And Rasterio, Pyogrio,
    PostGIS rasters and QGIS all use **GDAL** for files. So a buffer in Shapely, `ST_Buffer` in PostGIS and `native:buffer`
    in QGIS give the same shape. Learn it once, and the other tools feel familiar.

    Daily picture: GEOS is like one car engine. Shapely, PostGIS and QGIS are three cars built around it.
    Different dashboards, same engine under the bonnet.
    """)
    nb.md("""
    ## The recommended order (and why)

    Your main goal is **GeoPandas + Shapely**, and **a bit of PostGIS**. So the order is:

    | # | Notebook | Why at this point | Time (approx.) |
    |---|---|---|---|
    | 1 | `A1_shapely` | GeoPandas is built on Shapely. First learn one shape, then a table of shapes. | 2 weeks |
    | 2 | `A2_pyproj` | Every distance or area is wrong if the coordinate system is wrong. Fix this early. | 1 week |
    | 3 | `A3_geopandas` | **Your main target.** Tables of shapes: joins, overlays, counts, models. | 4 weeks |
    | 4 | `A4_pyogrio_fiona` | Read and write real files quickly and safely. | 0.5 week |
    | 5 | `A6_pysal` | Statistical questions: "is this pattern real or chance?" Moran's I, hot spots, spatial regression. | 1.5 weeks |
    | 6 | `B0_postgis_setup` | Start a database and load Riverton into it. | 0.5 week |
    | 7 | `B1_postgis_internal` | See GEOS, PROJ, GDAL at work inside SQL. | 1.5 weeks |
    | 8 | `B2_psycopg` | Send SQL from Python safely. | 0.5 week |
    | 9 | `B3_sqlalchemy_geoalchemy2` | Connections and tables as Python objects. | 0.5 week |
    | 10 | `B4_geopandas_postgis` | The bridge you will use most: `read_postgis` / `to_postgis`. | 1 week |
    | 11 | `A5_rasterio` | Rasters (elevation, satellite). Needed before GRASS and SAGA. | 1.5 weeks |
    | 12 | `D0_desktop_gis_setup` | Install and check QGIS, GDAL, GRASS, SAGA. | 0.5 week |
    | 13 | `D1_qgis_native` | QGIS Processing tools from Python: overlays, repair, joins, networks. | 1 week |
    | 14 | `D2_gdal_ogr` | The command-line toolbox for converting, reprojecting and clipping. | 1 week |
    | 15 | `D3_grass` | Hydrology, terrain, visibility, cost surfaces. | 1 week |
    | 16 | `D4_saga` | Terrain and hydrology indices (wetness, height above channels, landforms). | 0.5 week |
    | 17 | `C_capstone` | One Riverton project that combines everything. | 1 week |

    So in total about **20 weeks at ~5 hours per week**. You can go faster; you should not skip the tests.
    If time is short, do 1–10 and 17 first (your main goal), then add 11–16.

    This order follows two well-known open courses: the University of Helsinki's
    [Automating GIS Processes](https://autogis-site.readthedocs.io/) (Shapely → GeoPandas → CRS → spatial joins/overlay → rasters)
    and the official [Introduction to PostGIS workshop](https://postgis.net/workshops/postgis-intro/)
    (geometries → relationships → joins → indexes → projections → geography → rasters).
    The PySAL notebook follows the structure of *Geographic Data Science with Python* (Rey, Arribas-Bel & Wolf):
    weights → spatial autocorrelation → local statistics → spatial regression.
    """)
    nb.md("""
    ## How every exercise works (the same 4 steps each time)

    1. **Purpose** — what does this command do? (one sentence, your own words)
    2. **Real life** — where would a planner or analyst use it?
    3. **Hint** — hidden. Open it only after you tried.
    4. **Code** — fill the blanks `____`, run the cell, look at the result.

    Then open **✅ Solution** and compare. Being wrong first is fine: that is where learning happens.

    Each notebook has **4 levels**:

    | Level | Name | What you do |
    |---|---|---|
    | 1 | Basics | Create and look at things |
    | 2 | Core tools | One command, one job |
    | 3 | Combining | Chains of commands = a small workflow |
    | 4 | Professional | Real questions: first name the **type of question**, then plan, then code |

    Every notebook ends with a **🏁 Final test**: *"We want to do A, B, C, D in Riverton — how do you do it with this library?"*
    plus **modelling questions**: *"We want to check X in the region — how do we model it geographically?"*
    """)
    nb.md("""
    ## The 8 types of spatial question (used in all Level 4 exercises)

    A professional first asks: **what kind of question is this?** The type tells you which tools to pick.

    | Type | The question sounds like… | Daily example | Typical tools |
    |---|---|---|---|
    | **Descriptive** | What is where? How many? | "How many bakeries are in my district?" | filter, count, `sjoin` + `groupby` |
    | **Measurement** | How long, how big, how far? | "How long is my walk to work?" | `length`, `area`, `distance` (in metres!) |
    | **Proximity** | What is near what? | "Which pharmacy is closest to me?" | `buffer`, `sjoin_nearest`, `ST_DWithin` |
    | **Overlay** | Where do layers overlap? | "Which part of my garden is in the shade *and* has good soil?" | `intersection`, `overlay`, `clip` |
    | **Statistical** | Is this pattern real or just chance? | "Are accidents really more frequent near main roads, or did we just notice them more?" | compare with random points, correlation, PySAL: Moran's I, hot spots, spatial regression |
    | **Modelling** | How can we represent a process with shapes and numbers? | "If a school takes children from its nearest area, which schools are overcrowded?" | assumptions + joins + formulas |
    | **Decision / suitability** | Where is the best place for X? | "Where should I put my tent: flat, near water, not in the flood zone?" | overlay of rules, scoring, terrain from GRASS/SAGA |
    | **Temporal** | How does it change over time? | "When are the roads busiest?" | `groupby` on dates/hours |

    Keep this table open. In Level 4 you will be asked: *"Step 1 · What type of question is this?"*
    """)
    nb.md("## Check your environment\n\nRun the next cell. If something is missing, install it with `pip install -r ../requirements.txt`.")
    nb.code("""
    import importlib, shutil
    for lib in ["shapely", "pyproj", "geopandas", "pyogrio", "fiona", "rasterio",
                "libpysal", "esda", "mapclassify", "spreg", "pointpats",
                "psycopg", "sqlalchemy", "geoalchemy2", "matplotlib"]:
        try:
            m = importlib.import_module(lib)
            print(f"✅ {lib:12s} {getattr(m, '__version__', '')}")
        except ImportError:
            print(f"❌ {lib:12s} missing -> pip install {lib}")
    # desktop engines (group D) are programs, not Python packages
    for tool in ["qgis_process", "gdalinfo", "ogr2ogr", "grass", "saga_cmd"]:
        print(("✅ " if shutil.which(tool) else "⚪ ") + f"{tool:12s}" + ("" if shutil.which(tool) else " not found (needed only for group D, see D0)"))
    """)
    nb.md("## Meet Riverton, your training town\n\nAll notebooks use the same fictional town, so you learn the libraries, not a new dataset each time.")
    nb.code(SETUP)
    nb.code("""
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pyogrio

    print(pyogrio.list_layers(GPKG))
    nbh = gpd.read_file(GPKG, layer="neighbourhoods")
    ax = nbh.plot(column="population", cmap="Blues", edgecolor="grey", figsize=(6, 6), legend=True)
    for layer, style in [("river", dict(color="steelblue", linewidth=3)),
                         ("roads", dict(color="black", linewidth=1)),
                         ("parks", dict(color="green", alpha=.5)),
                         ("schools", dict(color="orange", markersize=40)),
                         ("clinics", dict(color="red", marker="+", markersize=80))]:
        gpd.read_file(GPKG, layer=layer).plot(ax=ax, **style)
    nbh.apply(lambda r: ax.annotate(r["name"], r.geometry.centroid.coords[0], ha="center", fontsize=8), axis=1)
    ax.set_title("Riverton (EPSG:32633, metres)")
    plt.show()
    """)
    nb.md("""
    | Layer | Shape | What it holds |
    |---|---|---|
    | `neighbourhoods` | polygons (9) | name, population, median income, % over 65 |
    | `river` | line | the river *Riv* |
    | `roads` | lines (7) | name, `road_type` (primary/secondary), speed |
    | `schools` | points (6) | capacity, students |
    | `clinics` | points (3) | number of doctors |
    | `parks` | polygons (3) | park name |
    | `houses` | points (~1600) | one point = one building with 40 residents |
    | `accidents` | points (260) | date, hour, severity |
    | `sensors` | points (18) | air quality, PM2.5 (µg/m³) |
    | `shops_wgs84.csv` | plain table | shop kind + GPS lon/lat |
    | `dem.tif` / `satellite.tif` | rasters | elevation / red + near-infrared bands |
    """)
    nb.reflect("""
    Before you start, write 3 short lines. You will come back to them at the end of each notebook.

    1. **Why** do you want these skills? (e.g. PhD chapter, a job, a city project)
    2. **What one real question** would you like to answer with them in 3 months? (e.g. "Which districts lost green space?")
    3. **Which data** would you need for it, and where could you get it? (e.g. OpenStreetMap, census, satellite)
    """)
    return nb
