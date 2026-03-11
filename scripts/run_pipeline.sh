#!/usr/bin/env bash
set -eEuo pipefail

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

RUN_STAMP="$(date +%Y%m%d_%H%M%S)"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$LOG_DIR/pipeline_${RUN_STAMP}.log"
STRUCTURED_LOG_FILE="$LOG_DIR/pipeline_events_${RUN_STAMP}.jsonl"
SLA_METRIC_FILE="$LOG_DIR/pipeline_sla_${RUN_STAMP}.json"
START_TS="$(date +%s)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SLA_MAX_DURATION_SECONDS="${SLA_MAX_DURATION_SECONDS:-900}"
RAW_INPUT_PATH="${RAW_INPUT_PATH:-data/raw/uploads}"
SILVER_OUTPUT_PATH="${SILVER_OUTPUT_PATH:-data/silver/lakehouse}"
GOLD_OUTPUT_PATH="${GOLD_OUTPUT_PATH:-data/gold/vehicle_daily_summary}"
QUALITY_SILVER_PATH="${QUALITY_SILVER_PATH:-$SILVER_OUTPUT_PATH}"
export RAW_INPUT_PATH SILVER_OUTPUT_PATH GOLD_OUTPUT_PATH QUALITY_SILVER_PATH
PIPELINE_FINALIZED=0

count_files() {
  local path="$1"
  local pattern="$2"
  if [[ -d "$path" ]]; then
    find "$path" -type f -name "$pattern" | wc -l | tr -d ' '
  else
    echo "0"
  fi
}

emit_event() {
  local level="$1"
  local event="$2"
  local message="$3"
  local step="${4:-}"
  local status="${5:-}"
  local timestamp_utc
  timestamp_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  EVENT_LEVEL="$level" \
  EVENT_NAME="$event" \
  EVENT_MESSAGE="$message" \
  EVENT_STEP="$step" \
  EVENT_STATUS="$status" \
  EVENT_TIMESTAMP_UTC="$timestamp_utc" \
  EVENT_RUN_ID="$RUN_ID" \
  EVENT_LOG_FILE="$LOG_FILE" \
  "$PYTHON_BIN" - <<'PY' >>"$STRUCTURED_LOG_FILE"
import json
import os

event = {
    "timestamp_utc": os.environ["EVENT_TIMESTAMP_UTC"],
    "run_id": os.environ["EVENT_RUN_ID"],
    "level": os.environ["EVENT_LEVEL"],
    "event": os.environ["EVENT_NAME"],
    "message": os.environ["EVENT_MESSAGE"],
    "step": os.environ.get("EVENT_STEP") or None,
    "status": os.environ.get("EVENT_STATUS") or None,
    "log_file": os.environ["EVENT_LOG_FILE"],
}
print(json.dumps({k: v for k, v in event.items() if v is not None}))
PY
}

write_sla_metric() {
  local pipeline_status="$1"
  local success_criteria_met="$2"
  local duration_seconds="$3"
  local raw_json_files="$4"
  local silver_parquet_files="$5"
  local gold_parquet_files="$6"
  local end_ts
  local within_duration_sla="false"
  local sla_met="false"

  end_ts="$(date +%s)"
  if (( duration_seconds <= SLA_MAX_DURATION_SECONDS )); then
    within_duration_sla="true"
  fi

  if [[ "$pipeline_status" == "success" && "$success_criteria_met" == "true" && "$within_duration_sla" == "true" ]]; then
    sla_met="true"
  fi

  SLA_RUN_ID="$RUN_ID" \
  SLA_STATUS="$pipeline_status" \
  SLA_SUCCESS_CRITERIA="$success_criteria_met" \
  SLA_DURATION="$duration_seconds" \
  SLA_THRESHOLD="$SLA_MAX_DURATION_SECONDS" \
  SLA_WITHIN_DURATION="$within_duration_sla" \
  SLA_MET="$sla_met" \
  SLA_RAW_JSON="$raw_json_files" \
  SLA_SILVER_PARQUET="$silver_parquet_files" \
  SLA_GOLD_PARQUET="$gold_parquet_files" \
  SLA_START_TS="$START_TS" \
  SLA_END_TS="$end_ts" \
  "$PYTHON_BIN" - <<'PY' >"$SLA_METRIC_FILE"
import json
import os

metric = {
    "run_id": os.environ["SLA_RUN_ID"],
    "pipeline_status": os.environ["SLA_STATUS"],
    "success_criteria_met": os.environ["SLA_SUCCESS_CRITERIA"] == "true",
    "sla": {
        "name": "pipeline_completion",
        "duration_seconds": int(os.environ["SLA_DURATION"]),
        "threshold_seconds": int(os.environ["SLA_THRESHOLD"]),
        "within_duration_threshold": os.environ["SLA_WITHIN_DURATION"] == "true",
        "met": os.environ["SLA_MET"] == "true",
    },
    "counts": {
        "raw_json_files": int(os.environ["SLA_RAW_JSON"]),
        "silver_parquet_files": int(os.environ["SLA_SILVER_PARQUET"]),
        "gold_parquet_files": int(os.environ["SLA_GOLD_PARQUET"]),
    },
    "timing": {
        "start_unix_epoch": int(os.environ["SLA_START_TS"]),
        "end_unix_epoch": int(os.environ["SLA_END_TS"]),
    },
}
print(json.dumps(metric, indent=2))
PY
}

