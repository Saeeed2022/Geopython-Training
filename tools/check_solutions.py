"""Run every notebook's setup cells + solution code, in order, as a test.

Usage:  python tools/check_solutions.py [name ...]
"""
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "content"))
import build_all  # noqa: E402

import matplotlib
matplotlib.use("Agg")


def run(nb):
    os.chdir(HERE.parent / "notebooks")
    ns = {"__name__": "__main__"}
    for i, src in enumerate(nb.checks):
        try:
            exec(compile(src, f"{nb.name}[{i}]", "exec"), ns)
        except Exception:
            print(f"\n❌ {nb.name} block {i} failed:\n{src}\n")
            traceback.print_exc()
            return False
    print(f"✅ {nb.name}: {len(nb.checks)} blocks ran")
    return True


if __name__ == "__main__":
    wanted = sys.argv[1:]
    ok = True
    for nb in build_all.all_notebooks():
        if not wanted or nb.name in wanted:
            ok &= run(nb)
    sys.exit(0 if ok else 1)
