-- Star schema for NYC Yellow Taxi trip data.

CREATE TABLE IF NOT EXISTS dim_location (
    location_id     INTEGER PRIMARY KEY,
    borough         TEXT NOT NULL,
    zone            TEXT NOT NULL,
    service_zone    TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER PRIMARY KEY,      -- YYYYMMDD
    date            DATE NOT NULL UNIQUE,
    year            SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    day             SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,         -- 0=Monday .. 6=Sunday
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_trips (
    trip_id                BIGSERIAL PRIMARY KEY,
    pickup_datetime         TIMESTAMP NOT NULL,
    dropoff_datetime        TIMESTAMP NOT NULL,
    pickup_date_id          INTEGER REFERENCES dim_date(date_id),
    pickup_location_id      INTEGER REFERENCES dim_location(location_id),
    dropoff_location_id     INTEGER REFERENCES dim_location(location_id),
    passenger_count          SMALLINT,
    trip_distance            NUMERIC(8, 2),
    fare_amount               NUMERIC(10, 2),
    tip_amount                NUMERIC(10, 2),
    total_amount              NUMERIC(10, 2),
    payment_type              SMALLINT,
    trip_duration_minutes     NUMERIC(10, 2)
);

CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_date ON fact_trips(pickup_date_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_location ON fact_trips(pickup_location_id);
