from nbbuild import NB, SETUP
from d0_desktop_setup import DSETUP


def build():
    nb = NB("D2_gdal_ogr", "D2 · GDAL/OGR command-line tools — convert, reproject, clip")
    nb.md("""
    **What GDAL/OGR is:** the library under almost every GIS program. **GDAL** handles rasters, **OGR** handles vectors
    (they are one project today). You have used it all along without seeing it: Rasterio, Pyogrio, Fiona, QGIS and PostGIS rasters all call it.
    Here you use its **command-line tools** directly — the fastest way to convert, reproject and clip whole files.

    | Tool | Job | Python twin you know |
    |---|---|---|
    | `ogrinfo` / `gdalinfo` | describe a vector / raster file | `pyogrio.read_info` / `rasterio.open().profile` |
    | `ogr2ogr` | convert, reproject, filter, clip vectors (also into PostGIS) | `read_file` + `to_crs` + `to_file` |
    | `gdal_translate` | convert or cut rasters | `rasterio` window + write |
    | `gdalwarp` | reproject and clip rasters | `rasterio.warp.reproject`, `rasterio.mask` |
    | `gdaldem` | slope, hillshade, aspect | numpy `gradient` (A5 4.3) |
    | `gdal_rasterize`, `gdal_grid`, `gdal_contour`, `gdal_viewshed` | vector → raster, interpolation, contours, visibility | `rasterio.features.rasterize` |

    **Daily picture:** Python libraries are like cooking with separate knives and pans. GDAL tools are the food processor:
    one command, whole file, done — and exactly the same command works on Windows, Mac, Linux and servers.

    In Jupyter you can write `!ogr2ogr ...`. We use the helper `sh("...")`, which also hides progress bars.
    **Where this fits in your plan:** the professional's everyday file toolbox. Learn the 5 core commands well.
    """)
    nb.code(SETUP)
    nb.code(DSETUP)
    nb.code("""
    import geopandas as gpd
    import rasterio
    import matplotlib.pyplot as plt
    from rasterio.plot import show
    G, D, O = quote(GPKG), quote(DEM), OUT        # quoted paths for shell commands
    """)

    nb.level(1, "Basics: describe files", "read what is inside a vector or raster file from the command line.",
             "Reading the label on a box before opening it.")
    nb.ex("1.1", "Describe a vector layer", "ogrinfo -so file layer",
          purpose_a="Prints a summary of a layer (`-so` = summary only): geometry type, feature count, extent, CRS and fields.",
          life_a="Checking a file from a partner before loading it.",
          hint="`ogrinfo -so {G} schools`. Without a layer name, it lists the layers.",
          starter="""
          sh(f"ogrinfo -so {G} ____")
          """,
          solution="""
          sh(f"ogrinfo -so {G} schools")
          """)
    nb.ex("1.2", "Describe a raster", "gdalinfo [-stats] file",
          purpose_a="Prints size, pixel size, CRS, corner coordinates, bands, nodata; `-stats` adds min/max/mean.",
          life_a="Checking the resolution and nodata value of a downloaded elevation model.",
          hint="`gdalinfo -stats {D}`.",
          starter="""
          sh(f"gdalinfo ____ {D}")
          """,
          solution="""
          sh(f"gdalinfo -stats {D}")
          """)
    nb.ex("1.3", "Describe a CRS", "gdalsrsinfo -o proj4 EPSG:32633",
          purpose_a="Prints a CRS definition in several formats (WKT, PROJ string, EPSG).",
          life_a="Translating a CRS for software that wants a PROJ string instead of an EPSG code.",
          hint="`-o proj4` gives the short form; `-o wkt2` the full modern form.",
          starter="""
          sh("gdalsrsinfo -o ____ EPSG:32633")
          """,
          solution="""
          sh("gdalsrsinfo -o proj4 EPSG:32633")
          """)
    nb.ex("1.4", "Value at one location", "gdallocationinfo -valonly -geoloc file x y",
          purpose_a="Prints the pixel value at a map coordinate (`-geoloc` = coordinates in the raster's CRS).",
          life_a="Quick checks: 'what is the elevation at the town hall?'",
          hint="Town hall ≈ 391440 5820080. Expect ~46.7 (same as A5 2.1).",
          starter="""
          sh(f"gdallocationinfo -valonly ____ {D} 391440 5820080")
          """,
          solution="""
          sh(f"gdallocationinfo -valonly -geoloc {D} 391440 5820080")
          """)

    nb.level(2, "Core tools: ogr2ogr and gdal_translate / gdalwarp", "convert, reproject and filter vectors; cut, convert and reproject rasters.",
             "Changing a document's format, language and page size in one go.")
    nb.ex("2.1", "Convert and reproject a vector", "ogr2ogr -f GeoJSON -t_srs EPSG:4326 out.geojson in.gpkg layer",
          purpose_a="Copies a layer into another format (`-f`) and CRS (`-t_srs` = target CRS). Note the order: **output first, then input**.",
          life_a="Publishing schools as GeoJSON in lon/lat for a web map (A4 3.1 in one command).",
          hint="`ogr2ogr -f GeoJSON -t_srs EPSG:4326 {O}/schools.geojson {G} schools`. For formats like GeoPackage, `-overwrite` allows re-running; a GeoJSON file must be deleted first.",
          starter="""
          (O / "schools.geojson").unlink(missing_ok=True)      # GeoJSON cannot be overwritten in place
          sh(f"ogr2ogr -f GeoJSON -t_srs ____ {O}/schools.geojson {G} schools")
          print(gpd.read_file(O / "schools.geojson").crs)
          """,
          solution="""
          (O / "schools.geojson").unlink(missing_ok=True)      # GeoJSON cannot be overwritten in place
          sh(f"ogr2ogr -f GeoJSON -t_srs EPSG:4326 {O}/schools.geojson {G} schools")
          print(gpd.read_file(O / "schools.geojson").crs)
          """)
    nb.ex("2.2", "Filter with -where and -select", "ogr2ogr -where \"...\" -select a,b",
          purpose_a="`-where` keeps only rows matching an SQL condition; `-select` keeps only the listed fields.",
          life_a="Extract only fatal accidents with only date and hour, for a journalist (A4 test A).",
          hint="`-where \"severity = 'fatal'\"` and `-select date,hour`. Mind the quotes: double outside, single inside.",
          starter="""
          sh(f\"\"\"ogr2ogr -overwrite -f GPKG {O}/fatal.gpkg {G} accidents -where "____" -select date,hour\"\"\")
          sh(f"ogrinfo -so {O}/fatal.gpkg accidents")
          """,
          solution="""
          sh(f\"\"\"ogr2ogr -overwrite -f GPKG {O}/fatal.gpkg {G} accidents -where "severity = 'fatal'" -select date,hour\"\"\")
          sh(f"ogrinfo -so {O}/fatal.gpkg accidents")
          """)
    nb.ex("2.3", "SQL with spatial functions inside ogr2ogr", "ogr2ogr -dialect SQLite -sql \"SELECT ST_Buffer(geom, 600) ...\"",
          purpose_a="Runs an SQL query (with SpatiaLite spatial functions) on the file while converting — a small database query without a database.",
          life_a="Make school catchments or join tables in one command inside a data pipeline.",
          hint="In a GeoPackage the geometry column is called `geom`. `-sql \"SELECT school, ST_Buffer(geom, 600) AS geom FROM schools\"` and `-nln catchments` (new layer name).",
          starter="""
          sh(f\"\"\"ogr2ogr -overwrite -f GPKG {O}/catch.gpkg {G} -dialect SQLite -nln catchments -sql "SELECT school, ____(geom, 600) AS geom FROM schools" \"\"\")
          gpd.read_file(O / "catch.gpkg").plot(alpha=.4); plt.show()
          """,
          solution="""
          sh(f\"\"\"ogr2ogr -overwrite -f GPKG {O}/catch.gpkg {G} -dialect SQLite -nln catchments -sql "SELECT school, ST_Buffer(geom, 600) AS geom FROM schools" \"\"\")
          gpd.read_file(O / "catch.gpkg").plot(alpha=.4); plt.show()
          """)
    nb.ex("2.4", "Cut and convert a raster", "gdal_translate -projwin ulx uly lrx lry / -of COG",
          purpose_a="Copies a raster, optionally cutting a box (`-projwin` in map coordinates: upper-left x, y, lower-right x, y) or changing format (`-of`).",
          life_a="Cut your city out of a national DEM; make a **Cloud-Optimised GeoTIFF** (COG) that web apps can read in small pieces.",
          hint="Oldtown: `-projwin 392000 5822000 394000 5820000`. Then `-of COG` for the whole DEM.",
          starter="""
          sh(f"gdal_translate -q -projwin 392000 5822000 ____ ____ {D} {O}/oldtown_dem.tif")
          sh(f"gdal_translate -q -of ____ {D} {O}/dem_cog.tif")
          print(rasterio.open(O / "oldtown_dem.tif").shape, rasterio.open(O / "dem_cog.tif").profile.get("tiled"))
          """,
          solution="""
          sh(f"gdal_translate -q -projwin 392000 5822000 394000 5820000 {D} {O}/oldtown_dem.tif")
          sh(f"gdal_translate -q -of COG {D} {O}/dem_cog.tif")
          print(rasterio.open(O / "oldtown_dem.tif").shape, rasterio.open(O / "dem_cog.tif").profile.get("tiled"))
          """)
    nb.ex("2.5", "Reproject a raster", "gdalwarp -t_srs EPSG:4326 -r bilinear in.tif out.tif",
          purpose_a="Warps a raster into a new CRS; `-r` chooses the resampling method (bilinear for continuous values, near for classes).",
          life_a="Aligning a DEM with climate data in lon/lat (A5 3.5 in one line).",
          hint="`gdalwarp -q -overwrite -t_srs EPSG:4326 -r bilinear {D} {O}/dem_4326.tif`.",
          starter="""
          sh(f"gdalwarp -q -overwrite -t_srs ____ -r ____ {D} {O}/dem_4326.tif")
          print(rasterio.open(O / "dem_4326.tif").crs, rasterio.open(O / "dem_4326.tif").res)
          """,
          solution="""
          sh(f"gdalwarp -q -overwrite -t_srs EPSG:4326 -r bilinear {D} {O}/dem_4326.tif")
          print(rasterio.open(O / "dem_4326.tif").crs, rasterio.open(O / "dem_4326.tif").res)
          """)

    nb.level(3, "Combining: clip, terrain, rasterize, interpolate", "cut rasters with polygons, derive terrain, and move between vector and raster.",
             "Cutting a photo along a drawn outline, adding shading, and turning a list of points into a heat map.")
    nb.ex("3.1", "Clip a raster with a polygon", "gdalwarp -cutline file -cl layer -cwhere \"...\" -crop_to_cutline",
          purpose_a="Keeps only the pixels inside a polygon read from a vector file, and crops the output to its box.",
          life_a="DEM of one district; satellite image of a nature reserve.",
          hint="`-cutline {G} -cl neighbourhoods -cwhere \"name='Hillcrest'\" -crop_to_cutline`. Mean elevation should be ≈ 85 m (A5 3.1).",
          starter="""
          sh(f\"\"\"gdalwarp -q -overwrite -cutline {G} -cl neighbourhoods -cwhere "name='____'" -crop_to_cutline {D} {O}/hillcrest.tif\"\"\")
          sh(f"gdalinfo -stats {O}/hillcrest.tif", quiet=True)
          print(rasterio.open(O / "hillcrest.tif").read(1, masked=True).mean())
          """,
          solution="""
          sh(f\"\"\"gdalwarp -q -overwrite -cutline {G} -cl neighbourhoods -cwhere "name='Hillcrest'" -crop_to_cutline {D} {O}/hillcrest.tif\"\"\")
          sh(f"gdalinfo -stats {O}/hillcrest.tif", quiet=True)
          print(rasterio.open(O / "hillcrest.tif").read(1, masked=True).mean())
          """)
    nb.ex("3.2", "Terrain from a DEM", "gdaldem slope / hillshade / aspect",
          purpose_a="Computes terrain products from an elevation raster: slope (degrees), hillshade (shaded relief), aspect (direction a slope faces).",
          life_a="Hillshade makes maps readable; slope limits where you can build or cycle comfortably.",
          hint="`gdaldem slope {D} {O}/slope.tif` and `gdaldem hillshade {D} {O}/hillshade.tif`. Add `-q` for quiet.",
          starter="""
          sh(f"gdaldem ____ -q {D} {O}/slope.tif")
          sh(f"gdaldem ____ -q {D} {O}/hillshade.tif")
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          show(rasterio.open(O / "hillshade.tif"), ax=axs[0], cmap="gray"); show(rasterio.open(O / "slope.tif"), ax=axs[1], cmap="magma")
          plt.show()
          """,
          solution="""
          sh(f"gdaldem slope -q {D} {O}/slope.tif")
          sh(f"gdaldem hillshade -q {D} {O}/hillshade.tif")
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          show(rasterio.open(O / "hillshade.tif"), ax=axs[0], cmap="gray"); show(rasterio.open(O / "slope.tif"), ax=axs[1], cmap="magma")
          plt.show()
          """)
    nb.ex("3.3", "Vector to raster: a population grid", "gdal_rasterize -a field -add -tr 250 250",
          purpose_a="Burns vector features into raster cells; `-a` takes the value from a field, `-add` sums values that fall in the same cell.",
          life_a="Residents per 250 m cell (A5 test C) — the input for many raster models.",
          hint="`-a residents -add -init 0 -tr 250 250 -te 390000 5818000 396000 5824000 -ot Float32 {G} -l houses {O}/pop250.tif`. The total should equal all residents.",
          starter="""
          sh(f"gdal_rasterize -q -a ____ -add -init 0 -tr 250 250 -te 390000 5818000 396000 5824000 -ot Float32 {G} -l houses {O}/pop250.tif")
          pop = rasterio.open(O / "pop250.tif").read(1)
          print(pop.shape, pop.sum(), pop.max())
          """,
          solution="""
          sh(f"gdal_rasterize -q -a residents -add -init 0 -tr 250 250 -te 390000 5818000 396000 5824000 -ot Float32 {G} -l houses {O}/pop250.tif")
          pop = rasterio.open(O / "pop250.tif").read(1)
          print(pop.shape, pop.sum(), pop.max())
          """)
    nb.ex("3.4", "Interpolate sensor values (IDW)", "gdal_grid -zfield pm25 -a invdist:power=2",
          purpose_a="Estimates a continuous surface from scattered points; inverse distance weighting (IDW) gives nearer sensors more weight.",
          life_a="An air-pollution map for every street from 18 sensors.",
          hint="`-zfield pm25 -a invdist:power=2:smoothing=0 -txe 390000 396000 -tye 5824000 5818000 -outsize 120 120 -ot Float32 -l sensors`. Daily maths: power 2 means a sensor twice as far counts 4 times less.",
          starter="""
          sh(f"gdal_grid -q -zfield ____ -a invdist:power=2:smoothing=0 -txe 390000 396000 -tye 5824000 5818000 -outsize 120 120 -ot Float32 -l sensors {G} {O}/pm25_idw.tif")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(rasterio.open(O / "pm25_idw.tif"), ax=ax, cmap="YlOrRd")
          gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="black", linewidth=.6)
          gpd.read_file(GPKG, layer="sensors").plot(ax=ax, color="blue"); plt.show()
          """,
          solution="""
          sh(f"gdal_grid -q -zfield pm25 -a invdist:power=2:smoothing=0 -txe 390000 396000 -tye 5824000 5818000 -outsize 120 120 -ot Float32 -l sensors {G} {O}/pm25_idw.tif")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(rasterio.open(O / "pm25_idw.tif"), ax=ax, cmap="YlOrRd")
          gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="black", linewidth=.6)
          gpd.read_file(GPKG, layer="sensors").plot(ax=ax, color="blue"); plt.show()
          """,
          note="IDW is a simple model: it cannot know that pollution follows roads. Compare the map with the roads — the test asks you to judge it.")
    nb.ex("3.5", "Contour lines", "gdal_contour -a elev -i 5",
          purpose_a="Draws lines of equal elevation from a DEM (`-i` = interval, `-a` = name of the elevation field).",
          life_a="Classic topographic maps; checking where the land rises above a flood level.",
          hint="`gdal_contour -q -a elev -i 5 {D} {O}/contours.gpkg -f GPKG` (delete an old file first with `-overwrite` not supported → remove it in Python).",
          starter="""
          (O / "contours.gpkg").unlink(missing_ok=True)
          sh(f"gdal_contour -q -a elev -i ____ {D} {O}/contours.gpkg -f GPKG")
          ct = gpd.read_file(O / "contours.gpkg")
          ct.plot(column="elev", cmap="terrain", legend=True, figsize=(5, 5)); plt.show()
          """,
          solution="""
          (O / "contours.gpkg").unlink(missing_ok=True)
          sh(f"gdal_contour -q -a elev -i 5 {D} {O}/contours.gpkg -f GPKG")
          ct = gpd.read_file(O / "contours.gpkg")
          ct.plot(column="elev", cmap="terrain", legend=True, figsize=(5, 5)); plt.show()
          """)

    nb.level(4, "Professional: pipelines, databases and models", "load databases, model visibility, and build repeatable conversion pipelines.",
             "A factory line: each machine does one job, and the line runs the same way every day.")
    nb.pro("4.1", "Load layers straight into PostGIS", "Data engineering (ETL into a database)",
           scenario="Load the `schools` and `houses` layers into PostGIS with `ogr2ogr` (no Python reading), as `schools_ogr` and `houses_ogr`, with a spatial index. Needs the database from B0.",
           plan_hint="`ogr2ogr -f PostgreSQL PG:\"host=localhost user=geo password=geo dbname=geotrain\" file layer -nln new_name -overwrite`. ogr2ogr creates the GIST index by default. Build the PG string from the DSN.",
           starter="""
           from urllib.parse import urlparse
           from geotrain.db import DSN, sql
           u = urlparse(DSN)
           PG = f'PG:"host={u.hostname} port={u.port or 5432} user={u.username} password={u.password} dbname={u.path[1:]}"'
           for layer in ["schools", "houses"]:
               sh(f"ogr2ogr -f ____ {PG} {G} {layer} -nln {layer}_ogr -overwrite")
           sql("SELECT f_table_name, type, srid FROM geometry_columns WHERE f_table_name LIKE '%_ogr'")
           """,
           solution="""
           from urllib.parse import urlparse
           from geotrain.db import DSN, sql
           u = urlparse(DSN)
           PG = f'PG:"host={u.hostname} port={u.port or 5432} user={u.username} password={u.password} dbname={u.path[1:]}"'
           for layer in ["schools", "houses"]:
               sh(f"ogr2ogr -f PostgreSQL {PG} {G} {layer} -nln {layer}_ogr -overwrite")
           sql("SELECT f_table_name, type, srid FROM geometry_columns WHERE f_table_name LIKE '%_ogr'")
           """,
           answer="ogr2ogr is the standard ETL tool for PostGIS: fast, streams big files, handles CRS and field types. Use it for bulk loads; use `to_postgis` when the data is already a GeoDataFrame.")
    nb.pro("4.2", "What can a new lookout tower see?", "Modelling (visibility)",
           scenario="Riverton plans a 30 m lookout tower on the hilltop (391 225, 5 822 975). What share of the town is visible from the top? Which neighbourhoods see it least?",
           plan_hint="`gdal_viewshed -ox 391225 -oy 5822975 -oz 30 {D} out.tif` → 255 = visible, 0 = not. Zonal share per neighbourhood with `rasterio.mask` (A5 3.4).",
           starter="""
           import numpy as np
           from rasterio.mask import mask
           sh(f"gdal_viewshed -q -ox 391225 -oy 5822975 -oz ____ {D} {O}/viewshed.tif")
           vs = rasterio.open(O / "viewshed.tif")
           print("visible share of town:", round((vs.read(1) == 255).mean(), 3))
           nbh = gpd.read_file(GPKG, layer="neighbourhoods")
           nbh["visible"] = [float((mask(vs, [g], crop=True)[0] == 255).mean()) for g in nbh.geometry]
           nbh.sort_values("visible")[["name", "visible"]].round(2)
           """,
           solution="""
           import numpy as np
           from rasterio.mask import mask
           sh(f"gdal_viewshed -q -ox 391225 -oy 5822975 -oz 30 {D} {O}/viewshed.tif")
           vs = rasterio.open(O / "viewshed.tif")
           print("visible share of town:", round((vs.read(1) == 255).mean(), 3))
           nbh = gpd.read_file(GPKG, layer="neighbourhoods")
           nbh["visible"] = [float((mask(vs, [g], crop=True)[0] == 255).mean()) for g in nbh.geometry]
           nbh.sort_values("visible")[["name", "visible"]].round(2)
           """,
           answer="""
           A viewshed model uses only the terrain: in flat Riverton almost everything is visible. Its big limit: **buildings and trees are missing**. With a surface model (DSM, e.g. from LiDAR) instead of a bare-earth DEM, the result would be very different.
           """)
    nb.pro("4.3", "A repeatable conversion pipeline", "Data engineering (automation)",
           scenario="Write a function `publish(layer)` that exports a Riverton layer as (1) GeoJSON in EPSG:4326 and (2) FlatGeobuf in EPSG:32633, then returns the feature count of each output. Run it for all point layers.",
           plan_hint="Two `ogr2ogr` calls with `-f GeoJSON -t_srs EPSG:4326` and `-f FlatGeobuf`. Count with `pyogrio.read_info(path)[\"features\"]`.",
           starter="""
           import pyogrio
           def publish(layer):
               gj, fgb = O / f"{layer}.geojson", O / f"{layer}.fgb"
               gj.unlink(missing_ok=True); fgb.unlink(missing_ok=True)
               sh(f"ogr2ogr -f GeoJSON -t_srs EPSG:4326 {gj} {G} {layer}")
               sh(f"ogr2ogr -f ____ {fgb} {G} {layer}")
               return {"layer": layer, "geojson": pyogrio.read_info(gj)["features"], "fgb": pyogrio.read_info(fgb)["features"]}
           import pandas as pd
           pd.DataFrame([publish(l) for l in ["schools", "clinics", "sensors", "accidents"]])
           """,
           solution="""
           import pyogrio
           def publish(layer):
               gj, fgb = O / f"{layer}.geojson", O / f"{layer}.fgb"
               gj.unlink(missing_ok=True); fgb.unlink(missing_ok=True)
               sh(f"ogr2ogr -f GeoJSON -t_srs EPSG:4326 {gj} {G} {layer}")
               sh(f"ogr2ogr -f FlatGeobuf {fgb} {G} {layer}")
               return {"layer": layer, "geojson": pyogrio.read_info(gj)["features"], "fgb": pyogrio.read_info(fgb)["features"]}
           import pandas as pd
           pd.DataFrame([publish(l) for l in ["schools", "clinics", "sensors", "accidents"]])
           """,
           answer="Small functions around GDAL commands make data publishing boring and reliable — which is exactly what you want. The same commands can run on a server every night.")
    nb.md("""
    ### GDAL in Python (optional)

    GDAL also has its own Python API (`from osgeo import gdal, ogr`), with functions that mirror the tools:
    `gdal.Warp(...)`, `gdal.Translate(...)`, `gdal.VectorTranslate(...)`, `gdal.DEMProcessing(...)`.
    Install it with conda (`conda install -c conda-forge gdal`) or OSGeo4W. For most work, the command-line tools above plus Rasterio/Pyogrio are enough.
    """)

    nb.test("""
    Use GDAL/OGR tools through `sh()`. For each: **question type → command(s) → check → interpretation.**
    """, [
        ("task", """
        **A.** Export the neighbourhoods as a **Shapefile in EPSG:4326** with only `name` and `population`. Check the result with `ogrinfo`.
        """, """
        ```python
        sh(f"ogr2ogr -overwrite -f 'ESRI Shapefile' -t_srs EPSG:4326 -select name,population {O}/nbh_4326.shp {G} neighbourhoods")
        sh(f"ogrinfo -so {O}/nbh_4326.shp nbh_4326")
        ```
        """),
        ("task", """
        **B.** Make a **100 m** resolution version of the DEM (from 50 m) with averaging, and compare the maximum elevation before and after.
        """, """
        ```python
        sh(f"gdalwarp -q -overwrite -tr 100 100 -r average {D} {O}/dem100.tif")
        print(rasterio.open(DEM).read(1, masked=True).max(), rasterio.open(O / "dem100.tif").read(1, masked=True).max())
        ```
        Averaging lowers the peak: coarser rasters smooth extremes (see A5 test E on resolution).
        """),
        ("task", """
        **C.** Keep only the houses inside **Oldtown** using `ogr2ogr -clipsrc` and count them.
        """, """
        ```python
        sh(f\"\"\"ogr2ogr -overwrite -f GPKG {O}/oldtown_houses.gpkg {G} houses -clipsrc {G} -clipsrclayer neighbourhoods -clipsrcwhere "name='Oldtown'" \"\"\")
        print(pyogrio.read_info(O / "oldtown_houses.gpkg")["features"])
        ```
        """),
        ("model", """
        **D · Modelling air quality.** The IDW map (3.4) ignores roads. Propose a better model for PM2.5 across Riverton, using tools from this course.
        """, """
        **Land-use regression:** explain PM2.5 at the sensors with predictors (distance to primary roads, road length within 300 m, greenness NDVI, population density), then predict on a grid.
        Steps: predictor rasters with `gdal_proximity`/`gdal_rasterize`/NDVI (A5) → sample at sensors → regression (`spreg`, A6, and check the residuals' spatial autocorrelation) → apply the model to every cell.
        Or **kriging** of the residuals (regression-kriging). Recommendation: land-use regression, because pollution is driven by roads, which IDW cannot see.
        """),
    ])
    nb.reflect("""
    Which file conversions do you do by hand today? Write the one `ogr2ogr` or `gdalwarp` command that would replace them.
    """)
    return nb
