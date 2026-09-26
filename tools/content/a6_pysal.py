from nbbuild import NB, SETUP

GRID = '''
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

def make_grid(size):
    """Square grid over Riverton with accidents, residents and primary-road length per cell."""
    cells = [box(x, y, x + size, y + size)
             for y in range(5_818_000, 5_824_000, size) for x in range(390_000, 396_000, size)]
    g = gpd.GeoDataFrame({"cell": range(len(cells))}, geometry=cells, crs=32633)
    acc = gpd.sjoin(L["accidents"], g, predicate="within").groupby("cell").size()
    res = gpd.sjoin(L["houses"], g, predicate="within").groupby("cell")["residents"].sum()
    prim = gpd.clip(L["roads"].query("road_type == 'primary'"), g.union_all())
    road = gpd.overlay(prim[["geometry"]], g, how="intersection", keep_geom_type=True)
    g["accidents"] = g["cell"].map(acc).fillna(0)
    g["residents"] = g["cell"].map(res).fillna(0).astype(float)
    g["road_km"] = g["cell"].map(road.assign(km=road.length / 1000).groupby("cell")["km"].sum()).fillna(0)
    return g

L = {n: gpd.read_file(GPKG, layer=n) for n in ["accidents", "houses", "roads", "sensors", "neighbourhoods"]}
grid = make_grid(500)                     # 12 x 12 = 144 cells of 500 m
print(len(grid), "cells;", int(grid.accidents.sum()), "accidents")
'''


