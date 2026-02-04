# AV-Lakehouse: Scalable Sensor Data Indexing & Versioning

## Overview
AV-Lakehouse is a hands-on project that simulates an autonomous vehicle (AV) sensor data pipeline — from raw ingestion to analytics-ready storage with version control.

The goal is to demonstrate real-world AV data engineering patterns:

- Handling raw sensor data (images + metadata)
- Converting semi-structured data into optimized Parquet tables
- Partitioning for fast querying
- Tracking dataset versions reproducibly using DVC

This project intentionally uses small sample data (not multi-TB datasets) to keep the workflow lightweight while still realistic.

---

## Architecture

```text
Raw Sensor Data (Waymo TFRecords)
        |
        v
Mock Upload Script (Python)
        |
        v
Raw Lake (Images + JSON metadata)
        |
        v
Spark ETL (PySpark)
        |
        v
Partitioned Parquet Lakehouse
        |
        v
Dataset Versioning (DVC)

```
---

```md
## Tech Stack

| Layer | Technology |
|------|------------|
| Language | Python 3.10 |
| Data Processing | PySpark |
| Storage Format | Apache Parquet |
| Raw Dataset | Waymo Open Dataset (tutorial frames) |
| Versioning | DVC |
| Environment | Python virtualenv |

```text
av-sensor-ingestion-engine/
│
├── src/
│   ├── ingestion/
│   │   └── mock_upload_waymo.py
│   └── spark_jobs/
│       └── etl_to_parquet.py
│
├── data/
│   ├── raw/
│   │   └── uploads/
│   └── processed/
│       └── lakehouse/
│
├── scripts/
│   └── inspect_frame.py
│
├── .dvc/
├── data/processed/lakehouse.dvc
└── README.md
```
Phase 1 — Raw Ingestion (Data Lake)
Goal: Simulate a vehicle uploading raw sensor data.

Reads Waymo tutorial TFRecord frames

Extracts front camera images

Writes:

JPG images

JSON metadata (timestamps, pose, vehicle_id, frame_id)

Example output:

data/raw/uploads/
└── vehicle_id=sim-001/
    └── date=2026-02-01/
        ├── frame_000000_front.jpg
        ├── frame_000001_front.jpg
        └── frame_000000.json
Run:

python src/ingestion/mock_upload_waymo.py
Phase 2 — Spark ETL (Lakehouse Core)
Goal: Convert messy JSON metadata into analytics-ready Parquet.

Transformations:

Convert timestamps from microseconds → seconds

Normalize fields

Add simple quality flags

Preserve pose and LiDAR metadata

Partition output by date and vehicle_id

Output:

data/processed/lakehouse/
└── date=2026-02-01/
    └── vehicle_id=sim-001/
        ├── part-*.parquet
        └── _SUCCESS
Run:

python src/spark_jobs/etl_to_parquet.py
Phase 3 — Dataset Versioning (DVC)
Goal: Enable reproducibility and dataset evolution.

Track Parquet lakehouse using DVC

Commit metadata to Git

Keep large data files out of Git

dvc init
dvc add data/processed/lakehouse
git add data/processed/lakehouse.dvc data/processed/.gitignore
git commit -m "Track processed lakehouse with DVC"
This enables:

Dataset versioning (v1.0, v1.1, …)

Rollbacks

Reproducible experiments

Why This Project Matters
This project mirrors real AV data workflows:

Sensor ingestion

Scalable storage formats

Spark-based ETL

Dataset traceability

It demonstrates practical data engineering skills — not toy scripts.

Notes
GPU is not required

TensorFlow GPU warnings can be safely ignored

Designed to run on a laptop or VM

Author
Built as a learning-focused AV data engineering project.


---

