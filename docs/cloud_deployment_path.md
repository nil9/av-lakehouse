# Cloud Deployment Path (Minimal, Config-Driven)

This project now supports environment-driven storage paths for Silver and Gold outputs so the same Spark jobs can target local files, S3 (`s3a://...`), or ADLS (`abfss://...`) without code changes.

## Architecture Diagram

```text
                 +---------------------------+
                 |   Bronze ingestion job    |
                 | (raw JSON in uploads dir) |
                 +-------------+-------------+
                               |
                               v
                 +---------------------------+
                 |   Silver transform job    |
                 | RAW_INPUT_PATH            |
                 | SILVER_OUTPUT_PATH        |
                 +-------------+-------------+
                               |
                               v
                 +---------------------------+
                 |   Data quality checks     |
                 | QUALITY_SILVER_PATH       |
                 +-------------+-------------+
                               |
                               v
                 +---------------------------+
                 |    Gold aggregation job   |
                 | SILVER_OUTPUT_PATH        |
                 | GOLD_OUTPUT_PATH          |
                 +---------------------------+
```

## Cloud-Ready Configuration Pattern

Environment variables used by the pipeline:

- `RAW_INPUT_PATH`
- `SILVER_OUTPUT_PATH`
- `GOLD_OUTPUT_PATH`
- `QUALITY_SILVER_PATH` (defaults to `SILVER_OUTPUT_PATH`)

### Local default values

- `RAW_INPUT_PATH=data/raw/uploads`
- `SILVER_OUTPUT_PATH=data/silver/lakehouse`
- `GOLD_OUTPUT_PATH=data/gold/vehicle_daily_summary`

## How I'd run on AWS (S3 path example)

```bash
export RAW_INPUT_PATH="data/raw/uploads"
export SILVER_OUTPUT_PATH="s3a://my-av-lakehouse/silver/lakehouse"
export GOLD_OUTPUT_PATH="s3a://my-av-lakehouse/gold/vehicle_daily_summary"
export QUALITY_SILVER_PATH="$SILVER_OUTPUT_PATH"

# Spark runtime must include S3 credentials + hadoop-aws package in real deployment.
./scripts/run_pipeline.sh
```

## How I'd run on Azure (ADLS path example)

```bash
export RAW_INPUT_PATH="data/raw/uploads"
export SILVER_OUTPUT_PATH="abfss://silver@myaccount.dfs.core.windows.net/lakehouse"
export GOLD_OUTPUT_PATH="abfss://gold@myaccount.dfs.core.windows.net/vehicle_daily_summary"
export QUALITY_SILVER_PATH="$SILVER_OUTPUT_PATH"

# Spark runtime must include ADLS auth/spark.hadoop configs in real deployment.
./scripts/run_pipeline.sh
```

## Notes

- This repo remains local-demo-first.
- Cloud examples above show configuration compatibility, not full credential/bootstrap automation.
