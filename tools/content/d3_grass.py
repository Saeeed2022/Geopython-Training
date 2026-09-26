from nbbuild import NB, SETUP
from d0_desktop_setup import DSETUP


def build():
    nb = NB("D3_grass", "D3 · GRASS GIS — hydrology, terrain and environmental modelling")
    nb.md("""
    **What GRASS GIS is:** one of the oldest and largest open-source GIS (since 1982), with more than 500 tools.
    Its strengths are **raster modelling**: hydrology (where water flows and collects), terrain, visibility, cost surfaces,
    and environmental models. Tool names tell you the data type: `r.` raster, `v.` vector, `g.` general, `i.` imagery.

    **Daily picture:** QGIS native is a Swiss-army knife; GRASS is a science laboratory with specialised instruments.
    You go there when the question is about processes in the landscape: water, slope, visibility, movement.

    **Two ways to use it:**
    1. **Through QGIS Processing** (what we do): `qrun(grass_alg("r.watershed"), elevation=..., basin=...)`.
       QGIS creates a temporary GRASS workspace, imports your files, runs the tool and exports the result as GeoTIFF/GeoPackage.
    2. **GRASS on its own**, with its *project* (formerly *location*: one CRS), *mapset* (your workspace) and *region*
       (the extent and cell size of every calculation). Faster for long workflows; see Level 4.

    **Parameter names** are GRASS's own, lower case (`elevation=`, `threshold=`). Flags such as `-s` are passed as `**{"-s": True}`.
    Use `qhelp(grass_alg("r.watershed"))` to see them all.
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
    enable_grass()
    nbh = gpd.read_file(GPKG, layer="neighbourhoods")
    houses = gpd.read_file(GPKG, layer="houses")
    river = gpd.read_file(GPKG, layer="river")

    def sample(tif, gdf):
        \"\"\"Raster values at the points of a GeoDataFrame (masked where no data).\"\"\"
        with rasterio.open(tif) as src:
            return np.ma.array([v[0] for v in src.sample(list(zip(gdf.geometry.x, gdf.geometry.y)), masked=True)])
    """)

    nb.level(1, "Basics: statistics, slope and the region", "run your first GRASS tools and understand the computational region.",
             "Before measuring a field, agree on its borders and on the size of the squares you count in.")
    nb.ex("1.1", "Raster statistics", "r.univar",
          purpose_a="Computes univariate statistics of a raster (count, min, max, mean, standard deviation…).",
          life_a="First look at an elevation model or a temperature map; checking for strange values.",
          hint="`qrun(grass_alg(\"r.univar\"), map=str(DEM), output=str(OUT / \"univar.txt\"))`. The output is a text table with `|` as separator.",
          starter="""
          qrun(grass_alg("r.____"), map=str(DEM), output=str(OUT / "univar.txt"))
          pd.read_csv(OUT / "univar.txt", sep="|").T
          """,
          solution="""
          qrun(grass_alg("r.univar"), map=str(DEM), output=str(OUT / "univar.txt"))
          pd.read_csv(OUT / "univar.txt", sep="|").T
          """)
    nb.ex("1.2", "Slope and aspect", "r.slope.aspect",
          purpose_a="Computes slope (steepness) and aspect (the compass direction a slope faces) from a DEM.",
          life_a="Solar panels work best on south-facing slopes; steep slopes limit building and cycling.",
          hint="`elevation=str(DEM)`, `slope=str(OUT / \"g_slope.tif\")`, `aspect=str(OUT / \"g_aspect.tif\")`. By default slope is in degrees.",
          starter="""
          res = qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), ____=str(OUT / "g_slope.tif"), aspect=str(OUT / "g_aspect.tif"))
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          show(rasterio.open(res["slope"]), ax=axs[0], cmap="magma", title="slope (°)")
          show(rasterio.open(res["aspect"]), ax=axs[1], cmap="twilight", title="aspect (°)"); plt.show()
          """,
          solution="""
          res = qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), slope=str(OUT / "g_slope.tif"), aspect=str(OUT / "g_aspect.tif"))
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          show(rasterio.open(res["slope"]), ax=axs[0], cmap="magma", title="slope (°)")
          show(rasterio.open(res["aspect"]), ax=axs[1], cmap="twilight", title="aspect (°)"); plt.show()
          """,
          note="GRASS aspect is counted **counter-clockwise from east** by default (0 = east, 90 = north). Use flag `-n` for compass degrees from north.")
    nb.ex("1.3", "The region: change the cell size on the fly", "GRASS_REGION_CELLSIZE_PARAMETER",
          purpose_a="Every GRASS calculation happens in a *region* (extent + cell size). Through QGIS you can set the cell size; GRASS resamples the input to it.",
          life_a="A quick test run at 200 m before the slow final run at 10 m.",
          hint="Run r.slope.aspect again with `GRASS_REGION_CELLSIZE_PARAMETER=200` and compare the raster shapes (120×120 at 50 m vs 30×30 at 200 m).",
          starter="""
          res200 = qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), slope=str(OUT / "g_slope200.tif"), GRASS_REGION_CELLSIZE_PARAMETER=____)
          print(rasterio.open(res["slope"]).shape, "->", rasterio.open(res200["slope"]).shape)
          print("max slope:", rasterio.open(res["slope"]).read(1, masked=True).max().round(2), "->", rasterio.open(res200["slope"]).read(1, masked=True).max().round(2))
          """,
          solution="""
          res200 = qrun(grass_alg("r.slope.aspect"), elevation=str(DEM), slope=str(OUT / "g_slope200.tif"), GRASS_REGION_CELLSIZE_PARAMETER=200)
          print(rasterio.open(res["slope"]).shape, "->", rasterio.open(res200["slope"]).shape)
          print("max slope:", rasterio.open(res["slope"]).read(1, masked=True).max().round(2), "->", rasterio.open(res200["slope"]).read(1, masked=True).max().round(2))
          """,
          note="Coarser cells smooth the terrain, so the steepest slopes disappear. Always report the cell size of a terrain analysis.")

    nb.level(2, "Core tools: where does the water go?", "prepare a DEM for hydrology and compute flow accumulation, basins and streams.",
             "Pour a bucket of water on a sand model of the town: it flows downhill, gathers in valleys, and each valley collects from its own area.")
    nb.ex("2.1", "Fill depressions", "r.fill.dir",
          purpose_a="Removes small pits (cells lower than all neighbours) so water can flow out; also returns flow directions.",
          life_a="Real DEMs have many fake pits (measurement noise); without filling, simulated water gets stuck in them.",
          hint="`input=str(DEM)`, `output=` (filled DEM), `direction=` and `areas=` (problem areas) are all required outputs. Count how many cells changed.",
          starter="""
          res = qrun(grass_alg("r.fill.dir"), input=str(DEM), output=str(OUT / "g_filled.tif"),
                     direction=str(OUT / "g_dir.tif"), areas=str(OUT / "g_areas.tif"))
          before = rasterio.open(DEM).read(1, masked=True)
          after = rasterio.open(res["____"]).read(1, masked=True)
          print("cells raised:", int((after > before + 1e-4).sum()), "| max raise:", float((after - before).max()).__round__(2), "m")
          """,
          solution="""
          res = qrun(grass_alg("r.fill.dir"), input=str(DEM), output=str(OUT / "g_filled.tif"),
                     direction=str(OUT / "g_dir.tif"), areas=str(OUT / "g_areas.tif"))
          before = rasterio.open(DEM).read(1, masked=True)
          after = rasterio.open(res["output"]).read(1, masked=True)
          print("cells raised:", int((after > before + 1e-4).sum()), "| max raise:", float((after - before).max()).__round__(2), "m")
          """)
    nb.ex("2.2", "Flow accumulation", "r.watershed accumulation=",
          purpose_a="For each cell, counts how many upstream cells drain through it. High values = valleys and streams.",
          life_a="Where does rainwater concentrate in a storm? Where should drains or retention ponds go?",
          hint="`elevation=str(DEM)`, `threshold=400`, `accumulation=`. Plot the log of the absolute value (numbers grow very fast downstream).",
          starter="""
          ws = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=400, **{"-s": True},
                    ____=str(OUT / "g_acc.tif"))
          acc = rasterio.open(ws["accumulation"]).read(1, masked=True)
          ax = plt.subplots(figsize=(5, 5))[1]
          show(np.log10(np.abs(acc) + 1), transform=rasterio.open(ws["accumulation"]).transform, ax=ax, cmap="Blues")
          river.plot(ax=ax, color="red", linewidth=1); plt.show()
          """,
          solution="""
          ws = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=400, **{"-s": True},
                    accumulation=str(OUT / "g_acc.tif"))
          acc = rasterio.open(ws["accumulation"]).read(1, masked=True)
          ax = plt.subplots(figsize=(5, 5))[1]
          show(np.log10(np.abs(acc) + 1), transform=rasterio.open(ws["accumulation"]).transform, ax=ax, cmap="Blues")
          river.plot(ax=ax, color="red", linewidth=1); plt.show()
          """,
          note="Negative accumulation means water may flow in from outside the map (the value is an under-estimate). `-s` = single flow direction (D8), easier to interpret.")
    nb.ex("2.3", "Watershed basins and streams", "r.watershed basin= stream= threshold=",
          purpose_a="Splits the land into drainage basins (each drains to one stream segment); `threshold` = minimum basin size in cells.",
          life_a="Which area drains into which stream — the basic unit of water management and flood planning.",
          hint="Add `basin=` and `stream=`. Threshold 400 cells × 2 500 m² = 1 km². Count basins with `np.unique`.",
          starter="""
          ws = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=____, **{"-s": True},
                    basin=str(OUT / "g_basin.tif"), stream=str(OUT / "g_stream.tif"))
          basin = rasterio.open(ws["basin"]).read(1, masked=True)
          print(len(np.unique(basin.compressed())), "basins")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(basin, transform=rasterio.open(ws["basin"]).transform, ax=ax, cmap="tab20")
          nbh.boundary.plot(ax=ax, color="white", linewidth=.5); plt.show()
          """,
          solution="""
          ws = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=400, **{"-s": True},
                    basin=str(OUT / "g_basin.tif"), stream=str(OUT / "g_stream.tif"))
          basin = rasterio.open(ws["basin"]).read(1, masked=True)
          print(len(np.unique(basin.compressed())), "basins")
          ax = plt.subplots(figsize=(5, 5))[1]
          show(basin, transform=rasterio.open(ws["basin"]).transform, ax=ax, cmap="tab20")
          nbh.boundary.plot(ax=ax, color="white", linewidth=.5); plt.show()
          """)
    nb.ex("2.4", "Moving-window statistics", "r.neighbors method=average size=5",
          purpose_a="Replaces each cell by a statistic (average, max…) of the cells around it — a moving window (focal statistics).",
          life_a="Smoothing noisy data; 'average greenness within 125 m of each cell'; local relief = max − min.",
          hint="`input=str(DEM)`, `method=0` (average; see `qhelp` for the list), `size=5` (5 × 5 cells), `output=`.",
          starter="""
          nbr = qrun(grass_alg("r.neighbors"), input=str(DEM), method=0, size=____, output=str(OUT / "g_smooth.tif"))
          a, b = rasterio.open(DEM).read(1, masked=True), rasterio.open(nbr["output"]).read(1, masked=True)
          print("std before:", round(float(a.std()), 2), "after:", round(float(b.std()), 2))
          """,
          solution="""
          nbr = qrun(grass_alg("r.neighbors"), input=str(DEM), method=0, size=5, output=str(OUT / "g_smooth.tif"))
          a, b = rasterio.open(DEM).read(1, masked=True), rasterio.open(nbr["output"]).read(1, masked=True)
          print("std before:", round(float(a.std()), 2), "after:", round(float(b.std()), 2))
          """)

    nb.level(3, "Combining: streams, floods, visibility, movement cost", "use GRASS's modelling tools and bring the results back into GeoPandas.",
             "From 'where is it low?' to 'where would water actually go, and how hard is it to walk there?'")
    nb.ex("3.1", "Extract a stream network as vectors", "r.stream.extract stream_vector=",
          purpose_a="Derives stream lines from the DEM wherever flow accumulation exceeds a threshold, and exports them as vector lines.",
          life_a="Mapping small streams that are missing from official maps; checking that a DEM 'sees' the real river.",
          hint="`elevation=str(DEM)`, `threshold=800`, `stream_vector=str(OUT / \"g_streams.gpkg\")`, `GRASS_OUTPUT_TYPE_PARAMETER=2` (lines). Then compare with the real river: mean distance of stream vertices to the river.",
          starter="""
          st = qrun(grass_alg("r.stream.extract"), elevation=str(DEM), threshold=____, stream_vector=str(OUT / "g_streams.gpkg"),
                    GRASS_OUTPUT_TYPE_PARAMETER=2)
          streams = gpd.read_file(st["stream_vector"])
          print(len(streams), "stream segments,", round(streams.length.sum() / 1000, 1), "km")
          ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); streams.plot(ax=ax, color="blue"); river.plot(ax=ax, color="red", linewidth=2, alpha=.5); plt.show()
          """,
          solution="""
          st = qrun(grass_alg("r.stream.extract"), elevation=str(DEM), threshold=800, stream_vector=str(OUT / "g_streams.gpkg"),
                    GRASS_OUTPUT_TYPE_PARAMETER=2)
          streams = gpd.read_file(st["stream_vector"])
          print(len(streams), "stream segments,", round(streams.length.sum() / 1000, 1), "km")
          ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); streams.plot(ax=ax, color="blue"); river.plot(ax=ax, color="red", linewidth=2, alpha=.5); plt.show()
          """)
    nb.ex("3.2", "Flood from the river, only where water can reach", "r.lake",
          purpose_a="Fills a 'lake' from a seed point up to a water level, flooding only cells **connected** to the seed (unlike the bathtub model in A5).",
          life_a="Which land floods if the river rises 3 m at the town outlet?",
          hint="""Seed = the **lowest** point of the river inside the town (sample the DEM along the river). `water_level` = seed elevation + 3.
          `coordinates=f"{x},{y}"`. If the seed is on higher ground than the water level, GRASS stops with an error — the helper shows it.""",
          starter="""
          line = river.geometry.iloc[0]
          pts = gpd.GeoDataFrame(geometry=[line.interpolate(d) for d in np.arange(300, line.length - 300, 50)], crs=river.crs)
          elev = sample(DEM, pts)
          seed = pts.geometry.iloc[int(elev.argmin())]
          lake = qrun(grass_alg("r.lake"), elevation=str(DEM), water_level=float(elev.min()) + ____,
                      coordinates=f"{seed.x},{seed.y}", lake=str(OUT / "g_lake.tif"))
          depth = sample(lake["lake"], houses)
          print(f"seed at {elev.min():.1f} m; flooded houses: {depth.count()}, residents: {houses.residents[~depth.mask].sum()}")
          """,
          solution="""
          line = river.geometry.iloc[0]
          pts = gpd.GeoDataFrame(geometry=[line.interpolate(d) for d in np.arange(300, line.length - 300, 50)], crs=river.crs)
          elev = sample(DEM, pts)
          seed = pts.geometry.iloc[int(elev.argmin())]
          lake = qrun(grass_alg("r.lake"), elevation=str(DEM), water_level=float(elev.min()) + 3,
                      coordinates=f"{seed.x},{seed.y}", lake=str(OUT / "g_lake.tif"))
          depth = sample(lake["lake"], houses)
          print(f"seed at {elev.min():.1f} m; flooded houses: {depth.count()}, residents: {houses.residents[~depth.mask].sum()}")
          """)
    nb.ex("3.3", "Visibility from the lookout tower", "r.viewshed",
          purpose_a="Computes which cells are visible from an observer point (with height above ground), considering the terrain.",
          life_a="Visual impact of a wind turbine or a tower; placing CCTV or fire lookouts.",
          hint="`input=str(DEM)`, `coordinates=\"391225,5822975\"`, `observer_elevation=30`, flag `-b` (1 = visible, 0 = not).",
          starter="""
          vs = qrun(grass_alg("r.viewshed"), input=str(DEM), coordinates="391225,5822975", observer_elevation=____,
                    **{"-b": True}, output=str(OUT / "g_view.tif"))
          print("visible share:", round(float(rasterio.open(vs["output"]).read(1, masked=True).mean()), 3))
          """,
          solution="""
          vs = qrun(grass_alg("r.viewshed"), input=str(DEM), coordinates="391225,5822975", observer_elevation=30,
                    **{"-b": True}, output=str(OUT / "g_view.tif"))
          print("visible share:", round(float(rasterio.open(vs["output"]).read(1, masked=True).mean()), 3))
          """,
          note="Compare with GDAL `gdal_viewshed` (D2 4.2): two engines, same idea — they should roughly agree.")
    nb.ex("3.4", "Cost distance: effort to reach a clinic", "r.cost",
          purpose_a="Accumulates the 'cost' of moving from start points across a friction raster (each cell has a cost to cross). The result is an effort distance, not metres.",
          life_a="Walking effort to the nearest clinic when slopes make walking harder; wildlife movement across a landscape.",
          hint="Make a friction raster with Rasterio: `1 + slope / 2` (flat = 1, steeper = harder). Then `input=friction`, `start_points=V(\"clinics\")`, `output=`.",
          starter="""
          with rasterio.open(OUT / "g_slope.tif") as s:
              prof = s.profile; fr = 1 + s.read(1, masked=True).filled(0) / ____
          with rasterio.open(OUT / "friction.tif", "w", **prof) as d:
              d.write(fr.astype("float32"), 1)
          cost = qrun(grass_alg("r.cost"), input=str(OUT / "friction.tif"), start_points=V("clinics"), output=str(OUT / "g_cost.tif"))
          houses["effort"] = sample(cost["output"], houses).filled(np.nan)
          ax = plt.subplots(figsize=(5, 5))[1]
          show(rasterio.open(cost["output"]), ax=ax, cmap="viridis"); gpd.read_file(GPKG, layer="clinics").plot(ax=ax, color="red"); plt.show()
          houses["effort"].describe().round(1)
          """,
          solution="""
          with rasterio.open(OUT / "g_slope.tif") as s:
              prof = s.profile; fr = 1 + s.read(1, masked=True).filled(0) / 2
          with rasterio.open(OUT / "friction.tif", "w", **prof) as d:
              d.write(fr.astype("float32"), 1)
          cost = qrun(grass_alg("r.cost"), input=str(OUT / "friction.tif"), start_points=V("clinics"), output=str(OUT / "g_cost.tif"))
          houses["effort"] = sample(cost["output"], houses).filled(np.nan)
          ax = plt.subplots(figsize=(5, 5))[1]
          show(rasterio.open(cost["output"]), ax=ax, cmap="viridis"); gpd.read_file(GPKG, layer="clinics").plot(ax=ax, color="red"); plt.show()
          houses["effort"].describe().round(1)
          """,
          note="`r.walk` is the more realistic version: it uses a walking-time formula for uphill and downhill movement.")

    nb.level(4, "Professional: environmental modelling questions", "use GRASS results to answer modelling and decision questions, and run GRASS on its own.",
             "An environmental consultant: 'which basin needs flood protection first, and why?'")
    nb.pro("4.1", "Which drainage basin holds most people?", "Modelling (hydrological units + population)",
           scenario="Using the basins from 2.3: how many residents live in each basin? Which basin should get the first storm-water plan?",
           plan_hint="Sample the basin raster at every house → groupby basin → sum residents. Houses in cells with no basin get -1: keep them apart. Map the top basin.",
           starter="""
           houses["basin"] = sample(OUT / "g_basin.tif", houses).filled(-1).astype(int)
           print("residents without a basin (water drains off the map edge):", houses.loc[houses.basin < 0, "residents"].sum())
           per_basin = houses[houses.basin >= 0].groupby("basin")["residents"].sum().sort_values(ascending=False)
           print(per_basin.head())
           top = per_basin.index[____]
           ax = plt.subplots(figsize=(5, 5))[1]
           show((basin == top).astype("uint8"), transform=rasterio.open(OUT / "g_basin.tif").transform, ax=ax, cmap="Reds")
           nbh.boundary.plot(ax=ax, color="grey"); plt.show()
           """,
           solution="""
           houses["basin"] = sample(OUT / "g_basin.tif", houses).filled(-1).astype(int)
           print("residents without a basin (water drains off the map edge):", houses.loc[houses.basin < 0, "residents"].sum())
           per_basin = houses[houses.basin >= 0].groupby("basin")["residents"].sum().sort_values(ascending=False)
           print(per_basin.head())
           top = per_basin.index[0]
           ax = plt.subplots(figsize=(5, 5))[1]
           show((basin == top).astype("uint8"), transform=rasterio.open(OUT / "g_basin.tif").transform, ax=ax, cmap="Reds")
           nbh.boundary.plot(ax=ax, color="grey"); plt.show()
           """,
           answer="Basins, not neighbourhoods, are the right unit for water questions: rain does not care about administrative borders. Cells near the map edge have no complete basin — in a real study, use a DEM that covers the whole catchment, not only the town. Combining a physical unit (basin) with a social variable (residents) is typical environmental modelling.")
    nb.pro("4.2", "Bathtub vs connected flood: how different are the models?", "Modelling (model comparison)",
           scenario="""
           Compare three flood models for a 3 m rise: (A) **bathtub** — every cell below *median river level + 3 m* floods (A5 idea);
           (B) **r.lake** from the lowest river point + 3 m (3.2); (C) r.lake from the **median** river point + 3 m.
           Count flooded houses in each and explain the differences.
           """,
           plan_hint="Bathtub: `sample(DEM, houses) < np.ma.median(elev) + 3`. For (C), seed = the river point whose elevation is closest to the median.",
           starter="""
           lvl = float(np.ma.median(elev))
           a = int((sample(DEM, houses) < lvl + 3).sum())
           b = int(depth.count())
           seed_c = pts.geometry.iloc[int(np.abs(elev - lvl).argmin())]
           lake_c = qrun(grass_alg("r.lake"), elevation=str(DEM), water_level=lvl + ____, coordinates=f"{seed_c.x},{seed_c.y}", lake=str(OUT / "g_lake_c.tif"))
           c = int(sample(lake_c["lake"], houses).count())
           pd.Series({"A bathtub": a, "B r.lake lowest point": b, "C r.lake median point": c}, name="flooded houses")
           """,
           solution="""
           lvl = float(np.ma.median(elev))
           a = int((sample(DEM, houses) < lvl + 3).sum())
           b = int(depth.count())
           seed_c = pts.geometry.iloc[int(np.abs(elev - lvl).argmin())]
           lake_c = qrun(grass_alg("r.lake"), elevation=str(DEM), water_level=lvl + 3, coordinates=f"{seed_c.x},{seed_c.y}", lake=str(OUT / "g_lake_c.tif"))
           c = int(sample(lake_c["lake"], houses).count())
           pd.Series({"A bathtub": a, "B r.lake lowest point": b, "C r.lake median point": c}, name="flooded houses")
           """,
           answer="""
           The bathtub model floods every low cell, even hollows the water cannot reach. r.lake floods only connected cells. And the answer depends strongly on **where** the water level is measured, because the river bed is not flat.
           **Recommendation:** use connected models (r.lake, or better a hydraulic model / official flood map), and state the reference point and level. Present the range of results, not one number.
           """)
    nb.pro("4.3", "GRASS on its own: a scripted session", "Reproducibility (native GRASS workflow)",
           scenario="Run a short GRASS workflow **without QGIS**: import the DEM, set the region, compute basins, and report the number of basins. Use a temporary GRASS project.",
           plan_hint="Write the GRASS commands in a small shell script and run `grass --tmp-location EPSG:32633 --exec bash script.sh` (GRASS 8.4+ also accepts `--tmp-project`). Commands: `r.in.gdal`, `g.region raster=`, `r.watershed`, `r.stats -c`.",
           starter="""
           script = OUT / "grass_job.sh"
           script.write_text(f\"\"\"
           r.in.gdal -o input={DEM} output=dem --quiet
           g.region raster=____
           r.watershed -s elevation=dem threshold=400 basin=basins --quiet
           echo "basins: $(r.stats -n basins | wc -l)"
           \"\"\")
           sh(f"grass --tmp-location EPSG:32633 --exec bash {quote(script)}")
           """,
           solution="""
           script = OUT / "grass_job.sh"
           script.write_text(f\"\"\"
           r.in.gdal -o input={DEM} output=dem --quiet
           g.region raster=dem
           r.watershed -s elevation=dem threshold=400 basin=basins --quiet
           echo "basins: $(r.stats -n basins | wc -l)"
           \"\"\")
           sh(f"grass --tmp-location EPSG:32633 --exec bash {quote(script)}")
           """,
           answer="A native GRASS session keeps data inside GRASS between steps, so long chains are faster than importing and exporting at every QGIS call. For Python inside GRASS, use `grass.script` (`gs.run_command(...)`) or the `grass.jupyter` package.")

    nb.test("""
    Use GRASS tools. For each: **question type → GRASS tools in order → code → interpretation + main assumption.**
    """, [
        ("task", """
        **A.** Compute the **topographic wetness index** (TWI) with `r.watershed` (`tci=` output) and report the mean TWI at houses in each neighbourhood.
        """, """
        ```python
        tw = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=400, tci=str(OUT / "g_tci.tif"))
        houses["tci"] = sample(tw["tci"], houses).filled(np.nan)
        print(houses.merge(nbh[["nb_id", "name"]], on="nb_id").groupby("name")["tci"].mean().round(2).sort_values())
        ```
        High TWI = places where water tends to collect (wet soils, basements at risk).
        """),
        ("task", """
        **B.** Which neighbourhood is **most visible** from the tower (3.3)? Use zonal statistics on the viewshed.
        """, """
        ```python
        z = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(OUT / "g_view.tif"), RASTER_BAND=1,
                 COLUMN_PREFIX="vis_", STATISTICS=[2], OUTPUT=str(OUT / "nbh_vis.gpkg"))
        print(gpd.read_file(z["OUTPUT"])[["name", "vis_mean"]].sort_values("vis_mean").round(2))
        ```
        GRASS computes, QGIS native summarises — tools from different engines combine freely through files.
        """),
        ("model", """
        **C · Modelling storm water.** Riverton plans a **retention pond** to protect Oldtown from heavy rain. How would you use GRASS to choose its location?
        """, """
        1. Fill the DEM (`r.fill.dir`) → flow accumulation and basins (`r.watershed`).
        2. Find the basin(s) draining into Oldtown (houses sampled with the basin raster, 4.1).
        3. Candidate cells: high accumulation (water arrives there), **upstream** of Oldtown, low slope (`r.slope.aspect`), not built up, public land.
        4. Check storage: `r.lake` at the candidate with a planned dam height → pond area and volume.
        Recommendation: rank candidates by 'upstream area captured ÷ cost', and test with a rainfall scenario.
        """),
        ("model", """
        **D · Modelling movement.** You want to model how far elderly residents can walk to a clinic in 10 minutes, with hills. Which GRASS tool and inputs?
        """, """
        `r.walk`: inputs = DEM (uphill/downhill effort), friction raster (roads easy, fields harder, river impassable except at bridges), start points = clinics.
        Output = travel time in seconds → threshold 600 s → join to houses → share per neighbourhood. Lower the walking speed for elderly people (e.g. 3 km/h instead of 5) and compare.
        """),
    ])
    nb.reflect("""
    Is there a water, terrain or visibility question in your research area? Write it, and list the GRASS tools you would chain.
    """)
    return nb
