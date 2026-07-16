import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_SQL_PATH = PROJECT_ROOT / "sql" / "schema.sql"

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]

TAXI_MONTH = os.environ["TAXI_MONTH"]

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

TRIP_DATA_URL = (
    f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{TAXI_MONTH}.parquet"
)
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

TRIP_DATA_RAW_PATH = RAW_DATA_DIR / f"yellow_tripdata_{TAXI_MONTH}.parquet"
ZONE_LOOKUP_RAW_PATH = RAW_DATA_DIR / "taxi_zone_lookup.csv"
