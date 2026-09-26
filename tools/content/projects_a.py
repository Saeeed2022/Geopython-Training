"""End-of-notebook projects for group A."""
from nbbuild import SETUP

PSETUP = '''
from geotrain.projects import build_projects, PROJ_DIR, publish
build_projects()                      # writes data/projects/ the first time
print(sorted(p.name for p in PROJ_DIR.iterdir()))
'''

PG_NOTE = ("**Database note:** the last task publishes your result to PostGIS with `publish()` (a small helper around "
           "`to_postgis`, explained in B4). The database is the one you started in `00_START_HERE`. If it is not running yet, "
           "skip that code and open the saved GeoPackage in QGIS instead.")


def p_a1(nb):
    nb.project(
        "Tram line A or B? A Shapely study",
        f"""Riverton must choose between two tram lines. Option A runs diagonally south-west → north-east (€310 million),
        option B runs north-south and then north-west (€240 million). Compare them with **Shapely only**: length, stops,
        residents and schools served, river crossings (each needs a bridge), and cost per resident served. Then write a recommendation. {PG_NOTE}""",
        [("tram.gpkg", "two proposed lines: `option` (A/B), `cost_million_eur`"),
         ("riverton.gpkg → houses, river, schools", "the Riverton layers you know")],
        [("""**Length and cost.** Length of each option in km and cost per km.""", """
          ```python
          for opt, line in lines.items():
              print(opt, round(line.length / 1000, 2), "km,", round(cost[opt] / (line.length / 1000), 1), "M€/km")
          ```
          """),
         ("""**Stops.** Place a stop every **500 m** along each line (include the start). How many stops per option?""", """
          ```python
          stops = {opt: [line.interpolate(d) for d in np.arange(0, line.length + 1, 500)] for opt, line in lines.items()}
          print({opt: len(s) for opt, s in stops.items()})
          ```
          """),
         ("""**Who is served?** Residents living within **400 m** of any stop (melt the circles with `union_all` so nobody counts twice). Cost per resident served?""", """
          ```python
          served = {}
          for opt, s in stops.items():
              zone = shapely.union_all([p.buffer(400) for p in s])
              served[opt] = int(residents[shapely.within(houses, zone)].sum())
          print(served, {opt: round(cost[opt] * 1e6 / served[opt]) for opt in served}, "€ per resident")
          ```
          """),
         ("""**Bridges and schools.** How many times does each line cross the river? How many schools lie within 400 m of a stop?""", """
          ```python
          schools = gpd.read_file(GPKG, layer="schools")
          for opt, line in lines.items():
              cross = line.intersection(river)
              n_cross = len(getattr(cross, "geoms", [cross])) if not cross.is_empty else 0
              zone = shapely.union_all([p.buffer(400) for p in stops[opt]])
              print(opt, "river crossings:", n_cross, "| schools served:", int(shapely.within(schools.geometry.values, zone).sum()))
          ```
          """),
         ("""**Save and publish** the stops and the 400 m catchments of both options as layers (GeoPackage + PostGIS schema `projects`).""", """
          ```python
          st = gpd.GeoDataFrame([{"option": o, "stop_no": i + 1, "geometry": p} for o, s in stops.items() for i, p in enumerate(s)], crs=32633)
          ca = gpd.GeoDataFrame([{"option": o, "residents": served[o], "geometry": shapely.union_all([p.buffer(400) for p in s])}
                                 for o, s in stops.items()], crs=32633)
          st.to_file(PROJ_DIR / "a1_tram_result.gpkg", layer="stops"); ca.to_file(PROJ_DIR / "a1_tram_result.gpkg", layer="catchments")
          publish({"tram_lines": tram, "tram_stops": st, "tram_catchments": ca})
          ```
          **Recommendation (example):** choose the option with the lower cost per resident served, unless it needs more bridges (extra cost and risk). State the assumptions: 400 m walking circle, 500 m stop spacing, straight-line distance.
          """)],
        setup=PSETUP + '''
tram = gpd.read_file(PROJ_DIR / "tram.gpkg")
lines = dict(zip(tram["option"], tram.geometry))          # {"A": LineString, "B": LineString}
cost = dict(zip(tram["option"], tram["cost_million_eur"]))
''',
        qgis="""
        1. Drag `data/projects/a1_tram_result.gpkg` into QGIS (or, after connecting, **geotrain → projects → tram_stops / tram_catchments**).
        2. Style `tram_catchments` by `option` (*Categorized*), 50 % transparent; show `tram_stops` as small squares; add `houses` from `riverton.gpkg`.
        3. Use the **Identify** tool on a catchment to read its `residents`.
        4. Make a print layout (*Project → New Print Layout*) with a title, legend and scale bar: your one-page recommendation map.
        """,
        deliver=["Table: length, stops, residents served, schools, river crossings, cost per resident for A and B",
                 "Layers `tram_stops` and `tram_catchments` (GeoPackage and PostGIS)", "One-page map + 3-sentence recommendation"])


