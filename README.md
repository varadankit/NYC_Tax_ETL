# NYC Taxi ETL — Data Engineering Learning Project

A small but realistic batch ETL pipeline: download public NYC TLC Yellow Taxi trip
data, clean it with pandas, and load it into a Postgres star schema running in Docker.

## Architecture

```
NYC TLC (public S3/CloudFront)          Postgres (Docker)
   |  parquet + CSV                        ^
   v                                        |
extract.py --> transform.py --> load.py ----+
 (download,     (pandas clean,   (schema DDL,
  idempotent)    feature eng.)    truncate+COPY load)
```

- **Extract** (`src/extract.py`): downloads one month of Yellow Taxi trip data
  (parquet) and the taxi zone lookup (CSV) from the public NYC TLC CloudFront
  bucket. Skips re-downloading if the file is already on disk.
- **Transform** (`src/transform.py`): pure pandas functions that clean the raw
  data (drop nulls, filter out bad fares/distances/durations that are common
  in this dataset) and engineer `trip_duration_minutes`. No I/O — fully
  unit-testable.
- **Load** (`src/load.py`): applies the schema (`sql/schema.sql`) if needed,
  then truncate-and-loads all three tables. `fact_trips` (millions of rows) is
  loaded with Postgres `COPY` for speed — a plain row-by-row `INSERT` would be
  far too slow at this volume.
- **Orchestrate** (`src/pipeline.py`): runs extract → transform → load in
  order with logging and no silent error handling.

## Data model (star schema)

- `dim_location` — taxi zones (borough, zone, service zone)
- `dim_date` — one row per calendar day in the loaded range
- `fact_trips` — one row per trip, FKs into both dimensions

## Setup

```bash
# 1. Start Postgres + pgAdmin
docker compose up -d

# 2. Create a virtualenv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run the pipeline
python -m src.pipeline
```

`.env` (already created from `.env.example`) controls DB credentials and which
month of data to pull (`TAXI_MONTH=YYYY-MM`). Data must exist at
`https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_<MONTH>.parquet`
— NYC TLC publishes with a ~2 month lag, so if a month 404s, try an earlier one.

## Exploring the data

pgAdmin is available at [http://localhost:5050](http://localhost:5050) (login
with `PGADMIN_EMAIL`/`PGADMIN_PASSWORD` from `.env`). Register a server pointing
at host `postgres`, port `5432`, using the `POSTGRES_*` credentials from `.env`.

Example query once loaded:

```sql
SELECT dl.borough, ROUND(AVG(f.fare_amount), 2) AS avg_fare, COUNT(*) AS trips
FROM fact_trips f
JOIN dim_location dl ON f.pickup_location_id = dl.location_id
GROUP BY dl.borough
ORDER BY avg_fare DESC;
```

## Tests

```bash
pytest tests/
```

Covers the transform logic (cleaning rules, date dimension generation) without
needing a database.

## Idempotency

Re-running `python -m src.pipeline` is safe: `extract` skips files already on
disk, and `load` truncates every table before reloading, so you never get
duplicate rows.

## Where to go next

This project intentionally stops at "one script, one month, one machine."
Natural next steps as you keep learning:

- **Orchestration**: replace `pipeline.py`'s manual sequencing with Airflow or
  Dagster — add scheduling, retries, and a DAG view.
- **Transforms in SQL**: move the cleaning logic into dbt models instead of
  pandas, and learn `dbt test` for data quality checks.
- **Incremental loads**: instead of truncate-and-load, load multiple months
  and only insert *new* data on each run.
- **Data quality**: add explicit validation (e.g. Great Expectations) instead
  of silently filtering bad rows in `transform.py`.
- **Containerize the pipeline itself**: put `src/` in its own Dockerfile so
  the whole thing runs with `docker compose up`, no local venv needed.
- **Cloud**: swap local Postgres for a managed warehouse (BigQuery, Snowflake,
  RDS) and practice IAM/networking.