def build():
    nb = NB("A6_pysal", "A6 · PySAL — spatial statistics: is the pattern real?")
    nb.md("""
    **What PySAL is:** the *Python Spatial Analysis Library*, a family of packages for **spatial statistics**:

    | Package | Job | Daily question |
    |---|---|---|
    | `libpysal` | **spatial weights**: who is whose neighbour | "Which houses are next door to mine?" |
    | `mapclassify` | split values into classes for maps | "Where do I draw the line between 'low' and 'high'?" |
    | `esda` | exploratory spatial data analysis: Moran's I, hot spots | "Are high values clustered, or spread by chance?" |
    | `spreg` | spatial regression | "What explains accidents, if neighbours influence each other?" |
    | `pointpats` | point-pattern analysis | "Are these points clustered, regular or random?" |

    **Why it matters:** in A3 you asked "is it real or chance?" with a home-made Monte Carlo test. PySAL gives you the
    standard, published tools for that question. They are the tools you will cite in a PhD or a paper.

    **The one big idea — Tobler's first law of geography:** *"Everything is related to everything else, but near things
    are more related than distant things."* Daily picture: house prices in your street are more like your neighbour's
    than like prices across town. Spatial statistics measure **how strong** that "near is similar" effect is.

    **Where this fits in your plan:** right after GeoPandas. It turns the **statistical** question type into proper methods.
    Riverton's 9 neighbourhoods are too few for statistics, so we work on a **grid of 500 m cells** (144 cells).
    """)
    nb.code(SETUP)
    nb.code(GRID)
    nb.code("""
    import libpysal
    from libpysal import weights
    import esda
    import mapclassify
    import spreg
    import pointpats
    ax = grid.plot(column="accidents", cmap="Reds", legend=True, edgecolor="white", figsize=(5, 5))
    L["roads"].plot(ax=ax, color="black", linewidth=.6); ax.set_title("accidents per 500 m cell"); plt.show()
    """)

    nb.level(1, "Basics: spatial weights — who is my neighbour?", "build the neighbour lists (weights) that every spatial statistic needs.",
             "Before asking 'are neighbours similar?', you must agree who counts as a neighbour: the house next door? the whole street? everyone within 1 km?")
    nb.ex("1.1", "Queen contiguity", "weights.Queen.from_dataframe(gdf)",
          purpose_a="Makes a neighbour list where two polygons are neighbours if they share an edge **or a corner** (like the queen in chess).",
          life_a="Defining neighbouring districts for a 'do rich districts border rich districts?' analysis.",
          hint="`w = weights.Queen.from_dataframe(grid, use_index=False)`. `w.n` = number of units, `w.mean_neighbors`, `w.neighbors[0]` = neighbours of cell 0 (a corner cell).",
          starter="""
          wq = weights.____.from_dataframe(grid, use_index=False)
          print(wq.n, "cells | mean neighbours:", round(wq.mean_neighbors, 2))
          print("neighbours of corner cell 0:", wq.neighbors[____])
          print("neighbours of cell 13 (inside):", wq.neighbors[13])
          """,
          solution="""
          wq = weights.Queen.from_dataframe(grid, use_index=False)
          print(wq.n, "cells | mean neighbours:", round(wq.mean_neighbors, 2))
          print("neighbours of corner cell 0:", wq.neighbors[0])
          print("neighbours of cell 13 (inside):", wq.neighbors[13])
          """,
          note="Inside cells have 8 queen neighbours, edge cells 5, corner cells 3.")
    nb.ex("1.2", "Rook contiguity", "weights.Rook.from_dataframe(gdf)",
          purpose_a="Neighbours only if they share an **edge** (like the rook in chess): no corner neighbours.",
          life_a="Used when touching at a single point should not count (e.g. two fields that only meet at a corner).",
          hint="Same call with `Rook`. Compare the neighbour count of cell 13: queen 8, rook 4.",
          starter="""
          wr = weights.____.from_dataframe(grid, use_index=False)
          print(len(wq.neighbors[13]), "queen vs", len(wr.neighbors[13]), "rook neighbours")
          """,
          solution="""
          wr = weights.Rook.from_dataframe(grid, use_index=False)
          print(len(wq.neighbors[13]), "queen vs", len(wr.neighbors[13]), "rook neighbours")
          """)
    nb.ex("1.3", "K nearest neighbours for points", "weights.KNN.from_dataframe(points, k=4)",
          purpose_a="Each point's neighbours are its k closest points. Everyone gets the same number of neighbours.",
          life_a="Air-quality sensors are points, not touching polygons; 'my 4 nearest sensors' is a natural neighbourhood.",
          hint="`weights.KNN.from_dataframe(L[\"sensors\"], k=4)`. Look at `w.neighbors[0]`.",
          starter="""
          wk = weights.KNN.from_dataframe(L["sensors"], k=____)
          print(wk.n, "sensors, neighbours of sensor 0:", wk.neighbors[0])
          """,
          solution="""
          wk = weights.KNN.from_dataframe(L["sensors"], k=4)
          print(wk.n, "sensors, neighbours of sensor 0:", wk.neighbors[0])
          """)
    nb.ex("1.4", "Distance band", "weights.DistanceBand.from_dataframe(points, threshold=d)",
          purpose_a="Neighbours are all points within distance d. Some points may have many neighbours, some none ('islands').",
          life_a="'Shops within 1 km compete with each other' — a fixed distance matters more than a fixed count.",
          hint="`threshold=1500`, `binary=True`. Check `w.islands` (points with no neighbour) and `w.cardinalities` (number of neighbours per point).",
          starter="""
          wd = weights.DistanceBand.from_dataframe(L["sensors"], threshold=____, binary=True, silence_warnings=True)
          print("islands:", wd.islands)
          print("neighbours per sensor:", list(wd.cardinalities.values()))
          """,
          solution="""
          wd = weights.DistanceBand.from_dataframe(L["sensors"], threshold=1500, binary=True, silence_warnings=True)
          print("islands:", wd.islands)
          print("neighbours per sensor:", list(wd.cardinalities.values()))
          """,
          note="**Recommendation:** polygons that tile the space → Queen; points → KNN (no islands). Always say which weights you used; results depend on it.")

    nb.level(2, "Core tools: spatial lag and map classes", "compute 'the average of my neighbours' and classify values honestly for maps.",
             "Your street's reputation is the average of the houses around you. And the colour breaks on a map can make the same data look calm or alarming.")
    nb.ex("2.1", "Row-standardise the weights", "w.transform = 'r'",
          purpose_a="Rescales each row of weights so they sum to 1; then 'neighbour sum' becomes 'neighbour average'.",
          life_a="Needed so a cell with 8 neighbours is not treated as '8 times more influenced' than a corner cell with 3.",
          hint="Set `wq.transform = \"r\"`. Check: the weights of cell 0 are 1/3 each.",
          starter="""
          wq.transform = "____"
          print(wq.weights[0])
          """,
          solution="""
          wq.transform = "r"
          print(wq.weights[0])
          """)
    nb.ex("2.2", "Spatial lag: the average of my neighbours", "weights.lag_spatial(w, y)",
          purpose_a="For every unit, computes the (weighted) average of its neighbours' values.",
          life_a="'How dangerous is the area around this cell?' — smoother than a single cell's count.",
          hint="`grid[\"acc_lag\"] = weights.lag_spatial(wq, grid[\"accidents\"])`. Compare the two maps side by side.",
          starter="""
          grid["acc_lag"] = weights.____(wq, grid["accidents"])
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          grid.plot(column="accidents", cmap="Reds", ax=axs[0], legend=True); axs[0].set_title("own value")
          grid.plot(column="acc_lag", cmap="Reds", ax=axs[1], legend=True); axs[1].set_title("average of neighbours")
          plt.show()
          """,
          solution="""
          grid["acc_lag"] = weights.lag_spatial(wq, grid["accidents"])
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          grid.plot(column="accidents", cmap="Reds", ax=axs[0], legend=True); axs[0].set_title("own value")
          grid.plot(column="acc_lag", cmap="Reds", ax=axs[1], legend=True); axs[1].set_title("average of neighbours")
          plt.show()
          """)
    nb.ex("2.3", "Map classes: quantiles vs natural breaks", "mapclassify.Quantiles(y, k=5) / NaturalBreaks",
          purpose_a="Splits values into classes: quantiles = same **number** of units per class; natural breaks = class borders at big jumps in the data.",
          life_a="Choosing breaks for a public map: the same data can look 'everywhere bad' or 'a few hot spots' depending on the method.",
          hint="Print both classifiers; they show the class borders and counts. With many zeros, quantiles struggle (several classes share the value 0).",
          starter="""
          y = grid["accidents"]
          print(mapclassify.____(y, k=5))
          print(mapclassify.____(y, k=5))
          """,
          solution="""
          y = grid["accidents"]
          print(mapclassify.Quantiles(y, k=5))
          print(mapclassify.NaturalBreaks(y, k=5))
          """)
    nb.ex("2.4", "Classified choropleth in one line", "gdf.plot(column=..., scheme='NaturalBreaks', k=5)",
          purpose_a="GeoPandas calls mapclassify for you when you pass `scheme=`.",
          life_a="The standard way to make publication maps with honest class breaks.",
          hint="Try `scheme=\"NaturalBreaks\"` and `scheme=\"EqualInterval\"`, `legend=True`.",
          starter="""
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          grid.plot(column="accidents", scheme="____", k=5, cmap="Reds", legend=True, ax=axs[0]); axs[0].set_title("natural breaks")
          grid.plot(column="accidents", scheme="EqualInterval", k=5, cmap="Reds", legend=True, ax=axs[1]); axs[1].set_title("equal interval")
          plt.show()
          """,
          solution="""
          fig, axs = plt.subplots(1, 2, figsize=(10, 4))
          grid.plot(column="accidents", scheme="NaturalBreaks", k=5, cmap="Reds", legend=True, ax=axs[0]); axs[0].set_title("natural breaks")
          grid.plot(column="accidents", scheme="EqualInterval", k=5, cmap="Reds", legend=True, ax=axs[1]); axs[1].set_title("equal interval")
          plt.show()
          """)

    nb.level(3, "Combining: global and local spatial autocorrelation", "measure clustering for the whole town (Moran's I), then find where the clusters are (LISA, Getis-Ord).",
             "First the doctor asks 'do you have a fever?' (global). Then 'where does it hurt?' (local).")
    nb.ex("3.1", "Global Moran's I", "esda.Moran(y, w)",
          purpose_a="One number for the whole map: I > 0 means similar values cluster, I ≈ 0 means random, I < 0 means a checkerboard. `p_sim` says how likely such an I is by chance (permutation test).",
          life_a="'Do high-accident cells sit next to other high-accident cells?' before deciding if a local hot-spot search makes sense.",
          hint="`mi = esda.Moran(grid[\"accidents\"], wq)`, then `mi.I`, `mi.EI` (expected under randomness ≈ −1/(n−1)), `mi.p_sim`.",
          starter="""
          mi = esda.____(grid["accidents"], wq)
          print(f"I = {mi.I:.3f}, expected if random = {mi.EI:.3f}, p = {mi.p_sim}")
          """,
          solution="""
          mi = esda.Moran(grid["accidents"], wq)
          print(f"I = {mi.I:.3f}, expected if random = {mi.EI:.3f}, p = {mi.p_sim}")
          """,
          note="The permutation test is the Monte Carlo idea from A3: shuffle the values over the cells 999 times and see how often I is as big.")
    nb.ex("3.2", "Sanity check: shuffle the map", "Moran on randomly shuffled values",
          purpose_q="What is the **purpose** of computing Moran's I on shuffled values?",
          purpose_a="Shuffling destroys any spatial pattern, so I should drop near 0 and p should be large. It proves you understand what Moran's I measures.",
          life_a="A good habit: test your method on data where you know the answer.",
          hint="`np.random.default_rng(0).permutation(grid[\"accidents\"].values)`.",
          starter="""
          shuffled = np.random.default_rng(0).____(grid["accidents"].values)
          m0 = esda.Moran(shuffled, wq)
          print(f"shuffled: I = {m0.I:.3f}, p = {m0.p_sim}")
          """,
          solution="""
          shuffled = np.random.default_rng(0).permutation(grid["accidents"].values)
          m0 = esda.Moran(shuffled, wq)
          print(f"shuffled: I = {m0.I:.3f}, p = {m0.p_sim}")
          """)
    nb.ex("3.3", "Local Moran (LISA): where are the clusters?", "esda.Moran_Local(y, w)",
          purpose_a="One statistic per unit. With `q` (quadrant) it labels each unit: 1 = High-High (hot spot), 2 = Low-High, 3 = Low-Low (cold spot), 4 = High-Low (outlier); `p_sim` says which are significant.",
          life_a="Finding the exact streets where accidents cluster, to place speed cameras.",
          hint="`lisa = esda.Moran_Local(grid[\"accidents\"], wq, seed=1)`. Significant hot spots: `(lisa.q == 1) & (lisa.p_sim < 0.05)`.",
          starter="""
          lisa = esda.____(grid["accidents"], wq, seed=1)
          labels = {1: "HH hot spot", 2: "LH", 3: "LL cold spot", 4: "HL outlier"}
          grid["lisa"] = [labels[q] if p < 0.05 else "not significant" for q, p in zip(lisa.q, lisa.p_sim)]
          print(grid["lisa"].value_counts())
          ax = grid.plot(column="lisa", categorical=True, legend=True, cmap="Set1", figsize=(6, 6), edgecolor="white")
          L["roads"].plot(ax=ax, color="black", linewidth=.6); plt.show()
          """,
          solution="""
          lisa = esda.Moran_Local(grid["accidents"], wq, seed=1)
          labels = {1: "HH hot spot", 2: "LH", 3: "LL cold spot", 4: "HL outlier"}
          grid["lisa"] = [labels[q] if p < 0.05 else "not significant" for q, p in zip(lisa.q, lisa.p_sim)]
          print(grid["lisa"].value_counts())
          ax = grid.plot(column="lisa", categorical=True, legend=True, cmap="Set1", figsize=(6, 6), edgecolor="white")
          L["roads"].plot(ax=ax, color="black", linewidth=.6); plt.show()
          """)
    nb.ex("3.4", "Getis-Ord Gi*: hot spots by intensity", "esda.G_Local(y, w, star=True)",
          purpose_a="For each unit, compares the sum of values around it (including itself) with the town average. Large positive z = hot spot, large negative = cold spot.",
          life_a="The classic 'hot-spot analysis' in crime and health studies (ArcGIS/QGIS call it Getis-Ord Gi*).",
          hint="Gi* needs **binary** weights (1 = neighbour, 0 = not): pass `transform=\"B\"` — without it, esda row-standardises silently. `g.Zs` are z-scores; |z| > 1.96 ≈ significant at 5 %.",
          starter="""
          wb = weights.Queen.from_dataframe(grid, use_index=False)
          g = esda.G_Local(grid["accidents"], wb, transform="____", star=True, seed=1)
          grid["gi_z"] = g.Zs
          print((grid["gi_z"] > 1.96).sum(), "hot cells,", (grid["gi_z"] < -1.96).sum(), "cold cells")
          grid.plot(column="gi_z", cmap="coolwarm", legend=True, vmin=-4, vmax=4, figsize=(5, 5)); plt.show()
          """,
          solution="""
          wb = weights.Queen.from_dataframe(grid, use_index=False)
          g = esda.G_Local(grid["accidents"], wb, transform="B", star=True, seed=1)
          grid["gi_z"] = g.Zs
          print((grid["gi_z"] > 1.96).sum(), "hot cells,", (grid["gi_z"] < -1.96).sum(), "cold cells")
          grid.plot(column="gi_z", cmap="coolwarm", legend=True, vmin=-4, vmax=4, figsize=(5, 5)); plt.show()
          """)

    nb.level(4, "Professional: statistical and modelling questions", "handle multiple testing, the areal unit problem, spatial regression, and point patterns.",
             "A careful scientist asks: would I get the same answer with a different grid? Am I fooled by testing 144 cells at once? Does my model leave a pattern behind?")
    nb.pro("4.1", "How many hot spots survive a stricter test?", "Statistical (multiple testing)",
           scenario="With 144 cells tested at p < 0.05, about 7 cells could look significant **by pure chance** (144 × 0.05). Use the False Discovery Rate (FDR) on the Gi* p-values (`g.p_norm`) to set a stricter threshold. How many hot cells remain?",
           plan_hint="`thr = esda.fdr(g.p_norm, 0.05)` returns a stricter p-threshold. Hot and significant = `(g.Zs > 0) & (g.p_norm <= thr)`. Daily picture: if 144 people each flip a coin 5 times, someone will get 5 heads — that is not magic.",
           starter="""
           thr = esda.____(g.p_norm, 0.05)
           loose = (g.Zs > 0) & (g.p_norm < 0.05)
           strict = (g.Zs > 0) & (g.p_norm <= thr)
           print(f"p < 0.05: {loose.sum()} hot cells | FDR (p <= {thr:.4f}): {strict.sum()} hot cells")
           ax = grid.plot(color="lightgrey", edgecolor="white", figsize=(5, 5)); grid[strict].plot(ax=ax, color="red")
           L["roads"].plot(ax=ax, color="black", linewidth=.6); ax.set_title("hot spots after FDR"); plt.show()
           """,
           solution="""
           thr = esda.fdr(g.p_norm, 0.05)
           loose = (g.Zs > 0) & (g.p_norm < 0.05)
           strict = (g.Zs > 0) & (g.p_norm <= thr)
           print(f"p < 0.05: {loose.sum()} hot cells | FDR (p <= {thr:.4f}): {strict.sum()} hot cells")
           ax = grid.plot(color="lightgrey", edgecolor="white", figsize=(5, 5)); grid[strict].plot(ax=ax, color="red")
           L["roads"].plot(ax=ax, color="black", linewidth=.6); ax.set_title("hot spots after FDR"); plt.show()
           """,
           answer="""
           Local statistics test many places at once, so some 'hot spots' are chance. The cells that survive FDR are the ones worth acting on — in Riverton they sit on the dangerous junctions.
           Note: esda also gives permutation p-values (`g.p_sim`). For skewed counts they are more cautious; report which p-values you used.
           """)
    nb.pro("4.2", "Does the answer change with the grid size? (MAUP)", "Statistical (modifiable areal unit problem)",
           scenario="Compute global Moran's I for accidents on grids of **250 m, 500 m and 1000 m**. Does the strength of clustering change?",
           plan_hint="Loop over sizes: `make_grid(size)`, Queen weights row-standardised, `esda.Moran`. Keep I and p in a small table.",
           starter="""
           rows = []
           for size in [250, 500, 1000]:
               gg = make_grid(size)
               ww = weights.Queen.from_dataframe(gg, use_index=False); ww.transform = "r"
               m = esda.Moran(gg["accidents"], ww)
               rows.append({"cell_m": size, "cells": len(gg), "I": round(m.I, 3), "p": m.p_sim})
           pd.DataFrame(rows)
           """,
           solution="""
           rows = []
           for size in [250, 500, 1000]:
               gg = make_grid(size)
               ww = weights.Queen.from_dataframe(gg, use_index=False); ww.transform = "r"
               m = esda.Moran(gg["accidents"], ww)
               rows.append({"cell_m": size, "cells": len(gg), "I": round(m.I, 3), "p": m.p_sim})
           pd.DataFrame(rows)
           """,
           answer="""
           I changes with the cell size: the result is partly an effect of how you cut space. This is the **Modifiable Areal Unit Problem** (MAUP).
           **Recommendation:** choose the unit from the process (accidents happen on streets → street segments, or a size that matches the planning decision), and report a sensitivity check like this one.
           """)
    nb.pro("4.3", "What explains accidents? OLS vs spatial regression", "Modelling (spatial regression)",
           scenario="""
           Model accidents per cell from `road_km` (primary road length) and `residents`. First fit an ordinary regression (OLS).
           Check whether its **residuals** are still spatially clustered (Moran's I of residuals). If yes, fit a **spatial lag model** and compare.
           """,
           plan_hint="""
           `y = grid[["accidents"]].values`, `X = grid[["road_km", "residents"]].values`.
           `ols = spreg.OLS(y, X, w=wq, spat_diag=True, moran=True, name_y=..., name_x=[...])` → `ols.moran_res` = (I, z, p).
           `lag = spreg.ML_Lag(y, X, w=wq, name_y=..., name_x=[...])` → `lag.rho` = how much a cell depends on its neighbours.
           Compare fit with `ols.aic` vs `lag.aic` (lower = better).
           """,
           starter="""
           y = grid[["accidents"]].values
           X = grid[["road_km", "residents"]].values
           ols = spreg.OLS(y, X, w=wq, spat_diag=True, moran=True, name_y="accidents", name_x=["road_km", "residents"])
           print("OLS coefficients:", ols.betas.ravel().round(3), "| residual Moran I, p:", np.round(ols.moran_res[0], 3), round(ols.moran_res[2], 4))
           lag = spreg.____(y, X, w=wq, name_y="accidents", name_x=["road_km", "residents"])
           print("lag rho:", round(float(lag.rho), 3), "| AIC OLS:", round(ols.aic, 1), " AIC lag:", round(lag.aic, 1))
           """,
           solution="""
           y = grid[["accidents"]].values
           X = grid[["road_km", "residents"]].values
           ols = spreg.OLS(y, X, w=wq, spat_diag=True, moran=True, name_y="accidents", name_x=["road_km", "residents"])
           print("OLS coefficients:", ols.betas.ravel().round(3), "| residual Moran I, p:", np.round(ols.moran_res[0], 3), round(ols.moran_res[2], 4))
           lag = spreg.ML_Lag(y, X, w=wq, name_y="accidents", name_x=["road_km", "residents"])
           print("lag rho:", round(float(lag.rho), 3), "| AIC OLS:", round(ols.aic, 1), " AIC lag:", round(lag.aic, 1))
           """,
           answer="""
           Road length is the main driver (each km of primary road adds several accidents per cell). If OLS residuals are still clustered, OLS breaks its assumption of independent errors,
           so its p-values are too optimistic. The spatial lag model adds 'the neighbours' accidents' as an explanation (`rho`). Compare AIC and the coefficients.
           Print `ols.summary` or `lag.summary` for the full report (with the LM tests that help choose between lag and error models).
           """,
           why="Spatial regression is the standard answer to 'which factors explain this spatial pattern?' when neighbours influence each other.")
    nb.pro("4.4", "Are accidents clustered as points? (Ripley's K)", "Statistical (point-pattern analysis)",
           scenario="Without any grid: are the 260 accident points more clustered than random points in the same area, and at which distances?",
           plan_hint="`pointpats.k_test(coords, n_simulations=99, keep_simulations=True)` compares Ripley's K with random patterns. Result: `support` (distances), `statistic` (K), `pvalue` per distance. Small p at a distance = clustered at that scale.",
           starter="""
           coords = np.column_stack([L["accidents"].geometry.x, L["accidents"].geometry.y])
           res = pointpats.____(coords, support=np.linspace(50, 1500, 12), n_simulations=99, keep_simulations=True)
           sims = res.simulations
           plt.plot(res.support, res.statistic, "r-", label="accidents")
           plt.fill_between(res.support, sims.min(axis=0), sims.max(axis=0), color="grey", alpha=.4, label="random envelope")
           plt.xlabel("distance (m)"); plt.ylabel("K(d)"); plt.legend(); plt.show()
           print(pd.DataFrame({"d": res.support.round(), "p": res.pvalue.round(3)}).T)
           """,
           solution="""
           coords = np.column_stack([L["accidents"].geometry.x, L["accidents"].geometry.y])
           res = pointpats.k_test(coords, support=np.linspace(50, 1500, 12), n_simulations=99, keep_simulations=True)
           sims = res.simulations
           plt.plot(res.support, res.statistic, "r-", label="accidents")
           plt.fill_between(res.support, sims.min(axis=0), sims.max(axis=0), color="grey", alpha=.4, label="random envelope")
           plt.xlabel("distance (m)"); plt.ylabel("K(d)"); plt.legend(); plt.show()
           print(pd.DataFrame({"d": res.support.round(), "p": res.pvalue.round(3)}).T)
           """,
           answer="If the red line is above the grey envelope, accidents are more clustered than random at that distance. No grid = no MAUP. Same caution as before: 'random' here means anywhere in the box, not only on streets.")

    nb.test("""
    For each: **question type → which weights / method and why → code → interpretation (including one limitation).**
    """, [
        ("stat", """
        **A.** Is air pollution (PM2.5) at the 18 sensors spatially autocorrelated? Choose suitable weights.
        """, """
        Points → KNN weights (no islands). Only 18 sensors, so use few neighbours.
        ```python
        wk4 = weights.KNN.from_dataframe(L["sensors"], k=4); wk4.transform = "r"
        m = esda.Moran(L["sensors"]["pm25"], wk4)
        print(round(m.I, 3), m.p_sim)
        ```
        With 18 points, the test has little power: a non-significant p does **not** prove there is no pattern.
        """),
        ("task", """
        **B.** Find the **residents** hot spots (where many people live) on the 500 m grid with Getis-Ord Gi*, and list the 5 cells with the highest z-score.
        """, """
        ```python
        gr = esda.G_Local(grid["residents"], wb, transform="B", star=True, seed=1)
        print(grid.assign(z=gr.Zs).nlargest(5, "z")[["cell", "residents", "z"]])
        ```
        """),
        ("decision", """
        **C.** The police can install **3 speed cameras**. Using your analysis, where would you put them and why? What extra data would you want first?
        """, """
        Pick cells that are **significant HH hot spots after FDR** (4.1) **and** lie on primary roads; among them, choose those with the most serious/fatal accidents.
        Extra data: traffic volume (accidents per vehicle-km is fairer than raw counts), speed measurements, accident causes.
        Recommendation: rank by rate (per traffic) rather than by count, because busy roads have more accidents simply because more cars pass.
        """),
        ("model", """
        **D · Modelling.** For your own research: you want to check whether **poor health clusters** in a city and **what explains it** (income, green space, pollution).
        Describe the full modelling plan with PySAL, step by step.
        """, """
        1. Units: small areas (census tracts) or a grid; justify the choice (MAUP) and plan a sensitivity check.
        2. Weights: Queen for areas (or KNN); row-standardise.
        3. Map with honest classes (mapclassify), then global Moran's I on the health rate. For rates with small populations use `esda.Moran_Rate` (it corrects unstable rates).
        4. LISA / Gi* for local clusters; FDR correction.
        5. OLS with income, green space (NDVI from A5), pollution; test the residuals with Moran's I and the LM tests.
        6. If there is spatial dependence: spatial lag (neighbours' health influences) or spatial error (unmeasured spatial factors) model; compare AIC and interpret.
        7. Report limits: ecological fallacy (area results do not describe individuals), MAUP, causality.
        """),
    ])
    nb.reflect("""
    Which spatial-statistics question appears in your PhD topic? Write it in one sentence, and name the weights and the method you would start with.
    """)
    return nb
