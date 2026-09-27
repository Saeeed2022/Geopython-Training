"""End-of-notebook projects for group D (desktop GIS engines)."""

PSETUP = '''
from geotrain.projects import build_projects, PROJ_DIR, publish
build_projects()
P = lambda name, layer=None: f"{PROJ_DIR / name}" + (f"|layername={layer}" if layer else "")
'''


def p_d1(nb):
    nb.project(
        "Fire-engine response times on the street network",
        """Riverton has one fire station. The fire brigade's target: reach every building within **4 minutes** of driving.
        Using the new **street network** (with speeds and only 3 bridges over the river), compute the 2- and 4-minute service areas
        with QGIS's network tools, find the buildings outside the 4-minute area, and test three candidate sites for a second station.""",
        [("streets.gpkg", "1 172 segments: `speed_kmh` (50 main / 30 local), `bridge`"),
         ("fire_stations.gpkg", "the current station"), ("buildings.gpkg", "~1 700 buildings with residents")],
        [("""**Service areas.** With `native:serviceareafromlayer`, *fastest* path (`STRATEGY=1`), speed from `speed_kmh`: which streets are reachable in **2** and in **4 minutes**? (Travel cost for 'fastest' is in **hours**: 4 min = 4/60.) Report km of street reached (merge the output lines first).""", """
          ```python
          def service(minutes, start, name):
              r = qrun("native:serviceareafromlayer", _project=minimal_project(), INPUT=P("streets.gpkg"), STRATEGY=1,
                       SPEED_FIELD="speed_kmh", DEFAULT_SPEED=30, DEFAULT_DIRECTION=2, TOLERANCE=1,
                       START_POINTS=start, TRAVEL_COST2=minutes / 60, OUTPUT_LINES=str(OUT / f"{name}.gpkg"))
              return gpd.read_file(r["OUTPUT_LINES"]).dissolve()
          sa2, sa4 = service(2, P("fire_stations.gpkg"), "fire_2min"), service(4, P("fire_stations.gpkg"), "fire_4min")
          print("km reached: 2 min", round(sa2.length.sum() / 1000, 1), "| 4 min", round(sa4.length.sum() / 1000, 1),
                "| whole network", round(streets.length.sum() / 1000, 1))
          ```
          """),
         ("""**Covered buildings.** A building is covered if it lies within **50 m** of a reachable street. Share of residents covered in 4 minutes?""", """
          ```python
          bld["covered4"] = bld.distance(sa4.geometry.iloc[0]) <= 50
          res = bld[bld.residents > 0]
          print(f"{res.loc[res.covered4, 'residents'].sum() / res.residents.sum():.1%} of residents covered in 4 min")
          ```
          """),
         ("""**The river effect.** The station is south of the river. What **share** of residents is uncovered north vs south of the river? (Build a polygon 'north of the river line' and test `within`.) Compare shares, not counts — the two sides have different populations.""", """
          ```python
          import numpy as np
          from shapely.geometry import Polygon
          xs = np.array(river.coords)[:, 0]; ys = np.array(river.coords)[:, 1]
          north_poly = Polygon(list(zip(xs, ys)) + [(xs[-1], 5_830_000), (xs[0], 5_830_000)])
          side = np.where(res.within(north_poly), "north", "south")
          out = res.assign(side=side, unc=~res.covered4).groupby("side").apply(
              lambda g: pd.Series({"residents": g.residents.sum(), "uncovered_share": round((g.residents * g.unc).sum() / g.residents.sum(), 2)}), include_groups=False)
          out
          ```
          The far (north) side has the larger uncovered share: with only 3 bridges, engines must detour. That is why a second station north of the river is worth testing next.
          """),
         ("""**Where should station 2 go?** Test three candidates — (391 000, 5 823 000), (394 750, 5 822 500), (393 000, 5 819 000). For each, compute its 4-minute area and the residents **newly** covered (not covered by station 1). Pick the best.""", """
          ```python
          cands = gpd.GeoDataFrame({"cand": ["NW", "NE", "S"]},
                                   geometry=gpd.points_from_xy([391_000, 394_750, 393_000], [5_823_000, 5_822_500, 5_819_000]), crs=32633)
          gain = {}
          for _, c in cands.iterrows():
              f = OUT / f"cand_{c.cand}.gpkg"
              cands[cands.cand == c.cand].to_file(f, layer="c")
              sa = service(4, str(f), f"cand_{c.cand}_4min")
              newly = res[(~res.covered4) & (res.distance(sa.geometry.iloc[0]) <= 50)]
              gain[c.cand] = int(newly.residents.sum())
          print(gain, "-> best:", max(gain, key=gain.get))
          ```
          """),
         ("""**Publish** the 4-minute area, covered/uncovered buildings and the candidates to PostGIS.""", """
          ```python
          publish({"fire_area_4min": sa4, "fire_buildings": bld[["bldg_id", "residents", "covered4", "geometry"]], "fire_candidates": cands})
          ```
          """)],
        setup=PSETUP + '''
import pandas as pd
streets = gpd.read_file(PROJ_DIR / "streets.gpkg")
bld = gpd.read_file(PROJ_DIR / "buildings.gpkg")
river = gpd.read_file(GPKG, layer="river").geometry.iloc[0]
''',
        qgis="""
        1. Load `fire_area_4min`, `fire_buildings` (style: `covered4` true = grey, false = red) and `fire_candidates` from **geotrain → projects**, plus `streets.gpkg` (bridges in thick blue: `"bridge" = true`).
        2. In QGIS itself: *Processing Toolbox → Network analysis → Service area (from point)* — click on a candidate on the map as start point, choose `streets`, *Fastest*, speed field `speed_kmh`, travel cost `0.0667` (4 min). Same result as your script?
        3. Build a **Graphical Model** (*Processing → Graphical Modeler*) with two steps: service area → extract buildings within distance. Save it; it is a clickable version of your script.
        """,
        deliver=["2- and 4-minute service areas and coverage %", "North/south gap analysis", "Best second-station site with numbers", "QGIS map + graphical model (.model3)"])