def p_a2(nb):
    nb.project(
        "Cyclists' GPS tracks: from degrees to real distances",
        f"""Five volunteers recorded their morning bike rides with a phone app (one point every 10 s, in WGS84 lon/lat).
        The city wants each ride's length, duration and speed, a check of how wrong the numbers would be in the wrong CRS,
        and the tracks on a map. Use **PyProj** for all coordinate work. {PG_NOTE}""",
        [("gps_tracks.csv", "columns `track_id`, `time`, `lon`, `lat` (EPSG:4326)")],
        [("""**First look.** Number of points, start time and duration (minutes) per track.""", """
          ```python
          summary = gps.groupby("track_id").agg(points=("lon", "size"), start=("time", "min"), end=("time", "max"))
          summary["minutes"] = (summary["end"] - summary["start"]).dt.total_seconds() / 60
          summary
          ```
          """),
         ("""**Length and speed in UTM.** Transform to EPSG:32633 (`always_xy=True`), sum the segment lengths with Pythagoras, and compute the mean speed in km/h.""", """
          ```python
          to_utm = Transformer.from_crs(4326, 32633, always_xy=True)
          gps["x"], gps["y"] = to_utm.transform(gps["lon"].values, gps["lat"].values)
          def length_m(g):
              return float(np.hypot(np.diff(g["x"]), np.diff(g["y"])).sum())
          summary["km_utm"] = gps.groupby("track_id").apply(length_m, include_groups=False) / 1000
          summary["kmh"] = summary["km_utm"] / (summary["minutes"] / 60)
          summary[["km_utm", "minutes", "kmh"]].round(2)
          ```
          GPS noise (a few metres per point) makes zig-zags, so tracks look slightly longer than the real route.
          """),
         ("""**Check with the ellipsoid.** Compute each track's length with `Geod.line_length(lons, lats)` and compare with UTM (difference in metres).""", """
          ```python
          geod = Geod(ellps="WGS84")
          summary["km_geod"] = gps.groupby("track_id").apply(lambda g: geod.line_length(g["lon"], g["lat"]), include_groups=False) / 1000
          summary["diff_m"] = (summary["km_utm"] - summary["km_geod"]) * 1000
          summary[["km_utm", "km_geod", "diff_m"]].round(3)
          ```
          A few metres on several km: UTM is fine locally.
          """),
         ("""**The wrong CRS.** Compute the lengths in Web Mercator (EPSG:3857). By what factor are they too long? Compare with the theory 1/cos(latitude).""", """
          ```python
          to_merc = Transformer.from_crs(4326, 3857, always_xy=True)
          mx, my = to_merc.transform(gps["lon"].values, gps["lat"].values)
          gps["mx"], gps["my"] = mx, my
          km_merc = gps.groupby("track_id").apply(lambda g: np.hypot(np.diff(g["mx"]), np.diff(g["my"])).sum(), include_groups=False) / 1000
          print((km_merc / summary["km_utm"]).round(3).tolist(), "theory:", round(1 / math.cos(math.radians(gps["lat"].mean())), 3))
          ```
          """),
         ("""**Tracks as lines, which cross the river?** Build one LineString per track (UTM), test `intersects` with the river, and publish lines and points.""", """
          ```python
          from shapely import LineString as LS
          import geopandas as gpd
          river_line = gpd.read_file(GPKG, layer="river").geometry.iloc[0]
          tracks = gpd.GeoDataFrame([{"track_id": t, "km": round(summary.loc[t, "km_utm"], 2), "kmh": round(summary.loc[t, "kmh"], 1),
                                      "geometry": LS(list(zip(g["x"], g["y"])))} for t, g in gps.groupby("track_id")], crs=32633)
          tracks["crosses_river"] = tracks.intersects(river_line)
          points = gpd.GeoDataFrame(gps[["track_id", "time"]], geometry=gpd.points_from_xy(gps["x"], gps["y"]), crs=32633)
          tracks.to_file(PROJ_DIR / "a2_tracks.gpkg", layer="tracks"); points.to_file(PROJ_DIR / "a2_tracks.gpkg", layer="points")
          publish({"gps_tracks": tracks, "gps_points": points})
          tracks.drop(columns="geometry")
          ```
          """)],
        setup=SETUP + PSETUP + '''
import numpy as np, pandas as pd, math
gps = pd.read_csv(PROJ_DIR / "gps_tracks.csv", parse_dates=["time"])
gps.head()
''',
        qgis="""
        1. Load `gps_tracks` and `gps_points` (PostGIS schema `projects`, or `a2_tracks.gpkg`).
        2. Style `gps_tracks` by `track_id` (*Categorized*), line width 1 mm; label with `kmh`.
        3. **Animate the rides:** open `gps_points` → *Layer Properties → Temporal* → tick *Dynamic Temporal Control*,
           configuration *Single Field with Date/Time* = `time`. Then *View → Panels → Temporal Controller* → press ▶.
        4. Set the project CRS to EPSG:3857 and use the *Measure Line* tool on a track: QGIS measures on the ellipsoid by default — compare with your numbers.
        """,
        deliver=["Table per track: points, minutes, km (UTM and ellipsoid), km/h, crosses river", "Explanation (2 sentences) of the Web Mercator error",
                 "QGIS animation (screenshot) of the rides"])


