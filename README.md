# AV-Lakehouse: Scalable Sensor Data Indexing & Versioning

## Overview
**AV-Lakehouse** is a hands-on project that simulates an autonomous vehicle (AV) sensor data pipeline — from raw ingestion to analytics-ready storage with version control.

The goal is to demonstrate real-world AV data engineering patterns:

- Handling raw sensor data (images + metadata)
- Converting semi-structured data into optimized Parquet tables
- Partitioning for fast querying
- Tracking dataset versions reproducibly using DVC

This project intentionally uses small sample data (not multi-TB datasets) to keep the workflow lightweight while still realistic.

---

## Architecture

```text

Raw Lake (Bronze)
- Images + raw JSON metadata
|
v
Spark ETL (Bronze → Silver)
|
v
Cleaned & Partitioned Parquet (Silver)
|
v
Aggregations / Analytics Tables (Gold)
|
v
Dataset Versioning (DVC)


```
---


## Tech Stack

| Layer | Technology |
|------|------------|
| Language | Python 3.10 |
| Data Processing | PySpark |
| Storage Format | Apache Parquet |
| Raw Dataset | Waymo Open Dataset (tutorial frames) |
| Versioning | DVC |
| Environment | Python virtualenv |

## Project Structure

```text
av-sensor-ingestion-engine/
│
├── src/
│   ├── ingestion/
│   │   └── bronze_ingestion.py          # TFRecords → Bronze (images + JSON)
│   │
│   └── spark_jobs/
│       ├── silver_transform.py          # Bronze → Silver Parquet
│       └── gold_aggregation.py          # Silver → Gold aggregates
│
├── data/
│   ├── bronze/
│   │   └── vehicle_id=sim-001/
│   │       └── date=2026-02-01/
│   │           ├── frame_000000_front.jpg
│   │           ├── frame_000000.json
│   │           └── ...
│   │
│   ├── silver/
│   │   └── date=2026-02-01/
│   │       └── vehicle_id=sim-001/
│   │           ├── part-*.snappy.parquet
│   │           └── _SUCCESS
│   │
│   └── gold/
│       └── date=2026-02-01/
│           └── vehicle_id=sim-001/
│               ├── part-*.snappy.parquet
│               └── _SUCCESS
│
├── scripts/
│   └── inspect_frame.py
│
├── .dvc/
├── data/silver.dvc                      # DVC tracks Silver (core dataset)
├── data/gold.dvc                        # optional but good
│
├── .gitignore
├── .dvcignore
├── requirements.txt
└── README.md

```
## Phase 1 — Bronze Layer: Raw Ingestion

**Goal**: Simulate a vehicle uploading raw sensor data.

- Reads Waymo tutorial TFRecord frames

- Extracts front camera images

- Writes:

  - JPG images

  - JSON metadata (timestamps, pose, vehicle_id, frame_id)

Example output:
```text
data/raw/uploads/
└── vehicle_id=sim-001/
    └── date=2026-02-01/
        ├── frame_000000_front.jpg
        ├── frame_000001_front.jpg
        └── frame_000000.json
```
Run:

```text

python src/ingestion/bronze_ingestion.py

```

## Phase 2 — Silver Layer: Spark ETL & Normalization
**Goal**: Convert messy JSON metadata into analytics-ready Parquet.

This layer applies schema enforcement, normalization, and partitioning to make data query- and analytics-ready.


**Transformations**:

- Convert timestamps from microseconds → seconds

- Normalize fields

- Add simple quality flags

- Preserve pose and LiDAR metadata

- Partition output by **date** and **vehicle_id**

Output:

```text

data/silver/
└── date=2026-02-01/
    └── vehicle_id=sim-001/
        ├── part-*.snappy.parquet
        └── _SUCCESS

```
Run:

```text

python src/spark_jobs/silver_transform.py

```
## Phase 3 — Gold Layer: Aggregations & Analytics

**Goal**: Produce analytics-ready datasets for downstream consumers.

- Read from Silver Parquet tables
- Perform aggregations and business logic
- Write optimized Gold tables (e.g. counts, time-based metrics)

**Example use cases:**
- Frame counts per vehicle per day
- Sensor availability metrics
- Quality monitoring



## Phase 4 —  Dataset Versioning & Reproducibility (DVC)

**Goal**: Enable reproducibility and dataset evolution.

- Track Parquet lakehouse using DVC

- Commit metadata to Git

- Keep large data files out of Git
- Each Git commit references a specific dataset version via `.dvc` metadata


```text
dvc init
dvc add data/processed/lakehouse
git add data/processed/lakehouse.dvc data/processed/.gitignore
git commit -m "Track processed lakehouse with DVC"
```

This enables:

- Dataset versioning (v1.0, v1.1, …)

- Rollbacks

- Reproducible experiments

## Why This Project Matters

This project mirrors **real AV data workflows**:

- Sensor ingestion

- Scalable storage formats

- Spark-based ETL

- Dataset traceability

It demonstrates **practical data engineering skills** — not toy scripts.

## Next Steps (Optional Extensions)

- Add object labels and create Dataset v1.1

- Integrate MinIO (local S3)

- Add Prefect/Dagster orchestration

- Add basic data quality checks

- Query Parquet with Spark SQL

## Notes

- GPU is not required

- TensorFlow GPU warnings can be safely ignored

- Designed to run on a laptop or VM

## Author

Built as a learning-focused AV data engineering project.


---

