# AV-Lakehouse: Consulting-Focused Data Platform Blueprint
[![CI](https://github.com/nil9/av-lakehouse/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/nil9/av-lakehouse/actions/workflows/ci.yml)

## Executive Summary

AV-Lakehouse is a practical blueprint for running autonomous vehicle (AV) sensor data ingestion and analytics as an operating service, not just a script.

It demonstrates how to move from raw sensor frames to trusted analytics outputs with:

- repeatable ETL layers (Bronze, Silver, Gold)
- quality gates and fail-fast behavior
- operational observability artifacts
- CI and containerized execution
- dataset versioning with DVC

This repository is intentionally lightweight (tutorial-scale data) so teams can validate patterns before scaling to production-grade data volume.

## Business Outcomes

This implementation is framed around outcomes a delivery team can present to engineering leadership:

- Faster analytics onboarding:
  - Raw and transformed datasets are clearly separated and query-ready.
- Lower data incident risk:
  - Data quality checks enforce required fields, null thresholds, and timestamp validity.
- Higher operational confidence:
  - Structured logs, SLA artifacts, and runbooks support incident triage.
- Better delivery velocity:
  - CI gates enforce lint/test/sample checks on every change.
- Reproducible data releases:
  - DVC enables deterministic roll-forward and rollback.

## Operating Model

The repo supports a simple DataOps operating model suitable for a small platform team.

### Roles and responsibilities

- Data Engineer:
  - owns ingestion and transformations (`src/ingestion`, `src/spark_jobs`)
- Analytics Engineer:
  - consumes Gold outputs and defines downstream metrics
- Platform/DevOps:
  - maintains CI, container runtime, and environment consistency
- On-call Engineer:
  - triages incidents with logs, SLA JSON, and runbook guidance

### Run cadence

- CI on push/PR for code quality and behavioral checks
- Local/containerized pipeline runs for development validation
- Dataset version checkpointing after significant schema or logic changes

### Control points

- Quality gate after Silver transformation
- Pipeline-level success criteria and SLA output
- Structured event trail for step-level accountability

## Architecture

```text
Bronze (raw uploads: images + JSON metadata)
  -> Silver (cleaned, normalized, partitioned Parquet)
  -> Gold (aggregated analytics tables)
  -> DVC versioning (dataset lineage and reproducibility)
```

## Core Capabilities Delivered

### 1) Data Pipeline

- Bronze ingestion from Waymo tutorial frames
- Canonical schema harmonization for Waymo-like and OEM-B-like source payloads
- Silver normalization with Spark
- Gold aggregations for analytics use cases

### 2) Data Quality Controls

- Required column checks
- Null-ratio thresholds
- Event timestamp validity windows
- Hard pipeline failure when thresholds are violated

### 3) Observability Artifacts

For each run, the pipeline emits:

- Step log: `logs/pipeline_<timestamp>.log`
- Structured events: `logs/pipeline_events_<timestamp>.jsonl`
- SLA metric: `logs/pipeline_sla_<timestamp>.json`
- Quality reports: `logs/quality_report_<timestamp>.json` and `.md`

Incident guide:

- [`docs/incident_runbook.md`](docs/incident_runbook.md)

### 4) CI/CD Basics

GitHub Actions pipeline stages:

- `lint`: `ruff check src scripts tests`
- `tests`: `pytest tests/test_schema_harmonization.py tests/test_data_quality.py`
- `sample-run`: builds sample Silver data and executes quality check

### 5) Containerized Runtime

- `Dockerfile` for reproducible local runtime
- `docker-compose.yml` for one-command orchestration

## Tech Stack

| Layer | Technology |
|------|------------|
| Language | Python 3.10 |
| Processing | PySpark |
| Storage | Apache Parquet |
| Source Data | Waymo tutorial frames |
| Versioning | DVC |
| CI | GitHub Actions |
| Container Runtime | Docker / Docker Compose |

## How To Run

### Local pipeline

```bash
./scripts/run_pipeline.sh
```

Useful runtime config:

```bash
export QUALITY_MAX_NULL_RATIO_DATE=0.0
export QUALITY_MAX_NULL_RATIO_VEHICLE_ID=0.0
export QUALITY_MAX_NULL_RATIO_FRAME_ID=0.0
export QUALITY_MAX_NULL_RATIO_TIMESTAMP_MICROS=0.0
export QUALITY_MAX_NULL_RATIO_EVENT_TIME=0.0
export QUALITY_MAX_NULL_RATIO_HAS_LIDAR=0.0
export QUALITY_MAX_INVALID_EVENT_TIME_RATIO=0.0
export QUALITY_MIN_EVENT_TIME="2010-01-01 00:00:00"
export QUALITY_MAX_EVENT_TIME="2035-01-01 00:00:00"
export SLA_MAX_DURATION_SECONDS=900
./scripts/run_pipeline.sh
```

Run quality checks independently:

```bash
python3 scripts/run_data_quality_checks.py
```

### Docker run

Build:

```bash
docker build -t av-lakehouse:local .
```

Run full pipeline:

```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  av-lakehouse:local
```

Run quality checks only:

```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  av-lakehouse:local \
  bash -lc "python3 scripts/run_data_quality_checks.py"
```

Optional compose:

```bash
docker compose up --build
```

## Project Structure (Key Paths)

```text
src/ingestion/bronze_ingestion.py
src/harmonization/canonical_schema.py
src/spark_jobs/silver_transform.py
src/spark_jobs/gold_aggregation.py
src/quality/data_quality.py
scripts/run_pipeline.sh
scripts/run_data_quality_checks.py
docs/incident_runbook.md
.github/workflows/ci.yml
Dockerfile
docker-compose.yml
```

## Trade-offs and Current Constraints

Current design decisions are intentional for speed and clarity:

- Local-first execution:
  - No external orchestration service yet (Prefect/Airflow not included).
- Tutorial-scale dataset:
  - Validates patterns, but not a throughput benchmark.
- Batch-oriented processing:
  - No streaming ingestion path in current scope.
- Simple SLA model:
  - Single completion SLI/SLO; no per-step latency budgets yet.
- Lightweight governance:
  - Quality rules are code-driven and configurable, but not connected to a centralized data catalog.

### Canonical schema harmonization

A dedicated harmonization module maps distinct mock manufacturer payloads into one canonical Silver contract (date, vehicle_id, frame_id, timestamp_micros, event_time, has_lidar, camera_name, image_path, source_manufacturer).

- Mapping implementation: `src/harmonization/canonical_schema.py`
- Mock source schemas: `data/mock_sources/waymo_like.json`, `data/mock_sources/oem_b_like.json`
- Mapping documentation: `docs/schema_harmonization.md`
- Validation tests: `tests/test_schema_harmonization.py`

## Roadmap

### Near term (0-30 days)

- Add per-step duration metrics and trend snapshots
- Add schema evolution tests for backward compatibility
- Add Makefile targets for common local/dev workflows

### Mid term (30-90 days)

- Add orchestration layer (Prefect or Dagster)
- Add object-level labels and enriched Gold datasets
- Add remote artifact storage (MinIO/S3) for DVC and logs

### Longer term (90+ days)

- Introduce streaming ingestion path
- Add cost/performance benchmarking at larger data scales
- Add policy-driven data contracts and catalog integration

## Why This Matters In Consulting Context

This repo can be used as:

- a discovery accelerator for data platform engagements
- a reference implementation for DataOps operating model discussions
- a practical artifact to communicate trade-offs between delivery speed and production hardening

