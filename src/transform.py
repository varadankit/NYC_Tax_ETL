import logging

import pandas as pd

logger = logging.getLogger(__name__)

TRIP_COLUMN_RENAME = {
    "tpep_pickup_datetime": "pickup_datetime",
    "tpep_dropoff_datetime": "dropoff_datetime",
    "PULocationID": "pickup_location_id",
    "DOLocationID": "dropoff_location_id",
}

MAX_TRIP_DISTANCE_MILES = 100
MAX_FARE_AMOUNT = 1000
MIN_TRIP_DURATION_MINUTES = 1
MAX_TRIP_DURATION_MINUTES = 180


def clean_zone_lookup(zones_raw: pd.DataFrame) -> pd.DataFrame:
    """Shape the taxi zone lookup CSV into the dim_location table."""
    zones = zones_raw.rename(
        columns={
            "LocationID": "location_id",
            "Borough": "borough",
            "Zone": "zone",
            "service_zone": "service_zone",
        }
    )[["location_id", "borough", "zone", "service_zone"]]
    zones = zones.dropna(subset=["location_id"])
    zones["location_id"] = zones["location_id"].astype(int)
    zones[["borough", "zone", "service_zone"]] = zones[
        ["borough", "zone", "service_zone"]
    ].fillna("Unknown")
    return zones.drop_duplicates(subset=["location_id"])


def clean_trips(trips_raw: pd.DataFrame) -> pd.DataFrame:
    """Clean raw trip records and engineer trip_duration_minutes.

    Drops rows with missing keys/timestamps and filters out data-entry
    errors that are common in this dataset: negative/zero fares or
    distances, and trips with an impossible duration.
    """
    trips = trips_raw.rename(columns=TRIP_COLUMN_RENAME)

    required_cols = [
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_location_id",
        "dropoff_location_id",
        "trip_distance",
        "fare_amount",
        "total_amount",
    ]
    trips = trips.dropna(subset=required_cols)

    trips["trip_duration_minutes"] = (
        trips["dropoff_datetime"] - trips["pickup_datetime"]
    ).dt.total_seconds() / 60

    trips = trips[
        (trips["trip_distance"] > 0)
        & (trips["trip_distance"] <= MAX_TRIP_DISTANCE_MILES)
        & (trips["fare_amount"] > 0)
        & (trips["fare_amount"] <= MAX_FARE_AMOUNT)
        & (trips["total_amount"] > 0)
        & (trips["trip_duration_minutes"] >= MIN_TRIP_DURATION_MINUTES)
        & (trips["trip_duration_minutes"] <= MAX_TRIP_DURATION_MINUTES)
    ]

    trips["passenger_count"] = trips["passenger_count"].fillna(1).astype(int)
    trips["tip_amount"] = trips["tip_amount"].fillna(0)
    trips["payment_type"] = trips["payment_type"].fillna(-1).astype(int)

    keep_cols = [
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_location_id",
        "dropoff_location_id",
        "passenger_count",
        "trip_distance",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "payment_type",
        "trip_duration_minutes",
    ]
    trips = trips[keep_cols].drop_duplicates().reset_index(drop=True)

    logger.info(
        "Cleaned trips: %d rows kept out of %d raw rows", len(trips), len(trips_raw)
    )
    return trips


def build_dim_date(min_ts: pd.Timestamp, max_ts: pd.Timestamp) -> pd.DataFrame:
    """Generate one row per calendar day covering [min_ts, max_ts]."""
    dates = pd.date_range(start=min_ts.normalize(), end=max_ts.normalize(), freq="D")
    dim_date = pd.DataFrame({"date": dates})
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["day_of_week"] = dim_date["date"].dt.dayofweek
    dim_date["is_weekend"] = dim_date["day_of_week"] >= 5
    return dim_date[
        ["date_id", "date", "year", "month", "day", "day_of_week", "is_weekend"]
    ]


def add_pickup_date_id(trips: pd.DataFrame) -> pd.DataFrame:
    """Attach the dim_date foreign key derived from pickup_datetime."""
    trips = trips.copy()
    trips["pickup_date_id"] = (
        trips["pickup_datetime"].dt.strftime("%Y%m%d").astype(int)
    )
    return trips