def p_d2(nb):
    nb.project(
        "An open-data release with GDAL/OGR",
        """Riverton publishes an **open-data package**. Using only GDAL/OGR command-line tools, produce: cloud-optimised rasters
        (elevation, hillshade, temperature), one GeoPackage with the main vector layers, a web GeoJSON, a district extract,
        and the same vectors in a PostGIS schema `opendata` for the city's map server. Then check everything.""",
        [("dem.tif, lst.tif", "elevation and land-surface temperature rasters"),
         ("streets.gpkg, buildings.gpkg, tracts.gpkg", "vector layers"), ("riverton.gpkg → neighbourhoods", "for the district extract")],
        [("""**Rasters as COG.** Write `dem_cog.tif`, `hillshade_cog.tif` (from `gdaldem`) and `lst_cog.tif` into `release/` as Cloud-Optimised GeoTIFFs.""", """
          ```python
          REL.mkdir(exist_ok=True)
          sh(f"gdal_translate -q -of COG {quote(DEM)} {quote(REL / 'dem_cog.tif')}")
          sh(f"gdaldem hillshade -q {quote(DEM)} {quote(OUT / 'hs_tmp.tif')}")
          sh(f"gdal_translate -q -of COG {quote(OUT / 'hs_tmp.tif')} {quote(REL / 'hillshade_cog.tif')}")
          sh(f"gdal_translate -q -of COG {quote(PROJ_DIR / 'lst.tif')} {quote(REL / 'lst_cog.tif')}")
          print(sorted(p.name for p in REL.glob("*.tif")))
          ```
          """),
         ("""**One GeoPackage, three layers.** Put streets, buildings and tracts into `release/riverton_open_data.gpkg` with `ogr2ogr` (first layer creates the file, the next ones use `-update`).""", """
          ```python
          pkg = REL / "riverton_open_data.gpkg"
          pkg.unlink(missing_ok=True)
          for i, name in enumerate(["streets", "buildings", "tracts"]):
              extra = "" if i == 0 else "-update"
              sh(f"ogr2ogr {extra} -f GPKG -nln {name} {quote(pkg)} {quote(PROJ_DIR / (name + '.gpkg'))}")
          sh(f"ogrinfo -so {quote(pkg)}")
          ```
          """),
         ("""**For the web and for one district.** (a) tracts as GeoJSON in EPSG:4326 with only `tract_id`, `population`; (b) the buildings of **Oldtown** only (`-clipsrc` with the neighbourhood).""", """
          ```python
          (REL / "tracts.geojson").unlink(missing_ok=True)
          sh(f"ogr2ogr -f GeoJSON -t_srs EPSG:4326 -select tract_id,population {quote(REL / 'tracts.geojson')} {quote(PROJ_DIR / 'tracts.gpkg')}")
          sh(f\"\"\"ogr2ogr -overwrite -f GPKG {quote(REL / 'oldtown_buildings.gpkg')} {quote(PROJ_DIR / 'buildings.gpkg')} -clipsrc {quote(GPKG)} -clipsrclayer neighbourhoods -clipsrcwhere "name='Oldtown'" \"\"\")
          print(pyogrio.read_info(REL / "oldtown_buildings.gpkg")["features"], "buildings in Oldtown")
          ```
          """),
         ("""**Into PostGIS** schema `opendata` with `ogr2ogr` (`-lco SCHEMA=opendata`), all three layers.""", """
          ```python
          from urllib.parse import urlparse
          from geotrain.db import DSN, sql
          u = urlparse(DSN)
          PGC = f'PG:"host={u.hostname} port={u.port or 5432} user={u.username} password={u.password} dbname={u.path[1:]}"'
          sql("CREATE SCHEMA IF NOT EXISTS opendata")
          for name in ["streets", "buildings", "tracts"]:
              sh(f"ogr2ogr -f PostgreSQL {PGC} {quote(PROJ_DIR / (name + '.gpkg'))} -nln {name} -lco SCHEMA=opendata -lco OVERWRITE=YES -overwrite")
          sql("SELECT f_table_name, type, srid FROM geometry_columns WHERE f_table_schema = 'opendata' ORDER BY 1")
          ```
          """),
         ("""**Release check.** A table with every file in `release/`: size (kB), and feature count or raster size — the 'contents' page of the package.""", """
          ```python
          rows = []
          for f in sorted(REL.iterdir()):
              if f.suffix == ".tif":
                  with rasterio.open(f) as r:
                      rows.append({"file": f.name, "kB": f.stat().st_size // 1024, "content": f"raster {r.width}×{r.height}, {r.crs}"})
              elif f.suffix in (".gpkg", ".geojson"):
                  rows.append({"file": f.name, "kB": f.stat().st_size // 1024,
                               "content": ", ".join(f"{n} ({pyogrio.read_info(f, layer=n)['features']})" for n, _ in pyogrio.list_layers(f))})
          pd.DataFrame(rows)
          ```
          """)],
        setup=PSETUP + '''
import pandas as pd, pyogrio, rasterio
REL = OUT / "release"
''',
        qgis="""
        1. Drag `release/dem_cog.tif` and `hillshade_cog.tif` into QGIS; set the hillshade to *Multiply* blending over the DEM for a nice relief map.
        2. Open `riverton_open_data.gpkg`: QGIS shows its three layers in one dialog.
        3. Load **geotrain → opendata → buildings** from PostGIS: same data, now served by the database.
        4. Check the COG: *Layer Properties → Information* shows overviews and internal tiling — that is what makes COGs fast on the web.
        """,
        deliver=["`release/` folder: 3 COGs, 1 GeoPackage, 1 GeoJSON, 1 district extract", "Schema `opendata` in PostGIS", "Contents table of the package"])


