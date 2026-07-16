import logging
import time

import pandas as pd

from config import settings
from src import db, extract, load, transform

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run() -> None:
    start = time.monotonic()
    logger.info("=== Pipeline start (month=%s) ===", settings.TAXI_MONTH)

    logger.info("--- Extract ---")
    trip_path, zone_path = extract.extract()

    logger.info("--- Transform ---")
    trips_raw = pd.read_parquet(trip_path)
    zones_raw = pd.read_csv(zone_path)

    dim_location = transform.clean_zone_lookup(zones_raw)
    fact_trips = transform.clean_trips(trips_raw)
    fact_trips = transform.add_pickup_date_id(fact_trips)
    dim_date = transform.build_dim_date(
        fact_trips["pickup_datetime"].min(), fact_trips["pickup_datetime"].max()
    )

    logger.info(
        "Transformed: %d dim_location rows, %d dim_date rows, %d fact_trips rows",
        len(dim_location),
        len(dim_date),
        len(fact_trips),
    )

    logger.info("--- Load ---")
    db.apply_schema()
    load.load_all(dim_location, dim_date, fact_trips)

    elapsed = time.monotonic() - start
    logger.info("=== Pipeline finished in %.1fs ===", elapsed)


if __name__ == "__main__":
    run()
