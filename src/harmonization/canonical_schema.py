import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_COLUMNS = (
    "date",
    "vehicle_id",
    "frame_id",
    "timestamp_micros",
    "event_time",
    "has_lidar",
    "camera_name",
    "image_path",
    "source_manufacturer",
)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"true", "1", "yes", "y", "available"}
    return False


def _event_time_from_micros(timestamp_micros: int) -> str:
    ts_seconds = timestamp_micros / 1_000_000
    return datetime.fromtimestamp(ts_seconds, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _normalize_waymo_like(record: dict[str, Any]) -> dict[str, Any]:
    timestamp_micros = int(record["timestamp_micros"])
    return {
        "date": record["date"],
        "vehicle_id": record["vehicle_id"],
        "frame_id": record["frame_id"],
        "timestamp_micros": timestamp_micros,
        "event_time": _event_time_from_micros(timestamp_micros),
        "has_lidar": _to_bool(record.get("has_lidar", False)),
        "camera_name": record.get("camera_name", "UNKNOWN"),
        "image_path": record.get("image_path", ""),
        "source_manufacturer": "waymo_like",
    }


def _normalize_oem_b_like(record: dict[str, Any]) -> dict[str, Any]:
    frame = record["frame"]
    sensors = record.get("sensors", {})
    lidar = sensors.get("lidar", {})
    assets = record.get("assets", {})

    timestamp_micros = int(frame["captured_at_us"])
    return {
        "date": record["capture_date"],
        "vehicle_id": record["vehicle"],
        "frame_id": frame["id"],
        "timestamp_micros": timestamp_micros,
        "event_time": _event_time_from_micros(timestamp_micros),
        "has_lidar": _to_bool(lidar.get("available", False)),
        "camera_name": sensors.get("camera", "UNKNOWN").upper(),
        "image_path": assets.get("front_image", ""),
        "source_manufacturer": "oem_b_like",
    }


def harmonize_source_record(source_name: str, record: dict[str, Any]) -> dict[str, Any]:
    """Map a source record into the canonical Silver contract."""
    if source_name == "waymo_like":
        return _normalize_waymo_like(record)
    if source_name == "oem_b_like":
        return _normalize_oem_b_like(record)
    raise ValueError(f"Unsupported source_name '{source_name}'")


def _read_json_records(file_path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Input JSON must be an object or array of objects")


def harmonize_json_file(file_path: str | Path, source_name: str) -> list[dict[str, Any]]:
    records = _read_json_records(file_path)
    return [harmonize_source_record(source_name, record) for record in records]


def write_canonical_jsonl(records: list[dict[str, Any]], output_file: str | Path) -> Path:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row) + "\n")
    return output_path
