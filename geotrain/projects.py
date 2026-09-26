"""Project data for the end-of-notebook projects.

Every notebook ends with a project that uses its own layer(s). They are generated here
(fixed random seed, so everyone gets the same data) and written to data/projects/:

    streets.gpkg        detailed street network (segments, bridges, speeds)
    buildings.gpkg      building footprints with floors, use, year, residents
    tracts.gpkg         36 census tracts (1 km²) with a health survey (asthma cases) and NO2 pollution
    tram.gpkg           two proposed tram lines (option A and B)
    gps_tracks.csv      cyclists' GPS points (lon/lat, WGS84, with timestamps)
    delivery/           a 'messy' data delivery from a contractor (A4 project)
    lst.tif             land-surface temperature on a hot summer afternoon (°C)
    bike_*.csv          bike-share stations, members and trips (SQL projects)
    fire_stations.gpkg  one fire station (D1 project)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point, box
from shapely import affinity

from .riverton import make_riverton, _river, X0, Y0, SIZE, CRS_LOCAL, DATA_DIR

PROJ_DIR = DATA_DIR / "projects"


def make_streets():
    river = _river()
    bridges_x = {X0 + 1000, X0 + 3000, X0 + 4750}
    step = 250
    rows = []
    coords = range(0, SIZE + 1, step)
    for i in coords:                       # vertical streets
        for j in coords[:-1]:
            rows.append(("v", X0 + i, LineString([(X0 + i, Y0 + j), (X0 + i, Y0 + j + step)])))
    for j in coords:                       # horizontal streets
        for i in coords[:-1]:
            rows.append(("h", Y0 + j, LineString([(X0 + i, Y0 + j), (X0 + i + step, Y0 + j)])))
    out = []
    for k, (orient, pos, geom) in enumerate(rows):
        crosses = geom.intersects(river)
        bridge = crosses and orient == "v" and pos in bridges_x
        if crosses and not bridge:
            continue                       # no crossing without a bridge
        main = (orient == "v" and pos in (X0 + 3000, X0 + 500, X0 + 5500)) or (orient == "h" and pos in (Y0 + 3000, Y0 + 500, Y0 + 5500))
        name = (f"{'North' if orient == 'v' else 'East'} St {(pos - (X0 if orient == 'v' else Y0)) // step + 1}")
        out.append({"street_id": len(out) + 1, "name": name, "kind": "main" if main else "local",
                    "speed_kmh": 50 if main else 30, "bridge": bool(bridge), "geometry": geom})
    return gpd.GeoDataFrame(out, crs=CRS_LOCAL)


def make_buildings(seed=11):
    rng = np.random.default_rng(seed)
    base = make_riverton()
    h = base["houses"]
    rows = []
    for _, r in h.iterrows():
        size = rng.uniform(12, 24)
        g = affinity.rotate(box(r.geometry.x - size / 2, r.geometry.y - size / 2,
                                r.geometry.x + size / 2, r.geometry.y + size / 2), rng.uniform(0, 90))
        floors = int(rng.choice([1, 2, 3, 4, 6, 8], p=[.2, .3, .2, .15, .1, .05]))
        rows.append({"bldg_id": int(r.house_id), "nb_id": int(r.nb_id), "use": "residential", "floors": floors,
                     "year_built": int(rng.integers(1890, 2024)), "residents": int(r.residents), "geometry": g})
    for k in range(120):                   # shops, offices, workshops without residents
        x, y = rng.uniform(X0 + 200, X0 + SIZE - 200), rng.uniform(Y0 + 200, Y0 + SIZE - 200)
        if Point(x, y).distance(_river()) < 80:
            continue
        s = rng.uniform(25, 60)
        rows.append({"bldg_id": 10_000 + k, "nb_id": int((y - Y0) // 2000 * 3 + (x - X0) // 2000 + 1),
                     "use": str(rng.choice(["commercial", "office", "industrial"], p=[.5, .3, .2])),
                     "floors": int(rng.integers(1, 6)), "year_built": int(rng.integers(1950, 2024)),
                     "residents": 0, "geometry": box(x - s / 2, y - s / 2, x + s / 2, y + s / 2)})
    return gpd.GeoDataFrame(rows, crs=CRS_LOCAL)


def make_tracts(seed=5):
    rng = np.random.default_rng(seed)
    base = make_riverton()
    cells = [box(X0 + i * 1000, Y0 + j * 1000, X0 + (i + 1) * 1000, Y0 + (j + 1) * 1000)
             for j in range(6) for i in range(6)]
    t = gpd.GeoDataFrame({"tract_id": [f"T{k + 1:02d}" for k in range(36)]}, geometry=cells, crs=CRS_LOCAL)
    pop = gpd.sjoin(base["houses"], t, predicate="within").groupby("index_right")["residents"].sum()
    t["population"] = t.index.map(pop).fillna(0).astype(int)
    nb = gpd.sjoin(t.assign(geometry=t.centroid), base["neighbourhoods"][["median_income", "pct_over65", "geometry"]], predicate="within")
    t["median_income"] = (nb["median_income"] * rng.normal(1, 0.08, 36)).round(-2).astype(int)
    t["pct_over65"] = (nb["pct_over65"] + rng.normal(0, 2, 36)).round(1)
    primary = base["roads"].query("road_type == 'primary'").union_all()
    t["dist_main_road_m"] = t.centroid.distance(primary).round()
    d_centre = t.centroid.distance(Point(X0 + 3000, Y0 + 3000))
    t["no2_ugm3"] = (14 + 26 * np.exp(-d_centre / 1600) + 4 * np.exp(-t["dist_main_road_m"] / 300) + rng.normal(0, 1.5, 36)).round(1)
    rate = 0.030 + 0.0018 * (t["no2_ugm3"] - 20) - 0.0000008 * (t["median_income"] - 38000)
    t["asthma_cases"] = rng.poisson(np.clip(rate, 0.01, None) * t["population"]).astype(int)
    return t


def make_tram():
    a = LineString([(X0 + 300, Y0 + 900), (X0 + 1500, Y0 + 1500), (X0 + 3000, Y0 + 3000),
                    (X0 + 4200, Y0 + 4300), (X0 + 5700, Y0 + 5100)])
    b = LineString([(X0 + 3000, Y0 + 200), (X0 + 3000, Y0 + 3000), (X0 + 2200, Y0 + 4200), (X0 + 1200, Y0 + 5800)])
    return gpd.GeoDataFrame({"option": ["A", "B"], "cost_million_eur": [310, 240]}, geometry=[a, b], crs=CRS_LOCAL)


def make_gps_tracks(seed=21):
    rng = np.random.default_rng(seed)
    streets = make_streets()
    routes = [
        [(X0 + 500, Y0 + 500), (X0 + 500, Y0 + 3000), (X0 + 3000, Y0 + 3000), (X0 + 3000, Y0 + 5500)],
        [(X0 + 5500, Y0 + 500), (X0 + 3000, Y0 + 500), (X0 + 3000, Y0 + 4000), (X0 + 1000, Y0 + 4000)],
        [(X0 + 1000, Y0 + 5500), (X0 + 1000, Y0 + 1500), (X0 + 4750, Y0 + 1500), (X0 + 4750, Y0 + 5000)],
        [(X0 + 250, Y0 + 2000), (X0 + 5750, Y0 + 2000)],
        [(X0 + 4750, Y0 + 5750), (X0 + 4750, Y0 + 250)],
    ]
    rows = []
    from pyproj import Transformer
    to_ll = Transformer.from_crs(CRS_LOCAL, 4326, always_xy=True)
    start = pd.Timestamp("2025-06-14 07:30:00")
    for tid, pts in enumerate(routes, 1):
        line = LineString(pts)
        speed = rng.uniform(3.5, 6.5)                 # m/s (13–23 km/h)
        t0 = start + pd.Timedelta(minutes=int(rng.integers(0, 90)))
        for k, d in enumerate(np.arange(0, line.length, speed * 10)):   # one point every 10 s
            p = line.interpolate(d)
            x, y = p.x + rng.normal(0, 4), p.y + rng.normal(0, 4)
            lon, lat = to_ll.transform(x, y)
            rows.append({"track_id": tid, "time": t0 + pd.Timedelta(seconds=10 * k), "lon": round(lon, 6), "lat": round(lat, 6)})
    del streets
    return pd.DataFrame(rows)


def make_delivery(folder, seed=31):
    """A contractor's delivery with typical problems (missing CRS, invalid, duplicates, swapped lon/lat)."""
    rng = np.random.default_rng(seed)
    folder.mkdir(parents=True, exist_ok=True)
    from shapely.geometry import Polygon
    # 1) playgrounds.shp with NO .prj (CRS missing), one bow-tie polygon
    pg = []
    for k in range(12):
        x, y = rng.uniform(X0 + 300, X0 + SIZE - 300), rng.uniform(Y0 + 300, Y0 + SIZE - 300)
        pg.append(box(x, y, x + rng.uniform(30, 80), y + rng.uniform(30, 80)))
    x, y = X0 + 2500, Y0 + 1200
    pg.append(Polygon([(x, y), (x + 60, y + 60), (x + 60, y), (x, y + 60)]))
    play = gpd.GeoDataFrame({"play_id": range(1, 14), "surface": rng.choice(["sand", "rubber", "grass"], 13)}, geometry=pg, crs=CRS_LOCAL)
    play.to_file(folder / "playgrounds.shp")
    (folder / "playgrounds.prj").unlink(missing_ok=True)
    # 2) benches.geojson in WGS84 with duplicates and one empty geometry
    pts = gpd.GeoSeries([Point(rng.uniform(X0, X0 + SIZE), rng.uniform(Y0, Y0 + SIZE)) for _ in range(40)], crs=CRS_LOCAL).to_crs(4326)
    b = gpd.GeoDataFrame({"bench_id": range(1, 41), "condition": rng.choice(["good", "worn", "broken"], 40)}, geometry=pts)
    b = pd.concat([b, b.iloc[[3, 7, 7]]], ignore_index=True)          # duplicates
    b.loc[len(b)] = {"bench_id": 99, "condition": "good", "geometry": Point()}
    gpd.GeoDataFrame(b, geometry="geometry", crs=4326).to_file(folder / "benches.geojson", driver="GeoJSON")
    # 3) trees.csv with lon/lat, some rows have lon and lat swapped
    tp = gpd.GeoSeries([Point(rng.uniform(X0, X0 + SIZE), rng.uniform(Y0, Y0 + SIZE)) for _ in range(60)], crs=CRS_LOCAL).to_crs(4326)
    trees = pd.DataFrame({"tree_id": range(1, 61), "species": rng.choice(["oak", "lime", "plane", "birch"], 60),
                          "lon": tp.x.round(6), "lat": tp.y.round(6)})
    swap = trees.sample(6, random_state=1).index
    trees.loc[swap, ["lon", "lat"]] = trees.loc[swap, ["lat", "lon"]].values
    trees.to_csv(folder / "trees.csv", index=False)
    # 4) bins.gpkg: coordinates are UTM metres but the file says EPSG:4326 (wrong CRS label)
    bins = gpd.GeoDataFrame({"bin_id": range(1, 21)},
                            geometry=[Point(rng.uniform(X0, X0 + SIZE), rng.uniform(Y0, Y0 + SIZE)) for _ in range(20)])
    bins.set_crs(4326, allow_override=True).to_file(folder / "bins.gpkg", layer="bins")


