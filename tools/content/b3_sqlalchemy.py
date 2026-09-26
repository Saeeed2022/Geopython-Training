from nbbuild import NB, SETUP
import projects_b


def build():
    nb = NB("B3_sqlalchemy_geoalchemy2", "B3 · SQLAlchemy & GeoAlchemy2 — the database as Python objects")
    nb.md("""
    **What they are:**
    - **SQLAlchemy** manages connections (an *engine* keeps a pool of open lines) and can describe tables and queries as Python objects.
      GeoPandas `read_postgis`/`to_postgis` use a SQLAlchemy engine.
    - **GeoAlchemy2** teaches SQLAlchemy about PostGIS: a `Geometry` column type and all `ST_` functions via `func.ST_...`.

    **Two styles:**
    - **Core**: write SQL-like expressions in Python (`select(table).where(...)`).
    - **ORM** (Object Relational Mapper): one Python **class** = one table, one **object** = one row.

    **Daily picture:** Psycopg is phoning the database and speaking SQL yourself. SQLAlchemy is a switchboard with a translator:
    you speak Python, it speaks SQL for you, and it keeps the lines open so the next call is quicker.

    **Where this fits in your plan:** you need the *engine* for B4. The ORM matters if you later build a web app (Flask, FastAPI) on PostGIS.

    ⚙️ The database from **B0** must be running.
    """)
    nb.code(SETUP)
    nb.code("""
    import sqlalchemy as sa
    from sqlalchemy import create_engine, text, select, func
    import geoalchemy2
    from geotrain.db import DSN
    URL = DSN.replace("postgresql://", "postgresql+psycopg://", 1)     # tell SQLAlchemy to use psycopg 3
    print("SQLAlchemy", sa.__version__, "| GeoAlchemy2", geoalchemy2.__version__)
    """)

    nb.level(1, "Basics: engine and text queries", "create an engine, run SQL text with bound parameters, and read results.",
             "Getting a switchboard installed once, then making many calls through it.")
    nb.ex("1.1", "Create an engine", "create_engine(url)",
          purpose_a="Creates an engine: it knows how to reach the database and keeps a pool of connections to reuse.",
          life_a="Created once at the start of a notebook, a script or a web app; everything else uses it.",
          hint="`engine = create_engine(URL)`. Then `with engine.connect() as conn: conn.execute(text(\"SELECT 1\"))`.",
          starter="""
          engine = ____(URL)
          with engine.connect() as conn:
              print(conn.execute(text("SELECT postgis_version()")).scalar())
          """,
          solution="""
          engine = create_engine(URL)
          with engine.connect() as conn:
              print(conn.execute(text("SELECT postgis_version()")).scalar())
          """)
    nb.ex("1.2", "Bound parameters in text()", "text('... :name').bindparams / execute(sql, {'name': value})",
          purpose_a="Placeholders written `:name`, filled safely from a dict (SQLAlchemy's version of `%s`).",
          life_a="The same safe querying as in B2, with the style used in most Python web apps.",
          hint="`text(\"SELECT school FROM schools WHERE capacity > :cap\")`, then pass `{\"cap\": 800}`.",
          starter="""
          with engine.connect() as conn:
              rows = conn.execute(text("SELECT school, capacity FROM schools WHERE capacity > ____"), {"cap": ____}).all()
          rows
          """,
          solution="""
          with engine.connect() as conn:
              rows = conn.execute(text("SELECT school, capacity FROM schools WHERE capacity > :cap"), {"cap": 800}).all()
          rows
          """)
    nb.ex("1.3", "Write safely: engine.begin()", "with engine.begin() as conn:",
          purpose_a="Opens a transaction that **commits automatically** at the end, or rolls back if an error happens.",
          life_a="Updating a table in one safe block: all changes or none.",
          hint="Create a small table `notes (id serial, txt text)`, insert one row, then read it back with `engine.connect()`.",
          starter="""
          with engine.____() as conn:
              conn.execute(text("DROP TABLE IF EXISTS notes"))
              conn.execute(text("CREATE TABLE notes (id serial PRIMARY KEY, txt text)"))
              conn.execute(text("INSERT INTO notes (txt) VALUES (:t)"), {"t": "first note"})
          with engine.connect() as conn:
              print(conn.execute(text("SELECT * FROM notes")).all())
          """,
          solution="""
          with engine.begin() as conn:
              conn.execute(text("DROP TABLE IF EXISTS notes"))
              conn.execute(text("CREATE TABLE notes (id serial PRIMARY KEY, txt text)"))
              conn.execute(text("INSERT INTO notes (txt) VALUES (:t)"), {"t": "first note"})
          with engine.connect() as conn:
              print(conn.execute(text("SELECT * FROM notes")).all())
          """)

    nb.level(2, "Core: tables and queries as Python objects", "describe an existing table in Python and build spatial queries with `func.ST_...`.",
             "Instead of writing the letter yourself, you fill in a form and the office writes the letter.")
    nb.ex("2.1", "Reflect an existing table", "sa.Table(name, MetaData(), autoload_with=engine)",
          purpose_a="Reads a table's structure from the database into a Python `Table` object; GeoAlchemy2 recognises the geometry column.",
          life_a="Working with a large database whose tables you did not create, without retyping their columns.",
          hint="`schools = sa.Table(\"schools\", sa.MetaData(), autoload_with=engine)`. Print each column's name and type.",
          starter="""
          meta = sa.MetaData()
          schools = sa.Table("schools", meta, autoload_with=____)
          for col in schools.columns:
              print(col.name, col.type)
          """,
          solution="""
          meta = sa.MetaData()
          schools = sa.Table("schools", meta, autoload_with=engine)
          for col in schools.columns:
              print(col.name, col.type)
          """)
    nb.ex("2.2", "A spatial Core query", "select(...).where(func.ST_DWithin(...))",
          purpose_a="Builds a SELECT in Python; `func.ST_...` calls any PostGIS function by name.",
          life_a="Queries built step by step in code, e.g. adding filters only when a user ticks a box in an app.",
          hint="Point: `func.ST_SetSRID(func.ST_Point(393000, 5821000), 32633)`. Condition: `func.ST_DWithin(schools.c.geometry, p, 1500)`. `print(stmt)` shows the SQL generated.",
          starter="""
          p = func.ST_SetSRID(func.ST_Point(393_000, 5_821_000), 32633)
          stmt = select(schools.c.school, func.ST_Distance(schools.c.geometry, p).label("dist")).where(func.____(schools.c.geometry, p, 1500))
          print(stmt)
          with engine.connect() as conn:
              print(conn.execute(stmt).all())
          """,
          solution="""
          p = func.ST_SetSRID(func.ST_Point(393_000, 5_821_000), 32633)
          stmt = select(schools.c.school, func.ST_Distance(schools.c.geometry, p).label("dist")).where(func.ST_DWithin(schools.c.geometry, p, 1500))
          print(stmt)
          with engine.connect() as conn:
              print(conn.execute(stmt).all())
          """)

    nb.level(3, "ORM: one class = one table", "define a spatial table as a Python class, add objects, and query them.",
             "A class is a blank form ('Tree: species, location'); each filled-in form is one row in the table.")
    nb.code("""
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
    from geoalchemy2 import Geometry, WKTElement
    from geoalchemy2.shape import to_shape, from_shape
    import shapely
    """)
    nb.ex("3.1", "Define a spatial class and create its table", "class Bench(Base): geom = mapped_column(Geometry('POINT', srid=32633))",
          purpose_a="Declares a table as a Python class, including a PostGIS geometry column; `create_all` creates it in the database (with a spatial index).",
          life_a="The data model of an app where citizens report broken benches on a map.",
          hint="Type `'POINT'`, `srid=32633`. `Base.metadata.create_all(engine)` creates missing tables.",
          starter="""
          class Base(DeclarativeBase):
              pass

          class Bench(Base):
              __tablename__ = "benches"
              id: Mapped[int] = mapped_column(primary_key=True)
              condition: Mapped[str]
              geom = mapped_column(Geometry("____", srid=____))

          Base.metadata.drop_all(engine)
          Base.metadata.____(engine)
          print(sa.inspect(engine).get_columns("benches"))
          """,
          solution="""
          class Base(DeclarativeBase):
              pass

          class Bench(Base):
              __tablename__ = "benches"
              id: Mapped[int] = mapped_column(primary_key=True)
              condition: Mapped[str]
              geom = mapped_column(Geometry("POINT", srid=32633))

          Base.metadata.drop_all(engine)
          Base.metadata.create_all(engine)
          print(sa.inspect(engine).get_columns("benches"))
          """)
    nb.ex("3.2", "Add rows as objects", "session.add(Bench(..., geom=WKTElement(...)))",
          purpose_a="Creates row objects in Python; a `Session` collects them and writes them on `commit()`.",
          life_a="Saving a citizen's report from a web form as a new row.",
          hint="`WKTElement(\"POINT(392800 5821400)\", srid=32633)` or `from_shape(shapely.Point(...), srid=32633)`.",
          starter="""
          with Session(engine) as session:
              session.add(Bench(condition="broken", geom=WKTElement("POINT(392800 5821400)", srid=32633)))
              session.add(Bench(condition="ok", geom=____(shapely.Point(394_100, 5_819_800), srid=32633)))
              session.add(Bench(condition="broken", geom=from_shape(shapely.Point(395_300, 5_823_100), srid=32633)))
              session.____()
          """,
          solution="""
          with Session(engine) as session:
              session.add(Bench(condition="broken", geom=WKTElement("POINT(392800 5821400)", srid=32633)))
              session.add(Bench(condition="ok", geom=from_shape(shapely.Point(394_100, 5_819_800), srid=32633)))
              session.add(Bench(condition="broken", geom=from_shape(shapely.Point(395_300, 5_823_100), srid=32633)))
              session.commit()
          """)
    nb.ex("3.3", "Query objects and get Shapely back", "session.scalars(select(Bench).where(...)) + to_shape()",
          purpose_a="Returns Bench objects matching a condition; `to_shape` turns the geometry into a Shapely object.",
          life_a="A maintenance crew's list: all broken benches and their coordinates.",
          hint="`select(Bench).where(Bench.condition == \"broken\")`. For each bench: `to_shape(b.geom)`.",
          starter="""
          with Session(engine) as session:
              for b in session.scalars(select(Bench).where(Bench.condition == "____")):
                  pt = ____(b.geom)
                  print(b.id, b.condition, pt.x, pt.y)
          """,
          solution="""
          with Session(engine) as session:
              for b in session.scalars(select(Bench).where(Bench.condition == "broken")):
                  pt = to_shape(b.geom)
                  print(b.id, b.condition, pt.x, pt.y)
          """)

    nb.level(4, "Professional: spatial ORM queries and design choices", "combine ORM and PostGIS functions, and choose the right tool.",
             "A craftsperson owns several tools and knows which one fits the job.")
    nb.pro("4.1", "Broken benches in the flood zone", "Overlay / proximity (ORM + PostGIS functions)",
           scenario="Which broken benches are within 150 m of the river? Use the ORM for benches and a reflected `river` table.",
           plan_hint="Reflect `river` like 2.1. Join: `select(Bench).join(river, func.ST_DWithin(Bench.geom, river.c.geometry, 150)).where(Bench.condition == 'broken')`.",
           starter="""
           river = sa.Table("river", meta, autoload_with=engine)
           stmt = (select(Bench.id, func.ST_Distance(Bench.geom, river.c.geometry).label("d"))
                   .join(river, func.____(Bench.geom, river.c.geometry, ____))
                   .where(Bench.condition == "broken"))
           with Session(engine) as session:
               print(session.execute(stmt).all())
           """,
           solution="""
           river = sa.Table("river", meta, autoload_with=engine)
           stmt = (select(Bench.id, func.ST_Distance(Bench.geom, river.c.geometry).label("d"))
                   .join(river, func.ST_DWithin(Bench.geom, river.c.geometry, 150))
                   .where(Bench.condition == "broken"))
           with Session(engine) as session:
               print(session.execute(stmt).all())
           """,
           answer="Any PostGIS function can be used through `func`. The ORM builds the SQL; PostGIS (with GEOS) evaluates it.")
    nb.pro("4.2", "Which tool when?", "Decision (tool choice)",
           scenario="""
           Choose the best tool (Psycopg, SQLAlchemy Core, SQLAlchemy ORM + GeoAlchemy2, GeoPandas) for:
           (a) a quick analysis and map of accidents per neighbourhood,
           (b) a web app where users add and edit benches,
           (c) a nightly bulk load of 5 million GPS points,
           (d) a reusable query builder with optional filters.
           Then show the SQL SQLAlchemy generates for one ORM query (`print(stmt.compile(engine))`).
           """,
           plan_hint="Think: who uses the result (you, an app, a pipeline)? How big is the data? Do you need objects or tables?",
           starter="""
           stmt = select(Bench).where(Bench.condition == "broken")
           print(stmt.____(engine))
           """,
           solution="""
           stmt = select(Bench).where(Bench.condition == "broken")
           print(stmt.compile(engine))
           """,
           answer="(a) GeoPandas — tables and plots. (b) ORM + GeoAlchemy2 — objects, validation, sessions. (c) Psycopg COPY — speed. (d) SQLAlchemy Core — composable queries.")

    nb.test("""
    For each: **plan in words → code → interpretation.**
    """, [
        ("task", """
        **A.** With a `text()` query and bound parameters, return the neighbourhood that contains the point (394 500, 5 822 700).
        """, """
        ```python
        with engine.connect() as conn:
            print(conn.execute(text("SELECT name FROM neighbourhoods WHERE ST_Contains(geometry, ST_SetSRID(ST_Point(:x, :y), 32633))"),
                               {"x": 394_500, "y": 5_822_700}).scalar())
        ```
        """),
        ("task", """
        **B.** With the ORM, mark every bench within 1 km of *Central Clinic* as `"checked"`, and commit.
        """, """
        ```python
        clinics = sa.Table("clinics", meta, autoload_with=engine)
        central = select(clinics.c.geometry).where(clinics.c.clinic == "Central Clinic").scalar_subquery()
        with Session(engine) as session:
            for b in session.scalars(select(Bench).where(func.ST_DWithin(Bench.geom, central, 1000))):
                b.condition = "checked"
            session.commit()
        with engine.connect() as conn:
            print(conn.execute(text("SELECT id, condition FROM benches ORDER BY id")).all())
        ```
        """),
        ("model", """
        **C · Modelling a data model.** Design the tables (classes) for a 'report a problem' app in Riverton: citizens report potholes, broken lights and fallen trees, with a photo and a status.
        Which geometry type(s) and SRID? Which columns? Why?
        """, """
        One table `reports`: `id`, `category` (pothole/light/tree), `status` (new/in progress/fixed), `created_at`, `photo_url`, `geom = Geometry("POINT", srid=4326)`.
        - SRID **4326**, because phones send GPS lon/lat; transform to 32633 in queries when measuring (`ST_Transform`) — or store both.
        - A `POINT` is enough: a citizen taps one spot.
        - An index on `geom` (GIST) and on `status`.
        Optional: table `users`, and a table `streets` (LINESTRING) to snap reports to the nearest street.
        """),
    ])
    projects_b.p_b3(nb)
    nb.reflect("""
    Do you expect to build an app one day, or mainly to analyse? Write which of Core / ORM / plain `text()` you will actually use, and why.
    """)
    return nb