def p_d3(nb):
    nb.project(
        "Storm-water risk per building with GRASS",
        """After a cloudburst, water runs over the ground to low points before it reaches the river. Rate every building's **surface-water
        risk** with GRASS: flow accumulation at the building, drainage basins as polygons, and the connected-flood model (`r.lake`, +3 m).
        Combine them into a risk class and publish it.""",
        [("dem.tif", "elevation"), ("buildings.gpkg", "footprints with residents"), ("riverton.gpkg → river", "the river")],
        [("""**Flow accumulation at each building.** `r.watershed` on the DEM, sample accumulation at building centroids (use absolute values). Which buildings are in the top 5 %?""", """
          ```python
          ws = qrun(grass_alg("r.watershed"), elevation=str(DEM), threshold=400, **{"-s": True},
                    accumulation=str(OUT / "p_acc.tif"), basin=str(OUT / "p_basin.tif"))
          cent = bld.centroid
          with rasterio.open(ws["accumulation"]) as a:
              bld["acc"] = np.abs(np.array([v[0] for v in a.sample(list(zip(cent.x, cent.y)))], dtype=float))
          top = bld["acc"] >= bld["acc"].quantile(0.95)
          print(int(top.sum()), "buildings in the top 5 % of flow accumulation,", int(bld.loc[top, "residents"].sum()), "residents")
          ```
          """),
         ("""**Basins as polygons.** Convert the basin raster to polygons (`r.to.vect`, type area) and count residents per basin.""", """
          ```python
          bv = qrun(grass_alg("r.to.vect"), input=ws["basin"], type=2, output=str(OUT / "p_basins.gpkg"), GRASS_OUTPUT_TYPE_PARAMETER=3)
          basins = gpd.read_file(bv["output"]).dissolve("value").reset_index()
          j = gpd.sjoin(bld.assign(geometry=cent), basins[["value", "geometry"]], predicate="within")
          basins["residents"] = basins["value"].map(j.groupby("value")["residents"].sum()).fillna(0)
          basins.nlargest(3, "residents")[["value", "residents"]]
          ```
          """),
         ("""**Connected flood (+3 m).** `r.lake` from the lowest river point; flood depth at each building.""", """
          ```python
          line = river.geometry.iloc[0]
          pts = [line.interpolate(d) for d in np.arange(300, line.length - 300, 50)]
          with rasterio.open(DEM) as d:
              el = np.ma.array([v[0] for v in d.sample([(p.x, p.y) for p in pts], masked=True)])
          seed = pts[int(el.argmin())]
          lk = qrun(grass_alg("r.lake"), elevation=str(DEM), water_level=float(el.min()) + 3, coordinates=f"{seed.x},{seed.y}", lake=str(OUT / "p_lake.tif"))
          with rasterio.open(lk["lake"]) as l:
              depth = np.ma.array([v[0] for v in l.sample(list(zip(cent.x, cent.y)), masked=True)])
          bld["flood_depth"] = depth.filled(0)
          print(int((bld.flood_depth > 0).sum()), "buildings flooded")
          ```
          """),
         ("""**Risk class** per building: 'high' if flooded, 'medium' if in the top 5 % of accumulation, else 'low'. Residents per class?""", """
          ```python
          bld["risk"] = np.where(bld.flood_depth > 0, "high", np.where(top, "medium", "low"))
          bld.groupby("risk")["residents"].agg(["count", "sum"])
          ```
          """),
         ("""**Publish** buildings with risk, and basins with residents, to PostGIS.""", """
          ```python
          publish({"storm_buildings": bld[["bldg_id", "residents", "acc", "flood_depth", "risk", "geometry"]], "storm_basins": basins})
          ```
          """)],
        setup=PSETUP + '''
bld = gpd.read_file(PROJ_DIR / "buildings.gpkg")
''',
        qgis="""
        1. Load `storm_buildings` (*Categorized* on `risk`: high red, medium orange, low grey) and `storm_basins` (outline only, labels = `residents`).
        2. Add `data/d_out/p_acc.tif` with a *Singleband pseudocolor* on a log scale (or clip values at 500) to see the flow paths.
        3. In QGIS: *Processing → GRASS → r.watershed* on `dem.tif` with the same threshold — confirm you get the same basins through the dialog.
        """,
        deliver=["Buildings with accumulation, flood depth and risk class", "Basins with residents", "Risk map in QGIS"])