on_error() {
  local exit_code="$1"
  local failed_command="${2:-unknown}"

  if [[ "$PIPELINE_FINALIZED" -eq 1 ]]; then
    exit "$exit_code"
  fi

  set +e
  local end_ts duration json_count silver_count gold_count
  end_ts="$(date +%s)"
  duration=$((end_ts - START_TS))
  json_count="$(count_files "$RAW_INPUT_PATH" '*.json')"
  silver_count="$(count_files "$SILVER_OUTPUT_PATH" '*.parquet')"
  gold_count="$(count_files "$GOLD_OUTPUT_PATH" '*.parquet')"

  emit_event "error" "pipeline_failed" "Pipeline execution failed at command: ${failed_command}" "" "failed"
  write_sla_metric "failed" "false" "$duration" "$json_count" "$silver_count" "$gold_count"
  echo "[PIPELINE] Failed (exit_code=${exit_code}, command='${failed_command}')." | tee -a "$LOG_FILE"
  echo "[PIPELINE] Structured logs: ${STRUCTURED_LOG_FILE}" | tee -a "$LOG_FILE"
  echo "[PIPELINE] SLA metric: ${SLA_METRIC_FILE}" | tee -a "$LOG_FILE"
  PIPELINE_FINALIZED=1
  exit "$exit_code"
}

trap 'on_error $? "$BASH_COMMAND"' ERR

run_step() {
  local name="$1"
  local cmd="$2"
  emit_event "info" "step_started" "Starting step '${name}'." "$name" "started"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] START ${name}" | tee -a "$LOG_FILE"

  if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] END   ${name}" | tee -a "$LOG_FILE"
    emit_event "info" "step_finished" "Step '${name}' completed." "$name" "success"
  else
    emit_event "error" "step_finished" "Step '${name}' failed." "$name" "failed"
    return 1
  fi
}

emit_event "info" "pipeline_started" "Pipeline execution started." "" "started"
echo "[PIPELINE] Run ID: ${RUN_ID}" | tee -a "$LOG_FILE"
echo "[PIPELINE] Structured logs: ${STRUCTURED_LOG_FILE}" | tee -a "$LOG_FILE"

run_step "bronze_ingestion" "${PYTHON_BIN} -m src.ingestion.bronze_ingestion"
run_step "silver_transform" "${PYTHON_BIN} -m src.spark_jobs.silver_transform"
run_step "data_quality_checks" "${PYTHON_BIN} scripts/run_data_quality_checks.py"
run_step "gold_aggregation" "${PYTHON_BIN} -m src.spark_jobs.gold_aggregation"

JSON_COUNT="$(count_files "$RAW_INPUT_PATH" '*.json')"
SILVER_PARQUET_COUNT="$(count_files "$SILVER_OUTPUT_PATH" '*.parquet')"
GOLD_PARQUET_COUNT="$(count_files "$GOLD_OUTPUT_PATH" '*.parquet')"
END_TS="$(date +%s)"
DURATION="$((END_TS - START_TS))"

echo "" | tee -a "$LOG_FILE"
echo "==== PIPELINE SUCCESS CRITERIA ====" | tee -a "$LOG_FILE"
echo "raw_json_files=${JSON_COUNT}" | tee -a "$LOG_FILE"
echo "silver_parquet_files=${SILVER_PARQUET_COUNT}" | tee -a "$LOG_FILE"
echo "gold_parquet_files=${GOLD_PARQUET_COUNT}" | tee -a "$LOG_FILE"
echo "duration_seconds=${DURATION}" | tee -a "$LOG_FILE"
echo "sla_max_duration_seconds=${SLA_MAX_DURATION_SECONDS}" | tee -a "$LOG_FILE"
echo "log_file=${LOG_FILE}" | tee -a "$LOG_FILE"
echo "structured_log_file=${STRUCTURED_LOG_FILE}" | tee -a "$LOG_FILE"
echo "sla_metric_file=${SLA_METRIC_FILE}" | tee -a "$LOG_FILE"
echo "raw_input_path=${RAW_INPUT_PATH}" | tee -a "$LOG_FILE"
echo "silver_output_path=${SILVER_OUTPUT_PATH}" | tee -a "$LOG_FILE"
echo "gold_output_path=${GOLD_OUTPUT_PATH}" | tee -a "$LOG_FILE"

SUCCESS_CRITERIA_MET="true"
if [[ "$JSON_COUNT" -eq 0 || "$SILVER_PARQUET_COUNT" -eq 0 || "$GOLD_PARQUET_COUNT" -eq 0 ]]; then
  SUCCESS_CRITERIA_MET="false"
fi

SUMMARY_STATUS="success"
if [[ "$SUCCESS_CRITERIA_MET" == "false" ]]; then
  SUMMARY_STATUS="failed"
fi

emit_event "info" "pipeline_summary" "Pipeline summary generated." "" "$SUMMARY_STATUS"

if [[ "$SUCCESS_CRITERIA_MET" == "false" ]]; then
  write_sla_metric "failed" "false" "$DURATION" "$JSON_COUNT" "$SILVER_PARQUET_COUNT" "$GOLD_PARQUET_COUNT"
  emit_event "error" "pipeline_failed" "Pipeline failed success criteria checks." "" "failed"
  echo "[PIPELINE] Failed success criteria checks." | tee -a "$LOG_FILE"
  PIPELINE_FINALIZED=1
  exit 1
fi

write_sla_metric "success" "true" "$DURATION" "$JSON_COUNT" "$SILVER_PARQUET_COUNT" "$GOLD_PARQUET_COUNT"
emit_event "info" "pipeline_completed" "Pipeline completed successfully." "" "success"
echo "[PIPELINE] All success criteria passed." | tee -a "$LOG_FILE"
PIPELINE_FINALIZED=1
