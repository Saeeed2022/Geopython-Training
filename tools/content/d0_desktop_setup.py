from nbbuild import NB, SETUP

DSETUP = '''
from geotrain.desktop import qrun, qhelp, qlist, sh, grass_alg, enable_grass, qgis_process_path, quote, minimal_project
OUT = DATA_DIR / "d_out"
OUT.mkdir(exist_ok=True)
V = lambda layer: f"{GPKG}|layername={layer}"       # how QGIS names a layer inside a GeoPackage
DEM = DATA_DIR / "dem.tif"
print("qgis_process:", qgis_process_path())
'''


def build():
    nb = NB("D0_desktop_gis_setup", "D0 · Desktop GIS engines — QGIS, GDAL/OGR, GRASS, SAGA from Jupyter")
    nb.md("""
    **What group D is:** four big GIS engines that you usually meet as buttons in **QGIS's Processing Toolbox**.
    Here you call them from Jupyter, so every step is written down and can be repeated.

    | Engine | Best at | Daily picture | Notebook |
    |---|---|---|---|
    | **QGIS native** | vector work: buffers, overlays, geometry repair, spatial joins, networks | the Swiss-army knife | D1 |
    | **GDAL / OGR** | converting, reprojecting and clipping rasters (GDAL) and vectors (OGR) | the universal plug adapter | D2 |
    | **GRASS GIS** | hydrology, terrain, raster and environmental modelling | a big scientific laboratory | D3 |
    | **SAGA GIS** | terrain and hydrological analysis (wetness, channels, landforms) | a specialist workshop for landscapes | D4 |

    **How they relate to what you know:**
    - GDAL/OGR is the engine inside **Rasterio, Pyogrio, Fiona and PostGIS rasters**. D2 shows the same engine as command-line tools.
    - QGIS native tools use **GEOS** (like Shapely/PostGIS) and **PROJ** (like PyProj).
    - GRASS and SAGA add hydrology and terrain methods that GeoPandas and Rasterio do not have.

    **Three ways to run a Processing tool:**
    1. **QGIS window:** Processing Toolbox → double-click a tool → fill the form. Good for learning; hard to repeat.
    2. **`qgis_process` command line:** `qgis_process run native:buffer -- INPUT=... DISTANCE=600 OUTPUT=...`.
       Works from **any** Jupyter, even if its Python is not QGIS's Python. **We use this**, through the helper `qrun()`.
    3. **PyQGIS** inside QGIS's own Python: `processing.run("native:buffer", {...})`. Same parameters as option 2.

    **Recommendation:** learn the tool in the QGIS window once (see the form), then write it with `qrun()`.
    Tip: in any QGIS tool dialog, *Advanced → Copy as qgis_process Command* gives you the exact command.
    """)
    nb.md("""
    ## Step 1 · Install (choose your system)

    | System | QGIS (includes GDAL, GRASS provider) | SAGA | GDAL command line |
    |---|---|---|---|
    | **Windows** | OSGeo4W installer → "Express install" → QGIS | OSGeo4W advanced install → `saga`; or saga-gis.sourceforge.io | included in OSGeo4W (use the *OSGeo4W Shell*) |
    | **macOS** | qgis.org installer (QGIS.app) | `brew install saga-gis` or conda | `brew install gdal` |
    | **Linux (Ubuntu)** | `sudo apt install qgis qgis-provider-grass grass` | `sudo apt install saga` | `sudo apt install gdal-bin` |
    | **conda (any)** | `conda install -c conda-forge qgis grass` | `conda install -c conda-forge saga` | `conda install -c conda-forge gdal` |

    Since QGIS 3.30, SAGA is **not** built into QGIS any more; inside QGIS you can add it with the *Processing Saga NextGen Provider* plugin.
    In this course we call SAGA directly with its own command-line tool, `saga_cmd` (D4).

    If `qgis_process` is not found, set `QGIS_PROCESS` to its full path before starting Jupyter
    (Windows: `C:\\OSGeo4W\\bin\\qgis_process-qgis.bat`; macOS: `/Applications/QGIS.app/Contents/MacOS/bin/qgis_process`).
    """)
    nb.code(SETUP)
    nb.code(DSETUP)

    nb.level(1, "Check the four engines", "confirm each engine answers, and see which versions you have.",
             "Before a long drive: check oil, water, tyres and fuel.")
    nb.ex("1.1", "Is QGIS Processing there?", "qgis_process --version",
          purpose_a="Prints the versions of QGIS and the libraries inside it (GDAL, GEOS, PROJ…).",
          life_a="A colleague's result differs from yours: first compare versions.",
          hint="Run the shell command with the helper: `sh(f\"{quote(qgis_process_path())} --version\")`.",
          starter="""
          sh(f"{quote(qgis_process_path())} ____")
          """,
          solution="""
          sh(f"{quote(qgis_process_path())} --version")
          """)
    nb.ex("1.2", "Switch on GRASS inside QGIS", "qgis_process plugins enable grassprovider",
          purpose_a="Activates the GRASS provider, so GRASS tools appear in QGIS Processing (and in `qgis_process list`).",
          life_a="Needed once on a new computer before using `grass:r.watershed` and friends.",
          hint="Call `enable_grass()`, then count GRASS tools with `qlist(\"r.watershed\")`.",
          starter="""
          enable_grass()
          print(qlist("____"))
          print("GRASS tool id:", grass_alg("r.watershed"))
          """,
          solution="""
          enable_grass()
          print(qlist("r.watershed"))
          print("GRASS tool id:", grass_alg("r.watershed"))
          """,
          note="QGIS 3.34 and older call them `grass7:...`, newer versions `grass:...`. `grass_alg()` finds the right name for you.")
    nb.ex("1.3", "How many tools per provider?", "qlist()",
          purpose_a="Lists all Processing algorithms; each id starts with its provider (`native:`, `gdal:`, `grass7:`/`grass:`, `qgis:`).",
          life_a="Knowing what your toolbox holds before planning an analysis.",
          hint="`ids = [r[0] for r in qlist()]`, then count the part before `:` with `collections.Counter`.",
          starter="""
          from collections import Counter
          ids = [r[0] for r in qlist()]
          Counter(i.split("____")[0] for i in ids)
          """,
          solution="""
          from collections import Counter
          ids = [r[0] for r in qlist()]
          Counter(i.split(":")[0] for i in ids)
          """)
    nb.ex("1.4", "GDAL and SAGA command-line tools", "gdalinfo --version / saga_cmd --version",
          purpose_a="Checks that the stand-alone GDAL and SAGA programs are on your PATH.",
          life_a="D2 (GDAL) and D4 (SAGA) call these programs directly.",
          hint="Two `sh()` calls. SAGA prints a banner; look for 'SAGA Version'.",
          starter="""
          sh("gdalinfo ____")
          sh("saga_cmd --version")
          """,
          solution="""
          sh("gdalinfo --version")
          sh("saga_cmd --version")
          """)
    nb.md("""
    ### ✅ Setup check

    If all four cells ran, go on with **D1** (QGIS native). Every D notebook starts with the same two setup cells.
    """)
    return nb
