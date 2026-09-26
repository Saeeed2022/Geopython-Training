from nbbuild import NB, SETUP
from d0_desktop_setup import DSETUP


def build():
    nb = NB("D1_qgis_native", "D1 · QGIS native algorithms — buffers, overlays, repair, spatial joins")
    nb.md("""
    **What QGIS native algorithms are:** the tools of QGIS's Processing Toolbox with ids starting `native:` (written in C++, fast)
    or `qgis:`. They cover almost everything you did with GeoPandas: buffer, clip, intersection, dissolve, spatial joins, field calculator…
    plus things GeoPandas does not have built in, such as **network service areas** and **clustering**.

    **Daily picture:** GeoPandas is cooking from a recipe you write yourself. QGIS native is a set of kitchen machines with buttons.
    Same food, different way of working. Knowing both means you can read and repeat a colleague's QGIS workflow in Python.

    **How we call them:** `qrun("native:buffer", INPUT=..., DISTANCE=..., OUTPUT=...)` returns the output paths.
    `qhelp("native:buffer")` shows the parameters, the same fields you see in the QGIS dialog.
    A layer inside a GeoPackage is written `file.gpkg|layername=schools`; the helper `V("schools")` does that for you.
    """)
    nb.code(SETUP)
    nb.code(DSETUP)
    nb.code("""
    import geopandas as gpd
    import matplotlib.pyplot as plt
    nbh = gpd.read_file(GPKG, layer="neighbourhoods")
    """)

    nb.level(1, "Basics: find, read and run a tool", "find an algorithm, read its parameters, run it and open the result.",
             "Finding the right machine in a workshop, reading its instruction plate, and pressing start.")
    nb.ex("1.1", "Find tools by keyword", "qlist('buffer')",
          purpose_a="Searches the Processing Toolbox by id or name, like the search box in QGIS.",
          life_a="You know *what* you want (a buffer) but not the tool's exact name.",
          hint="`qlist(\"buffer\")` returns `[id, name]` pairs. Notice buffers exist in several providers (native, gdal, grass).",
          starter="""
          for tool_id, name in qlist("____"):
              print(tool_id, "—", name)
          """,
          solution="""
          for tool_id, name in qlist("buffer"):
              print(tool_id, "—", name)
          """)
    nb.ex("1.2", "Read a tool's parameters", "qhelp('native:buffer')",
          purpose_a="Shows each parameter's name, meaning, type and allowed values (the text form of the QGIS dialog).",
          life_a="Before automating a tool, you check which parameters are required and what the codes mean (e.g. END_CAP_STYLE 0 = round).",
          hint="`qhelp(\"native:buffer\")`. Find DISTANCE, SEGMENTS, DISSOLVE and OUTPUT.",
          starter="""
          qhelp("____")
          """,
          solution="""
          qhelp("native:buffer")
          """)
    nb.ex("1.3", "Run a buffer and open the result", "qrun('native:buffer', ...)",
          purpose_a="Runs the algorithm and writes the output file; `qrun` returns a dict of output paths.",
          life_a="The 600 m catchment of each school, made by QGIS but scripted, so you can re-run it when the schools change.",
          hint="`INPUT=V(\"schools\")`, `DISTANCE=600`, `SEGMENTS=16`, `DISSOLVE=False`, `OUTPUT=str(OUT / \"school_buf.gpkg\")`. Then `gpd.read_file(res[\"OUTPUT\"])`.",
          starter="""
          res = qrun("native:buffer", INPUT=V("schools"), DISTANCE=____, SEGMENTS=16, DISSOLVE=False,
                     OUTPUT=str(OUT / "school_buf.gpkg"))
          buf = gpd.read_file(res["____"])
          ax = nbh.boundary.plot(color="grey"); buf.plot(ax=ax, alpha=.4); plt.show()
          buf[["school"]].assign(area=buf.area.round())
          """,
          solution="""
          res = qrun("native:buffer", INPUT=V("schools"), DISTANCE=600, SEGMENTS=16, DISSOLVE=False,
                     OUTPUT=str(OUT / "school_buf.gpkg"))
          buf = gpd.read_file(res["OUTPUT"])
          ax = nbh.boundary.plot(color="grey"); buf.plot(ax=ax, alpha=.4); plt.show()
          buf[["school"]].assign(area=buf.area.round())
          """,
          note="Compare with GeoPandas A3 2.3 (`schools.buffer(600)`): same shapes, because both use GEOS.")

    nb.level(2, "Core tools: repair, select, calculate, dissolve", "clean geometries and build new fields and layers with native tools.",
             "Tidying a messy spreadsheet: fix broken rows, filter, add a formula column, then group.")
    nb.ex("2.1", "Fix broken geometries", "native:fixgeometries",
          purpose_a="Repairs invalid geometries (self-crossings, bow-ties) so later tools do not fail or give wrong areas.",
          life_a="Hand-digitised parcels from a city office often contain bow-ties; fix them before any overlay.",
          hint="First we write a layer with one bow-tie using GeoPandas. Then run `native:fixgeometries` with `INPUT` and `OUTPUT`. Check `.is_valid` before and after.",
          starter="""
          from shapely import Polygon
          bad = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[Polygon([(0, 0), (10, 10), (10, 0), (0, 10)]),
                                                           Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])], crs=32633)
          bad.to_file(OUT / "bad.gpkg", layer="bad")
          res = qrun("native:____", INPUT=str(OUT / "bad.gpkg"), OUTPUT=str(OUT / "fixed.gpkg"))
          fixed = gpd.read_file(res["OUTPUT"])
          print(bad.is_valid.tolist(), "->", fixed.is_valid.tolist(), fixed.area.tolist())
          """,
          solution="""
          from shapely import Polygon
          bad = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[Polygon([(0, 0), (10, 10), (10, 0), (0, 10)]),
                                                           Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])], crs=32633)
          bad.to_file(OUT / "bad.gpkg", layer="bad")
          res = qrun("native:fixgeometries", INPUT=str(OUT / "bad.gpkg"), OUTPUT=str(OUT / "fixed.gpkg"))
          fixed = gpd.read_file(res["OUTPUT"])
          print(bad.is_valid.tolist(), "->", fixed.is_valid.tolist(), fixed.area.tolist())
          """,
          note="Twins: Shapely `make_valid` (A1 3.7), PostGIS `ST_MakeValid` (B1 1.4).")
    nb.ex("2.2", "Select by expression", "native:extractbyexpression",
          purpose_a="Keeps only features that match a QGIS expression (the same language as QGIS's 'Select by expression').",
          life_a="Only the primary roads, only the accidents at night, only parcels over 1 ha.",
          hint="QGIS expressions put **field names in double quotes** and **text in single quotes**: `EXPRESSION='\"road_type\" = \\'primary\\''`. In Python, write the whole expression inside a pair of `\"\"\"...\"\"\"` or use single quotes outside.",
          starter="""
          res = qrun("native:extractbyexpression", INPUT=V("roads"),
                     EXPRESSION=\"\"\"____\"\"\", OUTPUT=str(OUT / "primary.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "road_type"]]
          """,
          solution="""
          res = qrun("native:extractbyexpression", INPUT=V("roads"),
                     EXPRESSION=\"\"\""road_type" = 'primary'\"\"\", OUTPUT=str(OUT / "primary.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "road_type"]]
          """)
    nb.ex("2.3", "Field calculator", "native:fieldcalculator",
          purpose_a="Adds a new field computed with a QGIS expression; `$area`, `$length`, `$x` give geometry values.",
          life_a="Population density per neighbourhood; a label field; a class (e.g. 'north/centre/south').",
          hint="`FIELD_NAME=\"density\"`, `FIELD_TYPE=0` (0 = decimal number), `FORMULA='\"population\" / ($area / 1e6)'`.",
          starter="""
          res = qrun("native:fieldcalculator", INPUT=V("neighbourhoods"), FIELD_NAME="density", FIELD_TYPE=0,
                     FIELD_LENGTH=10, FIELD_PRECISION=1, FORMULA=\"\"\""population" / (____ / 1e6)\"\"\",
                     OUTPUT=str(OUT / "nbh_density.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "population", "density"]]
          """,
          solution="""
          res = qrun("native:fieldcalculator", INPUT=V("neighbourhoods"), FIELD_NAME="density", FIELD_TYPE=0,
                     FIELD_LENGTH=10, FIELD_PRECISION=1, FORMULA=\"\"\""population" / ($area / 1e6)\"\"\",
                     OUTPUT=str(OUT / "nbh_density.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "population", "density"]]
          """)
    nb.ex("2.4", "Chain two tools: classify, then dissolve", "fieldcalculator → native:dissolve",
          purpose_a="The output of one tool is the input of the next — a small pipeline (what the QGIS Graphical Modeler builds with boxes and arrows).",
          life_a="Build 3 districts from 9 neighbourhoods, in a way you can re-run next year.",
          hint="Step 1: text field `district` (`FIELD_TYPE=2` = text) with `CASE WHEN \"nb_id\" <= 3 THEN 'south' WHEN \"nb_id\" <= 6 THEN 'centre' ELSE 'north' END`. Step 2: `native:dissolve` with `FIELD=\"district\"`.",
          starter="""
          step1 = qrun("native:fieldcalculator", INPUT=V("neighbourhoods"), FIELD_NAME="district", FIELD_TYPE=2,
                       FIELD_LENGTH=10, FIELD_PRECISION=0,
                       FORMULA=\"\"\"CASE WHEN "nb_id" <= 3 THEN 'south' WHEN "nb_id" <= 6 THEN 'centre' ELSE 'north' END\"\"\",
                       OUTPUT=str(OUT / "nbh_district.gpkg"))
          step2 = qrun("native:____", INPUT=step1["OUTPUT"], FIELD="____", OUTPUT=str(OUT / "districts.gpkg"))
          d = gpd.read_file(step2["OUTPUT"])
          d.plot(column="district", legend=True, edgecolor="black"); plt.show()
          """,
          solution="""
          step1 = qrun("native:fieldcalculator", INPUT=V("neighbourhoods"), FIELD_NAME="district", FIELD_TYPE=2,
                       FIELD_LENGTH=10, FIELD_PRECISION=0,
                       FORMULA=\"\"\"CASE WHEN "nb_id" <= 3 THEN 'south' WHEN "nb_id" <= 6 THEN 'centre' ELSE 'north' END\"\"\",
                       OUTPUT=str(OUT / "nbh_district.gpkg"))
          step2 = qrun("native:dissolve", INPUT=step1["OUTPUT"], FIELD="district", OUTPUT=str(OUT / "districts.gpkg"))
          d = gpd.read_file(step2["OUTPUT"])
          d.plot(column="district", legend=True, edgecolor="black"); plt.show()
          """,
          note="QGIS's dissolve keeps the attributes of the first feature; it does not sum population (GeoPandas `dissolve(aggfunc=...)` can). For sums use *Aggregate* (`native:aggregate`).")

    nb.level(3, "Combining: spatial joins, overlays, raster statistics", "answer the A3 questions with QGIS tools, and add raster values to vectors.",
             "Same questions, a different toolbox — so you can check one tool's answer with the other.")
    nb.ex("3.1", "Join attributes by location", "native:joinattributesbylocation",
          purpose_a="Adds the attributes of one layer to another where their geometries meet a spatial rule (a spatial join, like `gpd.sjoin`).",
          life_a="Give every accident the name of its neighbourhood.",
          hint="`INPUT=V(\"accidents\")`, `JOIN=V(\"neighbourhoods\")`, `PREDICATE=5` (5 = 'are within'; 0 = intersect), `JOIN_FIELDS=\"name\"`, `METHOD=0` (one-to-many).",
          starter="""
          res = qrun("native:joinattributesbylocation", INPUT=V("accidents"), JOIN=V("neighbourhoods"),
                     PREDICATE=____, JOIN_FIELDS="name", METHOD=0, DISCARD_NONMATCHING=False,
                     OUTPUT=str(OUT / "acc_nbh.gpkg"))
          gpd.read_file(res["OUTPUT"])["name"].value_counts()
          """,
          solution="""
          res = qrun("native:joinattributesbylocation", INPUT=V("accidents"), JOIN=V("neighbourhoods"),
                     PREDICATE=5, JOIN_FIELDS="name", METHOD=0, DISCARD_NONMATCHING=False,
                     OUTPUT=str(OUT / "acc_nbh.gpkg"))
          gpd.read_file(res["OUTPUT"])["name"].value_counts()
          """)
    nb.ex("3.2", "Count points in polygons", "native:countpointsinpolygon",
          purpose_a="Counts how many points fall in each polygon and writes the count as a new field (join + groupby in one step).",
          life_a="Shops per district, trees per park, accidents per neighbourhood.",
          hint="`POLYGONS=V(\"neighbourhoods\")`, `POINTS=V(\"accidents\")`, `FIELD=\"n_acc\"`. You can also give `WEIGHT` (sum a field instead of counting).",
          starter="""
          res = qrun("native:countpointsinpolygon", POLYGONS=V("neighbourhoods"), POINTS=V("____"), FIELD="n_acc",
                     OUTPUT=str(OUT / "nbh_counts.gpkg"))
          cnt = gpd.read_file(res["OUTPUT"])
          cnt[["name", "n_acc"]].sort_values("n_acc", ascending=False)
          """,
          solution="""
          res = qrun("native:countpointsinpolygon", POLYGONS=V("neighbourhoods"), POINTS=V("accidents"), FIELD="n_acc",
                     OUTPUT=str(OUT / "nbh_counts.gpkg"))
          cnt = gpd.read_file(res["OUTPUT"])
          cnt[["name", "n_acc"]].sort_values("n_acc", ascending=False)
          """)
    nb.ex("3.3", "Overlay: which roads flood?", "native:buffer → native:clip",
          purpose_a="Clip keeps only the parts of a layer inside a mask polygon.",
          life_a="Road length under water if the river floods (A3 3.4, now with QGIS tools).",
          hint="Buffer the river by 150 m first, then `native:clip` with `INPUT=V(\"roads\")` and `OVERLAY=` the buffer output.",
          starter="""
          flood = qrun("native:buffer", INPUT=V("river"), DISTANCE=150, SEGMENTS=16, DISSOLVE=True, OUTPUT=str(OUT / "flood.gpkg"))
          res = qrun("native:____", INPUT=V("roads"), OVERLAY=flood["OUTPUT"], OUTPUT=str(OUT / "wet_roads.gpkg"))
          wet = gpd.read_file(res["OUTPUT"])
          wet.assign(km=wet.length / 1000).groupby("road_type")["km"].sum().round(2)
          """,
          solution="""
          flood = qrun("native:buffer", INPUT=V("river"), DISTANCE=150, SEGMENTS=16, DISSOLVE=True, OUTPUT=str(OUT / "flood.gpkg"))
          res = qrun("native:clip", INPUT=V("roads"), OVERLAY=flood["OUTPUT"], OUTPUT=str(OUT / "wet_roads.gpkg"))
          wet = gpd.read_file(res["OUTPUT"])
          wet.assign(km=wet.length / 1000).groupby("road_type")["km"].sum().round(2)
          """)
    nb.ex("3.4", "Nearest feature join", "native:joinbynearest",
          purpose_a="Joins each feature to its nearest feature(s) in another layer and adds a `distance` field (like `gpd.sjoin_nearest`).",
          life_a="Nearest clinic for each school, with the distance.",
          hint="`INPUT=V(\"schools\")`, `INPUT_2=V(\"clinics\")`, `FIELDS_TO_COPY=\"clinic\"`, `NEIGHBORS=1`.",
          starter="""
          res = qrun("native:joinbynearest", INPUT=V("schools"), INPUT_2=V("clinics"), FIELDS_TO_COPY="clinic",
                     NEIGHBORS=____, DISCARD_NONMATCHING=False, OUTPUT=str(OUT / "school_clinic.gpkg"))
          gpd.read_file(res["OUTPUT"])[["school", "clinic", "distance"]].round()
          """,
          solution="""
          res = qrun("native:joinbynearest", INPUT=V("schools"), INPUT_2=V("clinics"), FIELDS_TO_COPY="clinic",
                     NEIGHBORS=1, DISCARD_NONMATCHING=False, OUTPUT=str(OUT / "school_clinic.gpkg"))
          gpd.read_file(res["OUTPUT"])[["school", "clinic", "distance"]].round()
          """)
    nb.ex("3.5", "Zonal statistics (raster values per polygon)", "native:zonalstatisticsfb",
          purpose_a="Computes statistics of raster cells inside each polygon (mean, max…) and writes them as new fields.",
          life_a="Mean elevation of each neighbourhood (A5 3.4 in one tool).",
          hint="`INPUT=V(\"neighbourhoods\")`, `INPUT_RASTER=str(DEM)`, `RASTER_BAND=1`, `COLUMN_PREFIX=\"elev_\"`, `STATISTICS=[2, 6]` (2 = mean, 6 = max).",
          starter="""
          res = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(DEM), RASTER_BAND=1,
                     COLUMN_PREFIX="elev_", STATISTICS=[____, 6], OUTPUT=str(OUT / "nbh_elev.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "elev_mean", "elev_max"]].round(1)
          """,
          solution="""
          res = qrun("native:zonalstatisticsfb", INPUT=V("neighbourhoods"), INPUT_RASTER=str(DEM), RASTER_BAND=1,
                     COLUMN_PREFIX="elev_", STATISTICS=[2, 6], OUTPUT=str(OUT / "nbh_elev.gpkg"))
          gpd.read_file(res["OUTPUT"])[["name", "elev_mean", "elev_max"]].round(1)
          """)

    nb.level(4, "Professional: networks, clusters, reproducible pipelines", "use QGIS tools that go beyond GeoPandas, and build a pipeline you can check against Python.",
             "Using a GPS route planner instead of a ruler: the real path, not the straight line.")
    nb.pro("4.1", "Walking along streets vs. a circle", "Proximity (network vs. buffer model)",
           scenario="""
           From each clinic, which roads can you reach within **800 m along the road network**? Compare the network result with the simple 800 m circle:
           how many km of road are inside the circle, and how many are really reachable?
           """,
           plan_hint="""
           `native:serviceareafromlayer`: `INPUT=V("roads")` (the network), `START_POINTS=V("clinics")`, `STRATEGY=0` (shortest = distance),
           `TRAVEL_COST2=800`, `OUTPUT_LINES=...`. Network tools need a QGIS project: pass `_project=minimal_project()`. For the circle: buffer clinics 800 m and clip the roads.
           Daily picture: a circle on a map says 'close', but a river without a bridge can make a place 3 km away on foot.
           """,
           starter="""
           net = qrun("native:serviceareafromlayer", _project=minimal_project(), INPUT=V("roads"), STRATEGY=0, START_POINTS=V("clinics"),
                      TRAVEL_COST2=____, TOLERANCE=1, DEFAULT_DIRECTION=2, DEFAULT_SPEED=5,
                      OUTPUT_LINES=str(OUT / "service_lines.gpkg"))
           circ = qrun("native:buffer", INPUT=V("clinics"), DISTANCE=800, SEGMENTS=16, DISSOLVE=True, OUTPUT=str(OUT / "clinic800.gpkg"))
           inside = qrun("native:clip", INPUT=V("roads"), OVERLAY=circ["OUTPUT"], OUTPUT=str(OUT / "roads_in_circle.gpkg"))
           lines = gpd.read_file(net["OUTPUT_LINES"]); roads_c = gpd.read_file(inside["OUTPUT"])
           print(f"road inside circles: {roads_c.length.sum() / 1000:.1f} km | reachable on the network: {lines.dissolve().length.sum() / 1000:.1f} km")
           ax = gpd.read_file(circ["OUTPUT"]).plot(alpha=.2, figsize=(6, 6)); gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="lightgrey")
           lines.plot(ax=ax, color="red", linewidth=2); gpd.read_file(GPKG, layer="clinics").plot(ax=ax, color="black"); plt.show()
           """,
           solution="""
           net = qrun("native:serviceareafromlayer", _project=minimal_project(), INPUT=V("roads"), STRATEGY=0, START_POINTS=V("clinics"),
                      TRAVEL_COST2=800, TOLERANCE=1, DEFAULT_DIRECTION=2, DEFAULT_SPEED=5,
                      OUTPUT_LINES=str(OUT / "service_lines.gpkg"))
           circ = qrun("native:buffer", INPUT=V("clinics"), DISTANCE=800, SEGMENTS=16, DISSOLVE=True, OUTPUT=str(OUT / "clinic800.gpkg"))
           inside = qrun("native:clip", INPUT=V("roads"), OVERLAY=circ["OUTPUT"], OUTPUT=str(OUT / "roads_in_circle.gpkg"))
           lines = gpd.read_file(net["OUTPUT_LINES"]); roads_c = gpd.read_file(inside["OUTPUT"])
           print(f"road inside circles: {roads_c.length.sum() / 1000:.1f} km | reachable on the network: {lines.dissolve().length.sum() / 1000:.1f} km")
           ax = gpd.read_file(circ["OUTPUT"]).plot(alpha=.2, figsize=(6, 6)); gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="lightgrey")
           lines.plot(ax=ax, color="red", linewidth=2); gpd.read_file(GPKG, layer="clinics").plot(ax=ax, color="black"); plt.show()
           """,
           answer="""
           The network reaches less than the circle suggests: clinics that are not on a road first need a 'connector', and the network only follows real streets.
           This is the network model from the A1 test (Model 2), done with a ready-made QGIS tool.
           Limitation: Riverton's road layer has only 7 main roads; with a full street network (e.g. from OpenStreetMap) the result is much more realistic.
           """,
           why="Service areas / isochrones are the standard accessibility model in planning (15-minute city, emergency response).")
    nb.pro("4.2", "Where do accidents cluster? (DBSCAN)", "Descriptive / statistical (density-based clustering)",
           scenario="Find groups of accidents where at least **8** accidents lie within **150 m** of each other. How many clusters are there, and where?",
           plan_hint="`native:dbscanclustering`: `EPS=150` (the 150 m), `MIN_SIZE=8`, `FIELD_NAME=\"cluster\"`. Points that belong to no cluster get an empty value (noise).",
           starter="""
           res = qrun("native:dbscanclustering", INPUT=V("accidents"), MIN_SIZE=____, EPS=____, FIELD_NAME="cluster",
                      SIZE_FIELD_NAME="size", OUTPUT=str(OUT / "acc_clusters.gpkg"))
           cl = gpd.read_file(res["OUTPUT"])
           print(cl["cluster"].nunique(), "clusters;", cl["cluster"].isna().sum(), "accidents are noise")
           ax = nbh.boundary.plot(color="grey", figsize=(6, 6)); gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="lightgrey")
           cl[cl.cluster.isna()].plot(ax=ax, color="black", markersize=3); cl.dropna(subset=["cluster"]).plot(ax=ax, column="cluster", categorical=True, markersize=12); plt.show()
           """,
           solution="""
           res = qrun("native:dbscanclustering", INPUT=V("accidents"), MIN_SIZE=8, EPS=150, FIELD_NAME="cluster",
                      SIZE_FIELD_NAME="size", OUTPUT=str(OUT / "acc_clusters.gpkg"))
           cl = gpd.read_file(res["OUTPUT"])
           print(cl["cluster"].nunique(), "clusters;", cl["cluster"].isna().sum(), "accidents are noise")
           ax = nbh.boundary.plot(color="grey", figsize=(6, 6)); gpd.read_file(GPKG, layer="roads").plot(ax=ax, color="lightgrey")
           cl[cl.cluster.isna()].plot(ax=ax, color="black", markersize=3); cl.dropna(subset=["cluster"]).plot(ax=ax, column="cluster", categorical=True, markersize=12); plt.show()
           """,
           answer="""
           DBSCAN finds dense groups (here the dangerous junctions) and labels scattered points as noise.
           It *describes* clusters but does not test them against chance — for that use PySAL (A6: Gi*, LISA, Ripley's K). The result also depends on EPS and MIN_SIZE: try 100 m and 250 m.
           """)
    nb.pro("4.3", "Same question, two toolboxes: does QGIS agree with GeoPandas?", "Reproducibility (method check)",
           scenario="Count accidents per neighbourhood with QGIS (3.2) and with GeoPandas `sjoin`. Write a check that fails if any count differs.",
           plan_hint="Merge both results on `name` and compare with `assert (a == b).all()`. Daily picture: weighing a parcel on two scales before posting it.",
           starter="""
           acc = gpd.read_file(GPKG, layer="accidents")
           gp = gpd.sjoin(acc, nbh[["name", "geometry"]], predicate="within")["name"].value_counts()
           both = cnt[["name", "n_acc"]].assign(geopandas=cnt["name"].map(gp).fillna(0))
           assert (both["n_acc"] == both["____"]).all(), "QGIS and GeoPandas disagree!"
           print("✅ QGIS and GeoPandas agree"); both
           """,
           solution="""
           acc = gpd.read_file(GPKG, layer="accidents")
           gp = gpd.sjoin(acc, nbh[["name", "geometry"]], predicate="within")["name"].value_counts()
           both = cnt[["name", "n_acc"]].assign(geopandas=cnt["name"].map(gp).fillna(0))
           assert (both["n_acc"] == both["geopandas"]).all(), "QGIS and GeoPandas disagree!"
           print("✅ QGIS and GeoPandas agree"); both
           """,
           answer="Cross-checking two independent tools is a cheap and strong quality test. Small differences usually come from boundary rules (a point exactly on an edge) or buffer segments.")
    nb.md("""
    ### The same tool in PyQGIS (for when you work inside QGIS)

    In the QGIS Python console (or a Python that has `qgis` installed) the exact same call is:
    ```python
    import processing
    result = processing.run("native:buffer", {"INPUT": "riverton.gpkg|layername=schools", "DISTANCE": 600,
                                              "SEGMENTS": 16, "DISSOLVE": False, "OUTPUT": "memory:"})
    layer = result["OUTPUT"]
    ```
    Same ids, same parameter names. What you learn with `qrun()` transfers one-to-one.
    """)

    nb.test("""
    Use QGIS native tools through `qrun()` (and GeoPandas only to look at results). For each: **question type → tool chain → code → interpretation.**
    """, [
        ("task", """
        **A.** Make multi-ring buffers (200, 400, 600 m) around the clinics and count the houses in each ring.
        """, """
        Type: proximity. Chain: multi-ring buffer → count points (weighted by residents).
        ```python
        rings = qrun("native:multiringconstantbuffer", INPUT=V("clinics"), RINGS=3, DISTANCE=200, OUTPUT=str(OUT / "rings.gpkg"))
        c = qrun("native:countpointsinpolygon", POLYGONS=rings["OUTPUT"], POINTS=V("houses"), WEIGHT="residents",
                 FIELD="residents", OUTPUT=str(OUT / "rings_count.gpkg"))
        print(gpd.read_file(c["OUTPUT"])[["clinic", "ringId", "residents"]])
        ```
        """),
        ("task", """
        **B.** List the parks with the share of their area inside the 150 m flood zone, using QGIS tools only for the geometry work.
        """, """
        Type: overlay + measurement.
        ```python
        inter = qrun("native:intersection", INPUT=V("parks"), OVERLAY=str(OUT / "flood.gpkg"), OUTPUT=str(OUT / "park_flood.gpkg"))
        pf = gpd.read_file(inter["OUTPUT"]); parks = gpd.read_file(GPKG, layer="parks")
        print((pf.dissolve("park").area / parks.set_index("park").area).fillna(0).round(3))
        ```
        """),
        ("task", """
        **C.** Give every house the elevation of the DEM cell it stands on, and report the lowest 5 houses.
        """, """
        ```python
        s = qrun("native:rastersampling", INPUT=V("houses"), RASTERCOPY=str(DEM), COLUMN_PREFIX="elev_", OUTPUT=str(OUT / "houses_elev.gpkg"))
        print(gpd.read_file(s["OUTPUT"]).nsmallest(5, "elev_1")[["house_id", "elev_1"]])
        ```
        """),
        ("decision", """
        **D.** A colleague made a site-selection map by clicking through 12 QGIS tools. The council asks for the same map next year with new data. What do you recommend?
        """, """
        Turn the clicks into a script (`qrun` chain or PyQGIS) or a **Graphical Modeler** model (.model3), store it with the data, and re-run it.
        Recommendation: a script in a notebook, because it documents every parameter, can be checked by others, and runs in one go.
        """),
        ("model", """
        **E · Modelling.** Riverton wants a map of *'how long does it take to walk to the nearest clinic'* for every house. Which QGIS tools would you chain, and what data would you need first?
        """, """
        Data: a complete **street network** (OpenStreetMap footways + streets), clinics, houses.
        Chain: snap houses to the network → `native:shortestpathlayertopoint` or service areas with several costs (5, 10, 15 min at ~5 km/h) → join the band to each house (`joinattributesbylocation`) → summarise per neighbourhood.
        Assumptions: walking speed, no slopes (GRASS `r.walk` can add slope effects, D3), barriers like rivers only crossable at bridges.
        """),
    ])
    nb.reflect("""
    Which QGIS tools do you already use by clicking? Pick one of your own workflows and write the list of `native:` tool ids it uses — that is your first script.
    """)
    return nb
