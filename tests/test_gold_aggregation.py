import pytest

pytest.importorskip("pyspark")

from datetime import datetime

from src.spark_jobs.gold_aggregation import build_ai_compatible_export


def test_build_ai_compatible_export_contains_expected_fields(spark) -> None:
    rows = [
        {
            "date": "2026-02-01",
            "vehicle_id": "sim-001",
            "frame_id": "frame_000001",
            "timestamp_micros": 1760000000000000,
            "event_time": datetime(2026, 2, 1, 12, 0, 0),
            "has_lidar": True,
            "camera_name": "FRONT",
            "source_manufacturer": "waymo_like",
            "image_path": "data/raw/uploads/vehicle_id=sim-001/date=2026-02-01/frame_000001_front.jpg",
        }
    ]
    silver_df = spark.createDataFrame(rows)

    ai_df = build_ai_compatible_export(silver_df, "data/silver/lakehouse")
    ai_row = ai_df.collect()[0]

    assert len(ai_row.chunk_id) == 64
    assert ai_row.document_id == "waymo_like::sim-001::2026-02-01"
    assert ai_row.normalized_text == (
        "vehicle sim-001 frame frame_000001 camera front date 2026-02-01 "
        "lidar true source waymo_like"
    )
    assert ai_row.event_timestamp == "2026-02-01T12:00:00Z"
    assert ai_row.source_table_path == "data/silver/lakehouse"
    assert ai_row.source_image_path.endswith("frame_000001_front.jpg")
    assert '"vehicle_id":"sim-001"' in ai_row.metadata_json


def test_build_ai_compatible_export_has_lineage_and_timestamp_columns(spark) -> None:
    rows = [
        {
            "date": "2026-02-01",
            "vehicle_id": "sim-001",
            "frame_id": "frame_000001",
            "timestamp_micros": 1760000000000000,
            "event_time": datetime(2026, 2, 1, 12, 0, 0),
            "has_lidar": True,
            "camera_name": "FRONT",
            "source_manufacturer": "waymo_like",
            "image_path": "img.jpg",
        }
    ]

    ai_df = build_ai_compatible_export(spark.createDataFrame(rows), "data/silver/lakehouse")

    assert "exported_at_utc" in ai_df.columns
    assert "metadata_json" in ai_df.columns
    assert "source_table_path" in ai_df.columns
