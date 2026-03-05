import json
from pathlib import Path

import tensorflow as tf
from waymo_open_dataset import dataset_pb2 as open_dataset

WAYMO_TUTORIAL_FILE = "waymo-open-dataset/tutorial/frames"
OUTPUT_ROOT = Path("data/raw/uploads")
VEHICLE_ID = "sim-001"
MAX_FRAMES = 20


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    dataset = tf.data.TFRecordDataset(WAYMO_TUTORIAL_FILE, compression_type="")

    uploaded_frames = 0
    skipped_frames = 0

    for i, data in enumerate(dataset.take(MAX_FRAMES)):
        frame = open_dataset.Frame()
        frame.ParseFromString(bytearray(data.numpy()))

        timestamp = frame.timestamp_micros
        date = "2026-02-01"
        frame_id = f"frame_{i:06d}"

        base_dir = OUTPUT_ROOT / f"vehicle_id={VEHICLE_ID}" / f"date={date}"
        ensure_dir(base_dir)

        front_images = [img for img in frame.images if img.name == open_dataset.CameraName.FRONT]
        if not front_images:
            skipped_frames += 1
            continue

        img = front_images[0]
        image_path = base_dir / f"{frame_id}_front.jpg"
        tf.io.write_file(str(image_path), img.image)
        transform = frame.pose.transform

        metadata = {
            "vehicle_id": VEHICLE_ID,
            "frame_id": frame_id,
            "timestamp_micros": timestamp,
            "date": date,
            "camera_name": "FRONT",
            "image_path": str(image_path),
            "pose": {
                "tx": float(transform[3]),
                "ty": float(transform[7]),
                "tz": float(transform[11]),
                "T": list(map(float, transform)),
            },
            "lidar_count": len(frame.lasers),
            "has_lidar": len(frame.lasers) > 0,
        }

        json_path = base_dir / f"{frame_id}.json"
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)

        uploaded_frames += 1
        print(f"[BRONZE] Uploaded {frame_id}")

    print(
        "[BRONZE] Completed ingestion "
        f"(uploaded={uploaded_frames}, skipped={skipped_frames}, max_frames={MAX_FRAMES})"
    )

    return 0 if uploaded_frames > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
