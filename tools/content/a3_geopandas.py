from nbbuild import NB, SETUP


def build():
    nb = NB("A3_geopandas", "A3 · GeoPandas — tables of shapes (your main target)")
    nb.md("""
    **What GeoPandas is:** pandas (tables) + Shapely (shapes) + PyProj (CRS) + Pyogrio (files), in one object:
    the **GeoDataFrame**. Each row is a thing (a school, a road), each column an attribute, and one special column,
    `geometry`, holds a Shapely shape.

    **Daily picture:** an Excel sheet of your city's schools where one column is not text or a number but the school's
    shape on the map. Now you can ask the sheet: "which schools are within 1 km of the river?"

    **What you already know:** every Shapely command (`buffer`, `distance`, `intersects`…) works on the whole
    geometry column at once. Every PyProj idea comes back as `.crs` and `.to_crs()`.

    **Where this fits in your plan:** this is the tool you will use most. Levels 3 and 4 (spatial joins, overlays, models)
    are the core of daily GIS analysis.
    """)
    nb.code(SETUP)
    nb.code("""
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import matplotlib.pyplot as plt
    print("geopandas", gpd.__version__)
    """)

    # ---------------------------------------------------------------- level 1
    nb.level(1, "Basics: open, look, plot, convert", "load layers, read their CRS and geometry type, map them, and build points from a plain table.",
             "Opening a spreadsheet, looking at the first rows, and making a quick chart.")
    nb.ex("1.1", "Open a layer from a file", "gpd.read_file(path, layer=...)",
          purpose_a="Reads a vector file (GeoPackage, Shapefile, GeoJSON…) into a GeoDataFrame.",
          life_a="Loading the city's official neighbourhood boundaries to start any analysis.",
          hint="The GeoPackage `GPKG` holds many layers (like sheets in one Excel file). Ask for `layer=\"neighbourhoods\"`.",
          starter="""
          nbh = gpd.read_file(GPKG, layer="____")
          nbh.head()
          """,
          solution="""
          nbh = gpd.read_file(GPKG, layer="neighbourhoods")
          nbh.head()
          """)
    nb.ex("1.2", "Know your layer", ".crs / .geom_type / .shape / .total_bounds",
          purpose_a="Show the CRS, the kind of shapes, the number of rows × columns, and the box around all shapes.",
          life_a="The first 30 seconds with any new dataset: is it in metres or degrees? points or polygons? how big?",
          hint="These are attributes (no brackets) except that `geom_type` lives on the rows: `nbh.geom_type.unique()`.",
          starter="""
          print(nbh.____)
          print(nbh.geom_type.____())
          print(nbh.____)
          print(nbh.____)
          """,
          solution="""
          print(nbh.crs)
          print(nbh.geom_type.unique())
          print(nbh.shape)
          print(nbh.total_bounds)
          """)
    nb.ex("1.3", "A quick map (choropleth)", "gdf.plot(column=..., legend=True)",
          purpose_a="Draws the shapes; with `column=` it colours each shape by a value (a choropleth map).",
          life_a="A first look at where many people live, or where incomes are high.",
          hint="`column=\"median_income\"`, `cmap=\"viridis\"`, `legend=True`. You can draw a second layer on the same `ax`.",
          starter="""
          ax = nbh.plot(column="____", cmap="viridis", legend=True, edgecolor="white", figsize=(5, 5))
          gpd.read_file(GPKG, layer="river").plot(ax=ax, color="steelblue", linewidth=3)
          plt.show()
          """,
          solution="""
          ax = nbh.plot(column="median_income", cmap="viridis", legend=True, edgecolor="white", figsize=(5, 5))
          gpd.read_file(GPKG, layer="river").plot(ax=ax, color="steelblue", linewidth=3)
          plt.show()
          """)
    nb.ex("1.4", "Points from a plain table", "gpd.points_from_xy(df.lon, df.lat) + crs=",
          purpose_a="Turns x/y (here lon/lat) columns of a normal table into point geometries.",
          life_a="A list of addresses with GPS columns from Excel, a survey app, or a web download.",
          hint="Read the CSV with pandas. Build `gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)`. **Always set the CRS**: lon/lat from GPS is EPSG:4326.",
          starter="""
          df = pd.read_csv(DATA_DIR / "shops_wgs84.csv")
          shops = gpd.GeoDataFrame(df, geometry=gpd.____(df.____, df.____), crs=____)
          shops.head()
          """,
          solution="""
          df = pd.read_csv(DATA_DIR / "shops_wgs84.csv")
          shops = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
          shops.head()
          """)
    nb.ex("1.5", "Reproject a layer", "gdf.to_crs(epsg)",
          purpose_a="Transforms all geometries into another CRS (PyProj works in the background).",
          life_a="Bring the GPS shops into the same metre CRS as the neighbourhoods before measuring or joining.",
          hint="Target is Riverton's CRS: `nbh.crs` (or 32633). After it, x values should be around 390 000–396 000.",
          starter="""
          shops = shops.____(nbh.crs)
          print(shops.crs, shops.geometry.x.min().round(), shops.geometry.x.max().round())
          """,
          solution="""
          shops = shops.to_crs(nbh.crs)
          print(shops.crs, shops.geometry.x.min().round(), shops.geometry.x.max().round())
          """,
          note="Rule: **all layers in one analysis must share one CRS.** GeoPandas warns you if they do not.")

    # ---------------------------------------------------------------- level 2
    nb.level(2, "Core tools: new columns, filters, joins by name", "compute areas and distances as columns, select rows, and attach tables.",
             "Adding a 'total' column to a spreadsheet, filtering rows, and pasting in a column from another sheet.")
    nb.ex("2.1", "Area and density columns", "gdf.area",
          purpose_a="Returns the area of every geometry (in CRS units², here m²) as a new column.",
          life_a="Population density (people per km²) per neighbourhood, to compare crowded and quiet areas.",
          hint="1 km² = 1 000 000 m² (a square 1000 m × 1000 m). So `area_km2 = nbh.area / 1e6`. Density = population / area_km2.",
          starter="""
          nbh["area_km2"] = nbh.____ / 1e6
          nbh["density"] = nbh["population"] / nbh["____"]
          nbh[["name", "area_km2", "density"]].sort_values("density", ascending=False)
          """,
          solution="""
          nbh["area_km2"] = nbh.area / 1e6
          nbh["density"] = nbh["population"] / nbh["area_km2"]
          nbh[["name", "area_km2", "density"]].sort_values("density", ascending=False)
          """)
    nb.ex("2.2", "Filter rows by a rule", "gdf[gdf['col'] > value]",
          purpose_a="Keeps only the rows that meet a condition (a boolean mask), like the filter button in Excel.",
          life_a="Select the neighbourhoods where more than 25 % of people are over 65, to plan care services.",
          hint="The condition `nbh[\"pct_over65\"] > 25` gives True/False per row. Put it inside `nbh[...]`. Combine rules with `&` (and) / `|` (or) and brackets.",
          starter="""
          old = nbh[nbh["pct_over65"] ____ 25]
          old_poor = nbh[(nbh["pct_over65"] > 25) ____ (nbh["median_income"] < 30000)]
          print(old["name"].tolist(), old_poor["name"].tolist())
          """,
          solution="""
          old = nbh[nbh["pct_over65"] > 25]
          old_poor = nbh[(nbh["pct_over65"] > 25) & (nbh["median_income"] < 30000)]
          print(old["name"].tolist(), old_poor["name"].tolist())
          """)
    nb.ex("2.3", "Buffers as a new layer", "gdf.buffer(d) + set geometry",
          purpose_a="Buffers every geometry; putting the result in a copy of the table keeps the attributes with the new shapes.",
          life_a="The 600 m catchment of every school, keeping each school's name and capacity attached.",
          hint="`catch = schools.copy()` then `catch[\"geometry\"] = schools.buffer(600)`. Now each row is a circle with its school's data.",
          starter="""
          schools = gpd.read_file(GPKG, layer="schools")
          catch = schools.copy()
          catch["geometry"] = schools.____(600)
          ax = catch.plot(alpha=.3, figsize=(5, 5)); schools.plot(ax=ax, color="red"); plt.show()
          """,
          solution="""
          schools = gpd.read_file(GPKG, layer="schools")
          catch = schools.copy()
          catch["geometry"] = schools.buffer(600)
          ax = catch.plot(alpha=.3, figsize=(5, 5)); schools.plot(ax=ax, color="red"); plt.show()
          """)
    nb.ex("2.4", "Distance from every row to one shape", "gdf.distance(geom)",
          purpose_a="Distance from each geometry in the column to one other geometry (or row-by-row to another GeoSeries).",
          life_a="How far is each school from the river? (children's safety, flood risk).",
          hint="Take the one river line: `river.geometry.iloc[0]`. Round the result.",
          starter="""
          river = gpd.read_file(GPKG, layer="river")
          schools["dist_river_m"] = schools.____(river.geometry.____[0]).round()
          schools[["school", "dist_river_m"]]
          """,
          solution="""
          river = gpd.read_file(GPKG, layer="river")
          schools["dist_river_m"] = schools.distance(river.geometry.iloc[0]).round()
          schools[["school", "dist_river_m"]]
          """)
    nb.ex("2.5", "Attach a table by a shared name (attribute join)", "gdf.merge(df, on='key')",
          purpose_a="Joins a normal table to the GeoDataFrame using a common column (like VLOOKUP in Excel). No geometry involved.",
          life_a="Census tables arrive without shapes; you join them to the boundaries with the district code.",
          hint="Call `merge` on the **GeoDataFrame** (so the result stays spatial), `on=\"name\"`, `how=\"left\"` keeps all neighbourhoods.",
          starter="""
          unemployment = pd.DataFrame({"name": ["Oldtown", "Harbour", "Hillcrest", "Southpark"],
                                       "unemployed_pct": [6.1, 11.4, 3.2, 8.8]})
          nbh2 = nbh.____(unemployment, on="____", how="left")
          print(type(nbh2).__name__)
          nbh2[["name", "unemployed_pct"]]
          """,
          solution="""
          unemployment = pd.DataFrame({"name": ["Oldtown", "Harbour", "Hillcrest", "Southpark"],
                                       "unemployed_pct": [6.1, 11.4, 3.2, 8.8]})
          nbh2 = nbh.merge(unemployment, on="name", how="left")
          print(type(nbh2).__name__)
          nbh2[["name", "unemployed_pct"]]
          """,
          note="Rows without a match get `NaN` (empty). Always check how many rows matched: `nbh2['unemployed_pct'].notna().sum()`.")
    nb.ex("2.6", "Let GeoPandas pick a metric CRS", "gdf.estimate_utm_crs()",
          purpose_a="Suggests the best UTM CRS for the data's location, so you can measure in metres.",
          life_a="You get a GeoJSON in lon/lat (as most web data is) and need areas in m² quickly.",
          hint="Read `neighbourhoods.geojson` (it is in EPSG:4326). Compare `.area` before and after `to_crs(gdf.estimate_utm_crs())`.",
          starter="""
          web = gpd.read_file(DATA_DIR / "neighbourhoods.geojson")
          print(web.crs, web.area.iloc[0])                      # degrees² -> meaningless
          utm = web.to_crs(web.____())
          print(utm.crs, round(utm.area.iloc[0]))
          """,
          solution="""
          web = gpd.read_file(DATA_DIR / "neighbourhoods.geojson")
          print(web.crs, web.area.iloc[0])
          utm = web.to_crs(web.estimate_utm_crs())
          print(utm.crs, round(utm.area.iloc[0]))
          """)

    # ---------------------------------------------------------------- level 3
    nb.level(3, "Combining: spatial joins, overlays, dissolve", "join tables by location, cut layers with each other and summarise by area — the daily bread of GIS.",
             "Sorting your post by street, cutting a pizza along the lines of a map, and merging small boxes into bigger ones.")
    nb.code("""
    accidents = gpd.read_file(GPKG, layer="accidents")
    clinics = gpd.read_file(GPKG, layer="clinics")
    houses = gpd.read_file(GPKG, layer="houses")
    roads = gpd.read_file(GPKG, layer="roads")
    parks = gpd.read_file(GPKG, layer="parks")
    """)
    nb.ex("3.1", "Which neighbourhood is each accident in? (spatial join)", "gpd.sjoin(points, polygons, predicate='within')",
          purpose_a="Joins the attributes of one layer to another **by location** (here: the polygon each point falls in).",
          life_a="Counting crimes, accidents or shops per district when the points only have coordinates.",
          hint="Left = accidents (you keep one row per accident), right = `nbh[[\"name\", \"geometry\"]]`. Then `value_counts()` on `name`.",
          task="Attach the neighbourhood name to every accident, then count accidents per neighbourhood.",
          starter="""
          acc_nb = gpd.sjoin(accidents, nbh[["name", "geometry"]], predicate="____")
          counts = acc_nb["____"].value_counts()
          counts
          """,
          solution="""
          acc_nb = gpd.sjoin(accidents, nbh[["name", "geometry"]], predicate="within")
          counts = acc_nb["name"].value_counts()
          counts
          """,
          note="Accidents outside all neighbourhoods disappear (inner join). Use `how=\"left\"` to keep them and see `NaN`.")
    nb.ex("3.2", "Nearest facility for every point", "gpd.sjoin_nearest(a, b, distance_col='dist')",
          purpose_a="Joins each row of `a` to the **closest** row of `b` and can store the distance.",
          life_a="The nearest clinic for each school or house; the nearest fire station for each street.",
          hint="`gpd.sjoin_nearest(schools, clinics[[\"clinic\", \"geometry\"]], distance_col=\"dist_m\")`. Both layers must be in metres.",
          starter="""
          near = gpd.sjoin_nearest(schools, clinics[["clinic", "geometry"]], distance_col="____")
          near[["school", "clinic", "dist_m"]].round()
          """,
          solution="""
          near = gpd.sjoin_nearest(schools, clinics[["clinic", "geometry"]], distance_col="dist_m")
          near[["school", "clinic", "dist_m"]].round()
          """)
    nb.ex("3.3", "Overlay: cut polygons with polygons", "gpd.overlay(a, b, how='intersection')",
          purpose_a="Creates new polygons where two polygon layers overlap, carrying the attributes of both.",
          life_a="How much of each neighbourhood lies in the flood zone? (area per neighbourhood × zone).",
          hint="Make the flood zone a GeoDataFrame: `gpd.GeoDataFrame(geometry=river.buffer(150), crs=nbh.crs)`. Overlay with `nbh`. Then area in hectares = `.area / 10_000`.",
          starter="""
          flood = gpd.GeoDataFrame({"zone": ["flood"]}, geometry=river.buffer(____), crs=nbh.crs)
          pieces = gpd.overlay(nbh[["name", "geometry"]], flood, how="____")
          pieces["flood_ha"] = pieces.area / 10_000
          pieces[["name", "flood_ha"]].round(1)
          """,
          solution="""
          flood = gpd.GeoDataFrame({"zone": ["flood"]}, geometry=river.buffer(150), crs=nbh.crs)
          pieces = gpd.overlay(nbh[["name", "geometry"]], flood, how="intersection")
          pieces["flood_ha"] = pieces.area / 10_000
          pieces[["name", "flood_ha"]].round(1)
          """)
    nb.ex("3.4", "Clip a layer to an area", "gpd.clip(gdf, mask)",
          purpose_a="Cuts a layer to the shape of a mask: only the parts inside remain (lines are shortened, not dropped).",
          life_a="Kilometres of road that would be under water in a flood; the part of a railway inside a nature reserve.",
          hint="`gpd.clip(roads, flood)`. Then road length in km = `.length / 1000`, grouped by `road_type`.",
          starter="""
          wet_roads = gpd.____(roads, flood)
          wet_roads.assign(km=wet_roads.length / 1000).groupby("____")["km"].sum().round(2)
          """,
          solution="""
          wet_roads = gpd.clip(roads, flood)
          wet_roads.assign(km=wet_roads.length / 1000).groupby("road_type")["km"].sum().round(2)
          """)
    nb.ex("3.5", "Dissolve: merge small areas into big ones", "gdf.dissolve(by='col', aggfunc=...)",
          purpose_a="Merges geometries that share a value into one shape and summarises their attributes (a spatial `groupby`).",
          life_a="Merge neighbourhoods into three electoral districts and add up their population.",
          hint="First give each neighbourhood a `district` (south/centre/north from its row). Then `dissolve(by=\"district\", aggfunc={\"population\": \"sum\"})`.",
          starter="""
          nbh["district"] = ["south"] * 3 + ["centre"] * 3 + ["north"] * 3
          districts = nbh.____(by="____", aggfunc={"population": "sum"})
          ax = districts.plot(column="population", legend=True, edgecolor="black", figsize=(5, 5)); plt.show()
          districts[["population"]]
          """,
          solution="""
          nbh["district"] = ["south"] * 3 + ["centre"] * 3 + ["north"] * 3
          districts = nbh.dissolve(by="district", aggfunc={"population": "sum"})
          ax = districts.plot(column="population", legend=True, edgecolor="black", figsize=(5, 5)); plt.show()
          districts[["population"]]
          """)
    nb.ex("3.6", "Count per area and put it back on the map", "groupby → merge back → rate column",
          purpose_a="Combines a spatial join, a count, and an attribute join to get a **rate** per polygon.",
          life_a="Accidents per 1 000 residents per neighbourhood — a fair comparison between big and small areas.",
          hint="`counts` from 3.1 is a Series indexed by name. `rename(\"accidents\")`, then `nbh.merge(counts, left_on=\"name\", right_index=True, how=\"left\")`. Rate = accidents / population × 1000 (like 'goals per 1000 minutes').",
          starter="""
          nbh = nbh.merge(counts.rename("accidents"), left_on="name", right_index=True, how="left").fillna({"accidents": 0})
          nbh["acc_per_1000"] = nbh["accidents"] / nbh["____"] * ____
          nbh.sort_values("acc_per_1000", ascending=False)[["name", "accidents", "acc_per_1000"]].round(2)
          """,
          solution="""
          nbh = nbh.merge(counts.rename("accidents"), left_on="name", right_index=True, how="left").fillna({"accidents": 0})
          nbh["acc_per_1000"] = nbh["accidents"] / nbh["population"] * 1000
          nbh.sort_values("acc_per_1000", ascending=False)[["name", "accidents", "acc_per_1000"]].round(2)
          """)
    nb.ex("3.7", "Save your result", "gdf.to_file(path, layer=..., driver='GPKG')",
          purpose_a="Writes a GeoDataFrame to a file (here a new layer in a GeoPackage) for QGIS, colleagues or later notebooks.",
          life_a="Handing your 'accidents per 1000 residents' layer to the city's traffic department.",
          hint="Write to `DATA_DIR / \"my_results.gpkg\"`, layer `\"nbh_accident_rates\"`. Check with `pyogrio.list_layers`.",
          starter="""
          import pyogrio
          out = DATA_DIR / "my_results.gpkg"
          nbh.drop(columns="district").____(out, layer="____", driver="GPKG")
          print(pyogrio.list_layers(out))
          """,
          solution="""
          import pyogrio
          out = DATA_DIR / "my_results.gpkg"
          nbh.drop(columns="district").to_file(out, layer="nbh_accident_rates", driver="GPKG")
          print(pyogrio.list_layers(out))
          """)

    # ---------------------------------------------------------------- level 4
    nb.level(4, "Professional: the 8 question types in Riverton", "recognise the type of question, plan the chain of commands, and state your assumptions.",
             "A doctor first decides *what kind* of problem it is (infection? injury?), then chooses the test. You do the same with spatial questions.")
    nb.pro("4.1", "Who can reach a clinic on foot?", "Proximity / accessibility",
           scenario="What share of residents in **each neighbourhood** lives within **800 m** of a clinic? Which neighbourhood is worst served?",
           plan_hint="1) `sjoin_nearest(houses, clinics, distance_col=\"d\")`, 2) flag `d <= 800`, 3) weight by residents: groupby `nb_id`, sum residents that are served ÷ all residents, 4) add names.",
           starter="""
           h = gpd.sjoin_nearest(houses, clinics[["clinic", "geometry"]], distance_col="d")
           h["served"] = h["d"] <= ____
           share = (h["residents"] * h["served"]).groupby(h["nb_id"]).sum() / h.groupby("nb_id")["residents"].sum()
           nbh["share_clinic_800m"] = nbh["nb_id"].map(share)
           nbh.sort_values("share_clinic_800m")[["name", "share_clinic_800m"]].round(2)
           """,
           solution="""
           h = gpd.sjoin_nearest(houses, clinics[["clinic", "geometry"]], distance_col="d")
           h["served"] = h["d"] <= 800
           share = (h["residents"] * h["served"]).groupby(h["nb_id"]).sum() / h.groupby("nb_id")["residents"].sum()
           nbh["share_clinic_800m"] = nbh["nb_id"].map(share)
           nbh.sort_values("share_clinic_800m")[["name", "share_clinic_800m"]].round(2)
           """,
           answer="Proximity measured at the **house** level, then summarised per neighbourhood. Using houses instead of neighbourhood centroids avoids the error of treating a 4 km² area as one point.",
           why="This is the standard 'access to services' indicator (e.g. the 15-minute city).")
    nb.pro("4.2", "How many people live in the flood zone? Two models", "Modelling (and model comparison)",
           scenario="""
           Estimate the population inside the 150 m flood zone in two ways:
           **Model A – areal weighting:** assume people are spread evenly in each neighbourhood; population in zone = population × (flooded area ÷ neighbourhood area).
           **Model B – dasymetric (houses):** count residents of houses inside the zone.
           Compare and explain the difference.
           """,
           plan_hint="Model A: reuse `pieces` from 3.3, merge population and area, multiply by the share. Model B: `sjoin(houses, flood, predicate=\"within\")` and sum residents.",
           starter="""
           a = pieces.merge(nbh[["name", "population", "area_km2"]], on="name")
           a["pop_in_zone"] = a["population"] * (a.area / 1e6) / a["____"]
           model_a = a["pop_in_zone"].sum()
           model_b = gpd.sjoin(houses, flood, predicate="____")["residents"].sum()
           print(round(model_a), model_b)
           """,
           solution="""
           a = pieces.merge(nbh[["name", "population", "area_km2"]], on="name")
           a["pop_in_zone"] = a["population"] * (a.area / 1e6) / a["area_km2"]
           model_a = a["pop_in_zone"].sum()
           model_b = gpd.sjoin(houses, flood, predicate="within")["residents"].sum()
           print(round(model_a), model_b)
           """,
           answer="""
           Model A over-estimates, because it puts people in places where nobody lives (the river bank itself — in Riverton no houses stand within 60 m of the river).
           Model B uses where buildings really are, so it is closer to reality. **Recommendation:** use building-based (dasymetric) data when you have it; use areal weighting only when you do not, and say so.
           """,
           why="Moving data from one set of areas to another is called the *change of support* problem. Every model hides an assumption; name it.")
    nb.pro("4.3", "Are accidents really clustered near main roads?", "Statistical (Monte Carlo test)",
           scenario="Accidents look close to primary roads. Is that a real pattern or could it happen by chance? Compare the mean distance of real accidents to primary roads with 199 sets of **random** points.",
           plan_hint="""
           1) mean distance of real accidents to the union of primary roads.
           2) repeat 199 times: throw 260 random points in the town box, compute the same mean.
           3) p-value = (number of random means ≤ real mean + 1) / (199 + 1).
           Daily picture: if you roll a die 199 times and never get a result as extreme as yours, your die is probably loaded.
           """,
           starter="""
           import shapely
           primary = roads[roads.road_type == "primary"].union_all()
           real = accidents.distance(primary).mean()
           rng = np.random.default_rng(1)
           xmin, ymin, xmax, ymax = nbh.total_bounds
           sims = []
           for _ in range(____):
               pts = shapely.points(rng.uniform(xmin, xmax, len(accidents)), rng.uniform(ymin, ymax, len(accidents)))
               sims.append(shapely.distance(pts, primary).mean())
           sims = np.array(sims)
           p = ((sims <= real).sum() + 1) / (len(sims) + 1)
           print(f"real mean {real:.0f} m, random mean {sims.mean():.0f} m, p = {p:.3f}")
           """,
           solution="""
           import shapely
           primary = roads[roads.road_type == "primary"].union_all()
           real = accidents.distance(primary).mean()
           rng = np.random.default_rng(1)
           xmin, ymin, xmax, ymax = nbh.total_bounds
           sims = []
           for _ in range(199):
               pts = shapely.points(rng.uniform(xmin, xmax, len(accidents)), rng.uniform(ymin, ymax, len(accidents)))
               sims.append(shapely.distance(pts, primary).mean())
           sims = np.array(sims)
           p = ((sims <= real).sum() + 1) / (len(sims) + 1)
           print(f"real mean {real:.0f} m, random mean {sims.mean():.0f} m, p = {p:.3f}")
           """,
           answer="""
           The real mean is far smaller than any random mean, so p = 0.005 (the smallest possible with 199 runs): the clustering is **not chance**.
           Caution: random points should really be placed where accidents *can* happen (on streets, where people are). A fairer 'null model' would place random points on all roads.
           """,
           why="Statistical questions ask 'is it real?'. Monte Carlo (simulate chance many times) is simple and works for almost any spatial pattern. Next steps: Moran's I and hot-spot analysis with the `esda` library.")
    nb.pro("4.4", "Which primary schools are overcrowded? (demand model)", "Modelling (supply and demand)",
           scenario="Assume every house sends its children to the **nearest primary school**, and 5 % of residents are of primary-school age. Compare the modelled demand with each school's capacity.",
           plan_hint="1) keep primary schools, 2) `sjoin_nearest(houses, primary_schools)`, 3) children = residents × 0.05, 4) sum per school, 5) compare with `capacity` → ratio > 1 = overcrowded.",
           starter="""
           prim = schools[schools["level"] == "____"][["school", "capacity", "geometry"]]
           hs = gpd.sjoin_nearest(houses, prim)
           demand = (hs["residents"] * ____).groupby(hs["school"]).sum().rename("demand")
           res = prim.set_index("school").join(demand)
           res["load"] = (res["demand"] / res["capacity"]).round(2)
           res[["capacity", "demand", "load"]]
           """,
           solution="""
           prim = schools[schools["level"] == "primary"][["school", "capacity", "geometry"]]
           hs = gpd.sjoin_nearest(houses, prim)
           demand = (hs["residents"] * 0.05).groupby(hs["school"]).sum().rename("demand")
           res = prim.set_index("school").join(demand)
           res["load"] = (res["demand"] / res["capacity"]).round(2)
           res[["capacity", "demand", "load"]]
           """,
           answer="A simple **allocation model**: nearest facility + a demand rate. Its assumptions: straight-line distance, every child goes to the nearest school, the same child share everywhere. Improve with real age data and street distances.",
           why="The same pattern models hospitals, supermarkets, polling stations: supply points + demand points + a rule for who goes where.")
    nb.pro("4.5", "Where should the new clinic go?", "Decision / suitability (multi-criteria)",
           scenario="""
           Find the best location for a new clinic. Candidate sites: a 250 m grid of points over Riverton. Rules:
           (1) more than **1 000 m** from existing clinics, (2) outside the 150 m flood zone,
           (3) score = number of **residents over 65** within 800 m (use each house's neighbourhood `pct_over65`). Report the best site.
           """,
           plan_hint="Build the grid with `np.arange` + `points_from_xy`. Filter rules 1–2 with `.distance(...)` and `.within(...)`. For the score: `sjoin(houses_with_old, candidates.buffer(800))` then groupby candidate and sum.",
           starter="""
           xmin, ymin, xmax, ymax = nbh.total_bounds
           xs, ys = np.meshgrid(np.arange(xmin + 125, xmax, 250), np.arange(ymin + 125, ymax, 250))
           cand = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs.ravel(), ys.ravel()), crs=nbh.crs)
           cand = cand[(cand.distance(clinics.union_all()) > ____) & ~cand.within(flood.union_all())].reset_index(drop=True)
           old = houses.merge(nbh[["nb_id", "pct_over65"]], on="nb_id")
           old["old_res"] = old["residents"] * old["pct_over65"] / 100
           rings = cand.assign(geometry=cand.buffer(____)).reset_index(names="cand_id")
           score = gpd.sjoin(old, rings, predicate="within").groupby("cand_id")["old_res"].sum()
           cand["score"] = score.reindex(cand.index, fill_value=0)
           best = cand.loc[cand["score"].idxmax()]
           print(best.geometry, round(best.score))
           ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); cand.plot(ax=ax, column="score", legend=True, markersize=15)
           clinics.plot(ax=ax, color="red", marker="+", markersize=100); plt.show()
           """,
           solution="""
           xmin, ymin, xmax, ymax = nbh.total_bounds
           xs, ys = np.meshgrid(np.arange(xmin + 125, xmax, 250), np.arange(ymin + 125, ymax, 250))
           cand = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs.ravel(), ys.ravel()), crs=nbh.crs)
           cand = cand[(cand.distance(clinics.union_all()) > 1000) & ~cand.within(flood.union_all())].reset_index(drop=True)
           old = houses.merge(nbh[["nb_id", "pct_over65"]], on="nb_id")
           old["old_res"] = old["residents"] * old["pct_over65"] / 100
           rings = cand.assign(geometry=cand.buffer(800)).reset_index(names="cand_id")
           score = gpd.sjoin(old, rings, predicate="within").groupby("cand_id")["old_res"].sum()
           cand["score"] = score.reindex(cand.index, fill_value=0)
           best = cand.loc[cand["score"].idxmax()]
           print(best.geometry, round(best.score))
           ax = nbh.boundary.plot(color="grey", figsize=(5, 5)); cand.plot(ax=ax, column="score", legend=True, markersize=15)
           clinics.plot(ax=ax, color="red", marker="+", markersize=100); plt.show()
           """,
           answer="Hard rules remove sites (constraints); a score ranks the rest (the objective). This is the basic structure of every site-selection study.",
           why="In real projects you also add land availability, price and access by public transport, and you test how the result changes if you change a threshold (sensitivity analysis).")
    nb.pro("4.6", "When and where do accidents happen?", "Temporal (+ descriptive)",
           scenario="At which hour do most accidents happen? Are **serious and fatal** accidents more common at night (20:00–05:59) than by day?",
           plan_hint="`accidents[\"hour\"].value_counts().idxmax()`. Make a column `night = (hour >= 20) | (hour < 6)`. Then `pd.crosstab(night, severity, normalize=\"index\")` — shares per row.",
           starter="""
           print("peak hour:", accidents["hour"].value_counts().____())
           accidents["night"] = (accidents["hour"] >= 20) | (accidents["hour"] < ____)
           accidents["month"] = pd.to_datetime(accidents["date"]).dt.month
           print(pd.crosstab(accidents["night"], accidents["severity"], normalize="index").round(2))
           accidents.groupby("month").size().plot(kind="bar", title="accidents per month"); plt.show()
           """,
           solution="""
           print("peak hour:", accidents["hour"].value_counts().idxmax())
           accidents["night"] = (accidents["hour"] >= 20) | (accidents["hour"] < 6)
           accidents["month"] = pd.to_datetime(accidents["date"]).dt.month
           print(pd.crosstab(accidents["night"], accidents["severity"], normalize="index").round(2))
           accidents.groupby("month").size().plot(kind="bar", title="accidents per month"); plt.show()
           """,
           answer="Temporal questions use the same `groupby` tools on time columns. With few night accidents the shares are unstable: say how many cases each share is based on.")

    # ---------------------------------------------------------------- test
    nb.test("""
    The layers from above are loaded (`nbh`, `houses`, `schools`, `clinics`, `accidents`, `roads`, `parks`, `river`, `flood`, `shops`).
    For every question: **question type → plan in words → code → one sentence of interpretation → your main assumption.**
    """, [
        ("task", """
        **A · Shops.** Riverton wants to know which neighbourhood has **no pharmacy** and how many residents live there.
        """, """
        Type: descriptive (spatial join + missing values).
        ```python
        ph = shops[shops["kind"] == "pharmacy"]
        with_ph = gpd.sjoin(ph, nbh[["name", "geometry"]], predicate="within")["name"].unique()
        print(nbh.loc[~nbh["name"].isin(with_ph), ["name", "population"]])
        ```
        Assumption: people only use a pharmacy inside their own neighbourhood (in reality they cross borders — a distance-based check is better).
        """),
        ("task", """
        **B · Parks.** Rank neighbourhoods by **park area per resident** (m² per person).
        """, """
        Type: overlay + measurement.
        ```python
        p = gpd.overlay(nbh[["name", "population", "geometry"]], parks, how="intersection")
        per = p.assign(m2=p.area).groupby("name")["m2"].sum() / nbh.set_index("name")["population"]
        print(per.fillna(0).sort_values(ascending=False).round(1))
        ```
        """),
        ("task", """
        **C · Roads.** How many accidents happened within **50 m** of each named road? (An accident can count for two roads at a crossing.)
        """, """
        Type: proximity (buffer + join).
        ```python
        rb = roads[["name", "geometry"]].assign(geometry=roads.buffer(50))
        print(gpd.sjoin(accidents, rb, predicate="within")["name"].value_counts())
        ```
        """),
        ("task", """
        **D · Report.** Produce one layer with, per neighbourhood: population, accidents per 1000 residents, share served by a clinic, and flooded hectares. Save it to a GeoPackage.
        """, """
        Type: data integration (several joins).
        ```python
        fl = pieces.groupby("name")["flood_ha"].sum()
        report = nbh[["name", "population", "acc_per_1000", "share_clinic_800m", "geometry"]].copy()
        report["flood_ha"] = report["name"].map(fl).fillna(0)
        report.to_file(DATA_DIR / "my_results.gpkg", layer="riverton_report", driver="GPKG")
        report.drop(columns="geometry").round(2)
        ```
        """),
        ("stat", """
        **E · Statistics.** A councillor says: *"Richer neighbourhoods have fewer accidents."* Test it with the 9 neighbourhoods. What is your conclusion, and what are the limits?
        """, """
        ```python
        print(nbh[["median_income", "acc_per_1000"]].corr(method="spearman").iloc[0, 1].round(2))
        ```
        Compute a rank correlation (Spearman, robust with small samples). With only **9 areas**, even a strong-looking correlation can be chance, and the result depends on how the borders are drawn
        (the *Modifiable Areal Unit Problem*, MAUP). Also, correlation is not cause: rich areas may simply have fewer main roads.
        Recommendation: say "we cannot conclude this from 9 areas", and test at the accident/road level instead.
        """),
        ("model", """
        **F · Modelling heat.** The city wants to find **heat-vulnerable** places in summer. Which layers would you combine, and how would you model 'vulnerability' geographically?
        """, """
        A common model: **vulnerability = exposure × sensitivity ÷ capacity to cope.**
        - Exposure: little green space / far from parks (distance to parks, park share from overlay), later land-surface temperature from satellites (A5).
        - Sensitivity: share over 65 (`pct_over65`), density.
        - Coping capacity: income, distance to clinics.
        Steps: compute each indicator per neighbourhood (or per 250 m grid cell), rescale 0–1, combine with weights, map the result, then test how the ranking changes if the weights change.
        Recommendation: use a grid rather than neighbourhoods, because heat varies inside a neighbourhood.
        """),
        ("model", """
        **G · Modelling school catchments.** Your 'nearest school' model (4.4) gives Oak Primary too many children. Propose two ways to model catchments more realistically.
        """, """
        1. **Capacity-constrained allocation:** assign houses to the nearest school *with free places*; if full, the next nearest (a location-allocation problem).
        2. **Network distance:** use walking routes (OSMnx / pgRouting) instead of straight lines — the river and bridges change who is 'nearest'.
        3. (Bonus) **Voronoi polygons** of schools (`schools.voronoi_polygons()`) show the pure nearest-school areas, useful to communicate the simple model.
        Recommendation: 2 first (the river is a real barrier in Riverton), then 1.
        """),
    ])
    nb.reflect("""
    1. Which question **type** is most important in your own work (e.g. PhD on urban space)? Write one question of that type about your study area.
    2. Which data would you need, and which GeoPandas steps (in order) would you use?
    """)
    return nb