def p_a3(nb):
    nb.project(
        "Green-space access audit (buildings × parks × tracts)",
        f"""The WHO recommends that everyone lives within **300 m** of a green space. Riverton now has **building footprints** and
        **36 census tracts**. Audit green-space access: which buildings, tracts and neighbourhoods are badly served, and where
        would one new pocket park help most? Use **GeoPandas**. {PG_NOTE}""",
        [("buildings.gpkg", "~1 700 footprints: `use`, `floors`, `year_built`, `residents` (0 for non-residential)"),
         ("tracts.gpkg", "36 tracts of 1 km²: population, income, % over 65, asthma cases"),
         ("riverton.gpkg → parks, neighbourhoods", "parks and neighbourhoods")],
        [("""**Know the buildings.** How many buildings per `use`? Total residents? Built-up share (footprint area ÷ land area) per neighbourhood?""", """
          ```python
          print(bld["use"].value_counts(), bld["residents"].sum())
          fp = gpd.overlay(bld[["geometry"]], nbh[["name", "geometry"]], how="intersection")
          (fp.assign(a=fp.area).groupby("name")["a"].sum() / nbh.set_index("name").area * 100).round(2).sort_values()
          ```
          """),
         ("""**Distance to the nearest park** for every residential building (`sjoin_nearest`, `distance_col`). Share of residents within 300 m, per neighbourhood.""", """
          ```python
          res = bld[bld["residents"] > 0]
          near = gpd.sjoin_nearest(res, parks[["park", "geometry"]], distance_col="dist_park").drop_duplicates("bldg_id")
          near["ok"] = near["dist_park"] <= 300
          share = (near["residents"] * near["ok"]).groupby(near["nb_id"]).sum() / near.groupby("nb_id")["residents"].sum()
          nbh.assign(share_300m=nbh["nb_id"].map(share).fillna(0))[["name", "share_300m"]].round(2).sort_values("share_300m")
          ```
          """),
         ("""**Per tract:** share of residents within 300 m of a park, and park area (m²) per resident. Which 3 tracts are worst?""", """
          ```python
          cent = near.assign(geometry=near.centroid)[["residents", "ok", "geometry"]]
          j = gpd.sjoin(cent, tracts[["tract_id", "geometry"]], predicate="within")
          t_share = (j["residents"] * j["ok"]).groupby(j["tract_id"]).sum() / j.groupby("tract_id")["residents"].sum()
          pk = gpd.overlay(tracts[["tract_id", "geometry"]], parks, how="intersection")
          tracts["share_300m"] = tracts["tract_id"].map(t_share).fillna(0)
          tracts["park_m2_per_res"] = tracts["tract_id"].map(pk.assign(a=pk.area).groupby("tract_id")["a"].sum()).fillna(0) / tracts["population"].clip(lower=1)
          tracts.nsmallest(3, "share_300m")[["tract_id", "population", "share_300m", "park_m2_per_res"]].round(2)
          ```
          """),
         ("""**Model a pocket park.** Put a 1 ha round park (radius ≈ 56 m) at the centroid of each of the 3 worst tracts. How many **additional** residents would be within 300 m? Which location is best?""", """
          ```python
          worst = tracts.nsmallest(3, "share_300m")
          gain = {}
          for _, t in worst.iterrows():
              new_park = t.geometry.centroid.buffer(56)
              newly = near[(~near["ok"]) & (near.distance(new_park) <= 300)]
              gain[t["tract_id"]] = int(newly["residents"].sum())
          print(gain, "-> best:", max(gain, key=gain.get))
          ```
          A simple **what-if model**: change one input (a new park), re-run the indicator, compare. The centroid is only a first guess; real sites depend on free land.
          """),
         ("""**Publish** the residential buildings with `dist_park` and the tracts with the new indicators to PostGIS (schema `projects`).""", """
          ```python
          publish({"green_buildings": near[["bldg_id", "residents", "dist_park", "ok", "geometry"]], "green_tracts": tracts})
          near.to_file(PROJ_DIR / "a3_green.gpkg", layer="buildings"); tracts.to_file(PROJ_DIR / "a3_green.gpkg", layer="tracts")
          ```
          """)],
        setup=PSETUP + '''
bld = gpd.read_file(PROJ_DIR / "buildings.gpkg")
tracts = gpd.read_file(PROJ_DIR / "tracts.gpkg")
parks = gpd.read_file(GPKG, layer="parks")
nbh = gpd.read_file(GPKG, layer="neighbourhoods")
''',
        qgis="""
        1. Load `green_buildings` and `green_tracts` from **geotrain → projects**, plus `parks` (from `riverton.gpkg`).
        2. Style `green_buildings` with a *Graduated* colour on `dist_park` (breaks 0–150–300–600–max, green → red).
        3. Style `green_tracts` by `share_300m`; add labels with the expression `round("share_300m" * 100) || ' %'`.
        4. Use *Processing → Buffer* on `parks` (300 m) to check your numbers visually.
        """,
        deliver=["Tables: share within 300 m per neighbourhood and tract", "Pocket-park what-if result with the best location",
                 "Layers in PostGIS + QGIS map"])


