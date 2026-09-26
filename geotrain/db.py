"""Database helpers for the PostGIS notebooks (group B).

Change the connection with the environment variable GEOTRAIN_DSN, e.g.
    export GEOTRAIN_DSN="postgresql://geo:geo@localhost:5432/geotrain"
"""
import os

import pandas as pd

DSN = os.environ.get("GEOTRAIN_DSN", "postgresql://geo:geo@localhost:5432/geotrain")


def connect():
    """Open a psycopg (version 3) connection."""
    import psycopg
    return psycopg.connect(DSN)


def engine():
    """Return a SQLAlchemy engine (used by GeoPandas read_postgis/to_postgis)."""
    from sqlalchemy import create_engine
    return create_engine(DSN.replace("postgresql://", "postgresql+psycopg://", 1))


def sql(query: str, params=None) -> pd.DataFrame:
    """Run one SQL query and return the result as a pandas DataFrame.

    A small shortcut so the internal-library notebook (B1) can focus on SQL.
    You build this helper yourself in notebook B2.
    """
    with connect() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description is None:          # e.g. CREATE / INSERT
            conn.commit()
            return pd.DataFrame()
        cols = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
