from datetime import datetime

from src.spark_jobs.gold_aggregation import build_ai_compatible_export


def test_ai_export_falls_back_when_source_manufacturer_missing(spark) -> None:
    rows = [
        {
            "date": "2026-02-01",
            "vehicle_id": "sim-001",
            "frame_id": "frame_000001",
            "camera_name": "FRONT",
            "has_lidar": True,
            "image_path": "data/raw/uploads/frame_000001_front.jpg",
            "event_time": datetime(2026, 2, 1, 12, 0, 0),
        }
    ]
    df = spark.createDataFrame(rows)

    exported = build_ai_compatible_export(df, "data/silver/lakehouse")
    output = exported.collect()

    assert len(output) == 1
    assert output[0]["source_manufacturer"] == "unknown"
    assert output[0]["document_id"] == "unknown::sim-001::2026-02-01"