def p_a4(nb):
    nb.project(
        "Clean a messy data delivery",
        f"""A contractor delivered four files about street furniture. Each one has a typical problem: a missing CRS, a broken polygon,
        duplicates and empty geometries, swapped lon/lat, and a wrong CRS label. Inspect with **Pyogrio**, clean with GeoPandas,
        and deliver **one clean GeoPackage** (EPSG:32633) + PostGIS tables. {PG_NOTE}""",
        [("delivery/playgrounds.shp", "13 playground polygons — no `.prj` file (CRS unknown). The contractor says: 'it is UTM 33N'."),
         ("delivery/benches.geojson", "benches in WGS84 — with duplicates and one empty geometry"),
         ("delivery/trees.csv", "trees with lon/lat — some rows have lon and lat swapped"),
         ("delivery/bins.gpkg", "litter bins — labelled EPSG:4326, but the numbers look like metres")],
        [("""**Inventory.** For every file, show CRS, feature count, geometry type and bounds (`pyogrio.read_info`). Which problems can you already see?""", """
          ```python
          rows = []
          for f in ["playgrounds.shp", "benches.geojson", "bins.gpkg"]:
              i = pyogrio.read_info(DEL / f)
              rows.append({"file": f, "crs": i["crs"], "features": i["features"], "type": i["geometry_type"], "bounds": tuple(round(b) for b in i["total_bounds"])})
          pd.DataFrame(rows)
          ```
          Playgrounds: CRS `None`. Bins: CRS 4326 but bounds like 390 000 → impossible for degrees.
          """),
         ("""**Playgrounds:** set the CRS (EPSG:32633), find and repair invalid polygons.""", """
          ```python
          import shapely
          play = pyogrio.read_dataframe(DEL / "playgrounds.shp").set_crs(32633)
          print("invalid:", (~play.is_valid).sum())
          play["geometry"] = shapely.make_valid(play.geometry.values)
          print("invalid after:", (~play.is_valid).sum())
          ```
          """),
         ("""**Benches:** drop empty geometries and exact duplicates, then reproject to EPSG:32633.""", """
          ```python
          ben = pyogrio.read_dataframe(DEL / "benches.geojson")
          n0 = len(ben)
          ben = ben[~ben.is_empty & ben.geometry.notna()]
          ben = ben[~ben.assign(w=ben.geometry.to_wkb()).duplicated(["bench_id", "w"])].to_crs(32633)
          print(n0, "->", len(ben))
          ```
          """),
         ("""**Trees:** detect swapped rows (Riverton's latitude ≈ 52.5, longitude ≈ 13.4), fix them, and build points.""", """
          ```python
          trees = pd.read_csv(DEL / "trees.csv")
          swapped = trees["lon"] > trees["lat"]
          print("swapped rows:", swapped.sum())
          trees.loc[swapped, ["lon", "lat"]] = trees.loc[swapped, ["lat", "lon"]].values
          trees = gpd.GeoDataFrame(trees, geometry=gpd.points_from_xy(trees.lon, trees.lat), crs=4326).to_crs(32633)
          print(trees.total_bounds.round())
          ```
          """),
         ("""**Bins:** the label is wrong, the numbers are right → **override** the CRS (do not transform!). Then write all four clean layers to one GeoPackage, check it, and publish.""", """
          ```python
          bins = pyogrio.read_dataframe(DEL / "bins.gpkg").set_crs(32633, allow_override=True)
          clean = PROJ_DIR / "a4_street_furniture_clean.gpkg"
          clean.unlink(missing_ok=True)
          for name, g in {"playgrounds": play, "benches": ben, "trees": trees, "bins": bins}.items():
              pyogrio.write_dataframe(g, clean, layer=name)
          print(pyogrio.list_layers(clean))
          publish({"furniture_playgrounds": play, "furniture_benches": ben, "furniture_trees": trees, "furniture_bins": bins})
          ```
          Key lesson: `set_crs(allow_override=True)` **re-labels**; `to_crs` **transforms**. Using the wrong one moves your data to the wrong continent.
          """)],
        setup=PSETUP + '''
import pandas as pd
import geopandas as gpd
DEL = PROJ_DIR / "delivery"
print(sorted(p.name for p in DEL.iterdir()))
''',
        qgis="""
        1. First drag the **raw** `delivery/playgrounds.shp` into QGIS: QGIS asks for / guesses a CRS — see why a missing `.prj` is dangerous.
        2. Drag the raw `bins.gpkg`: it lands far outside the map (it believes the metres are degrees). Remove it.
        3. Load the clean layers from **geotrain → projects** (`furniture_*`) or from the clean GeoPackage: all four sit in Riverton.
        4. Run *Vector → Geometry Tools → Check Validity* on the clean playgrounds: no errors.
        """,
        deliver=["Inventory table with the problem of each file", "Clean GeoPackage with 4 layers in EPSG:32633",
                 "Short cleaning report (what you changed and why) for the contractor"])


