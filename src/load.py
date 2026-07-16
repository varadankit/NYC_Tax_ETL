import io
import logging

import pandas as pd
from sqlalchemy import text

from src.db import get_engine

logger = logging.getLogger(__name__)


def _truncate(table_name: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))


def _replace_table(df: pd.DataFrame, table_name: str) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))
    df.to_sql(
        table_name, engine, if_exists="append", index=False, method="multi", chunksize=1000
    )
    logger.info("Loaded %d rows into %s", len(df), table_name)


def load_dim_location(dim_location: pd.DataFrame) -> None:
    _replace_table(dim_location, "dim_location")


def load_dim_date(dim_date: pd.DataFrame) -> None:
    _replace_table(dim_date, "dim_date")


def load_fact_trips(fact_trips: pd.DataFrame) -> None:
    """Bulk load via COPY.

    to_sql's row-by-row INSERT is far too slow for millions of rows;
    COPY streams the data in one pass and is the standard Postgres
    bulk-load technique.
    """
    engine = get_engine()
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            buffer = io.StringIO()
            fact_trips.to_csv(buffer, index=False, header=False, na_rep="")
            buffer.seek(0)

            columns = ", ".join(fact_trips.columns)
            cursor.copy_expert(
                f"COPY fact_trips ({columns}) FROM STDIN WITH (FORMAT csv, NULL '')",
                buffer,
            )
        raw_conn.commit()
        logger.info("Loaded %d rows into fact_trips via COPY", len(fact_trips))
    finally:
        raw_conn.close()


def load_all(
    dim_location: pd.DataFrame, dim_date: pd.DataFrame, fact_trips: pd.DataFrame
) -> None:
    """Truncate-and-load all tables in FK-safe order (child before parents
    are touched, parents before child is repopulated) so re-running the
    pipeline is idempotent.
    """
    _truncate("fact_trips")
    load_dim_location(dim_location)
    load_dim_date(dim_date)
    load_fact_trips(fact_trips)
