"""Riverton: a small, fictional training town.

Every notebook uses the same town, so you get to know it like your own
neighbourhood. The data is generated (random seed fixed), so no download is
needed and every learner sees exactly the same numbers.

Coordinate system: WGS 84 / UTM zone 33N (EPSG:32633), units = metres.
The town is 6 km x 6 km, split into 9 neighbourhoods of 2 km x 2 km.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, box

CRS_LOCAL = "EPSG:32633"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

X0, Y0 = 390_000, 5_818_000          # south-west corner of the town
SIZE = 6_000                          # 6 km
CELL = 2_000                          # neighbourhood size

NAMES = [  # row by row, from south to north, west to east
    "Southpark", "Millbrook", "Eastfield",
    "Westend", "Oldtown", "Riverside",
    "Hillcrest", "Northgate", "Harbour",
]


def _river():
    xs = np.linspace(X0 - 200, X0 + SIZE + 200, 80)
    ys = Y0 + 3_300 + 450 * np.sin((xs - X0) / 900)
    return LineString(zip(xs, ys))


def make_riverton(seed: int = 42) -> dict:
    """Return a dict of GeoDataFrames that describe Riverton."""
    rng = np.random.default_rng(seed)

    # --- neighbourhoods (polygons) ---------------------------------------
    rows = []
    for i, name in enumerate(NAMES):
        r, c = divmod(i, 3)
        geom = box(X0 + c * CELL, Y0 + r * CELL, X0 + (c + 1) * CELL, Y0 + (r + 1) * CELL)
        rows.append({"nb_id": i + 1, "name": name, "geometry": geom})
    nbh = gpd.GeoDataFrame(rows, crs=CRS_LOCAL)
    # the centre (Oldtown) is dense, the edges are quieter
    nbh["population"] = [6200, 7400, 5100, 8300, 14800, 9600, 4300, 6900, 3800]
    nbh["median_income"] = [31000, 36500, 29500, 34000, 41000, 52000, 58000, 39500, 27500]
    nbh["pct_over65"] = [24.0, 18.5, 27.0, 16.0, 12.5, 19.0, 29.5, 21.0, 31.0]

    # --- river (line) and flood zone ------------------------------------
    river = gpd.GeoDataFrame({"name": ["Riv"], "geometry": [_river()]}, crs=CRS_LOCAL)

    # --- roads (lines) ---------------------------------------------------
    road_rows = [
        ("Ring Road", "primary", 70, [(X0 + 500, Y0 + 500), (X0 + 5500, Y0 + 500), (X0 + 5500, Y0 + 5500), (X0 + 500, Y0 + 5500), (X0 + 500, Y0 + 500)]),
        ("High Street", "primary", 50, [(X0, Y0 + 3000), (X0 + SIZE, Y0 + 3000)]),
        ("Station Avenue", "primary", 50, [(X0 + 3000, Y0), (X0 + 3000, Y0 + SIZE)]),
        ("Mill Lane", "secondary", 30, [(X0 + 1000, Y0), (X0 + 1000, Y0 + 2500), (X0 + 2200, Y0 + 2900)]),
        ("Church Road", "secondary", 30, [(X0, Y0 + 1500), (X0 + 4500, Y0 + 1500)]),
        ("Harbour Way", "secondary", 30, [(X0 + 4200, Y0 + 3000), (X0 + 4800, Y0 + 4800), (X0 + SIZE, Y0 + 5200)]),
        ("Hill Road", "secondary", 30, [(X0 + 1800, Y0 + 3000), (X0 + 1500, Y0 + 5000), (X0 + 800, Y0 + SIZE)]),
    ]
    roads = gpd.GeoDataFrame(
        [{"name": n, "road_type": t, "speed_kmh": s, "geometry": LineString(c)} for n, t, s, c in road_rows],
        crs=CRS_LOCAL,
    )

    # --- schools, clinics (points) ---------------------------------------
    schools = gpd.GeoDataFrame(
        {
            "school": ["Oak Primary", "River Primary", "Hill Academy", "East School", "Mill Primary", "North High"],
            "level": ["primary", "primary", "secondary", "primary", "primary", "secondary"],
            "capacity": [900, 800, 1400, 600, 700, 1600],
            "students": [955, 720, 1350, 610, 540, 1490],
            "geometry": [Point(X0 + 3300, Y0 + 2600), Point(X0 + 5000, Y0 + 3600), Point(X0 + 1200, Y0 + 4800),
                         Point(X0 + 5100, Y0 + 900), Point(X0 + 1300, Y0 + 1200), Point(X0 + 3400, Y0 + 5100)],
        },
        crs=CRS_LOCAL,
    )
    clinics = gpd.GeoDataFrame(
        {
            "clinic": ["Central Clinic", "Riverside Health", "Mill Surgery"],
            "doctors": [8, 4, 3],
            "geometry": [Point(X0 + 2900, Y0 + 3100), Point(X0 + 4700, Y0 + 3900), Point(X0 + 1600, Y0 + 900)],
        },
        crs=CRS_LOCAL,
    )

    # --- parks (polygons) -------------------------------------------------
    parks = gpd.GeoDataFrame(
        {
            "park": ["River Park", "Hill Park", "Mill Green"],
            "geometry": [box(X0 + 2200, Y0 + 3100, X0 + 3600, Y0 + 3900),
                         Polygon([(X0 + 300, Y0 + 4300), (X0 + 1300, Y0 + 4200), (X0 + 1100, Y0 + 5600), (X0 + 400, Y0 + 5400)]),
                         Point(X0 + 2000, Y0 + 700).buffer(300)],
        },
        crs=CRS_LOCAL,
    )

    # --- houses (points): where people live ----------------------------
    house_pts, house_nb = [], []
    for _, row in nbh.iterrows():
        n = int(row.population // 40)        # one point = one building of ~40 people
        minx, miny, maxx, maxy = row.geometry.bounds
        xs = rng.uniform(minx, maxx, n)
        ys = rng.uniform(miny, maxy, n)
        house_pts += [Point(x, y) for x, y in zip(xs, ys)]
        house_nb += [row.nb_id] * n
    houses = gpd.GeoDataFrame({"nb_id": house_nb, "residents": 40, "geometry": house_pts}, crs=CRS_LOCAL)
    river_zone = river.geometry.iloc[0].buffer(60)
    houses = houses[~houses.intersects(river_zone)].reset_index(drop=True)
    houses["house_id"] = np.arange(1, len(houses) + 1)

    # --- traffic accidents (points, with time) -------------------------
    primary = roads[roads.road_type == "primary"].geometry.union_all()
    n_acc = 260
    on_road = int(n_acc * 0.75)
    pos = rng.uniform(0, primary.length, on_road)
    near = [primary.interpolate(p) for p in pos]
    jitter = rng.normal(0, 40, (on_road, 2))
    acc_pts = [Point(p.x + dx, p.y + dy) for p, (dx, dy) in zip(near, jitter)]
    acc_pts += [Point(x, y) for x, y in zip(rng.uniform(X0, X0 + SIZE, n_acc - on_road),
                                           rng.uniform(Y0, Y0 + SIZE, n_acc - on_road))]
    dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n_acc), unit="D")
    hours = rng.choice(np.arange(24), n_acc, p=_hour_weights())
    accidents = gpd.GeoDataFrame(
        {
            "acc_id": np.arange(1, n_acc + 1),
            "date": dates,
            "hour": hours,
            "severity": rng.choice(["slight", "serious", "fatal"], n_acc, p=[0.80, 0.17, 0.03]),
            "geometry": acc_pts,
        },
        crs=CRS_LOCAL,
    )

    # --- air-quality sensors (points with a measured value) -------------
    sx = rng.uniform(X0 + 200, X0 + SIZE - 200, 18)
    sy = rng.uniform(Y0 + 200, Y0 + SIZE - 200, 18)
    sensors = gpd.GeoDataFrame({"sensor_id": [f"S{i:02d}" for i in range(1, 19)],
                                "geometry": [Point(x, y) for x, y in zip(sx, sy)]}, crs=CRS_LOCAL)
    d_road = sensors.distance(primary)
    sensors["pm25"] = (7 + 14 * np.exp(-d_road / 350) + rng.normal(0, 1.2, 18)).round(1)

    # --- shops: a plain table with GPS coordinates (lon/lat, WGS84) ------
    shop_xy = gpd.GeoSeries([Point(x, y) for x, y in zip(rng.uniform(X0, X0 + SIZE, 40),
                                                        rng.uniform(Y0, Y0 + SIZE, 40))], crs=CRS_LOCAL).to_crs(4326)
    shops = pd.DataFrame({
        "shop_id": np.arange(1, 41),
        "kind": rng.choice(["bakery", "grocery", "pharmacy", "cafe"], 40, p=[0.3, 0.3, 0.15, 0.25]),
        "lon": shop_xy.x.round(6),
        "lat": shop_xy.y.round(6),
    })

    return {
        "neighbourhoods": nbh, "river": river, "roads": roads, "schools": schools,
        "clinics": clinics, "parks": parks, "houses": houses, "accidents": accidents,
        "sensors": sensors, "shops": shops,
    }


def _hour_weights():
    w = np.array([1, 1, 1, 1, 1, 2, 4, 8, 10, 6, 5, 5, 6, 6, 6, 7, 9, 11, 9, 6, 4, 3, 2, 1], float)
    return w / w.sum()


def make_rasters(folder: Path, seed: int = 7):
    """Write dem.tif (elevation, 1 band) and satellite.tif (red + near-infrared, 2 bands)."""
    import rasterio
    from rasterio.transform import from_origin

    rng = np.random.default_rng(seed)
    res = 50                                   # 50 m pixels
    n = SIZE // res                            # 120 x 120 pixels
    transform = from_origin(X0, Y0 + SIZE, res, res)
    cols, rows = np.meshgrid(np.arange(n), np.arange(n))
    xs = X0 + (cols + 0.5) * res
    ys = Y0 + SIZE - (rows + 0.5) * res

    river = _river()
    river_y = Y0 + 3_300 + 450 * np.sin((xs - X0) / 900)
    d_river = np.abs(ys - river_y)
    hill = 55 * np.exp(-(((xs - (X0 + 1200)) ** 2 + (ys - (Y0 + 4900)) ** 2) / (2 * 1100 ** 2)))
    dem = 32 + 0.004 * d_river + 6 * (1 - np.exp(-d_river / 300)) + hill + rng.normal(0, 0.4, (n, n))
    dem = dem.astype("float32")
    dem[0:3, 0:3] = -9999                      # a few 'missing' pixels, to practise nodata

    greenness = np.clip(0.25 + 0.5 * np.exp(-d_river / 400) + 0.3 * hill / 55 + rng.normal(0, 0.05, (n, n)), 0.05, 0.95)
    red = (0.30 - 0.22 * greenness) * 10000
    nir = (0.20 + 0.40 * greenness) * 10000

    profile = dict(driver="GTiff", width=n, height=n, crs=CRS_LOCAL, transform=transform)
    with rasterio.open(folder / "dem.tif", "w", count=1, dtype="float32", nodata=-9999, **profile) as dst:
        dst.write(dem, 1)
        dst.set_band_description(1, "elevation_m")
    with rasterio.open(folder / "satellite.tif", "w", count=2, dtype="uint16", **profile) as dst:
        dst.write(red.astype("uint16"), 1)
        dst.write(nir.astype("uint16"), 2)
        dst.set_band_description(1, "red")
        dst.set_band_description(2, "nir")
    del river


def write_riverton(folder=DATA_DIR, rasters: bool = True) -> Path:
    """Write the Riverton files that the notebooks read.

    riverton.gpkg       one GeoPackage, many layers (EPSG:32633)
    neighbourhoods.geojson  GeoJSON copy in WGS84 (EPSG:4326)
    roads_shp/roads.shp     a Shapefile copy of the roads
    shops_wgs84.csv     plain CSV with lon/lat columns
    dem.tif, satellite.tif  rasters
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    layers = make_riverton()
    gpkg = folder / "riverton.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    for name, gdf in layers.items():
        if isinstance(gdf, gpd.GeoDataFrame):
            gdf.to_file(gpkg, layer=name, driver="GPKG")
    layers["neighbourhoods"].to_crs(4326).to_file(folder / "neighbourhoods.geojson", driver="GeoJSON")
    (folder / "roads_shp").mkdir(exist_ok=True)
    layers["roads"].to_file(folder / "roads_shp" / "roads.shp")
    layers["shops"].to_csv(folder / "shops_wgs84.csv", index=False)
    if rasters:
        make_rasters(folder)
    return folder


if __name__ == "__main__":
    print("Written to", write_riverton())