def p_a6(nb):
    nb.project(
        "Asthma in Riverton's tracts: cluster and cause?",
        f"""A health survey counted asthma cases in 36 census tracts. The health department asks: is asthma **clustered**, where are the
        hot spots, and is it linked to **traffic pollution** (NO₂) and **income**? Use **PySAL**. {PG_NOTE}""",
        [("tracts.gpkg", "36 tracts: `population`, `asthma_cases`, `median_income`, `pct_over65`, `no2_ugm3` (traffic pollution), `dist_main_road_m`")],
        [("""**Rates and a map.** Asthma cases per 1 000 residents; map with natural breaks.""", """
          ```python
          tr["rate"] = tr["asthma_cases"] / tr["population"] * 1000
          tr.plot(column="rate", scheme="NaturalBreaks", k=5, cmap="Reds", legend=True, edgecolor="white", figsize=(5, 5)); plt.show()
          tr["rate"].describe().round(1)
          ```
          """),
         ("""**Global clustering.** Queen weights (row-standardised) and Moran's I of the rate.""", """
          ```python
          wt = weights.Queen.from_dataframe(tr, use_index=False); wt.transform = "r"
          mt = esda.Moran(tr["rate"], wt)
          print(f"I = {mt.I:.3f}, p = {mt.p_sim}")
          ```
          """),
         ("""**Where?** Local Moran (LISA): label each tract HH / LL / LH / HL / not significant (p < 0.05). List the HH tracts.""", """
          ```python
          lt = esda.Moran_Local(tr["rate"], wt, seed=1)
          lab = {1: "HH", 2: "LH", 3: "LL", 4: "HL"}
          tr["lisa"] = [lab[q] if p < 0.05 else "ns" for q, p in zip(lt.q, lt.p_sim)]
          print(tr["lisa"].value_counts()); tr.loc[tr.lisa == "HH", ["tract_id", "rate", "no2_ugm3"]]
          ```
          """),
         ("""**Why?** OLS: rate ~ NO₂ + income. Are the residuals spatially clustered (Moran's I of residuals)? Interpret the signs of the coefficients.""", """
          ```python
          y = tr[["rate"]].values; X = tr[["no2_ugm3", "median_income"]].values
          ols_t = spreg.OLS(y, X, w=wt, moran=True, spat_diag=True, name_y="rate", name_x=["no2_ugm3", "median_income"])
          print("betas:", ols_t.betas.ravel().round(5), "| R²:", round(ols_t.r2, 2), "| residual Moran p:", round(ols_t.moran_res[2], 3))
          ```
          Positive coefficient on NO₂ = more asthma where the air is dirtier; negative on income = more asthma in poorer tracts.
          The rates are clustered, but the **residuals** are not: the two variables explain the spatial pattern, so OLS is acceptable here.
          Caution: tract-level results do not prove anything about individuals (**ecological fallacy**).
          """),
         ("""**Publish** the tracts with rate and LISA label to PostGIS for the health department.""", """
          ```python
          publish({"asthma_tracts": tr})
          tr.to_file(PROJ_DIR / "a6_asthma.gpkg", layer="tracts")
          ```
          """)],
        setup=PSETUP + '''
tr = gpd.read_file(PROJ_DIR / "tracts.gpkg")
''',
        qgis="""
        1. Load `asthma_tracts` from **geotrain → projects**.
        2. *Categorized* style on `lisa` with the classic LISA colours: HH red, LL blue, LH light blue, HL pink, ns grey.
        3. Add `roads` from `riverton.gpkg` on top, and label tracts with `no2_ugm3`: do the HH tracts sit in the busy, polluted centre?
        4. Optional: QGIS has no built-in Moran's I, but the plugin *Hotspot Analysis* uses PySAL — compare its result with yours.
        """,
        deliver=["Rate map + Moran's I with interpretation", "LISA map and list of hot-spot tracts", "Regression table with 3-sentence interpretation and limits"])


