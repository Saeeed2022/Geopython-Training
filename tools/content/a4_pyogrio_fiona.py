from nbbuild import NB, SETUP


def build():
    nb = NB("A4_pyogrio_fiona", "A4 · Pyogrio & Fiona — reading and writing vector files")
    nb.md("""
    **What they are:** two Python doors to **GDAL/OGR**, the C++ library that can read and write almost every GIS file format
    (GeoPackage, Shapefile, GeoJSON, FlatGeobuf, KML…). PostGIS also uses GDAL, for rasters.

    - **Pyogrio**: fast, reads a whole layer straight into a GeoDataFrame. It is GeoPandas' default engine since version 1.0.
    - **Fiona**: older, reads **one feature at a time** (like reading a book page by page). Useful for streaming huge files or fine control.

    **Daily picture:** GDAL is a universal plug adapter for travel. Pyogrio and Fiona are two ways of plugging your laptop into it.

    **Where this fits in your plan:** you already used `gpd.read_file()` — that was Pyogrio working in the background.
    Here you learn to read **only what you need** (columns, rows, area) and to choose the right file format.
    """)
    nb.code(SETUP)
    nb.code("""
    import pyogrio
    import fiona
    import geopandas as gpd
    print("pyogrio", pyogrio.__version__, "| fiona", fiona.__version__, "| GDAL", pyogrio.__gdal_version_string__)
    """)

    nb.level(1, "Basics: look inside a file before opening it", "list layers and read a file's description (metadata) without loading all the data.",
             "Reading the table of contents and the back cover before buying a book.")
    nb.ex("1.1", "What layers are in this file?", "pyogrio.list_layers(path)",
          purpose_a="Lists every layer (name + geometry type) inside a file.",
          life_a="A colleague sends a 2 GB GeoPackage. You first check what is inside before loading anything.",
          hint="Just pass the path `GPKG`.",
          starter="""
          pyogrio.____(GPKG)
          """,
          solution="""
          pyogrio.list_layers(GPKG)
          """)
    nb.ex("1.2", "Describe one layer", "pyogrio.read_info(path, layer=...)",
          purpose_a="Returns metadata of one layer: CRS, number of features, fields and their types, geometry type, bounds.",
          life_a="Check the CRS and the number of rows of the houses layer before a heavy analysis.",
          hint="The result is a dictionary. Read keys like `info[\"crs\"]`, `info[\"features\"]`, `info[\"fields\"]`.",
          starter="""
          info = pyogrio.____(GPKG, layer="houses")
          print(info["crs"], info["features"], info["fields"], info["geometry_type"])
          """,
          solution="""
          info = pyogrio.read_info(GPKG, layer="houses")
          print(info["crs"], info["features"], info["fields"], info["geometry_type"])
          """)
    nb.ex("1.3", "Read a layer into a GeoDataFrame", "pyogrio.read_dataframe(path, layer=...)",
          purpose_a="Reads a layer into a GeoDataFrame (what `gpd.read_file` does by default).",
          life_a="The standard way to start working with a layer.",
          hint="Same arguments as `gpd.read_file`.",
          starter="""
          roads = pyogrio.____(GPKG, layer="roads")
          roads.head()
          """,
          solution="""
          roads = pyogrio.read_dataframe(GPKG, layer="roads")
          roads.head()
          """)

    nb.level(2, "Core tools: read only what you need", "filter columns, rows and area while reading, so the computer never loads the rest.",
             "Ordering only the dishes you want instead of the whole menu.")
    nb.ex("2.1", "Only some columns", "read_dataframe(..., columns=[...])",
          purpose_a="Loads only the listed attribute columns (plus geometry).",
          life_a="A national building layer has 80 columns; you need 2. Loading fewer columns saves memory and time.",
          hint="`columns=[\"name\", \"road_type\"]`.",
          starter="""
          small = pyogrio.read_dataframe(GPKG, layer="roads", columns=[____, ____])
          small.columns.tolist()
          """,
          solution="""
          small = pyogrio.read_dataframe(GPKG, layer="roads", columns=["name", "road_type"])
          small.columns.tolist()
          """)
    nb.ex("2.2", "Only some rows (SQL filter)", "read_dataframe(..., where=\"...\")",
          purpose_a="Filters rows while reading with an SQL-like condition, so only matching features are loaded.",
          life_a="Load only primary roads, or only buildings built after 2000, from a huge file.",
          hint="`where=\"road_type = 'primary'\"` — text values in single quotes inside the double-quoted string.",
          starter="""
          primary = pyogrio.read_dataframe(GPKG, layer="roads", where="____")
          primary[["name", "road_type"]]
          """,
          solution="""
          primary = pyogrio.read_dataframe(GPKG, layer="roads", where="road_type = 'primary'")
          primary[["name", "road_type"]]
          """)
    nb.ex("2.3", "Only one area (spatial filter)", "read_dataframe(..., bbox=(minx, miny, maxx, maxy))",
          purpose_a="Reads only features that intersect a box, using the file's spatial index when it has one.",
          life_a="Load only the buildings of your study area from a country-wide file.",
          hint="Oldtown is the centre square: (392000, 5820000, 394000, 5822000). The box must be in the layer's CRS.",
          starter="""
          old_houses = pyogrio.read_dataframe(GPKG, layer="houses", bbox=(____, ____, ____, ____))
          print(len(old_houses), "of", info["features"], "houses loaded")
          """,
          solution="""
          old_houses = pyogrio.read_dataframe(GPKG, layer="houses", bbox=(392_000, 5_820_000, 394_000, 5_822_000))
          print(len(old_houses), "of", info["features"], "houses loaded")
          """,
          note="Use `mask=polygon` instead of `bbox` for an exact shape.")
    nb.ex("2.4", "Attributes only, no geometry", "read_dataframe(..., read_geometry=False)",
          purpose_a="Loads the attribute table only, as a normal pandas DataFrame (faster, less memory).",
          life_a="You only need a count per category; the shapes are not needed.",
          hint="`read_geometry=False`. Then `value_counts()` on `severity`.",
          starter="""
          table = pyogrio.read_dataframe(GPKG, layer="accidents", read_geometry=____)
          print(type(table).__name__)
          table["severity"].value_counts()
          """,
          solution="""
          table = pyogrio.read_dataframe(GPKG, layer="accidents", read_geometry=False)
          print(type(table).__name__)
          table["severity"].value_counts()
          """)

    nb.level(3, "Combining: write, convert formats, stream with Fiona", "write files in several formats, meet their limits, and read feature by feature.",
             "Saving a document as .docx, .pdf or .txt: each format keeps some things and loses others.")
    nb.code("""
    OUT = DATA_DIR / "a4_out"
    OUT.mkdir(exist_ok=True)
    schools = pyogrio.read_dataframe(GPKG, layer="schools")
    """)
    nb.ex("3.1", "Write a GeoJSON for the web", "pyogrio.write_dataframe(gdf, path)",
          purpose_a="Writes a GeoDataFrame to a file; the format is chosen from the file extension (or `driver=`).",
          life_a="Sending schools to a web developer who builds an online map (web maps expect GeoJSON in lon/lat).",
          hint="GeoJSON should be in EPSG:4326. So `schools.to_crs(4326)` first, then write to `OUT / \"schools.geojson\"`.",
          starter="""
          pyogrio.____(schools.to_crs(____), OUT / "schools.geojson")
          print((OUT / "schools.geojson").read_text()[:300])
          """,
          solution="""
          pyogrio.write_dataframe(schools.to_crs(4326), OUT / "schools.geojson")
          print((OUT / "schools.geojson").read_text()[:300])
          """)
    nb.ex("3.2", "The Shapefile trap: 10-letter column names", "write_dataframe(..., 'x.shp')",
          purpose_a="Writing a Shapefile works, but the format cuts column names to 10 characters (and has other old limits).",
          life_a="Your column `distance_to_river_m` comes back as `distance_t` — and a colleague cannot tell what it means.",
          hint="Add a long column name, write to `.shp`, read it back and print the columns.",
          starter="""
          s = schools.copy()
          s["distance_to_river_m"] = 123.0
          pyogrio.write_dataframe(s, OUT / "schools.____")
          print(pyogrio.read_dataframe(OUT / "schools.shp").columns.tolist())
          """,
          solution="""
          s = schools.copy()
          s["distance_to_river_m"] = 123.0
          pyogrio.write_dataframe(s, OUT / "schools.shp")
          print(pyogrio.read_dataframe(OUT / "schools.shp").columns.tolist())
          """,
          note="Other Shapefile limits: 2 GB max, one geometry type per file, 4+ files per layer. **Recommendation: use GeoPackage** unless someone really requires Shapefile.")
    nb.ex("3.3", "Add rows to an existing layer", "write_dataframe(..., append=True)",
          purpose_a="Adds new features to the end of an existing layer instead of overwriting it.",
          life_a="Every week new accident reports arrive; you add them to the same layer.",
          hint="Write the first 3 schools, then append the other 3 with `append=True`, and count the features.",
          starter="""
          p = OUT / "log.gpkg"
          pyogrio.write_dataframe(schools.iloc[:3], p, layer="schools")
          pyogrio.write_dataframe(schools.iloc[3:], p, layer="schools", append=____)
          print(pyogrio.read_info(p, layer="schools")["features"])
          """,
          solution="""
          p = OUT / "log.gpkg"
          pyogrio.write_dataframe(schools.iloc[:3], p, layer="schools")
          pyogrio.write_dataframe(schools.iloc[3:], p, layer="schools", append=True)
          print(pyogrio.read_info(p, layer="schools")["features"])
          """)
    nb.ex("3.4", "Fiona: read one feature at a time", "with fiona.open(path, layer=...) as src: for feat in src",
          purpose_a="Opens a layer as a stream; each loop step gives one feature (properties + geometry) without loading the whole file.",
          life_a="A 50 GB file that does not fit in memory: stream through it and keep only what you need.",
          hint="Inside the loop: `feat.properties[\"school\"]`, `feat.geometry.coordinates`. `src.schema` and `src.crs` describe the layer.",
          starter="""
          with fiona.____(GPKG, layer="schools") as src:
              print(src.crs, src.schema)
              for feat in src:
                  print(feat.properties["____"], feat.geometry.coordinates)
          """,
          solution="""
          with fiona.open(GPKG, layer="schools") as src:
              print(src.crs, src.schema)
              for feat in src:
                  print(feat.properties["school"], feat.geometry.coordinates)
          """)

    nb.level(4, "Professional: data engineering", "handle big files, check data quality automatically, and choose formats with reasons.",
             "A restaurant kitchen: checking every delivery before cooking, and storing food in the right containers.")
    nb.pro("4.1", "A file too big for memory", "Data engineering (chunked processing)",
           scenario="Pretend `houses` has 100 million rows. Count residents per neighbourhood by reading **500 features at a time**.",
           plan_hint="Loop with `skip_features=start, max_features=500` until the chunk is empty. Add up `groupby(\"nb_id\")[\"residents\"].sum()` from each chunk.",
           starter="""
           import pandas as pd
           total = pd.Series(dtype=float)
           start = 0
           while True:
               chunk = pyogrio.read_dataframe(GPKG, layer="houses", read_geometry=False, skip_features=____, max_features=____)
               if len(chunk) == 0:
                   break
               total = total.add(chunk.groupby("nb_id")["residents"].sum(), fill_value=0)
               start += 500
           total
           """,
           solution="""
           import pandas as pd
           total = pd.Series(dtype=float)
           start = 0
           while True:
               chunk = pyogrio.read_dataframe(GPKG, layer="houses", read_geometry=False, skip_features=start, max_features=500)
               if len(chunk) == 0:
                   break
               total = total.add(chunk.groupby("nb_id")["residents"].sum(), fill_value=0)
               start += 500
           total
           """,
           answer="Split, process, combine. Works because a sum can be built from partial sums. (For averages, keep sums **and** counts.)")
    nb.pro("4.2", "Automatic quality check for any file", "Data quality (descriptive)",
           scenario="Write a function `check(path, layer)` that reports: CRS missing?, number of features, empty geometries, invalid geometries, duplicate geometries. Run it on every Riverton layer.",
           plan_hint="Use `read_info` for CRS and count, then load the data and use `.is_empty`, `.is_valid`, `.geometry.duplicated()` (compare WKB). Return a dict; build a DataFrame from all dicts.",
           starter="""
           def check(path, layer):
               info = pyogrio.read_info(path, layer=layer)
               g = pyogrio.read_dataframe(path, layer=layer)
               return {"layer": layer, "crs": info["____"], "features": info["features"],
                       "empty": int(g.is_empty.sum()), "invalid": int((~g.is_valid).sum()),
                       "duplicates": int(g.geometry.to_wkb().duplicated().sum())}
           pd.DataFrame([check(GPKG, name) for name, _ in pyogrio.list_layers(GPKG)])
           """,
           solution="""
           def check(path, layer):
               info = pyogrio.read_info(path, layer=layer)
               g = pyogrio.read_dataframe(path, layer=layer)
               return {"layer": layer, "crs": info["crs"], "features": info["features"],
                       "empty": int(g.is_empty.sum()), "invalid": int((~g.is_valid).sum()),
                       "duplicates": int(g.geometry.to_wkb().duplicated().sum())}
           pd.DataFrame([check(GPKG, name) for name, _ in pyogrio.list_layers(GPKG)])
           """,
           answer="A small, reusable 'health check' run before every analysis catches most data problems early (missing CRS, broken shapes, double entries).")
    nb.pro("4.3", "Which format for which job?", "Decision (format choice)",
           scenario="Write the houses layer as GeoPackage, GeoJSON, FlatGeobuf and GeoParquet. Compare file sizes and reading times. Then decide which format to use for (a) sharing with QGIS users, (b) a web map, (c) a big analysis pipeline.",
           plan_hint="Loop over `{\"gpkg\": ..., \"geojson\": ..., \"fgb\": ...}` with `write_dataframe`; GeoParquet is written with `houses.to_parquet(...)`. Time reads with `time.perf_counter()`; size with `path.stat().st_size`.",
           starter="""
           import time
           houses = pyogrio.read_dataframe(GPKG, layer="houses")
           rows = []
           for ext in ["gpkg", "geojson", "fgb", "parquet"]:
               p = OUT / f"houses.{ext}"
               if ext == "parquet":
                   houses.to_parquet(p)
               else:
                   pyogrio.write_dataframe(houses if ext != "geojson" else houses.to_crs(4326), p)
               t = time.perf_counter()
               _ = gpd.read_parquet(p) if ext == "parquet" else pyogrio.read_dataframe(p)
               rows.append({"format": ext, "kB": p.stat().st_size // 1024, "read_ms": round(1000 * (time.perf_counter() - t), 1)})
           pd.DataFrame(rows)
           """,
           solution="""
           import time
           houses = pyogrio.read_dataframe(GPKG, layer="houses")
           rows = []
           for ext in ["gpkg", "geojson", "fgb", "parquet"]:
               p = OUT / f"houses.{ext}"
               if ext == "parquet":
                   houses.to_parquet(p)
               else:
                   pyogrio.write_dataframe(houses if ext != "geojson" else houses.to_crs(4326), p)
               t = time.perf_counter()
               _ = gpd.read_parquet(p) if ext == "parquet" else pyogrio.read_dataframe(p)
               rows.append({"format": ext, "kB": p.stat().st_size // 1024, "read_ms": round(1000 * (time.perf_counter() - t), 1)})
           pd.DataFrame(rows)
           """,
           answer="""
           (a) **GeoPackage** — one file, many layers, opens everywhere (QGIS, ArcGIS).
           (b) **GeoJSON** (small data) or FlatGeobuf (bigger, streamable) — the web understands them.
           (c) **GeoParquet** — small and very fast for Python/cloud pipelines (needs `pyarrow`).
           Shapefile: only when a partner insists.
           """)

    nb.test("""
    For every question: **question type → plan in words → code → interpretation.**
    """, [
        ("task", """
        **A.** From the accidents layer, load **only fatal accidents** and **only the columns** `date` and `hour`, then save them as GeoJSON for a journalist.
        """, """
        ```python
        fatal = pyogrio.read_dataframe(GPKG, layer="accidents", where="severity = 'fatal'", columns=["date", "hour"])
        pyogrio.write_dataframe(fatal.to_crs(4326), OUT / "fatal_accidents.geojson")
        print(len(fatal))
        ```
        """),
        ("task", """
        **B.** Load only the houses of **Harbour** (the north-east square: x 394 000–396 000, y 5 822 000–5 824 000) and count them. Then do it with `where=\"nb_id = 9\"` and compare.
        """, """
        ```python
        a = pyogrio.read_dataframe(GPKG, layer="houses", bbox=(394_000, 5_822_000, 396_000, 5_824_000))
        b = pyogrio.read_dataframe(GPKG, layer="houses", where="nb_id = 9")
        print(len(a), len(b))
        ```
        Both give the same houses here, because the neighbourhoods are squares. For real, irregular districts use `mask=polygon` or `where` on a code.
        """),
        ("task", """
        **C.** Convert every layer of `riverton.gpkg` into a separate **FlatGeobuf** file in `OUT`.
        """, """
        ```python
        for name, _ in pyogrio.list_layers(GPKG):
            pyogrio.write_dataframe(pyogrio.read_dataframe(GPKG, layer=name), OUT / f"{name}.fgb")
        print(sorted(p.name for p in OUT.glob("*.fgb")))
        ```
        """),
        ("decision", """
        **D.** The city's open-data portal offers the same buildings as Shapefile (ZIP), GeoJSON and GeoPackage. Which do you download and why?
        """, """
        GeoPackage: one file, no 10-character names, keeps the CRS, has a spatial index for fast `bbox` reads. GeoJSON only if it is small. Shapefile last.
        """),
        ("model", """
        **E · Modelling a data pipeline.** Every month, the police send a CSV of accidents with lon/lat. Design the steps to turn it into a clean, growing GeoPackage layer that the analysis in A3 can use.
        """, """
        1. Read the CSV (pandas) → `points_from_xy(lon, lat)`, `crs=4326`.
        2. Check: missing coordinates, points outside the town box, duplicates (same time + place).
        3. `to_crs(32633)`.
        4. `write_dataframe(..., append=True)` to `accidents` in the GeoPackage; keep a `source_month` column.
        5. Log how many rows were added or rejected.
        This is a small **ETL** (Extract, Transform, Load) process — the same idea as loading data into PostGIS later.
        """),
    ])
    nb.reflect("""
    Which file formats does your own data come in? Write the one-line Pyogrio command you would use to read only your study area.
    """)
    return nb