def p_d4(nb):
    nb.project(
        "Basement-flooding risk with SAGA terrain indices",
        """Insurers ask which buildings risk **wet basements**. Old buildings (built before 1950) in wet, low positions are most at risk.
        Use SAGA's **wetness index (TWI)**, **height above channel** and **TPI** (hollows) at every building, build a score, rank tracts, and publish.""",
        [("dem.tif", "elevation"), ("buildings.gpkg", "footprints: `year_built`, `residents`"), ("tracts.gpkg", "36 tracts")],
        [("""**Terrain indices.** Compute (or reuse from D4) TWI, vertical distance to channels (1 km² threshold) and TPI (radius 500 m) with `saga_cmd`.""", """
          ```python
          f = lambda n: quote(OUT / n)
          sh(f"saga_cmd ta_preprocessor 4 -ELEV {quote(DEM)} -FILLED {f('b_filled.tif')}", quiet=True)
          sh(f"saga_cmd ta_hydrology flow_accumulation -DEM {f('b_filled.tif')} -TCA {f('b_tca.tif')}", quiet=True)
          sh(f"saga_cmd ta_hydrology twi -DEM {f('b_filled.tif')} -TWI {f('b_twi.tif')}", quiet=True)
          sh(f"saga_cmd ta_channels 0 -ELEVATION {f('b_filled.tif')} -INIT_GRID {f('b_tca.tif')} -INIT_METHOD 2 -INIT_VALUE 1000000 -CHNLNTWRK {f('b_ch.tif')}", quiet=True)
          sh(f"saga_cmd ta_channels 3 -ELEVATION {f('b_filled.tif')} -CHANNELS {f('b_ch.tif')} -DISTANCE {f('b_vd.tif')}", quiet=True)
          sh(f"saga_cmd ta_morphometry 18 -DEM {quote(DEM)} -TPI {f('b_tpi.tif')} -RADIUS_MIN 0 -RADIUS_MAX 500", quiet=True)
          print(sorted(p.name for p in OUT.glob("b_*.tif")))
          ```
          """),
         ("""**Sample at buildings** (centroids): `twi`, `vdist`, `tpi`.""", """
          ```python
          cent = bld.centroid
          for col, name in [("twi", "b_twi.tif"), ("vdist", "b_vd.tif"), ("tpi", "b_tpi.tif")]:
              with rasterio.open(OUT / name) as r:
                  bld[col] = np.ma.array([v[0] for v in r.sample(list(zip(cent.x, cent.y)), masked=True)]).filled(np.nan)
          bld[["twi", "vdist", "tpi"]].describe().round(2)
          ```
          """),
         ("""**Score.** Rescale to 0–1: high TWI, low vdist, low (negative) TPI = risky; average them; multiply by 1.5 for buildings built before 1950. Top 20 buildings?""", """
          ```python
          sc = lambda s: (s - s.min()) / (s.max() - s.min())
          bld["score"] = (sc(bld.twi) + (1 - sc(bld.vdist)) + (1 - sc(bld.tpi))) / 3 * np.where(bld.year_built < 1950, 1.5, 1.0)
          bld.nlargest(20, "score")[["bldg_id", "year_built", "twi", "vdist", "tpi", "score"]].round(2).head()
          ```
          """),
         ("""**Tract ranking.** Mean score and number of 'high' buildings (score ≥ 90th percentile) per tract.""", """
          ```python
          high = bld["score"] >= bld["score"].quantile(0.9)
          j = gpd.sjoin(bld.assign(geometry=cent, high=high), tr[["tract_id", "geometry"]], predicate="within")
          rank = j.groupby("tract_id").agg(mean_score=("score", "mean"), high_buildings=("high", "sum")).sort_values("high_buildings", ascending=False)
          tr = tr.merge(rank, on="tract_id", how="left")
          rank.head()
          ```
          """),
         ("""**Publish** buildings with the score and the ranked tracts to PostGIS.""", """
          ```python
          publish({"basement_buildings": bld[["bldg_id", "year_built", "twi", "vdist", "tpi", "score", "geometry"]], "basement_tracts": tr})
          ```
          **Limits to state:** no drainage/sewer data, no groundwater levels, 50 m DEM; validate with insurance claims if available.
          """)],
        setup=PSETUP + '''
bld = gpd.read_file(PROJ_DIR / "buildings.gpkg")
tr = gpd.read_file(PROJ_DIR / "tracts.gpkg")
''',
        qgis="""
        1. Load `basement_buildings` (*Graduated* on `score`, 5 classes, *Quantile*) and `basement_tracts` (labels: `high_buildings`).
        2. Add `data/d_out/b_twi.tif` underneath with a blue ramp: do the high scores follow the wet valleys?
        3. With SAGA NextGen installed in QGIS, run *Topographic Wetness Index* from the Processing Toolbox and compare with your `b_twi.tif`.
        """,
        deliver=["Building score with the 3 indices", "Tract ranking table", "Map in QGIS + a paragraph on limits"])
