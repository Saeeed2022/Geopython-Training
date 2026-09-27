# Install the course on Windows in `C:\Geopython`

About 45 minutes, most of it waiting for downloads. Do the steps **in this order**.
At the end you will have:

| What | Where | Needed for |
|---|---|---|
| The course files | `C:\Geopython` | everything |
| Python + all libraries (conda environment `geopython`) | Miniforge | all notebooks |
| PostgreSQL + PostGIS database `geotrain` | Windows service | S1–S2, B0–B4, all projects |
| QGIS (with GRASS) | `C:\OSGeo4W` | all projects (maps), D1, D3 |
| SAGA command line | `C:\SAGA` | D4 only |

---

## Step 1 · Put the course files in `C:\Geopython`

**Option A — with Git (recommended, easy to update later).**
Install *Git for Windows* (git-scm.com, accept the defaults). Open **Command Prompt** and type:

```bat
git clone --branch claude/geopython-postgis-curriculum-06y7y3 https://github.com/saeeed2022/geopython-training.git C:\Geopython
```

Later, to get new versions: `cd C:\Geopython` then `git pull`.

**Option B — as a ZIP.** On GitHub open the repository, switch the branch to
`claude/geopython-postgis-curriculum-06y7y3`, click **Code → Download ZIP**, and extract it.
Rename/move the extracted folder so that you have `C:\Geopython\notebooks` (not `C:\Geopython\geopython-training-...\notebooks`).

✅ Check: the folder `C:\Geopython` contains `notebooks`, `geotrain`, `environment.yml`, `start_jupyter.bat`.

---

## Step 2 · Python and the libraries (Miniforge)

Why Miniforge (conda) and not plain `pip`? On Windows, GDAL, Rasterio and Fiona need compiled C libraries.
Conda brings them ready-made; pip often fails on Windows.

1. Download **Miniforge3-Windows-x86_64.exe** from github.com/conda-forge/miniforge and install it
   (*Just Me*, default folder `C:\Users\<you>\miniforge3`).
2. Start **Miniforge Prompt** (Start menu) and type:

```bat
cd /d C:\Geopython
mamba env create -f environment.yml
conda activate geopython
python -c "import geopandas, rasterio, esda, psycopg; print('OK', geopandas.__version__)"
```

✅ Check: the last line prints `OK 1.x`. Also `ogr2ogr --version` now works in this prompt (GDAL tools for D2).

---

## Step 3 · The database: PostgreSQL + PostGIS

**Option A — Windows installer (recommended: no Docker, runs as a normal Windows service).**

1. Download the **PostgreSQL 16** installer for Windows (EDB) from postgresql.org → *Download* → *Windows*.
2. Run it. Keep the defaults (port **5432**). Choose a password for the `postgres` superuser and **write it down**.
3. At the end, tick **Launch Stack Builder** → choose your PostgreSQL 16 → *Spatial Extensions* → **PostGIS 3.x Bundle** → install (say *Yes* to the questions about GDAL/PROJ environment variables).
4. Create the course user and database: Start menu → **SQL Shell (psql)** → press Enter four times (defaults) → type the `postgres` password → then paste:

```sql
CREATE USER geo WITH PASSWORD 'geo' SUPERUSER;
CREATE DATABASE geotrain OWNER geo;
\c geotrain
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_raster;
SELECT postgis_full_version();
\q
```

✅ Check: the `SELECT` prints a line starting with `POSTGIS="3...`. The database starts automatically with Windows.

**Option B — Docker Desktop** (needs WSL2 / virtualisation enabled):

```bat
docker run --name geotrain-db -e POSTGRES_USER=geo -e POSTGRES_PASSWORD=geo -e POSTGRES_DB=geotrain -p 5432:5432 -d postgis/postgis:16-3.4
```
Later you only need `docker start geotrain-db`.

> The notebooks connect to `postgresql://geo:geo@localhost:5432/geotrain`. If you chose other names or a password,
> set it once in Miniforge Prompt: `setx GEOTRAIN_DSN "postgresql://USER:PASSWORD@localhost:5432/DATABASE"` (then open a new prompt).

---

## Step 4 · QGIS (with GRASS)

1. Download the **OSGeo4W network installer** (qgis.org → *Download* → *OSGeo4W Network Installer*).
2. Run it → **Express Install** → tick **QGIS LTR** (GRASS comes with it) → Next. It installs to `C:\OSGeo4W`.
3. Open QGIS once. Then connect it to the database: **Browser panel → right-click PostgreSQL → New Connection** →
   Name `geotrain`, Host `localhost`, Port `5432`, Database `geotrain`, *Basic* authentication user `geo` / password `geo` → **Test Connection**.

The notebooks find `C:\OSGeo4W\bin\qgis_process-qgis-ltr.bat` automatically.
If you used the stand-alone QGIS installer instead, it is also found in `C:\Program Files\QGIS 3.xx\bin`.
Anywhere else: `setx QGIS_PROCESS "full\path\to\qgis_process-qgis-ltr.bat"`.

✅ Check (Miniforge Prompt): `C:\OSGeo4W\bin\qgis_process-qgis-ltr.bat --version` prints QGIS, GDAL and GEOS versions.

---

## Step 5 · SAGA (only for D4)

1. Download the Windows ZIP of SAGA (`saga-9.x.x_x64.zip`) from sourceforge.net/projects/saga-gis.
2. Extract it and rename the folder to **`C:\SAGA`** (so that `C:\SAGA\saga_cmd.exe` exists).

`start_jupyter.bat` adds `C:\SAGA` to the PATH for you. You can skip this step until you reach D4.

---

## Step 6 · Start the course

**Double-click `C:\Geopython\start_jupyter.bat`.** It activates the environment and opens JupyterLab in your browser
in the `notebooks` folder. Open **`00_START_HERE.ipynb`** and run the check cells:

| You should see | If not |
|---|---|
| ✅ for all Python libraries | Step 2 (did the environment activate?) |
| ✅ database / ✅ PostGIS | Step 3 (is the PostgreSQL service running? *Services* app → `postgresql-x64-16`) |
| ✅ qgis_process, gdalinfo, ogr2ogr | Step 4 / Step 2 |
| ✅ saga_cmd | Step 5 (only needed for D4) |

The first run creates the training data in `C:\Geopython\data` (a few seconds).

(Manual start instead of the .bat file: Miniforge Prompt → `conda activate geopython` → `cd /d C:\Geopython\notebooks` → `jupyter lab`.)

---

## Windows notes

- **D3 exercise 4.3** (a native GRASS session from a script) uses a Linux shell script. On Windows, open the *OSGeo4W Shell*
  and type the GRASS commands there; everything else in D3 runs through QGIS and works on Windows.
- **Antivirus / firewall** may ask whether Python or PostgreSQL may use the network: allow *private networks* (it is only your own computer, `localhost`).
- **Paths with spaces** (e.g. `C:\Users\Saeed Dalil\...`) are the most common cause of GIS tool errors. Keeping the course in `C:\Geopython` avoids them.
- **Updating the course:** `cd /d C:\Geopython` and `git pull` (Option A). Your answers live in the notebooks, so first make a copy of any notebook you edited, or commit it.
