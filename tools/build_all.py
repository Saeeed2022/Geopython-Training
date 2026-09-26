"""Regenerate every notebook in notebooks/ from tools/content/*.py."""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "content"))

MODULES = ["n00_start", "a1_shapely", "a2_pyproj", "a3_geopandas", "a4_pyogrio_fiona", "a5_rasterio", "a6_pysal",
           "b0_postgis_setup", "b1_postgis_internal", "b2_psycopg", "b3_sqlalchemy", "b4_geopandas_postgis",
           "d0_desktop_setup", "d1_qgis_native", "d2_gdal_ogr", "d3_grass", "d4_saga", "c_capstone"]


def all_notebooks():
    for m in MODULES:
        try:
            mod = importlib.import_module(m)
        except ModuleNotFoundError as e:
            if e.name == m:
                continue
            raise
        yield mod.build()


if __name__ == "__main__":
    for nb in all_notebooks():
        print("wrote", nb.save())
