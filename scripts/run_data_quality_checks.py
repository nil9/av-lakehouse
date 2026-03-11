#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


def main() -> int:
    from src.quality.data_quality import QualityConfig, run_data_quality_checks

    config = QualityConfig(
        silver_path=os.getenv(
            "QUALITY_SILVER_PATH", os.getenv("SILVER_OUTPUT_PATH", "data/silver/lakehouse")
        ),
        output_dir=os.getenv("QUALITY_OUTPUT_DIR", "logs"),
        min_valid_event_time=os.getenv(
            "QUALITY_MIN_EVENT_TIME", "2010-01-01 00:00:00"
        ),
        max_valid_event_time=os.getenv(
            "QUALITY_MAX_EVENT_TIME", "2035-01-01 00:00:00"
        ),
        max_null_ratio_date=_env_float("QUALITY_MAX_NULL_RATIO_DATE", 0.0),
        max_null_ratio_vehicle_id=_env_float("QUALITY_MAX_NULL_RATIO_VEHICLE_ID", 0.0),
        max_null_ratio_frame_id=_env_float("QUALITY_MAX_NULL_RATIO_FRAME_ID", 0.0),
        max_null_ratio_timestamp_micros=_env_float(
            "QUALITY_MAX_NULL_RATIO_TIMESTAMP_MICROS", 0.0
        ),
        max_null_ratio_event_time=_env_float("QUALITY_MAX_NULL_RATIO_EVENT_TIME", 0.0),
        max_null_ratio_has_lidar=_env_float("QUALITY_MAX_NULL_RATIO_HAS_LIDAR", 0.0),
        max_invalid_event_time_ratio=_env_float(
            "QUALITY_MAX_INVALID_EVENT_TIME_RATIO", 0.0
        ),
    )

    spark = SparkSession.builder.appName("DataQualityChecks").getOrCreate()
    try:
        is_valid, report, json_path, md_path = run_data_quality_checks(spark, config)
    finally:
        spark.stop()

    print(
        "[QUALITY] Completed checks "
        f"(status={report['status']}, json_report='{json_path}', markdown_report='{md_path}')"
    )

    if not is_valid:
        for violation in report["violations"]:
            print(f"[QUALITY] Violation: {violation}")
        return 1

    print("[QUALITY] All thresholds passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
