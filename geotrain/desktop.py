"""Helpers to call desktop-GIS engines from a notebook (group D).

- qrun()  runs any QGIS Processing algorithm (QGIS native, GDAL, GRASS…) through
          the `qgis_process` command-line tool. This works from any Python/Jupyter,
          even when the QGIS Python (PyQGIS) is a different Python installation.
- sh()    runs a command-line tool (ogr2ogr, gdalwarp, gdaldem, saga_cmd, grass…)
          and prints its output, like `!command` in Jupyter.

If qgis_process is not found, set the environment variable QGIS_PROCESS to its full path, e.g.
  Windows (OSGeo4W):  C:\\OSGeo4W\\bin\\qgis_process-qgis.bat
  macOS:              /Applications/QGIS.app/Contents/MacOS/bin/qgis_process
"""
import json
import os
import shlex
import shutil
import subprocess

ENV = dict(os.environ, QT_QPA_PLATFORM="offscreen")
ENV.setdefault("XDG_RUNTIME_DIR", "/tmp/runtime-" + str(os.getuid()) if hasattr(os, "getuid") else "")

_CANDIDATES = ["qgis_process", "qgis_process-qgis.bat", "qgis_process-qgis-ltr.bat",
               r"C:\OSGeo4W\bin\qgis_process-qgis-ltr.bat", r"C:\OSGeo4W\bin\qgis_process-qgis.bat",
               "/Applications/QGIS.app/Contents/MacOS/bin/qgis_process",
               "/Applications/QGIS-LTR.app/Contents/MacOS/bin/qgis_process"]


def qgis_process_path():
    """Return the path of the qgis_process tool, or None."""
    if os.environ.get("QGIS_PROCESS"):
        return os.environ["QGIS_PROCESS"]
    for c in _CANDIDATES:
        found = shutil.which(c) or (c if os.path.exists(c) else None)
        if found:
            return found
    if os.name == "nt":                      # QGIS stand-alone installer: C:\Program Files\QGIS 3.xx\bin\...
        import glob
        hits = sorted(glob.glob(r"C:\Program Files\QGIS*\bin\qgis_process-qgis*.bat"))
        if hits:
            return hits[-1]
    return None


def _run(args, check=True):
    p = subprocess.run(args, capture_output=True, text=True, env=ENV)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(map(str, args))}\n{p.stderr[-2000:]}\n{p.stdout[-2000:]}")
    return p


def sh(cmd, quiet=False, check=True):
    """Run a shell command (string). Prints its output without progress bars; returns the output text.

    check=False: do not raise when the program exits with an error code (e.g. `saga_cmd <library>`
    lists its tools and then exits with code 1).
    """
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=ENV)
    out = "\n".join(line for line in (p.stdout + p.stderr).splitlines()
                    if "%" not in line[:6] and not line.strip().endswith("%") and "XDG_RUNTIME_DIR" not in line)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}\n{out[-3000:]}")
    if not quiet:
        print(out.strip())
    return out


def qlist(text=""):
    """List QGIS Processing algorithms whose id or name contains `text`."""
    out = _run([qgis_process_path(), "list"]).stdout
    rows = [line.strip().split("\t") for line in out.splitlines() if line.startswith("\t")]
    return [r for r in rows if text.lower() in " ".join(r).lower()]


def qhelp(alg):
    """Print the parameters of one algorithm (what you would see in the QGIS dialog)."""
    out = _run([qgis_process_path(), "help", alg]).stdout
    start = out.find("Arguments")
    print(out[start:] if start >= 0 else out)


def minimal_project(crs="EPSG:32633"):
    """Write an empty QGIS project (some tools, e.g. network analysis, need one) and return its path."""
    import tempfile
    path = os.path.join(tempfile.gettempdir(), f"geotrain_{crs.replace(':', '_')}.qgs")
    with open(path, "w") as f:
        f.write("<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
                f'<qgis projectname="geotrain" version="3.34">\n'
                f"  <projectCrs><spatialrefsys><authid>{crs}</authid></spatialrefsys></projectCrs>\n</qgis>\n")
    return path


def qrun(alg, _project=None, **params):
    """Run a QGIS Processing algorithm and return its results (a dict of outputs).

    Parameter names are the same as in `qhelp(alg)`. A list value is passed as a comma-separated
    list of choices (e.g. STATISTICS=[2, 6]). Tools that need a QGIS project (network analysis)
    get one with `_project=minimal_project()`. Vector layers inside a GeoPackage: "file.gpkg|layername=roads".
    """
    args = [qgis_process_path(), "run", alg, "--json"]
    if _project:
        args.append(f"--PROJECT_PATH={_project}")
    args.append("--")
    for k, v in params.items():
        if isinstance(v, (list, tuple)):          # several choices, e.g. STATISTICS=[2, 6] -> "2,6"
            v = ",".join(str(i) for i in v)
        elif isinstance(v, bool):
            v = str(v).lower()
        args.append(f"{k}={v}")
    out = _run(args).stdout
    data = json.loads(out[out.find("{"):])
    errors = (data.get("log") or {}).get("errors") or []
    missing = [v for v in data["results"].values()
               if isinstance(v, str) and os.path.isabs(v.split("|")[0]) and not os.path.exists(v.split("|")[0])]
    if missing:
        raise RuntimeError(f"{alg} did not create {missing}.\n" + "\n".join(dict.fromkeys(errors)))
    return data["results"]


def grass_alg(name):
    """Return the QGIS id of a GRASS tool ('grass7:r.watershed' in QGIS < 3.36, 'grass:r.watershed' after)."""
    ids = [r[0] for r in qlist(name) if r[0].split(":", 1)[-1] == name]
    if not ids:
        raise RuntimeError(f"GRASS tool {name} not found. Enable the provider: `qgis_process plugins enable grassprovider`.")
    return ids[0]


def enable_grass():
    """Switch on the GRASS provider for qgis_process (needed once)."""
    return _run([qgis_process_path(), "plugins", "enable", "grassprovider"], check=False).stdout


def quote(path):
    """Quote a path for sh() commands (double quotes on Windows, POSIX quoting elsewhere)."""
    if os.name == "nt":
        return subprocess.list2cmdline([str(path)])
    return shlex.quote(str(path))
