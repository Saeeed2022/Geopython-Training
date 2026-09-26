from nbbuild import NB, SETUP


def build():
    nb = NB("A1_shapely", "A1 · Shapely — one shape at a time")
    nb.md("""
    **What Shapely is:** a library to create, change and measure **single geometries**: points, lines, polygons.
    It does no maps, no files and no coordinate systems. It is pure geometry on a flat sheet of paper.

    **Engine:** Shapely calls **GEOS** (a C++ library). PostGIS calls the same GEOS. So what you learn here
    comes back in SQL later (`buffer` → `ST_Buffer`, `intersects` → `ST_Intersects`).

    **Daily picture:** think of a sheet of squared paper. Shapely lets you draw a dot, a line or a shape on it,
    and then answer questions like "how long?", "how big?", "do these two overlap?".

    **Where this fits in your plan:** GeoPandas = a table where every row has one Shapely shape.
    If you understand one shape here, you understand the whole column later.

    ⚠️ Shapely does not know about metres or degrees. In this notebook all coordinates are **metres** on a flat plane.
    """)
    nb.code("""
    import shapely
    from shapely import Point, LineString, Polygon, MultiPoint
    print("Shapely", shapely.__version__, "| GEOS", shapely.geos_version_string)
    """)

    # ---------------------------------------------------------------- level 1
    nb.level(1, "Basics: create and inspect shapes", "draw points, lines and polygons and read their basic properties.",
             "A point is your front door. A line is the path to the bus stop. A polygon is your garden.")
    nb.ex("1.1", "Your first point", "Point(x, y)",
          purpose_a="Creates a single location (a dot) from an x and a y coordinate.",
          life_a="Store the location of a school, a tree, a bus stop or a GPS reading.",
          hint="Write `Point(x, y)` with x = 3 and y = 4. Then read `.x`, `.y` and `.wkt` (a text version of the shape).",
          task="Create a point `home` at x=3, y=4 and print its x, y and WKT text.",
          starter="""
          home = Point(____, ____)
          print(home.x, home.y)
          print(home.____)
          """,
          solution="""
          home = Point(3, 4)
          print(home.x, home.y)
          print(home.wkt)
          """)
    nb.ex("1.2", "A line and its length", "LineString([...]).length",
          purpose_a="`LineString` joins points in order into a line; `.length` sums the length of all its segments.",
          life_a="Length of a cycle path, a pipeline or a planned bus route.",
          hint="A line takes a **list of (x, y) pairs**. From (0,0) to (3,4) is 5 (think of the 3-4-5 triangle, like a ladder against a wall), then (3,4) to (3,10) is 6.",
          task="Make a walk from (0,0) → (3,4) → (3,10). How long is it?",
          starter="""
          walk = LineString([(____, ____), (3, 4), (____, ____)])
          print(walk.____)
          """,
          solution="""
          walk = LineString([(0, 0), (3, 4), (3, 10)])
          print(walk.length)   # 5 + 6 = 11
          """)
    nb.ex("1.3", "A polygon: area and perimeter", "Polygon([...]).area",
          purpose_a="`Polygon` closes a ring of points into a surface; `.area` gives its surface and `.length` its perimeter.",
          life_a="Area of a building plot, a park or a flood zone; perimeter = how much fence you need.",
          hint="A 20 × 10 rectangle. Area = 20 × 10 = 200 (like counting floor tiles). Perimeter = 20+10+20+10 = 60. You do not need to repeat the first point at the end.",
          task="Make a garden 20 m wide and 10 m deep. Print area and perimeter.",
          starter="""
          garden = Polygon([(0, 0), (____, 0), (20, ____), (0, 10)])
          print("area:", garden.____, " perimeter:", garden.____)
          """,
          solution="""
          garden = Polygon([(0, 0), (20, 0), (20, 10), (0, 10)])
          print("area:", garden.area, " perimeter:", garden.length)
          """)
    nb.ex("1.4", "Shapes as text (WKT) and back", "shapely.from_wkt()",
          purpose_a="Turns WKT text (Well-Known Text, e.g. `POINT (3 4)`) into a Shapely geometry; `.wkt` does the reverse.",
          life_a="Copying a shape from a PostGIS query result, a CSV cell or a QGIS window into Python.",
          hint="WKT for a triangle: `'POLYGON ((0 0, 4 0, 0 3, 0 0))'`. In WKT the ring **is** closed (the first point repeated).",
          task="Read this triangle from text and print its area (should be 4 × 3 / 2 = 6).",
          starter="""
          tri = shapely.____("POLYGON ((0 0, 4 0, 0 3, 0 0))")
          print(tri.area)
          """,
          solution="""
          tri = shapely.from_wkt("POLYGON ((0 0, 4 0, 0 3, 0 0))")
          print(tri.area)
          """)
    nb.ex("1.5", "Bounding box", ".bounds and .envelope",
          purpose_a="`.bounds` gives (minx, miny, maxx, maxy); `.envelope` gives the smallest upright rectangle around the shape.",
          life_a="Quick 'rough area' filters, e.g. download only satellite images that cover the box of your city.",
          hint="Use the triangle `tri` from 1.4. The box goes from x=0..4 and y=0..3.",
          starter="""
          print(tri.____)
          print(tri.____.wkt)
          """,
          solution="""
          print(tri.bounds)
          print(tri.envelope.wkt)
          """)

    # ---------------------------------------------------------------- level 2
    nb.level(2, "Core tools: measure and relate", "one command, one job: distance, buffer, and the yes/no spatial tests.",
             "Is my house inside the parking zone? How far is it to the bakery? What is the area 100 m around the school?")
    nb.code("""
    school = Point(0, 0)
    house_a = Point(300, 400)          # 500 m from the school (3-4-5 triangle x 100)
    house_b = Point(900, 50)
    park = Polygon([(200, 200), (600, 200), (600, 600), (200, 600)])
    """)
    nb.ex("2.1", "Distance", "a.distance(b)",
          purpose_a="Gives the shortest straight-line distance between two geometries (0 if they touch or overlap).",
          life_a="Straight-line distance from each house to the nearest school ('as the crow flies').",
          hint="Call it on one geometry and pass the other: `school.distance(house_a)`. Expect 500.",
          starter="""
          print(school.____(house_a))
          print(school.____(house_b))
          print(house_b.distance(____))     # distance from house_b to the park polygon
          """,
          solution="""
          print(school.distance(house_a))
          print(school.distance(house_b))
          print(house_b.distance(park))
          """,
          note="Distance to a polygon is measured to its **nearest edge**, not to its centre.")
    nb.ex("2.2", "Buffer", "geom.buffer(d)",
          purpose_a="Makes a new polygon containing every place within distance `d` of the geometry.",
          life_a="'Everything within 500 m of the school' (a catchment), or a 50 m noise zone along a road.",
          hint="`school.buffer(500)` is a circle of radius 500. Its area should be close to π × 500² ≈ 785 398 (a circle is drawn with many small straight sides, so slightly less).",
          task="Make a 500 m buffer around the school and compare its area with π·r².",
          starter="""
          import math
          zone = school.____(500)
          print(zone.area, math.pi * 500**2)
          """,
          solution="""
          import math
          zone = school.buffer(500)
          print(zone.area, math.pi * 500**2)
          """)
    nb.ex("2.3", "Inside or not?", "polygon.contains(point) / point.within(polygon)",
          purpose_a="Yes/no test: is one geometry completely inside the other? `a.contains(b)` equals `b.within(a)`.",
          life_a="Is this address inside the resident-parking zone? Is this tree inside the protected area?",
          hint="Use `zone` from 2.2. house_a is exactly 500 m away — on the edge! Points on the boundary are **not** 'within'. Try `house_a.within(zone)` and `zone.contains(Point(100, 100))`.",
          starter="""
          print(zone.____(Point(100, 100)))
          print(house_a.____(zone))
          print(house_b.within(zone))
          """,
          solution="""
          print(zone.contains(Point(100, 100)))   # True
          print(house_a.within(zone))            # False: on/near the edge
          print(house_b.within(zone))            # False
          """,
          note="Boundary cases matter. If 'on the edge' should count, use `zone.covers(p)` or `p.distance(school) <= 500`.")
    nb.ex("2.4", "Touch, overlap, intersect", "a.intersects(b) / a.touches(b)",
          purpose_a="`intersects` = do they share **any** point? `touches` = do they meet **only at the edge**, without overlapping?",
          life_a="Which plots border the road (touches)? Which plots are affected by a flood zone (intersects)?",
          hint="Two squares side by side share only an edge → touches=True, intersects=True. A square overlapping the park → touches=False, intersects=True.",
          starter="""
          plot1 = Polygon([(600, 200), (800, 200), (800, 400), (600, 400)])   # starts where the park ends
          plot2 = Polygon([(500, 500), (700, 500), (700, 700), (500, 700)])   # overlaps the park
          print("plot1:", park.____(plot1), park.____(plot1))
          print("plot2:", park.intersects(plot2), park.touches(plot2))
          """,
          solution="""
          plot1 = Polygon([(600, 200), (800, 200), (800, 400), (600, 400)])
          plot2 = Polygon([(500, 500), (700, 500), (700, 700), (500, 700)])
          print("plot1:", park.intersects(plot1), park.touches(plot1))   # True True
          print("plot2:", park.intersects(plot2), park.touches(plot2))   # True False
          """)
    nb.ex("2.5", "Centre points", ".centroid vs .representative_point()",
          purpose_a="`centroid` = the balance point of the shape (may fall outside it); `representative_point()` = a point **guaranteed inside**.",
          life_a="Placing a label on a map, or turning districts into points for a distance calculation.",
          hint="An L-shaped (or U-shaped) building has its balance point in the empty corner — like a boomerang's centre of mass lies in the air. Test `.within(shape)` for both.",
          starter="""
          u_shape = Polygon([(0, 0), (30, 0), (30, 30), (20, 30), (20, 10), (10, 10), (10, 30), (0, 30)])
          c = u_shape.____
          r = u_shape.____()
          print(c, c.within(u_shape))
          print(r, r.within(u_shape))
          """,
          solution="""
          u_shape = Polygon([(0, 0), (30, 0), (30, 30), (20, 30), (20, 10), (10, 10), (10, 30), (0, 30)])
          c = u_shape.centroid
          r = u_shape.representative_point()
          print(c, c.within(u_shape))   # outside!
          print(r, r.within(u_shape))   # inside
          """)

    # ---------------------------------------------------------------- level 3
    nb.level(3, "Combining: overlay and line tools", "chain commands to answer small planning questions.",
             "Cut the flood zone out of the park; put a bus stop every 400 m along a road.")
    nb.ex("3.1", "Intersection: the shared part", "a.intersection(b)",
          purpose_a="Returns the geometry where a and b overlap (the part they share).",
          life_a="Which part of the park lies inside the 500 m school zone? How much of a plot is in the flood zone?",
          hint="`park.intersection(zone)`. Then take `.area`. Share = shared area / park area.",
          task="What share (%) of the park lies within 500 m of the school?",
          starter="""
          shared = park.____(zone)
          print(round(100 * shared.area / park.____, 1), "%")
          """,
          solution="""
          shared = park.intersection(zone)
          print(round(100 * shared.area / park.area, 1), "%")
          """)
    nb.ex("3.2", "Union: melt shapes together", "shapely.union_all([...])",
          purpose_a="Merges many geometries into one, removing the overlaps (like melting ice cubes into one block).",
          life_a="Merge the catchments of 3 schools into one 'served area', so overlapping parts are not counted twice.",
          hint="Put the three buffers in a list. The union area is **smaller** than the sum of areas because overlaps count once.",
          starter="""
          stops = [Point(0, 0), Point(600, 0), Point(1200, 0)]
          circles = [p.buffer(400) for p in stops]
          merged = shapely.____(circles)
          print("sum:", round(sum(c.area for c in circles)), " union:", round(merged.____))
          """,
          solution="""
          stops = [Point(0, 0), Point(600, 0), Point(1200, 0)]
          circles = [p.buffer(400) for p in stops]
          merged = shapely.union_all(circles)
          print("sum:", round(sum(c.area for c in circles)), " union:", round(merged.area))
          """)
    nb.ex("3.3", "Difference: cut away", "a.difference(b)",
          purpose_a="Returns the part of `a` that is **not** in `b` (a cookie cutter).",
          life_a="Buildable land = plot minus protected area minus 20 m road setback.",
          hint="`park.difference(zone)` = the park **outside** the school zone. Check: difference area + intersection area = park area.",
          starter="""
          outside = park.____(zone)
          print(outside.area + shared.area, park.area)
          """,
          solution="""
          outside = park.difference(zone)
          print(outside.area + shared.area, park.area)
          """)
    nb.ex("3.4", "Walking along a line", "line.interpolate(d) / line.project(p)",
          purpose_a="`interpolate(d)` gives the point at distance d along the line; `project(p)` gives how far along the line a point lies.",
          life_a="Put a bus stop every 400 m on a route; find 'kilometre 2.3' on a motorway where an accident happened.",
          hint="Loop d over `range(0, int(road.length) + 1, 400)`. For project: a point off the road is first moved to the closest spot on it.",
          task="Place stops every 400 m along the road, then find how far along the road the café lies.",
          starter="""
          road = LineString([(0, 0), (1000, 0), (1000, 800)])     # 1800 m long
          stops = [road.____(d) for d in range(0, int(road.length) + 1, 400)]
          print([s.coords[0] for s in stops])
          cafe = Point(1050, 300)
          print("café is at", road.____(cafe), "m along the road")
          """,
          solution="""
          road = LineString([(0, 0), (1000, 0), (1000, 800)])
          stops = [road.interpolate(d) for d in range(0, int(road.length) + 1, 400)]
          print([s.coords[0] for s in stops])
          cafe = Point(1050, 300)
          print("café is at", road.project(cafe), "m along the road")   # 1300
          """)
    nb.ex("3.5", "Nearest points between two shapes", "shapely.ops.nearest_points(a, b)",
          purpose_a="Returns the pair of points (one on each shape) that are closest to each other.",
          life_a="Where should the footpath from the new housing estate join the existing road? Where exactly is the river closest to a house?",
          hint="`from shapely.ops import nearest_points`. It returns a tuple `(point_on_a, point_on_b)`. The distance between them equals `a.distance(b)`.",
          starter="""
          from shapely.ops import ____
          house = Point(400, 300)
          p_house, p_road = nearest_points(house, road)
          print(p_road, house.distance(road), p_house.distance(p_road))
          """,
          solution="""
          from shapely.ops import nearest_points
          house = Point(400, 300)
          p_house, p_road = nearest_points(house, road)
          print(p_road, house.distance(road), p_house.distance(p_road))
          """)
    nb.ex("3.6", "Simplify", "geom.simplify(tolerance)",
          purpose_a="Removes small wiggles (vertices) while keeping the shape within `tolerance` of the original.",
          life_a="Make a very detailed coastline light enough for a web map, or speed up heavy calculations.",
          hint="The circle has many vertices. Count them with `len(shape.exterior.coords)`. A bigger tolerance → fewer vertices, and a slightly smaller area.",
          starter="""
          circle = Point(0, 0).buffer(100, quad_segs=64)
          light = circle.____(5)
          print(len(circle.exterior.coords), "->", len(light.exterior.coords))
          print(round(circle.area), round(light.area))
          """,
          solution="""
          circle = Point(0, 0).buffer(100, quad_segs=64)
          light = circle.simplify(5)
          print(len(circle.exterior.coords), "->", len(light.exterior.coords))
          print(round(circle.area), round(light.area))
          """)
    nb.ex("3.7", "Broken shapes and how to repair them", "shapely.make_valid(geom)",
          purpose_a="`.is_valid` tells if a shape follows the rules (e.g. no self-crossing); `make_valid` repairs it.",
          life_a="Data digitised by hand often has 'bow-tie' polygons; many operations fail or give wrong areas until you fix them.",
          hint="A bow-tie (figure 8) crosses itself. Its `.area` is 0 because the two halves cancel out — like +1 and −1. `shapely.is_valid_reason(g)` explains why.",
          starter="""
          bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
          print(bowtie.is_valid, shapely.is_valid_reason(bowtie), bowtie.area)
          fixed = shapely.____(bowtie)
          print(fixed.geom_type, fixed.is_valid, fixed.area)
          """,
          solution="""
          bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
          print(bowtie.is_valid, shapely.is_valid_reason(bowtie), bowtie.area)
          fixed = shapely.make_valid(bowtie)
          print(fixed.geom_type, fixed.is_valid, fixed.area)   # MultiPolygon, True, 50
          """)

    # ---------------------------------------------------------------- level 4
    nb.level(4, "Professional: real questions in Riverton", "first name the question type, then plan, then code. Work with thousands of shapes quickly.",
             "A planner does not ask 'how do I buffer?'. They ask 'how many people live near the new station?'. You translate that into commands.")
    nb.md("We take Riverton's geometries out of the file as plain Shapely objects (GeoPandas is only used to open the file here).")
    nb.code(SETUP)
    nb.code("""
    import numpy as np
    import geopandas as gpd
    houses = gpd.read_file(GPKG, layer="houses").geometry.values          # ~1600 Shapely points
    residents = gpd.read_file(GPKG, layer="houses")["residents"].to_numpy()
    river = gpd.read_file(GPKG, layer="river").geometry.iloc[0]           # one LineString
    roads = gpd.read_file(GPKG, layer="roads")
    parks = gpd.read_file(GPKG, layer="parks").set_index("park").geometry
    station = Point(392_600, 5_821_200)                                   # a planned metro station
    print(len(houses), "houses | river length:", round(river.length), "m")
    """)
    nb.pro("4.1", "How many people live near the new station?", "Proximity (+ descriptive count)",
           scenario="The city plans a metro station at `station`. How many residents live within **800 m** (≈10 minutes walking)?",
           plan_hint="1) buffer the station by 800 m, 2) test each house with a **vectorised** function: `shapely.within(houses, zone)` tests all houses at once (like scanning all barcodes in one go instead of one by one), 3) sum the residents of the houses that are inside.",
           starter="""
           zone = station.____(800)
           inside = shapely.____(houses, zone)        # array of True/False
           print(inside.sum(), "houses,", residents[____].sum(), "residents")
           """,
           solution="""
           zone = station.buffer(800)
           inside = shapely.within(houses, zone)
           print(inside.sum(), "houses,", residents[inside].sum(), "residents")
           """,
           answer="Buffer + point-in-polygon + sum. The vectorised call is much faster than a Python loop.",
           why="Walking distance ≠ straight-line distance. A buffer is a first model. A professional would mention that a network (street) distance is more exact — see the test.")
    nb.pro("4.2", "How much of each park may flood?", "Overlay + measurement",
           scenario="Assume everything within **150 m** of the river may flood. For each park, what share (%) of its area is in that zone?",
           plan_hint="flood = river.buffer(150). For each park: `park.intersection(flood).area / park.area`.",
           starter="""
           flood = river.buffer(____)
           for name, geom in parks.items():
               share = geom.____(flood).area / geom.area
               print(f"{name:12s} {share:6.1%}")
           """,
           solution="""
           flood = river.buffer(150)
           for name, geom in parks.items():
               share = geom.intersection(flood).area / geom.area
               print(f"{name:12s} {share:6.1%}")
           """,
           answer="Overlay (intersection) and measurement (area ratio). A 150 m buffer is a *crude* flood model: real floods follow elevation (see Rasterio A5).")
    nb.pro("4.3", "Where can we build a playground?", "Decision / suitability",
           scenario="Find the land inside **River Park** that is (a) **more than 50 m from any road** (noise, safety) and (b) **outside the 150 m flood zone**. How many m² remain?",
           plan_hint="Start from the park, then subtract step by step: `park.difference(roads_buffer).difference(flood)`. Merge all road buffers first with `union_all`.",
           starter="""
           road_zone = shapely.union_all([g.buffer(____) for g in roads.geometry])
           ok = parks["River Park"].difference(____).difference(____)
           print(round(ok.area), "m² suitable")
           """,
           solution="""
           road_zone = shapely.union_all([g.buffer(50) for g in roads.geometry])
           ok = parks["River Park"].difference(road_zone).difference(flood)
           print(round(ok.area), "m² suitable")
           """,
           answer="Each rule is a 'cookie cutter'. Order does not change the result, but merging the road buffers first is cleaner and faster.",
           why="This 'rules as layers' logic is the heart of suitability analysis (also called multi-criteria or sieve mapping).")
    nb.pro("4.4", "Fast nearest river point for 1600 houses", "Proximity at scale (performance)",
           scenario="For every house, how far is the river? Report the mean distance and how many houses are closer than 100 m.",
           plan_hint="`shapely.distance(houses, river)` works on the whole array at once. Then numpy: `.mean()`, `(d < 100).sum()`.",
           starter="""
           d = shapely.____(houses, river)
           print(round(d.mean()), "m on average;", (d < ____).sum(), "houses closer than 100 m")
           """,
           solution="""
           d = shapely.distance(houses, river)
           print(round(d.mean()), "m on average;", (d < 100).sum(), "houses closer than 100 m")
           """,
           answer="Vectorised functions (`shapely.distance`, `shapely.within`, …) take arrays. Rule of thumb: never loop over thousands of shapes in Python when a vectorised function exists.")
    nb.pro("4.5", "A spatial index: find candidates fast", "Proximity at scale (spatial index)",
           scenario="Which houses lie within 200 m of **Station Avenue**? Use a spatial index (STRtree) so the computer checks only nearby houses.",
           plan_hint="`tree = shapely.STRtree(houses)`; `idx = tree.query(line, predicate='dwithin', distance=200)` returns the positions of matching houses. Daily picture: a library catalogue — you go to the right shelf instead of reading every book.",
           starter="""
           tree = shapely.____(houses)
           line = roads.set_index("name").geometry["Station Avenue"]
           idx = tree.query(line, predicate="____", distance=200)
           print(len(idx), "houses within 200 m")
           """,
           solution="""
           tree = shapely.STRtree(houses)
           line = roads.set_index("name").geometry["Station Avenue"]
           idx = tree.query(line, predicate="dwithin", distance=200)
           print(len(idx), "houses within 200 m")
           """,
           answer="An STRtree stores the boxes of all shapes. It first finds shapes whose boxes are near (fast), then checks the exact rule. PostGIS does the same with a GIST index (notebook B1).")

    # ---------------------------------------------------------------- test
    nb.test("""
    Use only Shapely (+ numpy). Riverton objects from Level 4 are loaded: `houses`, `residents`, `river`, `roads`, `parks`, `station`.
    Answer in this order: **question type → plan in words → code → one sentence of interpretation.**
    """, [
        ("task", """
        **A · Noise.** The city will widen **High Street**. Everything within **120 m** of it will be noisy during 2 years of works.
        How many residents are affected?
        """, """
        Type: proximity + count.
        ```python
        hs = roads.set_index("name").geometry["High Street"]
        noisy = shapely.dwithin(houses, hs, 120)
        print(residents[noisy].sum())
        ```
        `shapely.dwithin` avoids building the buffer at all (faster, same answer as `within(houses, hs.buffer(120))` apart from edge cases).
        """),
        ("task", """
        **B · Factory rule.** A factory may only be built if it is **at least 400 m from every house**. Is the point (394 500, 5 818 300) allowed?
        """, """
        Type: proximity / decision (yes/no).
        ```python
        site = Point(394_500, 5_818_300)
        print(shapely.distance(houses, site).min() >= 400)
        ```
        One line: the minimum distance to all houses decides the rule.
        """),
        ("task", """
        **C · Green area.** What is the **total park area** in hectares (1 ha = 10 000 m², a football pitch is about 0.7 ha),
        and how much of it is outside the 150 m flood zone?
        """, """
        Type: measurement + overlay.
        ```python
        all_parks = shapely.union_all(parks.values)
        flood = river.buffer(150)
        print(all_parks.area / 10_000, all_parks.difference(flood).area / 10_000)
        ```
        """),
        ("task", """
        **D · Bus stops.** Place a stop every **500 m** along **Station Avenue** and count how many residents live within **300 m** of at least one stop.
        """, """
        Type: proximity (+ union so nobody is counted twice).
        ```python
        line = roads.set_index("name").geometry["Station Avenue"]
        stops = [line.interpolate(d) for d in range(0, int(line.length) + 1, 500)]
        served = shapely.union_all([s.buffer(300) for s in stops])
        print(residents[shapely.within(houses, served)].sum())
        ```
        """),
        ("model", """
        **E · Modelling walkability.** We want to know which areas are within a **10-minute walk** of the new station.
        How would you **model** this geographically? Compare at least two models and say which you would recommend and why.
        """, """
        - **Model 1 – circle (buffer):** 10 min × 80 m/min ≈ 800 m buffer. Quick, only needs Shapely. Weakness: ignores streets, rivers, bridges. It **over-estimates** the area (you cannot walk through the river).
        - **Model 2 – network (isochrone):** walk along the street graph for 800 m (tools: OSMnx/networkx, or pgRouting in PostGIS). More realistic; needs street data.
        - **Model 3 – barrier-aware buffer:** buffer, then cut away the far side of the river where there is no bridge (`difference`). A middle way.

        **Recommendation:** start with Model 1 as a quick screening, and use Model 2 for the final decision, because planning decisions depend on real walking routes. Always state the walking speed you assumed.
        """),
        ("model", """
        **F · Modelling flood exposure.** The council asks: *"Which houses are at risk of flooding?"* Why is a river buffer a weak model,
        and what extra data would make it a strong model?
        """, """
        A buffer assumes water spreads the same distance everywhere. Water follows **height**: a house 50 m from the river but 10 m higher is safer than one 200 m away in a hollow.
        Better model: elevation data (DEM, notebook A5) → cells lower than *river level + x m* and connected to the river. Even better: official flood-hazard maps or hydraulic models.
        Recommendation: use the buffer only as a first filter, then refine with the DEM.
        """),
    ])
    nb.reflect("""
    1. Which Shapely commands do you think you will use **most** in your own project? Why?
    2. Write one question from your own field (e.g. the city you study) that you can now answer with a buffer, an intersection or a distance.
    """)
    return nb
