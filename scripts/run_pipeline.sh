#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pipeline_$(date +%Y%m%d_%H%M%S).log"
START_TS=$(date +%s)

run_step() {
  local name="$1"
  local cmd="$2"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] START ${name}" | tee -a "$LOG_FILE"
  eval "$cmd" 2>&1 | tee -a "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] END   ${name}" | tee -a "$LOG_FILE"
}

run_step "bronze_ingestion" "python src/ingestion/bronze_ingestion.py"
run_step "silver_transform" "python src/spark_jobs/silver_transform.py"
run_step "gold_aggregation" "python src/spark_jobs/gold_aggregation.py"

JSON_COUNT=$(find data/raw/uploads -type f -name '*.json' | wc -l | tr -d ' ')
SILVER_PARQUET_COUNT=$(find data/silver/lakehouse -type f -name '*.parquet' | wc -l | tr -d ' ')
GOLD_PARQUET_COUNT=$(find data/gold/vehicle_daily_summary -type f -name '*.parquet' | wc -l | tr -d ' ')

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))

echo "" | tee -a "$LOG_FILE"
echo "==== PIPELINE SUCCESS CRITERIA ====" | tee -a "$LOG_FILE"
echo "raw_json_files=${JSON_COUNT}" | tee -a "$LOG_FILE"
echo "silver_parquet_files=${SILVER_PARQUET_COUNT}" | tee -a "$LOG_FILE"
echo "gold_parquet_files=${GOLD_PARQUET_COUNT}" | tee -a "$LOG_FILE"
echo "duration_seconds=${DURATION}" | tee -a "$LOG_FILE"
echo "log_file=${LOG_FILE}" | tee -a "$LOG_FILE"

if [[ "$JSON_COUNT" -eq 0 || "$SILVER_PARQUET_COUNT" -eq 0 || "$GOLD_PARQUET_COUNT" -eq 0 ]]; then
  echo "[PIPELINE] Failed success criteria checks." | tee -a "$LOG_FILE"
  exit 1
fi

echo "[PIPELINE] All success criteria passed." | tee -a "$LOG_FILE"
