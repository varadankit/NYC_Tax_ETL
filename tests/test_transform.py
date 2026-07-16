import pandas as pd

from src.transform import (
    add_pickup_date_id,
    build_dim_date,
    clean_trips,
    clean_zone_lookup,
)


def test_clean_zone_lookup_renames_and_dedupes():
    raw = pd.DataFrame(
        {
            "LocationID": [1, 2, 2],
            "Borough": ["Manhattan", "Brooklyn", "Brooklyn"],
            "Zone": ["Battery Park", "DUMBO", "DUMBO"],
            "service_zone": ["Yellow Zone", "Boro Zone", "Boro Zone"],
        }
    )
    result = clean_zone_lookup(raw)
    assert list(result.columns) == ["location_id", "borough", "zone", "service_zone"]
    assert len(result) == 2


def test_clean_zone_lookup_fills_missing_fields_instead_of_dropping():
    # Real TLC data has placeholder rows like this (id 264 "Unknown", 265
    # "Outside of NYC") with a missing borough/zone; trips reference them,
    # so they must be kept, not silently dropped.
    raw = pd.DataFrame(
        {
            "LocationID": [264],
            "Borough": ["Unknown"],
            "Zone": [None],
            "service_zone": [None],
        }
    )
    result = clean_zone_lookup(raw)
    assert len(result) == 1
    assert result.loc[0, "zone"] == "Unknown"
    assert result.loc[0, "service_zone"] == "Unknown"


def _base_trip_row(**overrides):
    row = {
        "tpep_pickup_datetime": pd.Timestamp("2025-05-01 08:00:00"),
        "tpep_dropoff_datetime": pd.Timestamp("2025-05-01 08:15:00"),
        "PULocationID": 100,
        "DOLocationID": 200,
        "passenger_count": 1,
        "trip_distance": 3.2,
        "fare_amount": 12.5,
        "tip_amount": 2.0,
        "total_amount": 15.0,
        "payment_type": 1,
    }
    row.update(overrides)
    return row


def test_clean_trips_keeps_valid_row():
    raw = pd.DataFrame([_base_trip_row()])
    result = clean_trips(raw)
    assert len(result) == 1
    assert result.loc[0, "trip_duration_minutes"] == 15.0


def test_clean_trips_drops_negative_fare():
    raw = pd.DataFrame([_base_trip_row(fare_amount=-5.0)])
    result = clean_trips(raw)
    assert len(result) == 0


def test_clean_trips_drops_zero_distance():
    raw = pd.DataFrame([_base_trip_row(trip_distance=0.0)])
    result = clean_trips(raw)
    assert len(result) == 0


def test_clean_trips_drops_zero_duration():
    same_time = pd.Timestamp("2025-05-01 08:00:00")
    raw = pd.DataFrame(
        [_base_trip_row(tpep_pickup_datetime=same_time, tpep_dropoff_datetime=same_time)]
    )
    result = clean_trips(raw)
    assert len(result) == 0


def test_clean_trips_drops_missing_location():
    raw = pd.DataFrame([_base_trip_row(PULocationID=None)])
    result = clean_trips(raw)
    assert len(result) == 0


def test_build_dim_date_covers_full_range():
    dim_date = build_dim_date(pd.Timestamp("2025-05-01"), pd.Timestamp("2025-05-03"))
    assert len(dim_date) == 3
    assert dim_date["date_id"].tolist() == [20250501, 20250502, 20250503]
    assert dim_date.loc[dim_date["day"] == 3, "is_weekend"].iloc[0] == True  # 2025-05-03 is a Saturday


def test_add_pickup_date_id():
    trips = pd.DataFrame({"pickup_datetime": [pd.Timestamp("2025-05-01 08:00:00")]})
    result = add_pickup_date_id(trips)
    assert result.loc[0, "pickup_date_id"] == 20250501
