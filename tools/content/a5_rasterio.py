from nbbuild import NB, SETUP


def build():
    nb = NB("A5_rasterio", "A5 · Rasterio — working with images of the ground")
    nb.md("""
    **What Rasterio is:** a Python door to **GDAL** for **raster** data: grids of cells (pixels), each with a value —
    elevation, temperature, reflected light from a satellite. PostGIS uses the same GDAL for its raster functions.

    **Vector vs raster, a daily picture:**
    - **Vector** (Shapely/GeoPandas) = a drawing: a house is an exact outline.
    - **Raster** (Rasterio) = a photo made of tiles, like a mosaic floor. Each tile has one value (e.g. 34.2 m high).

    **Key idea: the transform.** A raster is just a table of numbers (rows × columns). The **affine transform** says where the
    top-left corner is and how big a pixel is. Simple maths: `x = x_left + column × pixel_size`, `y = y_top − row × pixel_size`
    (rows count **downwards**, like lines on a page).

    **Where this fits in your plan:** last in group A for your goal. You need it when the question involves height, heat, vegetation or land cover.
    Riverton has `dem.tif` (elevation, 50 m pixels) and `satellite.tif` (band 1 = red, band 2 = near-infrared).
    """)
    nb.code(SETUP)
    nb.code("""
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import rasterio
    from rasterio.plot import show
    import matplotlib.pyplot as plt
    DEM = DATA_DIR / "dem.tif"
    SAT = DATA_DIR / "satellite.tif"
    print("rasterio", rasterio.__version__, "| GDAL", rasterio.__gdal_version__)
    """)

    nb.level(1, "Basics: open a raster and read its numbers", "open a raster, read its description (profile) and its values as a numpy array.",
             "Looking at a photo's properties (size, resolution) before editing it.")
    nb.ex("1.1", "Open a raster and read its profile", "rasterio.open(path) / src.profile",
          purpose_a="Opens a raster file; `.profile` shows its size, number of bands, data type, CRS, transform and nodata value.",
          life_a="Checking a downloaded elevation model: which CRS, how big are the pixels, how is 'no data' marked?",
          hint="Use `with rasterio.open(DEM) as src:` so the file is closed afterwards. Print `src.profile`.",
          starter="""
          with rasterio.____(DEM) as src:
              print(src.____)
          """,
          solution="""
          with rasterio.open(DEM) as src:
              print(src.profile)
          """)
    nb.ex("1.2", "Size, pixel size, extent", "src.width, src.height, src.res, src.bounds, src.count",
          purpose_a="Give the number of columns and rows, the pixel size in CRS units, the covered box, and the number of bands.",
          life_a="A 50 m pixel cannot show single houses; you check the resolution before choosing a raster for your question.",
          hint="Simple maths check: width × pixel size = 120 × 50 = 6000 m = Riverton's width.",
          starter="""
          src = rasterio.open(DEM)          # kept open for the next exercises
          print(src.width, src.height, src.____, src.____, src.count)
          """,
          solution="""
          src = rasterio.open(DEM)
          print(src.width, src.height, src.res, src.bounds, src.count)
          """)
    nb.ex("1.3", "Read the values, respecting 'no data'", "src.read(1, masked=True)",
          purpose_a="Reads band 1 into a numpy array; `masked=True` hides the nodata cells so they do not spoil statistics.",
          life_a="Missing pixels coded as −9999 would pull the average elevation far down if you forgot to mask them.",
          hint="Compare `src.read(1).min()` with `src.read(1, masked=True).min()`.",
          starter="""
          raw = src.read(1)
          dem = src.read(1, masked=____)
          print("raw min:", raw.min(), "| masked min:", dem.min(), "| mean:", round(dem.mean(), 1))
          """,
          solution="""
          raw = src.read(1)
          dem = src.read(1, masked=True)
          print("raw min:", raw.min(), "| masked min:", dem.min(), "| mean:", round(dem.mean(), 1))
          """)

    nb.level(2, "Core tools: from coordinates to pixels and back", "find the value at a place, sample many places, show the raster with vector layers on top.",
             "Finding a seat in a cinema: 'row 12, seat 5' (pixel) vs 'where is my friend sitting' (coordinate).")
    nb.ex("2.1", "Which pixel is this place in?", "src.index(x, y) / src.xy(row, col)",
          purpose_a="`index` converts a map coordinate into (row, col); `xy` converts (row, col) into the coordinate of the pixel centre.",
          life_a="What is the elevation at the town hall? Where on the map is the highest pixel?",
          hint="Town hall ≈ (391 440, 5 820 080). `row, col = src.index(x, y)`, then `dem[row, col]`. For the highest point: `np.unravel_index(dem.argmax(), dem.shape)`.",
          starter="""
          row, col = src.____(391_440, 5_820_080)
          print("town hall:", row, col, dem[row, col], "m")
          r, c = np.unravel_index(dem.argmax(), dem.shape)
          print("highest point:", src.____(r, c), dem[r, c], "m")
          """,
          solution="""
          row, col = src.index(391_440, 5_820_080)
          print("town hall:", row, col, dem[row, col], "m")
          r, c = np.unravel_index(dem.argmax(), dem.shape)
          print("highest point:", src.xy(r, c), dem[r, c], "m")
          """)
    nb.ex("2.2", "Sample values at many points", "src.sample([(x, y), ...])",
          purpose_a="Returns the pixel values at a list of coordinates (one array of band values per point).",
          life_a="Elevation of every school, or the temperature at every sensor.",
          hint="Build the list with `zip(schools.geometry.x, schools.geometry.y)`. Each result is an array; take `[0]` for band 1.",
          starter="""
          schools = gpd.read_file(GPKG, layer="schools")
          schools["elev_m"] = [v[0] for v in src.____(list(zip(schools.geometry.x, schools.geometry.y)))]
          schools[["school", "elev_m"]].round(1)
          """,
          solution="""
          schools = gpd.read_file(GPKG, layer="schools")
          schools["elev_m"] = [v[0] for v in src.sample(list(zip(schools.geometry.x, schools.geometry.y)))]
          schools[["school", "elev_m"]].round(1)
          """)
    nb.ex("2.3", "Show raster and vectors together", "rasterio.plot.show(src, ax=ax)",
          purpose_a="Draws the raster in its real coordinates, so GeoPandas layers can be drawn on top on the same axes.",
          life_a="Checking visually that the river runs along the lowest land and the schools are where you expect.",
          hint="`fig, ax = plt.subplots()`, `show(src, ax=ax, cmap=\"terrain\")`, then `river.plot(ax=ax)`.",
          starter="""
          river = gpd.read_file(GPKG, layer="river")
          fig, ax = plt.subplots(figsize=(6, 6))
          ____(src, ax=ax, cmap="terrain")
          river.plot(ax=ax, color="blue"); schools.plot(ax=ax, color="red")
          plt.show()
          """,
          solution="""
          river = gpd.read_file(GPKG, layer="river")
          fig, ax = plt.subplots(figsize=(6, 6))
          show(src, ax=ax, cmap="terrain")
          river.plot(ax=ax, color="blue"); schools.plot(ax=ax, color="red")
          plt.show()
          """)
    nb.ex("2.4", "Read just a window", "src.read(1, window=from_bounds(...))",
          purpose_a="Reads only a rectangular part of the raster (a window), not the whole file.",
          life_a="A satellite image of a whole country is several GB; you read only your city.",
          hint="`from rasterio.windows import from_bounds`; `win = from_bounds(392000, 5820000, 394000, 5822000, transform=src.transform)`. 2000 m / 50 m = 40 pixels on each side.",
          starter="""
          from rasterio.windows import from_bounds
          win = from_bounds(392_000, 5_820_000, 394_000, 5_822_000, transform=src.____)
          part = src.read(1, window=win)
          print(part.shape)
          """,
          solution="""
          from rasterio.windows import from_bounds
          win = from_bounds(392_000, 5_820_000, 394_000, 5_822_000, transform=src.transform)
          part = src.read(1, window=win)
          print(part.shape)
          """)

    nb.level(3, "Combining: clip, calculate, write, zonal statistics", "cut rasters with polygons, compute new rasters from bands, save them, and summarise per area.",
             "Cutting a photo to a frame, adjusting its colours, and saving a new copy.")
    nb.code("""
    nbh = gpd.read_file(GPKG, layer="neighbourhoods")
    """)
    nb.ex("3.1", "Clip a raster with a polygon", "rasterio.mask.mask(src, [geom], crop=True)",
          purpose_a="Keeps only the pixels inside the given shapes (others become nodata); `crop=True` also cuts the array to the shape's box.",
          life_a="Elevation of one district only, or a satellite image cut to a nature reserve.",
          hint="`from rasterio.mask import mask`. Pass a **list** of geometries. It returns `(array, transform)`. Use `filled=False` to get a masked array.",
          starter="""
          from rasterio.mask import mask
          geom = nbh.loc[nbh["name"] == "Hillcrest", "geometry"].iloc[0]
          clip, clip_transform = ____(src, [geom], crop=True, filled=False)
          print(clip.shape, "mean elevation of Hillcrest:", round(clip.mean(), 1))
          """,
          solution="""
          from rasterio.mask import mask
          geom = nbh.loc[nbh["name"] == "Hillcrest", "geometry"].iloc[0]
          clip, clip_transform = mask(src, [geom], crop=True, filled=False)
          print(clip.shape, "mean elevation of Hillcrest:", round(clip.mean(), 1))
          """)
    nb.ex("3.2", "Map algebra: vegetation index (NDVI)", "(nir - red) / (nir + red)",
          purpose_a="Combines bands cell by cell with normal numpy maths. NDVI goes from −1 to 1; higher = more green vegetation.",
          life_a="Mapping green spaces, crop health, or the loss of trees in a city over time.",
          hint="Read bands 1 (red) and 2 (nir) as `float` (integers cannot hold decimals): `sat.read(1).astype(\"float32\")`. Plants reflect lots of near-infrared light and absorb red light.",
          starter="""
          sat = rasterio.open(SAT)
          red = sat.read(____).astype("float32")
          nir = sat.read(____).astype("float32")
          ndvi = (nir - red) / (nir + red)
          print(round(ndvi.min(), 2), round(ndvi.max(), 2))
          plt.imshow(ndvi, cmap="RdYlGn"); plt.colorbar(); plt.show()
          """,
          solution="""
          sat = rasterio.open(SAT)
          red = sat.read(1).astype("float32")
          nir = sat.read(2).astype("float32")
          ndvi = (nir - red) / (nir + red)
          print(round(ndvi.min(), 2), round(ndvi.max(), 2))
          plt.imshow(ndvi, cmap="RdYlGn"); plt.colorbar(); plt.show()
          """)
    nb.ex("3.3", "Write a new GeoTIFF", "rasterio.open(path, 'w', **profile)",
          purpose_a="Creates a raster file; the profile (copied and updated from the source) gives it the right size, CRS and transform.",
          life_a="Saving the NDVI so a colleague can open it in QGIS.",
          hint="`profile = sat.profile.copy()`, then `profile.update(count=1, dtype=\"float32\")`. Write with `dst.write(ndvi, 1)`.",
          starter="""
          profile = sat.profile.copy()
          profile.update(count=____, dtype="____")
          with rasterio.open(DATA_DIR / "ndvi.tif", "w", **profile) as dst:
              dst.write(ndvi, 1)
          print(rasterio.open(DATA_DIR / "ndvi.tif").profile)
          """,
          solution="""
          profile = sat.profile.copy()
          profile.update(count=1, dtype="float32")
          with rasterio.open(DATA_DIR / "ndvi.tif", "w", **profile) as dst:
              dst.write(ndvi, 1)
          print(rasterio.open(DATA_DIR / "ndvi.tif").profile)
          """)
    nb.ex("3.4", "Zonal statistics: one number per polygon", "loop: mask(...) per polygon → mean",
          purpose_a="Summarises raster values inside each polygon (mean, max…). It links the raster world to the vector table.",
          life_a="Mean greenness per neighbourhood; mean elevation per parcel; mean temperature per district.",
          hint="Loop over `nbh.geometry`, call `mask(rasterio.open(DATA_DIR / 'ndvi.tif'), [g], crop=True, filled=False)[0]`, append `.mean()`. (The library `rasterstats` does this in one line, but here you see how it works.)",
          starter="""
          nd = rasterio.open(DATA_DIR / "ndvi.tif")
          nbh["ndvi_mean"] = [float(mask(nd, [g], crop=True, filled=False)[0].____()) for g in nbh.geometry]
          nbh[["name", "ndvi_mean"]].round(2).sort_values("ndvi_mean")
          """,
          solution="""
          nd = rasterio.open(DATA_DIR / "ndvi.tif")
          nbh["ndvi_mean"] = [float(mask(nd, [g], crop=True, filled=False)[0].mean()) for g in nbh.geometry]
          nbh[["name", "ndvi_mean"]].round(2).sort_values("ndvi_mean")
          """)
    nb.ex("3.5", "Reproject a raster", "calculate_default_transform + reproject",
          purpose_a="Warps a raster into another CRS; pixels are re-computed (resampled) on a new grid.",
          life_a="Combining a DEM in UTM with climate data in lon/lat: both must share one grid before cell-by-cell maths.",
          hint="`calculate_default_transform(src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)` gives the new transform and size. Then `reproject(source=..., destination=np.empty(...), ...)`. Use `Resampling.bilinear` for continuous values like elevation.",
          starter="""
          from rasterio.warp import calculate_default_transform, reproject, Resampling
          t, w, h = calculate_default_transform(src.crs, "EPSG:4326", src.width, src.height, *src.bounds)
          out = np.empty((h, w), dtype="float32")
          reproject(source=raw, destination=out, src_transform=src.transform, src_crs=src.crs,
                    dst_transform=t, dst_crs="EPSG:4326", src_nodata=-9999, dst_nodata=-9999,
                    resampling=Resampling.____)
          print(out.shape, t)
          """,
          solution="""
          from rasterio.warp import calculate_default_transform, reproject, Resampling
          t, w, h = calculate_default_transform(src.crs, "EPSG:4326", src.width, src.height, *src.bounds)
          out = np.empty((h, w), dtype="float32")
          reproject(source=raw, destination=out, src_transform=src.transform, src_crs=src.crs,
                    dst_transform=t, dst_crs="EPSG:4326", src_nodata=-9999, dst_nodata=-9999,
                    resampling=Resampling.bilinear)
          print(out.shape, t)
          """,
          note="Use `Resampling.nearest` for categories (land-cover classes): you cannot average 'forest' and 'water'.")

    nb.level(4, "Professional: raster questions in Riverton", "combine raster and vector thinking to model, test and decide.",
             "A farmer reads the land: where is it low and wet, where is it steep, where is it green?")
    nb.pro("4.1", "Which houses are below the flood level?", "Modelling (elevation-based flood model)",
           scenario="""
           Improve the crude river buffer from A1. Model: *the river rises by 2 m*. Every cell lower than **river level + 2 m** floods.
           River level = median DEM value sampled along the river every 100 m. How many houses (and residents) are in flooded cells?
           Turn the flooded cells into polygons.
           """,
           plan_hint="""
           1) sample the DEM along the river (`river.interpolate(d)` every 100 m) → median = river level.
           2) `flooded = dem < level + 2` (a True/False raster).
           3) sample the flooded raster at every house.
           4) `rasterio.features.shapes(flooded.astype('uint8'), mask=flooded, transform=src.transform)` → polygons.
           """,
           starter="""
           from rasterio.features import shapes
           from shapely.geometry import shape
           line = river.geometry.iloc[0]
           pts = [line.interpolate(d) for d in np.arange(200, line.length - 200, 100)]
           level = np.median([v[0] for v in src.sample([(p.x, p.y) for p in pts])])
           flooded = (dem < level + ____).filled(False)
           houses = gpd.read_file(GPKG, layer="houses")
           r, c = rasterio.transform.rowcol(src.transform, houses.geometry.x, houses.geometry.y)
           houses["flooded"] = flooded[np.array(r), np.array(c)]
           print(f"river level {level:.1f} m; {houses.flooded.sum()} houses, {houses.loc[houses.flooded, 'residents'].sum()} residents")
           polys = gpd.GeoDataFrame(geometry=[shape(g) for g, v in shapes(flooded.astype("uint8"), mask=flooded, transform=src.transform)], crs=src.crs)
           print(len(polys), "flood polygons,", round(polys.area.sum() / 1e4), "ha")
           """,
           solution="""
           from rasterio.features import shapes
           from shapely.geometry import shape
           line = river.geometry.iloc[0]
           pts = [line.interpolate(d) for d in np.arange(200, line.length - 200, 100)]
           level = np.median([v[0] for v in src.sample([(p.x, p.y) for p in pts])])
           flooded = (dem < level + 2).filled(False)
           houses = gpd.read_file(GPKG, layer="houses")
           r, c = rasterio.transform.rowcol(src.transform, houses.geometry.x, houses.geometry.y)
           houses["flooded"] = flooded[np.array(r), np.array(c)]
           print(f"river level {level:.1f} m; {houses.flooded.sum()} houses, {houses.loc[houses.flooded, 'residents'].sum()} residents")
           polys = gpd.GeoDataFrame(geometry=[shape(g) for g, v in shapes(flooded.astype("uint8"), mask=flooded, transform=src.transform)], crs=src.crs)
           print(len(polys), "flood polygons,", round(polys.area.sum() / 1e4), "ha")
           """,
           answer="""
           A 'bathtub' model: water fills every cell below a level. Better than a buffer because it follows the terrain.
           Its limits: it ignores whether low cells are **connected** to the river (a hollow behind a dyke would not flood), and it ignores dykes, drains and flow speed.
           Next step: keep only flood polygons that touch the river (`polys[polys.intersects(line)]`). GRASS `r.lake` does this properly (D3 3.2), and SAGA's height above channels gives another model (D4 3.2).
           """,
           why="Moving between raster (cells) and vector (polygons, points) is a core professional skill: `sample`/`rowcol` (vector → raster value) and `shapes`/`rasterize` (raster ↔ vector).")
    nb.pro("4.2", "Are richer neighbourhoods greener?", "Statistical (correlation)",
           scenario="Use the mean NDVI per neighbourhood (3.4) and `median_income`. Compute the correlation and interpret it carefully.",
           plan_hint="`nbh[[\"ndvi_mean\", \"median_income\"]].corr(method=\"spearman\")`. Then think: 9 areas, MAUP, and what else could explain greenness (the river, the hill).",
           starter="""
           rho = nbh[["ndvi_mean", "median_income"]].corr(method="____").iloc[0, 1]
           print("Spearman rho:", round(rho, 2))
           ax = nbh.plot.scatter("median_income", "ndvi_mean"); plt.show()
           """,
           solution="""
           rho = nbh[["ndvi_mean", "median_income"]].corr(method="spearman").iloc[0, 1]
           print("Spearman rho:", round(rho, 2))
           ax = nbh.plot.scatter("median_income", "ndvi_mean"); plt.show()
           """,
           answer="""
           A positive rho suggests richer areas are greener (a known 'green inequality' pattern in real cities).
           But with n = 9 it is fragile, and a third factor (the hill and river make areas both green **and** attractive to rich people) may explain both. Correlation ≠ cause.
           """)
    nb.pro("4.3", "Where can Riverton build new homes?", "Decision / suitability (raster overlay)",
           scenario="""
           Suitable land for housing: slope **< 1.5°**, **not** in the 2 m flood model, and NDVI **< 0.3** (do not build on the greenest land).
           How many hectares are suitable? Show them on a map.
           """,
           plan_hint="""
           Slope with numpy: `dzdy, dzdx = np.gradient(dem.filled(np.nan), 50)` (50 m pixels), then `slope = degrees(arctan(sqrt(dzdx² + dzdy²)))`.
           Daily maths: tan(1.5°) ≈ 0.026, so 1.5° means climbing about 2.6 m over 100 m. Riverton is a lowland town, so we use a strict limit.
           Combine rules with `&` and `~`. One pixel = 50 × 50 = 2 500 m² = 0.25 ha.
           """,
           starter="""
           dzdy, dzdx = np.gradient(dem.filled(np.nan), ____)
           slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
           ok = (slope < ____) & ~flooded & (ndvi < ____)
           print(round(ok.sum() * 0.25), "ha suitable of", ok.size * 0.25, "ha")
           fig, ax = plt.subplots(figsize=(5, 5)); show(ok.astype("uint8"), transform=src.transform, ax=ax, cmap="Greens")
           nbh.boundary.plot(ax=ax, color="grey"); plt.show()
           """,
           solution="""
           dzdy, dzdx = np.gradient(dem.filled(np.nan), 50)
           slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
           ok = (slope < 1.5) & ~flooded & (ndvi < 0.3)
           print(round(ok.sum() * 0.25), "ha suitable of", ok.size * 0.25, "ha")
           fig, ax = plt.subplots(figsize=(5, 5)); show(ok.astype("uint8"), transform=src.transform, ax=ax, cmap="Greens")
           nbh.boundary.plot(ax=ax, color="grey"); plt.show()
           """,
           answer="Raster suitability = the same 'sieve' logic as the vector version in A1/A3, but cell by cell with numpy. Rasters are ideal when rules come from continuous surfaces (slope, height, greenness).")

    nb.test("""
    For every question: **question type → plan in words → code → interpretation.**
    """, [
        ("task", """
        **A.** What is the **mean elevation** of each park? Which park is highest?
        """, """
        ```python
        parks = gpd.read_file(GPKG, layer="parks")
        parks["elev"] = [float(mask(src, [g], crop=True, filled=False)[0].mean()) for g in parks.geometry]
        print(parks[["park", "elev"]].round(1).sort_values("elev"))
        ```
        """),
        ("task", """
        **B.** Give each air-quality sensor its NDVI value. Is PM2.5 lower where it is greener?
        """, """
        ```python
        sensors = gpd.read_file(GPKG, layer="sensors")
        sensors["ndvi"] = [v[0] for v in nd.sample(list(zip(sensors.geometry.x, sensors.geometry.y)))]
        print(round(sensors[["ndvi", "pm25"]].corr(method="spearman").iloc[0, 1], 2))
        ```
        Careful: in Riverton PM2.5 depends on distance to main roads; greenness may only be a proxy for 'far from roads'.
        """),
        ("task", """
        **C.** Make a **population raster**: count residents per 250 m cell using `rasterio.features.rasterize`.
        """, """
        ```python
        from rasterio.features import rasterize
        from rasterio.transform import from_origin
        t250 = from_origin(390_000, 5_824_000, 250, 250)
        pop = rasterize(zip(houses.geometry, houses.residents), out_shape=(24, 24), transform=t250, merge_alg=rasterio.enums.MergeAlg.add, dtype="float32")
        print(pop.sum(), pop.max())
        ```
        `merge_alg=add` sums the residents of all houses falling in the same cell.
        """),
        ("model", """
        **D · Modelling heat.** How would you build a simple **urban heat** model for Riverton with rasters, if you also had a thermal satellite band (land-surface temperature)?
        """, """
        1. Read the thermal band → land-surface temperature (LST) raster.
        2. Explain LST with other rasters: NDVI (cooler where green), distance to river (cooler near water), building density (rasterised houses).
        3. Fit a simple regression per cell (e.g. `LST ~ NDVI + dist_water + density`), check residuals on a map.
        4. Zonal statistics per neighbourhood → join with `pct_over65` to find heat-vulnerable people (vector).
        Recommendation: keep it at cell level as long as possible and aggregate at the end, so the neighbourhood borders do not hide hot spots.
        """),
        ("model", """
        **E · Modelling resolution.** A colleague wants to find houses at flood risk using a **1 km** DEM. What is the problem, and what do you recommend?
        """, """
        A 1 km pixel mixes river banks and hills into one average value: low strips along the river disappear, so the model misses risky houses.
        Rule of thumb: the pixel should be clearly smaller than the features that matter (river banks tens of metres wide → 1–10 m DEM, e.g. from LiDAR).
        Recommendation: use the finest DEM available and resample others to it, not the other way round.
        """),
    ])
    nb.reflect("""
    Do you need rasters in your own project (height, land cover, satellite images, night lights)? Write one question where a raster gives information that no vector layer can.
    """)
    return nb
