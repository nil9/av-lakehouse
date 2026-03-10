from src.harmonization.canonical_schema import (
    CANONICAL_COLUMNS,
    harmonize_json_file,
    harmonize_source_record,
)


def test_harmonize_waymo_like_mock_file() -> None:
    rows = harmonize_json_file("data/mock_sources/waymo_like.json", "waymo_like")

    assert len(rows) == 2
    assert set(rows[0].keys()) == set(CANONICAL_COLUMNS)
    assert rows[0]["source_manufacturer"] == "waymo_like"
    assert rows[0]["vehicle_id"] == "sim-001"
    assert rows[0]["event_time"] == "2025-10-09 08:53:20"


def test_harmonize_oem_b_like_mock_file() -> None:
    rows = harmonize_json_file("data/mock_sources/oem_b_like.json", "oem_b_like")

    assert len(rows) == 2
    assert set(rows[0].keys()) == set(CANONICAL_COLUMNS)
    assert rows[0]["source_manufacturer"] == "oem_b_like"
    assert rows[0]["frame_id"] == "oemb_900001"
    assert rows[0]["camera_name"] == "FRONT"
    assert rows[0]["has_lidar"] is True
    assert rows[1]["has_lidar"] is False


def test_unsupported_source_raises_error() -> None:
    try:
        harmonize_source_record("unknown_source", {})
    except ValueError as exc:
        assert "Unsupported source_name" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported source")
