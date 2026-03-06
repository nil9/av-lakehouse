import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit, sum, when


@dataclass(frozen=True)
class QualityConfig:
    silver_path: str = "data/silver/lakehouse"
    output_dir: str = "logs"
    min_valid_event_time: str = "2010-01-01 00:00:00"
    max_valid_event_time: str = "2035-01-01 00:00:00"
    max_null_ratio_date: float = 0.0
    max_null_ratio_vehicle_id: float = 0.0
    max_null_ratio_frame_id: float = 0.0
    max_null_ratio_timestamp_micros: float = 0.0
    max_null_ratio_event_time: float = 0.0
    max_null_ratio_has_lidar: float = 0.0
    max_invalid_event_time_ratio: float = 0.0


REQUIRED_COLUMNS = (
    "date",
    "vehicle_id",
    "frame_id",
    "timestamp_micros",
    "event_time",
    "has_lidar",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _null_ratio(df: DataFrame, column_name: str, row_count: int) -> float:
    if row_count == 0:
        return 1.0

    result = df.select(
        sum(when(col(column_name).isNull(), 1).otherwise(0)).alias("null_count")
    ).collect()[0]
    null_count = int(result["null_count"])
    return null_count / row_count


def _evaluate_checks(df: DataFrame, config: QualityConfig) -> tuple[bool, dict[str, Any]]:
    row_count = df.count()
    columns = set(df.columns)
    missing_columns = sorted(set(REQUIRED_COLUMNS) - columns)

    report: dict[str, Any] = {
        "generated_at_utc": _utc_now(),
        "silver_path": config.silver_path,
        "row_count": row_count,
        "required_columns": list(REQUIRED_COLUMNS),
        "missing_columns": missing_columns,
        "null_ratio_checks": {},
        "timestamp_validity": {},
        "status": "pass",
        "violations": [],
    }

    if row_count == 0:
        report["status"] = "fail"
        report["violations"].append("Silver dataset is empty.")
        return False, report

    if missing_columns:
        report["status"] = "fail"
        report["violations"].append(
            f"Missing required columns: {', '.join(missing_columns)}"
        )
        return False, report

    null_thresholds = {
        "date": config.max_null_ratio_date,
        "vehicle_id": config.max_null_ratio_vehicle_id,
        "frame_id": config.max_null_ratio_frame_id,
        "timestamp_micros": config.max_null_ratio_timestamp_micros,
        "event_time": config.max_null_ratio_event_time,
        "has_lidar": config.max_null_ratio_has_lidar,
    }

    for column_name, threshold in null_thresholds.items():
        ratio = _null_ratio(df, column_name, row_count)
        report["null_ratio_checks"][column_name] = {
            "null_ratio": ratio,
            "threshold": threshold,
            "passed": ratio <= threshold,
        }
        if ratio > threshold:
            report["violations"].append(
                f"Null ratio for '{column_name}' is {ratio:.6f}, above threshold {threshold:.6f}."
            )

    invalid_event_time_count = df.filter(
        col("event_time").isNull()
        | (col("event_time") < lit(config.min_valid_event_time).cast("timestamp"))
        | (col("event_time") > lit(config.max_valid_event_time).cast("timestamp"))
    ).count()
    invalid_event_time_ratio = invalid_event_time_count / row_count

    report["timestamp_validity"] = {
        "min_valid_event_time": config.min_valid_event_time,
        "max_valid_event_time": config.max_valid_event_time,
        "invalid_event_time_count": invalid_event_time_count,
        "invalid_event_time_ratio": invalid_event_time_ratio,
        "max_invalid_event_time_ratio": config.max_invalid_event_time_ratio,
        "passed": invalid_event_time_ratio <= config.max_invalid_event_time_ratio,
    }

    if invalid_event_time_ratio > config.max_invalid_event_time_ratio:
        report["violations"].append(
            "Invalid event_time ratio is "
            f"{invalid_event_time_ratio:.6f}, above threshold {config.max_invalid_event_time_ratio:.6f}."
        )

    if report["violations"]:
        report["status"] = "fail"

    return report["status"] == "pass", report


def _report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Quality Report",
        "",
        f"- Generated at (UTC): `{report['generated_at_utc']}`",
        f"- Silver path: `{report['silver_path']}`",
        f"- Rows checked: `{report['row_count']}`",
        f"- Status: `{report['status'].upper()}`",
        "",
        "## Required Columns",
        "",
        f"- Required: `{', '.join(report['required_columns'])}`",
        f"- Missing: `{', '.join(report['missing_columns']) if report['missing_columns'] else 'none'}`",
        "",
        "## Null Ratio Checks",
        "",
    ]

    for column_name, check in report["null_ratio_checks"].items():
        lines.append(
            f"- `{column_name}`: ratio={check['null_ratio']:.6f}, threshold={check['threshold']:.6f}, passed={check['passed']}"
        )

    timestamp_check = report["timestamp_validity"]
    lines.extend(
        [
            "",
            "## Timestamp Validity",
            "",
            f"- valid range: `{timestamp_check.get('min_valid_event_time', 'n/a')}` to `{timestamp_check.get('max_valid_event_time', 'n/a')}`",
            f"- invalid count: `{timestamp_check.get('invalid_event_time_count', 'n/a')}`",
            f"- invalid ratio: `{timestamp_check.get('invalid_event_time_ratio', 0.0):.6f}`",
            f"- threshold: `{timestamp_check.get('max_invalid_event_time_ratio', 0.0):.6f}`",
            f"- passed: `{timestamp_check.get('passed', False)}`",
            "",
            "## Violations",
            "",
        ]
    )

    if report["violations"]:
        lines.extend([f"- {violation}" for violation in report["violations"]])
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def run_data_quality_checks(
    spark: SparkSession, config: QualityConfig | None = None
) -> tuple[bool, dict[str, Any], Path, Path]:
    config = config or QualityConfig()
    report_dir = Path(config.output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    run_suffix = _run_id()

    try:
        df = spark.read.parquet(config.silver_path)
        is_valid, report = _evaluate_checks(df, config)
    except Exception as exc:  # pragma: no cover - defensive path for runtime failures
        is_valid = False
        report = {
            "generated_at_utc": _utc_now(),
            "silver_path": config.silver_path,
            "row_count": 0,
            "required_columns": list(REQUIRED_COLUMNS),
            "missing_columns": list(REQUIRED_COLUMNS),
            "null_ratio_checks": {},
            "timestamp_validity": {},
            "status": "fail",
            "violations": [f"Unable to read silver data: {exc}"],
        }

    json_report_path = report_dir / f"quality_report_{run_suffix}.json"
    markdown_report_path = report_dir / f"quality_report_{run_suffix}.md"
    json_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_report_path.write_text(_report_to_markdown(report), encoding="utf-8")

    return is_valid, report, json_report_path, markdown_report_path
