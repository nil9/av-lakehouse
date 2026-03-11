# Canonical Schema Harmonization

This module demonstrates cross-manufacturer harmonization by normalizing two mock source schemas into a single canonical Silver contract.

## Canonical Silver Contract

Canonical fields produced for every source record:

- `date`
- `vehicle_id`
- `frame_id`
- `timestamp_micros`
- `event_time`
- `has_lidar`
- `camera_name`
- `image_path`
- `source_manufacturer`

## Source Schemas Included

- Waymo-like mock records: `data/mock_sources/waymo_like.json`
- OEM-B-like mock records: `data/mock_sources/oem_b_like.json`

## Mapping Rules

| Canonical field | waymo_like input | oem_b_like input |
|---|---|---|
| `date` | `date` | `capture_date` |
| `vehicle_id` | `vehicle_id` | `vehicle` |
| `frame_id` | `frame_id` | `frame.id` |
| `timestamp_micros` | `timestamp_micros` | `frame.captured_at_us` |
| `event_time` | derived from `timestamp_micros` (UTC) | derived from `frame.captured_at_us` (UTC) |
| `has_lidar` | `has_lidar` | `sensors.lidar.available` (bool coercion) |
| `camera_name` | `camera_name` | `sensors.camera` (uppercased) |
| `image_path` | `image_path` | `assets.front_image` |
| `source_manufacturer` | constant `waymo_like` | constant `oem_b_like` |

## Usage

Use `src/harmonization/canonical_schema.py`:

- `harmonize_json_file(file_path, source_name)` to map one source file.
- `harmonize_source_record(source_name, record)` to map individual records.

This capability can be plugged in before the Silver transformation so multiple OEM payloads are normalized into one stable contract.
