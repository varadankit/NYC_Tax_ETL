from sqlalchemy import Engine, create_engine

from config import settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.DATABASE_URL)
    return _engine


def apply_schema() -> None:
    schema_sql = settings.SCHEMA_SQL_PATH.read_text()
    with get_engine().begin() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.exec_driver_sql(statement)
