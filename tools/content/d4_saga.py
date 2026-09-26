from nbbuild import NB, SETUP
from d0_desktop_setup import DSETUP
import projects_d


def build():
    nb = NB("D4_saga", "D4 · SAGA GIS — terrain and hydrological analysis")
    nb.md("""
    **What SAGA GIS is:** *System for Automated Geoscientific Analyses*, made at the Universities of Göttingen and Hamburg.
    It is especially rich in **terrain and hydrology** methods: wetness indices, channel networks, height above channels,
    landform classification, solar radiation. Many published terrain indices first appeared in SAGA.

    **Daily picture:** if GRASS is a big science lab, SAGA is a specialist workshop for landscapes — fewer rooms, but
    many fine instruments for reading the shape of the land.

    **How we use it:** with SAGA's own command-line tool `saga_cmd`:
    ```
    saga_cmd <library> <tool> -PARAM1 value -PARAM2 value
    saga_cmd ta_morphometry 0 -ELEVATION dem.tif -SLOPE slope.tif
    ```
    - A **library** groups tools: `ta_morphometry` (terrain shape), `ta_hydrology` (flow), `ta_channels` (streams, basins),
      `ta_preprocessor` (filling sinks), `ta_lighting` (hillshade, sun). `ta_` = terrain analysis.
    - `saga_cmd ta_morphometry` lists its tools; `saga_cmd ta_morphometry 0` shows the parameters of tool 0.
    - SAGA reads and writes GeoTIFF directly when you give `.tif` paths.

    **Where this fits in your plan:** after GRASS. Use SAGA when you need a specific terrain/hydrology index that
    other tools lack — and compare engines to check your results.
    """)
    nb.code(SETUP)
    nb.code(DSETUP)
    nb.code("""
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import rasterio
    import matplotlib.pyplot as plt
    from rasterio.plot import show
    D = quote(DEM)
    S = lambda name: quote(OUT / name)            # output path for saga_cmd
    nbh = gpd.read_file(GPKG, layer="neighbourhoods")
    houses = gpd.read_file(GPKG, layer="houses")
    river = gpd.read_file(GPKG, layer="river")

    def sample(tif, gdf):
        with rasterio.open(tif) as src:
            return np.ma.array([v[0] for v in src.sample(list(zip(gdf.geometry.x, gdf.geometry.y)), masked=True)])

    def read(name):
        return rasterio.open(OUT / name).read(1, masked=True)
    """)

    nb.level(1, "Basics: find tools and read their parameters", "navigate SAGA's libraries and run a first terrain tool.",
             "Walking into a workshop: read the labels on the drawers, open one, read the instructions on a tool.")
    nb.ex("1.1", "List the tools of a library", "saga_cmd ta_morphometry",
          purpose_a="Shows all tools in a library with their numbers (or short names).",
          life_a="Finding the right terrain index for your question, e.g. a 'Topographic Position Index'.",
          hint="`sh(\"saga_cmd ta_morphometry\", check=False)` — SAGA ends a listing with an error code, so we tell `sh` not to stop. Try also `ta_hydrology` and `ta_channels`.",
          starter="""
          sh("saga_cmd ____", check=False)
          """,
          solution="""
          sh("saga_cmd ta_morphometry", check=False)
          """)
    nb.ex("1.2", "Read one tool's parameters", "saga_cmd ta_morphometry 0",
          purpose_a="Shows the inputs, outputs and options of one tool (here: Slope, Aspect, Curvature).",
          life_a="Before scripting a tool, check parameter names and option codes (e.g. `-UNIT_SLOPE 1` = degrees).",
          hint="`sh(\"saga_cmd ta_morphometry 0\")`. Look for `-ELEVATION`, `-SLOPE`, `-UNIT_SLOPE`.",
          starter="""
          sh("saga_cmd ta_morphometry ____", check=False)
          """,
          solution="""
          sh("saga_cmd ta_morphometry 0", check=False)
          """)
    nb.ex("1.3", "Slope in degrees", "saga_cmd ta_morphometry 0 -ELEVATION dem -SLOPE out -UNIT_SLOPE 1",
          purpose_a="Computes slope from the DEM; `-UNIT_SLOPE 1` gives degrees (0 = radians, 2 = percent).",
          life_a="Terrain steepness for building, cycling or erosion studies.",
          hint="`saga_cmd ta_morphometry 0 -ELEVATION {D} -SLOPE {S('s_slope.tif')} -UNIT_SLOPE 1`.",
          starter="""
          sh(f"saga_cmd ta_morphometry 0 -ELEVATION {D} -SLOPE {S('s_slope.tif')} -UNIT_SLOPE ____", quiet=True)
          print("max slope:", round(float(read("s_slope.tif").max()), 2), "degrees")
          """,
          solution="""
          sh(f"saga_cmd ta_morphometry 0 -ELEVATION {D} -SLOPE {S('s_slope.tif')} -UNIT_SLOPE 1", quiet=True)
          print("max slope:", round(float(read("s_slope.tif").max()), 2), "degrees")
          """)

    nb.level(2, "Core tools: prepare the DEM and follow the water", "shade the relief, fill sinks, and compute flow accumulation and wetness.",
             "Rain on a roof: it runs along the slopes, gathers in the gutters, and the ground stays wet where lots of water arrives and the land is flat.")
    nb.ex("2.1", "Hillshade", "saga_cmd ta_lighting 0",
          purpose_a="Computes analytical hillshading: how bright each cell looks with the sun at a given direction and height.",
          life_a="A readable background for any terrain map.",
          hint="`-ELEVATION {D} -SHADE {S('s_shade.tif')}`. Options `-AZIMUTH 315 -DECLINATION 45` = sun from north-west, 45° high.",
          starter="""
          sh(f"saga_cmd ta_lighting 0 -ELEVATION {D} -____ {S('s_shade.tif')} -AZIMUTH 315 -DECLINATION 45", quiet=True)
          ax = plt.subplots(figsize=(5, 5))[1]; show(rasterio.open(OUT / "s_shade.tif"), ax=ax, cmap="gray"); plt.show()
          """,
          solution="""
          sh(f"saga_cmd ta_lighting 0 -ELEVATION {D} -SHADE {S('s_shade.tif')} -AZIMUTH 315 -DECLINATION 45", quiet=True)
          ax = plt.subplots(figsize=(5, 5))[1]; show(rasterio.open(OUT / "s_shade.tif"), ax=ax, cmap="gray"); plt.show()
          """)
    nb.ex("2.2", "Fill sinks (Wang & Liu)", "saga_cmd ta_preprocessor 4 -ELEV dem -FILLED out",
          purpose_a="Raises pits in the DEM so every cell can drain to the edge — the standard first step of hydrological analysis.",
          life_a="Without filling, simulated water gets stuck in fake holes and streams break into pieces.",
          hint="Tool 4 of `ta_preprocessor`. Compare with GRASS `r.fill.dir` (D3 2.1).",
          starter="""
          sh(f"saga_cmd ta_preprocessor ____ -ELEV {D} -FILLED {S('s_filled.tif')}", quiet=True)
          raised = read("s_filled.tif") - rasterio.open(DEM).read(1, masked=True)
          print("cells raised:", int((raised > 1e-4).sum()), "| max raise:", round(float(raised.max()), 2), "m")
          """,
          solution="""
          sh(f"saga_cmd ta_preprocessor 4 -ELEV {D} -FILLED {S('s_filled.tif')}", quiet=True)
          raised = read("s_filled.tif") - rasterio.open(DEM).read(1, masked=True)
          print("cells raised:", int((raised > 1e-4).sum()), "| max raise:", round(float(raised.max()), 2), "m")
          """)
    nb.ex("2.3", "Flow accumulation (catchment area)", "saga_cmd ta_hydrology flow_accumulation -DEM filled -TCA out",
          purpose_a="Computes for each cell the upslope area that drains through it (in m²) — the 'total catchment area'.",
          life_a="Where water concentrates: streams, gullies, places where drains overflow in storms.",
          hint="Use the **filled** DEM from 2.2. 1 km² = 1 000 000 m². Plot `log10(TCA)`.",
          starter="""
          sh(f"saga_cmd ta_hydrology flow_accumulation -DEM {S('s_filled.tif')} -____ {S('s_tca.tif')}", quiet=True)
          tca = read("s_tca.tif")
          print("largest catchment:", round(float(tca.max()) / 1e6, 1), "km²")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(np.log10(tca), transform=rasterio.open(OUT / "s_tca.tif").transform, ax=ax, cmap="Blues"); plt.show()
          """,
          solution="""
          sh(f"saga_cmd ta_hydrology flow_accumulation -DEM {S('s_filled.tif')} -TCA {S('s_tca.tif')}", quiet=True)
          tca = read("s_tca.tif")
          print("largest catchment:", round(float(tca.max()) / 1e6, 1), "km²")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(np.log10(tca), transform=rasterio.open(OUT / "s_tca.tif").transform, ax=ax, cmap="Blues"); plt.show()
          """)
    nb.ex("2.4", "Topographic Wetness Index (TWI)", "saga_cmd ta_hydrology twi -DEM filled -TWI out",
          purpose_a="TWI = ln(catchment area ÷ tan(slope)). High where much water arrives **and** the land is flat — likely wet soils.",
          life_a="Wet basements, soil moisture, where to expect flooding from rain (not only from the river).",
          hint="Daily maths: ln grows slowly — doubling the catchment adds only ln(2) ≈ 0.7 to TWI. Then sample TWI at houses.",
          starter="""
          sh(f"saga_cmd ta_hydrology ____ -DEM {S('s_filled.tif')} -TWI {S('s_twi.tif')}", quiet=True)
          houses["twi"] = sample(OUT / "s_twi.tif", houses).filled(np.nan)
          print(houses["twi"].describe().round(2))
          """,
          solution="""
          sh(f"saga_cmd ta_hydrology twi -DEM {S('s_filled.tif')} -TWI {S('s_twi.tif')}", quiet=True)
          houses["twi"] = sample(OUT / "s_twi.tif", houses).filled(np.nan)
          print(houses["twi"].describe().round(2))
          """)

    nb.level(3, "Combining: channels, basins, height above channels, landforms", "derive the drainage network and classic terrain indices, and bring them into vector analysis.",
             "Draw the streams, then ask for every house: 'how many metres above the nearest stream am I?'")
    nb.ex("3.1", "Channel network", "saga_cmd ta_channels 0 -INIT_GRID tca -INIT_VALUE ...",
          purpose_a="Starts channels wherever the catchment area is larger than a threshold and traces them downhill; outputs a channel grid and lines.",
          life_a="Mapping streams (including small ones) from a DEM.",
          hint="`-ELEVATION` filled DEM, `-INIT_GRID` the TCA from 2.3, `-INIT_METHOD 2` (greater than), `-INIT_VALUE 1000000` (1 km²), `-CHNLNTWRK` grid, `-SHAPES` lines (.shp).",
          starter="""
          sh(f"saga_cmd ta_channels 0 -ELEVATION {S('s_filled.tif')} -INIT_GRID {S('s_tca.tif')} -INIT_METHOD 2 -INIT_VALUE ____ "
             f"-CHNLNTWRK {S('s_channels.tif')} -SHAPES {S('s_channels.shp')}", quiet=True)
          ch = gpd.read_file(OUT / "s_channels.shp")
          print(len(ch), "channel segments,", round(ch.length.sum() / 1000, 1), "km")
          ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); ch.plot(ax=ax, color="blue"); river.plot(ax=ax, color="red", alpha=.5, linewidth=2); plt.show()
          """,
          solution="""
          sh(f"saga_cmd ta_channels 0 -ELEVATION {S('s_filled.tif')} -INIT_GRID {S('s_tca.tif')} -INIT_METHOD 2 -INIT_VALUE 1000000 "
             f"-CHNLNTWRK {S('s_channels.tif')} -SHAPES {S('s_channels.shp')}", quiet=True)
          ch = gpd.read_file(OUT / "s_channels.shp")
          print(len(ch), "channel segments,", round(ch.length.sum() / 1000, 1), "km")
          ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); ch.plot(ax=ax, color="blue"); river.plot(ax=ax, color="red", alpha=.5, linewidth=2); plt.show()
          """)
    nb.ex("3.2", "Vertical distance to the channel network", "saga_cmd ta_channels 3",
          purpose_a="For every cell, the height above the nearest channel it drains to (similar to the HAND index: Height Above Nearest Drainage).",
          life_a="A widely used flood-susceptibility indicator: cells only 1–2 m above a stream flood easily.",
          hint="`-ELEVATION` filled DEM, `-CHANNELS` the channel grid from 3.1, `-DISTANCE` output. Then sample at houses.",
          starter="""
          sh(f"saga_cmd ta_channels 3 -ELEVATION {S('s_filled.tif')} -CHANNELS {S('s_channels.tif')} -____ {S('s_vdist.tif')}", quiet=True)
          houses["vdist"] = sample(OUT / "s_vdist.tif", houses).filled(np.nan)
          print((houses["vdist"] < 2).sum(), "houses less than 2 m above a channel")
          """,
          solution="""
          sh(f"saga_cmd ta_channels 3 -ELEVATION {S('s_filled.tif')} -CHANNELS {S('s_channels.tif')} -DISTANCE {S('s_vdist.tif')}", quiet=True)
          houses["vdist"] = sample(OUT / "s_vdist.tif", houses).filled(np.nan)
          print((houses["vdist"] < 2).sum(), "houses less than 2 m above a channel")
          """)
    nb.ex("3.3", "Drainage basins as polygons", "saga_cmd ta_channels 5 -BASINS out.shp",
          purpose_a="Computes channels **and** their drainage basins in one tool, with basins as vector polygons.",
          life_a="Basins as polygons can be joined to houses, parcels or census areas with GeoPandas.",
          hint="`-DEM` filled DEM, `-THRESHOLD 5` (Strahler order threshold), `-BASINS` output .shp. Then count residents per basin with `gpd.sjoin`.",
          starter="""
          sh(f"saga_cmd ta_channels 5 -DEM {S('s_filled.tif')} -THRESHOLD 5 -____ {S('s_basins.shp')} -SEGMENTS {S('s_segments.shp')}", quiet=True)
          basins = gpd.read_file(OUT / "s_basins.shp").reset_index(names="basin_id")
          b = gpd.sjoin(houses, basins[["basin_id", "geometry"]], predicate="within").groupby("basin_id")["residents"].sum()
          print(len(basins), "basins; residents per basin (top 3):", b.nlargest(3).to_dict())
          ax = basins.plot(column="basin_id", cmap="tab20", figsize=(5, 5)); nbh.boundary.plot(ax=ax, color="white", linewidth=.5); plt.show()
          """,
          solution="""
          sh(f"saga_cmd ta_channels 5 -DEM {S('s_filled.tif')} -THRESHOLD 5 -BASINS {S('s_basins.shp')} -SEGMENTS {S('s_segments.shp')}", quiet=True)
          basins = gpd.read_file(OUT / "s_basins.shp").reset_index(names="basin_id")
          b = gpd.sjoin(houses, basins[["basin_id", "geometry"]], predicate="within").groupby("basin_id")["residents"].sum()
          print(len(basins), "basins; residents per basin (top 3):", b.nlargest(3).to_dict())
          ax = basins.plot(column="basin_id", cmap="tab20", figsize=(5, 5)); nbh.boundary.plot(ax=ax, color="white", linewidth=.5); plt.show()
          """)
    nb.ex("3.4", "Topographic Position Index (landforms)", "saga_cmd ta_morphometry 18",
          purpose_a="TPI = a cell's height minus the average height around it. Negative = valley or hollow, positive = ridge or hilltop, near 0 = flat or mid-slope.",
          life_a="Classifying landforms; cold-air pools collect in valleys (negative TPI) on clear nights.",
          hint="`-DEM {D} -TPI {S('s_tpi.tif')} -RADIUS_MAX 500` (search radius in metres). Mean TPI per neighbourhood with zonal statistics.",
          starter="""
          sh(f"saga_cmd ta_morphometry 18 -DEM {D} -TPI {S('s_tpi.tif')} -RADIUS_MIN 0 -RADIUS_MAX ____", quiet=True)
          z = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(OUT / "s_tpi.tif"), RASTER_BAND=1,
                   COLUMN_PREFIX="tpi_", STATISTICS=[2], OUTPUT=str(OUT / "nbh_tpi.gpkg"))
          gpd.read_file(z["OUTPUT"])[["name", "tpi_mean"]].sort_values("tpi_mean").round(2)
          """,
          solution="""
          sh(f"saga_cmd ta_morphometry 18 -DEM {D} -TPI {S('s_tpi.tif')} -RADIUS_MIN 0 -RADIUS_MAX 500", quiet=True)
          z = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(OUT / "s_tpi.tif"), RASTER_BAND=1,
                   COLUMN_PREFIX="tpi_", STATISTICS=[2], OUTPUT=str(OUT / "nbh_tpi.gpkg"))
          gpd.read_file(z["OUTPUT"])[["name", "tpi_mean"]].sort_values("tpi_mean").round(2)
          """)

    nb.level(4, "Professional: susceptibility models and engine choice", "combine terrain indices into a model, test its sensitivity, and compare engines.",
             "Three doctors measure your blood pressure with three devices: if they agree, you trust the number; if not, you ask why.")
    nb.pro("4.1", "How sensitive is the 'height above channel' model?", "Modelling (sensitivity analysis)",
           scenario="The number of houses '< 2 m above a channel' depends on where channels start. Repeat 3.1–3.2 with channel thresholds of **0.5, 1, 3 and 10 km²** and count the houses each time.",
           plan_hint="Loop over thresholds (in m²). Inside: ta_channels 0 → ta_channels 3 → sample at houses → count `< 2`. Keep a small table.",
           starter="""
           rows = []
           for km2 in [0.5, 1, 3, 10]:
               sh(f"saga_cmd ta_channels 0 -ELEVATION {S('s_filled.tif')} -INIT_GRID {S('s_tca.tif')} -INIT_METHOD 2 "
                  f"-INIT_VALUE {km2 * 1e6} -CHNLNTWRK {S('tmp_ch.tif')}", quiet=True)
               sh(f"saga_cmd ta_channels 3 -ELEVATION {S('s_filled.tif')} -CHANNELS {S('tmp_ch.tif')} -DISTANCE {S('tmp_vd.tif')}", quiet=True)
               vd = sample(OUT / "tmp_vd.tif", houses)
               rows.append({"threshold_km2": km2, "houses_below_2m": int((vd < ____).sum())})
           pd.DataFrame(rows)
           """,
           solution="""
           rows = []
           for km2 in [0.5, 1, 3, 10]:
               sh(f"saga_cmd ta_channels 0 -ELEVATION {S('s_filled.tif')} -INIT_GRID {S('s_tca.tif')} -INIT_METHOD 2 "
                  f"-INIT_VALUE {km2 * 1e6} -CHNLNTWRK {S('tmp_ch.tif')}", quiet=True)
               sh(f"saga_cmd ta_channels 3 -ELEVATION {S('s_filled.tif')} -CHANNELS {S('tmp_ch.tif')} -DISTANCE {S('tmp_vd.tif')}", quiet=True)
               vd = sample(OUT / "tmp_vd.tif", houses)
               rows.append({"threshold_km2": km2, "houses_below_2m": int((vd < 2).sum())})
           pd.DataFrame(rows)
           """,
           answer="""
           More channels (small threshold) → more houses 'close above a channel'. The model's answer depends on a choice you made.
           **Recommendation:** choose the threshold so the derived channels match the real streams (compare with the river layer or official maps), and report the sensitivity table with your result.
           """)
    nb.pro("4.2", "A simple flood-susceptibility index", "Modelling / decision (multi-criteria index)",
           scenario="""
           Combine two SAGA indices into one susceptibility score per house: **low height above channel** (vdist) and **high wetness** (TWI).
           Rescale both to 0–1 (1 = most susceptible), average them, and list the 10 % most susceptible houses per neighbourhood.
           """,
           plan_hint="Rescale: `(x - min) / (max - min)`. For vdist, lower is worse, so use `1 - scaled`. Top 10 %: `score >= score.quantile(0.9)`.",
           starter="""
           def scale(s):
               return (s - s.min()) / (s.max() - s.min())
           h = houses.dropna(subset=["vdist", "twi"]).copy()
           h["score"] = ((1 - scale(h["vdist"])) + scale(h["____"])) / 2
           top = h[h["score"] >= h["score"].quantile(0.9)]
           print(top.merge(nbh[["nb_id", "name"]], on="nb_id")["name"].value_counts())
           ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); h.plot(ax=ax, column="score", cmap="Blues", markersize=4, legend=True)
           river.plot(ax=ax, color="red", linewidth=1); plt.show()
           """,
           solution="""
           def scale(s):
               return (s - s.min()) / (s.max() - s.min())
           h = houses.dropna(subset=["vdist", "twi"]).copy()
           h["score"] = ((1 - scale(h["vdist"])) + scale(h["twi"])) / 2
           top = h[h["score"] >= h["score"].quantile(0.9)]
           print(top.merge(nbh[["nb_id", "name"]], on="nb_id")["name"].value_counts())
           ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); h.plot(ax=ax, column="score", cmap="Blues", markersize=4, legend=True)
           river.plot(ax=ax, color="red", linewidth=1); plt.show()
           """,
           answer="""
           A two-indicator index captures both river flooding (low above channel) and rain water collecting (wet, flat land).
           Limits: equal weights are a choice; no drainage system, no buildings. Validate with past flood records if they exist.
           """)
    nb.pro("4.3", "Three engines, one slope: do they agree?", "Reproducibility / decision (engine choice)",
           scenario="Compare slope (degrees) from **GDAL** (`gdaldem`), **GRASS** (`r.slope.aspect`) and **SAGA** (1.3). Compute the mean slope of each and their correlations. Do they agree? Then decide which engine you would use for which job.",
           plan_hint="Make the GDAL and GRASS slope rasters, read all three as arrays, fill masked cells with NaN, flatten, and use `pd.DataFrame(...).corr()`.",
           starter="""
           sh(f"gdaldem slope -q {D} {S('gdal_slope.tif')}")
           qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), slope=str(OUT / "grass_slope.tif"))
           arrs = {name: read(f).filled(np.nan).ravel() for name, f in
                   [("gdal", "gdal_slope.tif"), ("grass", "grass_slope.tif"), ("saga", "____")]}
           df = pd.DataFrame(arrs).dropna()
           print(df.mean().round(3)); df.corr().round(4)
           """,
           solution="""
           sh(f"gdaldem slope -q {D} {S('gdal_slope.tif')}")
           qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), slope=str(OUT / "grass_slope.tif"))
           arrs = {name: read(f).filled(np.nan).ravel() for name, f in
                   [("gdal", "gdal_slope.tif"), ("grass", "grass_slope.tif"), ("saga", "s_slope.tif")]}
           df = pd.DataFrame(arrs).dropna()
           print(df.mean().round(3)); df.corr().round(4)
           """,
           answer="""
           GDAL and GRASS give identical slopes (both use Horn's formula). SAGA's default method is different (a polynomial fitted to the 3 × 3 window), and on Riverton's slightly noisy DEM it gives higher slopes (mean ≈ 0.77° vs 0.68°, correlation ≈ 0.94).
           Lesson: 'slope' is not one number — it depends on the formula. Choose one method (SAGA's `-METHOD` option lets you pick Horn too), write it in your report, and never mix engines inside one comparison.
           **Which engine for which job:** GDAL for conversion, reprojection, clipping and quick terrain products; QGIS native for vector overlays, joins, networks; GRASS for large hydrology, cost-distance, viewshed and long raster workflows; SAGA for specialised terrain/hydrology indices (TWI, vertical distance to channels, TPI, landforms).
           """)

    nb.test("""
    Use SAGA (and other engines where useful). For each: **question type → tools in order → code → interpretation + limitation.**
    """, [
        ("task", """
        **A.** Compute the **sky view factor** (how much of the sky is visible from each cell; `ta_lighting 3`) and report its mean per neighbourhood.
        """, """
        ```python
        sh(f"saga_cmd ta_lighting 3 -DEM {D} -SVF {S('s_svf.tif')} -RADIUS 500", quiet=True)
        z = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(OUT / "s_svf.tif"), RASTER_BAND=1,
                 COLUMN_PREFIX="svf_", STATISTICS=[2], OUTPUT=str(OUT / "nbh_svf.gpkg"))
        print(gpd.read_file(z["OUTPUT"])[["name", "svf_mean"]].round(3))
        ```
        In a flat town the sky view factor is close to 1 everywhere; with a surface model including buildings it becomes a key urban-heat indicator.
        """),
        ("task", """
        **B.** Which neighbourhood has the **highest mean TWI** at its houses?
        """, """
        ```python
        print(houses.merge(nbh[["nb_id", "name"]], on="nb_id").groupby("name")["twi"].mean().round(2).sort_values(ascending=False).head(3))
        ```
        """),
        ("stat", """
        **C.** Are houses with a **low height above channel** also the ones with **high TWI**? Compute a rank correlation and interpret it.
        """, """
        ```python
        print(round(houses[["vdist", "twi"]].corr(method="spearman").iloc[0, 1], 2))
        ```
        A negative correlation means the two indicators partly measure the same thing (low, wet places). If they are strongly correlated, the index in 4.2 double-counts one effect — consider weights or keep only one.
        """),
        ("model", """
        **D · Modelling soil erosion.** A farmer's field on Riverton's hill loses soil in heavy rain. Which SAGA/GRASS tools would you use to model **where erosion is strongest**?
        """, """
        Use the **LS factor** (slope length and steepness): SAGA `ta_hydrology 22` (LS Factor) or GRASS `r.watershed length_slope=`. Combine it in the **USLE/RUSLE** equation:
        soil loss = R (rain) × K (soil) × LS (terrain) × C (land cover, from NDVI) × P (practices).
        Steps: fill DEM → catchment area → slope → LS → combine with R, K, C rasters (map algebra in Rasterio) → map the top 10 %.
        Validate with field observations of gullies.
        """),
        ("decision", """
        **E · Engine choice for your own project.** You have a city-wide DEM (1 m LiDAR, 5 GB), building footprints, and census areas. List the steps of a heat-and-flood vulnerability study and name the engine for each step.
        """, """
        1. Clip/reproject/resample the LiDAR DEM → **GDAL** (`gdalwarp`, COG for speed).
        2. Hydrology: fill, accumulation, basins → **GRASS** (fast on big rasters, `r.watershed`).
        3. Terrain indices: TWI, vertical distance to channels, sky view factor → **SAGA**.
        4. Zonal statistics per census area, spatial joins with buildings → **QGIS native** or GeoPandas / PostGIS (big data).
        5. Statistics: clusters and regression of vulnerability → **PySAL** (A6).
        6. Store and share results → **PostGIS** (B4).
        """),
    ])
    projects_d.p_d4(nb)
    nb.reflect("""
    Which terrain or water index would help your own research question? Find the SAGA tool for it with `saga_cmd ta_<library>`.
    """)
    return nb
