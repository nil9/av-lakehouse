import pytest

pytest.importorskip("pyspark")

from pathlib import Path
from datetime import datetime

from pyspark.sql.types import (
    BooleanType,
    StringType,
    StructField,
    StructType,
    TimestampType,
    LongType,
)

from src.quality.data_quality import QualityConfig, run_data_quality_checks


def test_data_quality_passes_for_valid_silver_data(spark, tmp_path: Path) -> None:
    silver_path = tmp_path / "silver"
    report_path = tmp_path / "reports"

    rows = [
        {
            "date": "2026-02-01",
            "vehicle_id": "sim-001",
            "frame_id": "frame_000001",
            "timestamp_micros": 1760000000000000,
            "event_time": datetime(2026, 2, 1, 12, 0, 0),
            "has_lidar": True,
        }
    ]
    spark.createDataFrame(rows).write.mode("overwrite").parquet(str(silver_path))

    config = QualityConfig(silver_path=str(silver_path), output_dir=str(report_path))
    is_valid, report, json_path, md_path = run_data_quality_checks(spark, config)

    assert is_valid is True
    assert report["status"] == "pass"
    assert json_path.exists()
    assert md_path.exists()


def test_data_quality_fails_on_null_ratio_threshold(spark, tmp_path: Path) -> None:
    silver_path = tmp_path / "silver"
    report_path = tmp_path / "reports"

    schema = StructType(
        [
            StructField("date", StringType(), True),
            StructField("vehicle_id", StringType(), True),
            StructField("frame_id", StringType(), True),
            StructField("timestamp_micros", LongType(), True),
            StructField("event_time", TimestampType(), True),
            StructField("has_lidar", BooleanType(), True),
        ]
    )
    rows = [
        (
            None,
            "sim-001",
            "frame_000001",
            1760000000000000,
            datetime(2026, 2, 1, 12, 0, 0),
            True,
        )
    ]
    spark.createDataFrame(rows, schema=schema).write.mode("overwrite").parquet(
        str(silver_path)
    )

    config = QualityConfig(
        silver_path=str(silver_path),
        output_dir=str(report_path),
        max_null_ratio_date=0.0,
    )
    is_valid, report, _, _ = run_data_quality_checks(spark, config)

    assert is_valid is False
    assert report["status"] == "fail"
    assert any("Null ratio for 'date'" in violation for violation in report["violations"])
