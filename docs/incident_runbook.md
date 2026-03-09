# Incident Runbook

## Purpose

This runbook provides first-response steps for failures in the AV-Lakehouse local pipeline.

Primary observability artifacts per run:

- Plain logs: `logs/pipeline_<timestamp>.log`
- Structured logs: `logs/pipeline_events_<timestamp>.jsonl`
- SLA metric: `logs/pipeline_sla_<timestamp>.json`
- Data quality reports: `logs/quality_report_<timestamp>.json` and `.md`

## Quick Triage

1. Find latest run artifacts:
   - `ls -1t logs/pipeline_*.log | head -n 1`
   - `ls -1t logs/pipeline_events_*.jsonl | head -n 1`
   - `ls -1t logs/pipeline_sla_*.json | head -n 1`
2. Check failed step from structured logs:
   - `tail -n 50 logs/pipeline_events_<timestamp>.jsonl`
3. Check quality gate violations if present:
   - `tail -n 120 logs/quality_report_<timestamp>.md`
4. Rerun with explicit SLA threshold if needed:
   - `SLA_MAX_DURATION_SECONDS=1200 ./scripts/run_pipeline.sh`

## Common Incidents

### 1) Spark startup failure

Symptoms:

- Pipeline fails early in `silver_transform`, `data_quality_checks`, or `gold_aggregation`
- Errors mention Java gateway, sockets, or Spark session creation

Actions:

1. Verify Java is available:
   - `java -version`
2. Set local Spark binding explicitly:
   - `export SPARK_LOCAL_IP=127.0.0.1`
3. Re-run pipeline:
   - `./scripts/run_pipeline.sh`

### 2) Data quality gate failure

Symptoms:

- `data_quality_checks` step fails
- Quality report contains threshold violations

Actions:

1. Open latest quality report:
   - `ls -1t logs/quality_report_*.md | head -n 1`
2. Inspect violating fields and ratios in the report.
3. Validate raw/silver content:
   - `find data/raw/uploads -type f -name '*.json' | wc -l`
   - `find data/silver/lakehouse -type f -name '*.parquet' | wc -l`
4. If thresholds are intentionally too strict, rerun with tuned env vars:
   - `export QUALITY_MAX_INVALID_EVENT_TIME_RATIO=0.05`
   - `./scripts/run_pipeline.sh`

### 3) Success criteria failure (empty outputs)

Symptoms:

- Pipeline summary shows one or more output counts as `0`
- `pipeline_status` in SLA metric is `failed`

Actions:

1. Check latest structured logs for the first failed step.
2. Confirm source tutorial file exists:
   - `ls -la waymo-open-dataset/tutorial/frames`
3. Re-run ingestion only to isolate source issue:
   - `python3 src/ingestion/bronze_ingestion.py`

### 4) SLA breach

Symptoms:

- `logs/pipeline_sla_<timestamp>.json` reports `"met": false` due to duration

Actions:

1. Confirm `duration_seconds` vs `threshold_seconds` in the SLA file.
2. Check which step consumed most time via plain and structured logs.
3. Re-run with higher threshold for local/dev context:
   - `SLA_MAX_DURATION_SECONDS=1800 ./scripts/run_pipeline.sh`
4. If repeated, reduce input scope (fewer frames) before rerunning.

## Escalation

Escalate when any of the following occur:

- Same incident repeats 3 consecutive runs.
- Quality violations indicate potential data corruption.
- Pipeline cannot complete within SLA after threshold tuning and retry.

Escalation package should include:

- Latest plain pipeline log
- Latest structured log
- Latest SLA metric JSON
- Latest quality report JSON/MD