def p_a5(nb):
    nb.project(
        "Urban heat: who suffers on a hot afternoon?",
        f"""A satellite measured **land-surface temperature (LST)** on a hot summer afternoon. Find the hottest places, test whether parks
        and the river cool their surroundings, and identify tracts where **heat and old age** meet. Use **Rasterio** (+ GeoPandas). {PG_NOTE}""",
        [("lst.tif", "land-surface temperature (°C), 50 m pixels, EPSG:32633"),
         ("buildings.gpkg, tracts.gpkg", "residents per building; % over 65 per tract"),
         ("riverton.gpkg → parks", "parks")],
        [("""**Look at the heat.** Min, mean, max LST; the temperature above which the hottest 10 % of cells lie; map.""", """
          ```python
          print(round(float(lst.min()), 1), round(float(lst.mean()), 1), round(float(lst.max()), 1))
          hot = float(np.percentile(lst.compressed(), 90)); print("hottest 10 % above", round(hot, 1), "°C")
          show(lst_src, cmap="inferno"); plt.show()
          ```
          """),
         ("""**Residents exposed.** Sample LST at every residential building (centroid). How many residents live in the hottest 10 % of cells?""", """
          ```python
          res = bld[bld.residents > 0].copy()
          c = res.centroid
          res["lst"] = [v[0] for v in lst_src.sample(list(zip(c.x, c.y)))]
          print(int(res.loc[res.lst >= hot, "residents"].sum()), "of", int(res.residents.sum()), "residents")
          ```
          """),
         ("""**Do parks cool?** Mean LST inside parks, in a 0–200 m ring around them, and elsewhere.""", """
          ```python
          from rasterio.mask import mask
          allp = parks.union_all()
          ring = allp.buffer(200).difference(allp)
          inside = mask(lst_src, [allp], filled=False)[0].mean()
          near_ = mask(lst_src, [ring], filled=False)[0].mean()
          rest = mask(lst_src, [allp.buffer(200)], invert=True, filled=False)[0].mean()
          print(f"parks {inside:.1f} °C | 0–200 m ring {near_:.1f} °C | elsewhere {rest:.1f} °C")
          ```
          """),
         ("""**Heat × age.** Mean LST per tract (zonal statistics). Which tracts are in the top third for **both** LST and % over 65?""", """
          ```python
          tr["lst_mean"] = [float(mask(lst_src, [g], crop=True, filled=False)[0].mean()) for g in tr.geometry]
          both = tr[(tr.lst_mean >= tr.lst_mean.quantile(2 / 3)) & (tr.pct_over65 >= tr.pct_over65.quantile(2 / 3))]
          both[["tract_id", "lst_mean", "pct_over65", "population"]].round(1)
          ```
          """),
         ("""**Publish** the tracts (with `lst_mean`) as a table and the LST raster into PostGIS (raster via GDAL, as in B1).""", """
          ```python
          publish({"heat_tracts": tr})
          from geotrain.db import connect
          with connect() as conn:
              conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster")
              conn.execute("SET postgis.gdal_enabled_drivers = 'GTiff'")
              conn.execute("DROP TABLE IF EXISTS projects.lst")
              conn.execute("CREATE TABLE projects.lst AS SELECT 1 AS rid, ST_FromGDALRaster(%s) AS rast", [(PROJ_DIR / "lst.tif").read_bytes()])
              conn.commit()
              print(conn.execute("SELECT ST_Width(rast), ST_SRID(rast) FROM projects.lst").fetchone())
          ```
          """)],
        setup=PSETUP + '''
import rasterio
lst_src = rasterio.open(PROJ_DIR / "lst.tif")
lst = lst_src.read(1, masked=True)
bld = gpd.read_file(PROJ_DIR / "buildings.gpkg")
tr = gpd.read_file(PROJ_DIR / "tracts.gpkg")
parks = gpd.read_file(GPKG, layer="parks")
''',
        qgis="""
        1. Drag `data/projects/lst.tif` into QGIS; *Symbology → Singleband pseudocolor*, colour ramp *Inferno*.
        2. PostGIS raster: in the Browser, **geotrain → projects → lst** also appears as a raster layer (QGIS reads rasters from PostGIS).
        3. Load `heat_tracts` and label with `round("lst_mean", 1)`.
        4. Use *Raster → Raster Calculator*: `"lst@1" > 36` to make a 'very hot' mask, and compare with your 90 % threshold.
        """,
        deliver=["Hot-cell threshold and residents exposed", "Park cooling table (inside / ring / elsewhere)",
                 "List of heat × age tracts", "LST raster and tracts in PostGIS, QGIS map"])