def make_lst(folder, seed=41):
    """Land-surface temperature (°C) at 50 m, hotter where built up, cooler near water and green."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.features import rasterize
    rng = np.random.default_rng(seed)
    b = make_buildings()
    t = from_origin(X0, Y0 + SIZE, 50, 50)
    built = rasterize(((g, 1) for g in b.geometry), out_shape=(120, 120), transform=t, merge_alg=rasterio.enums.MergeAlg.add, dtype="float32")
    from scipy.ndimage import uniform_filter
    density = uniform_filter(built, size=5)
    cols, rows = np.meshgrid(np.arange(120), np.arange(120))
    xs, ys = X0 + (cols + .5) * 50, Y0 + SIZE - (rows + .5) * 50
    d_river = np.abs(ys - (Y0 + 3300 + 450 * np.sin((xs - X0) / 900)))
    parks = make_riverton()["parks"]
    park = rasterize(((g, 1) for g in parks.geometry), out_shape=(120, 120), transform=t, dtype="uint8")
    from scipy.ndimage import distance_transform_edt
    d_park = distance_transform_edt(park == 0) * 50                  # metres to the nearest park cell
    lst = (29 + 9 * density / density.max() - 3.5 * np.exp(-d_river / 200) - 4 * park
           - 2.0 * np.exp(-d_park / 150) * (park == 0) + rng.normal(0, .6, (120, 120)))
    with rasterio.open(folder / "lst.tif", "w", driver="GTiff", width=120, height=120, count=1, dtype="float32",
                       crs=CRS_LOCAL, transform=t, nodata=-9999) as dst:
        dst.write(lst.astype("float32"), 1)
        dst.set_band_description(1, "land_surface_temperature_C")


def make_bike(folder, seed=51):
    rng = np.random.default_rng(seed)
    from pyproj import Transformer
    to_ll = Transformer.from_crs(CRS_LOCAL, 4326, always_xy=True)
    xs, ys = rng.uniform(X0 + 300, X0 + SIZE - 300, 24), rng.uniform(Y0 + 300, Y0 + SIZE - 300, 24)
    lon, lat = to_ll.transform(xs, ys)
    stations = pd.DataFrame({"station_id": range(1, 25), "name": [f"Station {c}" for c in "ABCDEFGHIJKLMNOPQRSTUVWX"],
                             "capacity": rng.choice([10, 15, 20, 30], 24), "lon": np.round(lon, 6), "lat": np.round(lat, 6),
                             "opened": pd.to_datetime("2023-03-01") + pd.to_timedelta(rng.integers(0, 600, 24), unit="D")})
    members = pd.DataFrame({"member_id": range(1, 801),
                            "age_group": rng.choice(["16-24", "25-39", "40-59", "60+"], 800, p=[.25, .4, .25, .1]),
                            "plan": rng.choice(["annual", "monthly", "pay-as-you-go"], 800, p=[.35, .25, .4]),
                            "joined": pd.to_datetime("2023-03-01") + pd.to_timedelta(rng.integers(0, 900, 800), unit="D")})
    n = 6000
    pop = rng.dirichlet(np.ones(24) * 0.8)                  # some stations are much busier
    start = rng.choice(stations.station_id, n, p=pop)
    end = rng.choice(stations.station_id, n, p=pop)
    hours = rng.choice(np.arange(24), n, p=np.array([1, 1, 1, 1, 1, 2, 5, 10, 12, 6, 4, 4, 5, 5, 5, 6, 9, 12, 9, 6, 4, 3, 2, 1]) / 115)
    ts = pd.to_datetime("2025-04-01") + pd.to_timedelta(rng.integers(0, 183, n), unit="D") + pd.to_timedelta(hours, unit="h") + pd.to_timedelta(rng.integers(0, 60, n), unit="m")
    member = np.where(rng.random(n) < 0.15, np.nan, rng.integers(1, 801, n))   # 15 % casual riders (no member id)
    trips = pd.DataFrame({"trip_id": range(1, n + 1), "member_id": member, "start_station": start, "end_station": end,
                          "start_time": ts, "duration_min": np.round(rng.gamma(2.2, 7, n), 1)})
    trips["member_id"] = trips["member_id"].astype("Int64")
    stations.to_csv(folder / "bike_stations.csv", index=False)
    members.to_csv(folder / "bike_members.csv", index=False)
    trips.to_csv(folder / "bike_trips.csv", index=False)


def build_projects(folder=PROJ_DIR, force=False):
    """Write all project data (only the first time, unless force=True). Returns the folder."""
    folder = Path(folder)
    if (folder / "_done").exists() and not force:
        return folder
    folder.mkdir(parents=True, exist_ok=True)
    make_streets().to_file(folder / "streets.gpkg", layer="streets")
    make_buildings().to_file(folder / "buildings.gpkg", layer="buildings")
    make_tracts().to_file(folder / "tracts.gpkg", layer="tracts")
    make_tram().to_file(folder / "tram.gpkg", layer="tram")
    make_gps_tracks().to_csv(folder / "gps_tracks.csv", index=False)
    make_delivery(folder / "delivery")
    make_lst(folder)
    make_bike(folder)
    gpd.GeoDataFrame({"station": ["Central Fire Station"], "engines": [3]},
                     geometry=[Point(X0 + 2900, Y0 + 2700)], crs=CRS_LOCAL).to_file(folder / "fire_stations.gpkg", layer="fire_stations")
    (folder / "_done").write_text("ok")
    return folder


def publish(layers: dict, schema: str = "projects"):
    """Write GeoDataFrames (or DataFrames) to PostGIS tables in `schema`, with spatial indexes.

    layers = {"table_name": gdf, ...}. Needs the database from B0 (or S1).
    """
    from sqlalchemy import text
    from .db import engine
    eng = engine()
    with eng.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    for name, df in layers.items():
        if isinstance(df, gpd.GeoDataFrame):
            df.to_postgis(name, eng, schema=schema, if_exists="replace", index=False)
        else:
            df.to_sql(name, eng, schema=schema, if_exists="replace", index=False)
        print(f"published {schema}.{name} ({len(df)} rows)")
    return eng
