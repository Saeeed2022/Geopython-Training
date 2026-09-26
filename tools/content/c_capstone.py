from nbbuild import NB, SETUP


def build():
    nb = NB("C_capstone", "C · Capstone — the Riverton 'Safe and Healthy Town' report")
    nb.md("""
    **The brief (from Riverton's mayor):**
    > "Next year we can build **one new clinic** and **one new primary school**. Before we decide, tell me:
    > who is badly served today, who is exposed to floods, where accidents concentrate, and where the two new buildings should go.
    > I need a map, a table, and a clear recommendation."

    **Your job:** use every library from the course. For each task you write:
    1. the **question type** (from `00_START_HERE`),
    2. the **libraries** and **where** each step happens (Python or PostGIS),
    3. your **assumptions**,
    4. the code and a one-sentence result.

    Model answers are hidden under each task. Try first; compare after.

    ⚙️ Needs the PostGIS database from B0 (for tasks 2 and 6). The other tasks run without it.
    """)
    nb.md("""
    ## Step 0 · Your project plan (write before coding)

    | Task | Question | Type | Libraries | Where |
    |---|---|---|---|---|
    | 1 | Profile of each neighbourhood | … | … | … |
    | 2 | Access to clinics and schools | … | … | … |
    | 3 | Flood exposure (two models) | … | … | … |
    | 4 | Are accidents clustered? | … | … | … |
    | 5 | Heat/age vulnerability index | … | … | … |
    | 6 | Best sites for the clinic and the school | … | … | … |
    | 7 | Deliver: map + table + data | … | … | … |
    """)
    nb.code(SETUP)
    nb.code("""
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import shapely
    import rasterio
    import matplotlib.pyplot as plt
    L = {name: gpd.read_file(GPKG, layer=name) for name in
         ["neighbourhoods", "houses", "schools", "clinics", "roads", "river", "parks", "accidents", "sensors"]}
    nbh = L["neighbourhoods"].copy()
    """)
    nb.test("""
    Seven tasks. Each one builds on the previous ones. Keep your variables — task 7 uses them.
    """, [
        ("task", """
        **Task 1 · Neighbourhood profile (descriptive).** Build one table per neighbourhood with: density (people/km²), share over 65,
        number of accidents, park area (ha), mean NDVI (from `satellite.tif`).
        """, """
        Type: descriptive. Libraries: GeoPandas (joins, overlay), Rasterio (zonal NDVI). All in Python — small data.
        ```python
        from rasterio.mask import mask
        nbh["density"] = nbh["population"] / (nbh.area / 1e6)
        acc = gpd.sjoin(L["accidents"], nbh[["name", "geometry"]], predicate="within")["name"].value_counts()
        nbh["accidents"] = nbh["name"].map(acc).fillna(0).astype(int)
        pk = gpd.overlay(nbh[["name", "geometry"]], L["parks"], how="intersection")
        nbh["park_ha"] = nbh["name"].map(pk.assign(ha=pk.area / 1e4).groupby("name")["ha"].sum()).fillna(0)
        with rasterio.open(DATA_DIR / "satellite.tif") as sat:
            vals = []
            for g in nbh.geometry:
                arr, _ = mask(sat, [g], crop=True)
                red, nir = arr[0].astype(float), arr[1].astype(float)
                vals.append(float(np.nanmean((nir - red) / (nir + red))))
        nbh["ndvi"] = vals
        nbh[["name", "density", "pct_over65", "accidents", "park_ha", "ndvi"]].round(2)
        ```
        """),
        ("task", """
        **Task 2 · Access (proximity), in PostGIS.** Per neighbourhood: share of residents within 800 m of a clinic **and** within 800 m of a primary school.
        Read the result into GeoPandas.
        """, """
        Type: proximity/accessibility. Heavy part in PostGIS (index + `ST_DWithin`), result read with `read_postgis`.
        ```python
        from geotrain.db import engine
        q = \"\"\"
            WITH h AS (
                SELECT nb_id, residents,
                       EXISTS (SELECT 1 FROM clinics c WHERE ST_DWithin(h.geometry, c.geometry, 800)) AS clinic,
                       EXISTS (SELECT 1 FROM schools s WHERE s.level = 'primary' AND ST_DWithin(h.geometry, s.geometry, 800)) AS school
                FROM houses h)
            SELECT n.nb_id,
                   sum(residents) FILTER (WHERE clinic)::float / sum(residents) AS share_clinic,
                   sum(residents) FILTER (WHERE school)::float / sum(residents) AS share_school,
                   n.geometry
            FROM h JOIN neighbourhoods n USING (nb_id) GROUP BY n.nb_id, n.geometry
        \"\"\"
        access = gpd.read_postgis(q, engine(), geom_col="geometry")
        nbh = nbh.merge(access[["nb_id", "share_clinic", "share_school"]], on="nb_id")
        nbh[["name", "share_clinic", "share_school"]].round(2)
        ```
        """),
        ("model", """
        **Task 3 · Flood exposure: compare two models.** Model A: houses within 150 m of the river (Shapely/GeoPandas buffer).
        Model B: houses on land lower than river level + 2 m (Rasterio DEM). How many residents does each find, and which do you trust more? Why?
        """, """
        Type: modelling + model comparison.
        ```python
        river = L["river"].geometry.iloc[0]
        H = L["houses"].copy()
        H["flood_A"] = shapely.dwithin(H.geometry.values, river, 150)
        with rasterio.open(DATA_DIR / "dem.tif") as dem:
            pts = [river.interpolate(d) for d in np.arange(200, river.length - 200, 100)]
            level = np.median([v[0] for v in dem.sample([(p.x, p.y) for p in pts])])
            H["elev"] = [v[0] for v in dem.sample(list(zip(H.geometry.x, H.geometry.y)))]
        H["flood_B"] = H["elev"] < level + 2
        print("A:", H.loc[H.flood_A, "residents"].sum(), " B:", H.loc[H.flood_B, "residents"].sum(),
              " both:", H.loc[H.flood_A & H.flood_B, "residents"].sum())
        nbh["flood_res"] = nbh["nb_id"].map(H[H.flood_B].groupby("nb_id")["residents"].sum()).fillna(0)
        ```
        Model B follows the terrain, so it finds low houses further from the river and ignores high ones near it. **Trust B more**, but say its limits (no dykes, no connectivity check).
        """),
        ("stat", """
        **Task 4 · Are accidents clustered near primary roads?** Give a p-value with a Monte Carlo test, and name one weakness of your 'random' model.
        """, """
        ```python
        prim = L["roads"].query("road_type == 'primary'").union_all()
        real = L["accidents"].distance(prim).mean()
        rng = np.random.default_rng(0)
        x0, y0, x1, y1 = nbh.total_bounds
        sims = np.array([shapely.distance(shapely.points(rng.uniform(x0, x1, 260), rng.uniform(y0, y1, 260)), prim).mean() for _ in range(199)])
        print(round(real), round(sims.mean()), ((sims <= real).sum() + 1) / 200)
        ```
        p = 0.005 → clustered. Weakness: random points are spread over all land, but accidents can only happen on streets; a fairer test places random points on the street network.
        """),
        ("model", """
        **Task 5 · Vulnerability index (modelling).** Build a simple index per neighbourhood from 0 (low) to 1 (high):
        higher `pct_over65`, lower `ndvi`, lower `share_clinic`, higher `flood_res` share → more vulnerable. Use equal weights. Which neighbourhoods rank highest?
        Then test: does the top-3 change if the weight of age is doubled?
        """, """
        ```python
        def scale(s):
            return (s - s.min()) / (s.max() - s.min())
        parts = pd.DataFrame({
            "age": scale(nbh["pct_over65"]),
            "green": 1 - scale(nbh["ndvi"]),
            "clinic": 1 - scale(nbh["share_clinic"]),
            "flood": scale(nbh["flood_res"] / nbh["population"]),
        })
        nbh["vuln"] = parts.mean(axis=1)
        nbh["vuln_age2"] = (parts["age"] * 2 + parts[["green", "clinic", "flood"]].sum(axis=1)) / 5
        print(nbh.nlargest(3, "vuln")["name"].tolist(), nbh.nlargest(3, "vuln_age2")["name"].tolist())
        ```
        A composite index = rescale + weight + combine. The weight test is a **sensitivity analysis**: if the top-3 stays the same, the result is robust; if not, report both.
        """),
        ("decision", """
        **Task 6 · Where should the new clinic and the new primary school go? (decision)**
        Rules for both: outside the 2 m flood model, more than 1 000 m from an existing facility of the same kind.
        Clinic score = vulnerable residents (residents × neighbourhood `vuln`) within 800 m.
        School score = modelled children (5 % of residents) within 800 m who are currently **more than** 800 m from a primary school.
        Use a 250 m candidate grid.
        """, """
        ```python
        x0, y0, x1, y1 = nbh.total_bounds
        xs, ys = np.meshgrid(np.arange(x0 + 125, x1, 250), np.arange(y0 + 125, y1, 250))
        grid = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs.ravel(), ys.ravel()), crs=nbh.crs)
        with rasterio.open(DATA_DIR / "dem.tif") as dem:
            grid["elev"] = [v[0] for v in dem.sample(list(zip(grid.geometry.x, grid.geometry.y)))]
        grid = grid[grid["elev"] >= level + 2]
        H = H.merge(nbh[["nb_id", "vuln"]], on="nb_id")
        prim_sch = L["schools"].query("level == 'primary'")
        H["far_school"] = H.distance(prim_sch.union_all()) > 800

        def best(cands, weights):
            rings = cands.assign(geometry=cands.buffer(800)).reset_index(names="cid")
            j = gpd.sjoin(H.assign(w=weights), rings, predicate="within")
            score = j.groupby("cid")["w"].sum()
            return rings.loc[score.idxmax(), "geometry"].centroid, round(score.max())

        c_cand = grid[grid.distance(L["clinics"].union_all()) > 1000]
        s_cand = grid[grid.distance(prim_sch.union_all()) > 1000]
        print("clinic:", best(c_cand, H["residents"] * H["vuln"]))
        print("school:", best(s_cand, H["residents"] * 0.05 * H["far_school"]))
        ```
        Report the sites **and** the rules. A good recommendation also says: "If we change the distance rule to 800 m, the best site moves to …" (sensitivity).
        """),
        ("task", """
        **Task 7 · Deliver.** Save the neighbourhood table (with all indicators) to a GeoPackage **and** to PostGIS as `riverton_report`, and draw one final map:
        vulnerability colours, clinics, schools, and your two proposed sites.
        """, """
        ```python
        from geotrain.db import engine
        out = nbh[["name", "population", "density", "pct_over65", "accidents", "park_ha", "ndvi",
                   "share_clinic", "share_school", "flood_res", "vuln", "geometry"]]
        out.to_file(DATA_DIR / "riverton_report.gpkg", layer="report", driver="GPKG")
        out.to_postgis("riverton_report", engine(), if_exists="replace", index=False)
        clinic_site, _ = best(c_cand, H["residents"] * H["vuln"])
        school_site, _ = best(s_cand, H["residents"] * 0.05 * H["far_school"])
        ax = out.plot(column="vuln", cmap="OrRd", legend=True, edgecolor="grey", figsize=(7, 7))
        L["river"].plot(ax=ax, color="steelblue", linewidth=3)
        L["clinics"].plot(ax=ax, color="red", marker="+", markersize=120, label="clinic")
        prim_sch.plot(ax=ax, color="blue", marker="^", markersize=60, label="primary school")
        gpd.GeoSeries([clinic_site], crs=nbh.crs).plot(ax=ax, color="red", marker="*", markersize=400, label="NEW clinic")
        gpd.GeoSeries([school_site], crs=nbh.crs).plot(ax=ax, color="blue", marker="*", markersize=400, label="NEW school")
        ax.legend(loc="lower left"); ax.set_title("Riverton: vulnerability and proposed sites"); plt.show()
        ```
        Your written recommendation should have 3 parts: **what** (the two sites), **why** (scores and rules), **how sure** (assumptions + sensitivity).
        """),
    ])
    nb.reflect("""
    Look back at the three lines you wrote in `00_START_HERE`.
    1. Can you now answer the question you wrote there? Which steps are still missing?
    2. What is your **next 3-month plan**? (Suggested next topics: networks with OSMnx / pgRouting, spatial statistics with PySAL/esda, interactive maps with folium or lonboard, and your own city's open data.)
    """)
    return nb
