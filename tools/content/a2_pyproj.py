from nbbuild import NB, SETUP


def build():
    nb = NB("A2_pyproj", "A2 · PyProj — putting shapes on the real Earth")
    nb.md("""
    **What PyProj is:** the Python door to **PROJ**, the library that knows every coordinate reference system (CRS)
    and converts coordinates between them. PostGIS uses the same PROJ inside `ST_Transform`.

    **Why you need it:** Shapely measures on flat paper. The Earth is round. A CRS is the recipe that flattens
    the Earth onto paper. Choose the wrong recipe, and your distances and areas are wrong.

    **Daily picture:** peeling an orange and pressing the peel flat. It always tears or stretches somewhere.
    Each CRS chooses *where* it stretches:
    - **Geographic CRS** (e.g. WGS 84, EPSG:4326): position in **degrees** (longitude, latitude), like GPS. Good for storing, bad for measuring.
    - **Projected CRS** (e.g. UTM 33N, EPSG:32633): position in **metres** on a flat sheet. Good for measuring in a local area.

    **Simple maths:** 1° of latitude ≈ 111 km everywhere. 1° of longitude ≈ 111 km × cos(latitude).
    At Riverton (52.5° N), cos(52.5°) ≈ 0.61, so 1° of longitude is only ≈ 68 km. That is why "degrees" are not a length.
    """)
    nb.code("""
    import pyproj
    from pyproj import CRS, Transformer, Geod
    print("pyproj", pyproj.__version__, "| PROJ", pyproj.proj_version_str)
    """)

    nb.level(1, "Basics: what is a CRS?", "read a CRS and understand its name, type and units.",
             "A postal address and a GPS reading describe the same house in two different 'languages'. A CRS is such a language.")
    nb.ex("1.1", "Look up a CRS by its EPSG code", "CRS.from_epsg(code)",
          purpose_a="Creates a CRS object from its EPSG number, so you can read its name, units and area of use.",
          life_a="Checking what 'EPSG:25832' means before using a dataset from a German city office.",
          hint="EPSG codes are ID numbers in a big catalogue (like ISBNs for books). 4326 = WGS 84 (GPS).",
          starter="""
          wgs84 = CRS.from_epsg(____)
          print(wgs84.name)
          print(wgs84.axis_info)
          """,
          solution="""
          wgs84 = CRS.from_epsg(4326)
          print(wgs84.name)
          print(wgs84.axis_info)
          """,
          note="Look at the axis order: officially **latitude first**, then longitude. Remember this for exercise 2.2.")
    nb.ex("1.2", "Geographic or projected?", "crs.is_geographic / crs.is_projected",
          purpose_a="Tells you whether the CRS uses degrees on the globe (geographic) or metres on a flat map (projected).",
          life_a="Before calculating a buffer of 500, check the data is projected; otherwise '500' means 500 degrees!",
          hint="Compare 4326 with 32633 (UTM zone 33 North, the CRS of Riverton). Units: `crs.axis_info[0].unit_name`.",
          starter="""
          utm = CRS.from_epsg(____)
          for c in [wgs84, utm]:
              print(c.name, "| geographic:", c.____, "| projected:", c.____, "| unit:", c.axis_info[0].unit_name)
          """,
          solution="""
          utm = CRS.from_epsg(32633)
          for c in [wgs84, utm]:
              print(c.name, "| geographic:", c.is_geographic, "| projected:", c.is_projected, "| unit:", c.axis_info[0].unit_name)
          """)
    nb.ex("1.3", "Where may I use this CRS?", "crs.area_of_use",
          purpose_a="Shows the region of the world for which a CRS was designed (outside it, errors grow).",
          life_a="UTM 33N is made for 12°–18° E. Using it for Spain would stretch distances noticeably.",
          hint="Just read the attribute: `utm.area_of_use`. It has `.name` and `.bounds` (west, south, east, north).",
          starter="""
          print(utm.____.name)
          print(utm.area_of_use.____)
          """,
          solution="""
          print(utm.area_of_use.name)
          print(utm.area_of_use.bounds)
          """)

    nb.level(2, "Core tools: transform coordinates", "convert a GPS position into metres and back, without the classic axis-order mistake.",
             "Translating a sentence from one language to another and back: you should get the same sentence.")
    nb.ex("2.1", "Transform GPS degrees into metres", "Transformer.from_crs(a, b, always_xy=True).transform(x, y)",
          purpose_a="Builds a converter between two CRSs and converts coordinates with it.",
          life_a="Your phone gives lon/lat of a bike accident; the city's map uses metres (UTM). You convert before comparing.",
          hint="From 4326 to 32633. With `always_xy=True` you always give **(lon, lat)** = (x, y). Riverton's town hall is at lon 13.4, lat 52.52.",
          starter="""
          to_utm = Transformer.from_crs(____, ____, always_xy=True)
          x, y = to_utm.transform(13.40, 52.52)
          print(round(x), round(y))
          """,
          solution="""
          to_utm = Transformer.from_crs(4326, 32633, always_xy=True)
          x, y = to_utm.transform(13.40, 52.52)
          print(round(x), round(y))
          """)
    nb.ex("2.2", "The axis-order trap", "always_xy=False (the default)",
          purpose_a="Shows that without `always_xy=True`, PyProj follows the official axis order of EPSG:4326: **latitude first**.",
          life_a="The most common bug in GIS: points land in the Indian Ocean or Somalia because lon and lat were swapped.",
          hint="Create a transformer **without** `always_xy`, and pass (13.40, 52.52) again. The result is far away because it reads 13.40 as latitude. Then pass (52.52, 13.40) instead.",
          starter="""
          strict = Transformer.from_crs(4326, 32633)          # no always_xy
          print(strict.transform(13.40, 52.52))                # wrong order for this transformer
          print(strict.transform(____, ____))                  # correct order: lat, lon
          """,
          solution="""
          strict = Transformer.from_crs(4326, 32633)
          print(strict.transform(13.40, 52.52))
          print(strict.transform(52.52, 13.40))
          """,
          note="**Recommendation:** always write `always_xy=True`. Then the order is always x=lon, y=lat, like Shapely and GeoPandas.")
    nb.ex("2.3", "Back again (inverse)", "Transformer.from_crs(32633, 4326, always_xy=True)",
          purpose_a="Converts metres back into lon/lat; a round trip should return the start point.",
          life_a="Sending your result (in metres) to a web map or app that expects GPS coordinates.",
          hint="Swap the two codes. Put the x, y from 2.1 in. You should get ≈ (13.40, 52.52).",
          starter="""
          to_gps = Transformer.from_crs(____, ____, always_xy=True)
          print(to_gps.transform(x, y))
          """,
          solution="""
          to_gps = Transformer.from_crs(32633, 4326, always_xy=True)
          print(to_gps.transform(x, y))
          """)
    nb.ex("2.4", "Find the right UTM zone", "pyproj.database.query_utm_crs_info()",
          purpose_a="Asks the PROJ database which UTM CRS fits a given location.",
          life_a="You receive GPS data from a new city and need a metre-based CRS for it.",
          hint="Simple maths: UTM zone = floor((lon + 180) / 6) + 1. For lon 13.4: (193.4 / 6) = 32.2 → zone 33. Use `AreaOfInterest(west, south, east, north)` with the same lon/lat four times.",
          starter="""
          import math
          from pyproj.aoi import AreaOfInterest
          from pyproj.database import query_utm_crs_info
          lon, lat = 13.40, 52.52
          print("zone by formula:", math.floor((lon + 180) / 6) + 1)
          info = query_utm_crs_info(datum_name="WGS 84", area_of_interest=AreaOfInterest(lon, lat, ____, ____))
          print(info[0].code, info[0].name)
          """,
          solution="""
          import math
          from pyproj.aoi import AreaOfInterest
          from pyproj.database import query_utm_crs_info
          lon, lat = 13.40, 52.52
          print("zone by formula:", math.floor((lon + 180) / 6) + 1)
          info = query_utm_crs_info(datum_name="WGS 84", area_of_interest=AreaOfInterest(lon, lat, lon, lat))
          print(info[0].code, info[0].name)
          """,
          note="GeoPandas has a shortcut: `gdf.estimate_utm_crs()` (notebook A3).")

    nb.level(3, "Combining: measure on the globe and reproject shapes", "measure true distances and areas, and move whole Shapely shapes between CRSs.",
             "Measuring a flight Berlin → New York with a string on a globe, not with a ruler on a flat map.")
    nb.ex("3.1", "True distance on the ellipsoid", "Geod(ellps='WGS84').inv(lon1, lat1, lon2, lat2)",
          purpose_a="Computes the shortest distance (and directions) between two lon/lat points on the curved Earth.",
          life_a="Flight or shipping distances, or checking long distances that a local UTM map would distort.",
          hint="`inv` returns (forward azimuth, back azimuth, distance in metres). Berlin (13.40, 52.52) → Paris (2.35, 48.86) is about 880 km.",
          starter="""
          geod = Geod(ellps="WGS84")
          az12, az21, dist = geod.____(13.40, 52.52, 2.35, 48.86)
          print(round(dist / 1000), "km, heading", round(az12), "degrees")
          """,
          solution="""
          geod = Geod(ellps="WGS84")
          az12, az21, dist = geod.inv(13.40, 52.52, 2.35, 48.86)
          print(round(dist / 1000), "km, heading", round(az12), "degrees")
          """)
    nb.ex("3.2", "Reproject a whole Shapely shape", "shapely.ops.transform(transformer.transform, geom)",
          purpose_a="Applies a coordinate conversion to every vertex of a Shapely geometry.",
          life_a="You drew a study area in Google Maps (lon/lat) and need it in metres to compute its area.",
          hint="Pass the *function* `to_utm.transform` (no brackets!) and the polygon. Then `.area` is in m².",
          starter="""
          from shapely import Polygon
          from shapely.ops import transform
          area_ll = Polygon([(13.39, 52.51), (13.41, 52.51), (13.41, 52.53), (13.39, 52.53)])
          area_m = transform(____, area_ll)
          print("in degrees²:", area_ll.area, "| in m²:", round(area_m.area))
          """,
          solution="""
          from shapely import Polygon
          from shapely.ops import transform
          area_ll = Polygon([(13.39, 52.51), (13.41, 52.51), (13.41, 52.53), (13.39, 52.53)])
          area_m = transform(to_utm.transform, area_ll)
          print("in degrees²:", area_ll.area, "| in m²:", round(area_m.area))
          """)
    nb.ex("3.3", "Area directly on the ellipsoid", "geod.geometry_area_perimeter(geom)",
          purpose_a="Computes the true area and perimeter of a lon/lat Shapely geometry on the curved Earth.",
          life_a="Areas of big regions (countries, forests) where any flat map would distort the result.",
          hint="Use `area_ll` from 3.2. The area comes out **negative** if the ring runs clockwise — take `abs()`.",
          starter="""
          a, p = geod.____(area_ll)
          print(round(abs(a)), "m² on the ellipsoid vs", round(area_m.area), "m² in UTM")
          """,
          solution="""
          a, p = geod.geometry_area_perimeter(area_ll)
          print(round(abs(a)), "m² on the ellipsoid vs", round(area_m.area), "m² in UTM")
          """,
          note="Very close: UTM is excellent for local work. The difference grows for big areas or far from the zone centre.")
    nb.ex("3.4", "Convert a bounding box", "transformer.transform_bounds(...)",
          purpose_a="Converts a whole box (minx, miny, maxx, maxy), sampling its edges so curved edges are covered.",
          life_a="Asking an online service for data 'inside the town' when the service wants the box in lon/lat.",
          hint="Riverton's box in metres is (390000, 5818000, 396000, 5824000). Use `to_gps.transform_bounds(*box)`.",
          starter="""
          box_m = (390_000, 5_818_000, 396_000, 5_824_000)
          print(to_gps.____(*box_m))
          """,
          solution="""
          box_m = (390_000, 5_818_000, 396_000, 5_824_000)
          print(to_gps.transform_bounds(*box_m))
          """)

    nb.level(4, "Professional: choosing the right CRS", "pick a CRS for the question, and prove how big the error of a bad choice is.",
             "Choosing the right map for a trip: a city map for walking, a road atlas for driving, a globe for flights.")
    nb.pro("4.1", "How wrong is Web Mercator?", "Measurement (error analysis)",
           scenario="Web maps (Google, OSM) use **Web Mercator, EPSG:3857**. A colleague measured Riverton's town area in EPSG:3857. How wrong is the result compared to UTM?",
           plan_hint="Transform `area_ll` to 3857 and compare the area with UTM. Theory: Mercator stretches lengths by 1/cos(lat), so **areas** by 1/cos²(lat). At 52.5°: 1/0.61² ≈ 2.7 — almost 3 times too big!",
           starter="""
           import math
           to_merc = Transformer.from_crs(4326, ____, always_xy=True)
           area_merc = transform(to_merc.transform, area_ll)
           print("ratio:", round(area_merc.area / area_m.area, 2), "| theory:", round(1 / math.cos(math.radians(52.52))**2, 2))
           """,
           solution="""
           import math
           to_merc = Transformer.from_crs(4326, 3857, always_xy=True)
           area_merc = transform(to_merc.transform, area_ll)
           print("ratio:", round(area_merc.area / area_m.area, 2), "| theory:", round(1 / math.cos(math.radians(52.52))**2, 2))
           """,
           answer="Measurement error analysis. Web Mercator is for **display**, never for measuring. That is why Greenland looks as big as Africa on web maps.")
    nb.pro("4.2", "Which CRS for which question?", "Decision (method choice)",
           scenario="""
           Match each task with a CRS: (a) population density of all EU regions, (b) distances inside Riverton, (c) storing GPS tracks from an app,
           (d) a background web map. Options: EPSG:3035 (LAEA Europe, *equal-area*), EPSG:32633 (UTM 33N), EPSG:4326 (WGS 84), EPSG:3857 (Web Mercator).
           Then confirm with code that EPSG:3035 is equal-area.
           """,
           plan_hint="Density = people ÷ **area**, so you need an equal-area CRS for a big region. Check a CRS's projection method with `CRS.from_epsg(3035).coordinate_operation.method_name`.",
           starter="""
           print(CRS.from_epsg(____).coordinate_operation.method_name)
           """,
           solution="""
           print(CRS.from_epsg(3035).coordinate_operation.method_name)
           """,
           answer="(a) 3035 — equal-area keeps areas right across Europe. (b) 32633 — local, metres, small distortion. (c) 4326 — universal storage format of GPS. (d) 3857 — what web tiles use, display only.")
    nb.pro("4.3", "Joining GPS data to a local map", "Data integration (measurement)",
           scenario="A cycling app recorded a crash at lon 13.3955, lat 52.5310. The city's clinic *Central Clinic* is at x=392 900, y=5 821 100 (EPSG:32633). How far is the crash from the clinic, in metres?",
           plan_hint="Never mix CRSs. Transform the GPS point to 32633 first (`always_xy=True`), then use Pythagoras: √(dx² + dy²), like the diagonal of a room.",
           starter="""
           cx, cy = to_utm.transform(____, ____)
           print(round(math.hypot(cx - 392_900, cy - 5_821_100)), "m")
           """,
           solution="""
           cx, cy = to_utm.transform(13.3955, 52.5310)
           print(round(math.hypot(cx - 392_900, cy - 5_821_100)), "m")
           """,
           answer="Transform first, then measure. Mixing degrees and metres in one calculation is the second most common GIS bug (after swapped lon/lat).")

    nb.test("""
    Answer in this order: **question type → plan in words → code → interpretation.**
    """, [
        ("task", """
        **A.** A partner sends you Riverton's school locations as GPS: Oak Primary at (13.42723, 52.52504). Convert it to UTM 33N and check it lies inside the town box (390 000–396 000, 5 818 000–5 824 000).
        """, """
        ```python
        x, y = Transformer.from_crs(4326, 32633, always_xy=True).transform(13.42723, 52.52504)
        print(round(x), round(y), 390_000 <= x <= 396_000 and 5_818_000 <= y <= 5_824_000)
        ```
        """),
        ("task", """
        **B.** Riverton wants to twin with a town at lon 21.01, lat 52.23 (Warsaw area). How far is it from Riverton town hall (13.40, 52.52) along the Earth's surface?
        """, """
        Type: measurement on the globe (the two towns are in different UTM zones, so use the ellipsoid).
        ```python
        print(round(Geod(ellps="WGS84").inv(13.40, 52.52, 21.01, 52.23)[2] / 1000), "km")
        ```
        """),
        ("task", """
        **C.** A dataset arrives with coordinates like (5 820 000, 391 000). What is probably wrong and how do you check it?
        """, """
        The numbers look like UTM but **x and y are swapped** (northing first). Check by plotting, or by transforming both orders to lon/lat and seeing which one lands where you expect.
        Fix: swap the columns before building points, or (for a whole GeoDataFrame) use `shapely.ops.transform(lambda x, y: (y, x), geom)`.
        """),
        ("decision", """
        **D.** You compare the green area per inhabitant in 30 European cities. Which CRS (or CRSs) do you use and why?
        """, """
        Either one equal-area CRS for all (EPSG:3035 LAEA Europe) so every m² is comparable, or each city in its own UTM zone.
        **Recommendation:** EPSG:3035, because one CRS for all cities makes the comparison simple and fair, and it is designed to keep areas right.
        """),
        ("model", """
        **E · Modelling.** You model the 'service area' of a regional hospital that covers a 60 km radius, crossing two UTM zones. How do you make sure the circle is a true 60 km everywhere?
        """, """
        A buffer of 60 000 in one UTM zone is slightly distorted in the neighbouring zone. Options:
        1. Use a **custom local projection** centred on the hospital, e.g. Azimuthal Equidistant: `CRS.from_proj4("+proj=aeqd +lat_0=52.5 +lon_0=13.4 +units=m")`. Distances **from the centre** are true in all directions. Buffer there, then transform back.
        2. Or compute points on the ellipsoid with `Geod.fwd` every few degrees of heading.
        Recommendation: option 1 — it is short, exact for 'distance from one point', and works with Shapely/GeoPandas.
        """),
    ])
    nb.reflect("""
    1. Which CRS will you use for your own study area? Look it up with `query_utm_crs_info` or your national mapping agency.
    2. Write down one dataset you already have and its CRS. Is it geographic or projected?
    """)
    return nb
