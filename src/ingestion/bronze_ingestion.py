import os
import json
from pathlib import Path

import numpy as np
import cv2
import tensorflow as tf

from waymo_open_dataset import dataset_pb2 as open_dataset
from waymo_open_dataset.utils import frame_utils

# -----------------------
# Configuration
# -----------------------
WAYMO_TUTORIAL_FILE = "waymo-open-dataset/tutorial/frames"
OUTPUT_ROOT = Path("data/raw/uploads")
VEHICLE_ID = "sim-001"
MAX_FRAMES = 20  # keep it small for demo

# -----------------------
# Helpers
# -----------------------
def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save_image(image, path: Path):
    
    image = np.asarray(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), image)


# -----------------------
# Main ingestion
# -----------------------
def main():
    dataset = tf.data.TFRecordDataset(WAYMO_TUTORIAL_FILE, compression_type="")
    

    for i, data in enumerate(dataset.take(MAX_FRAMES)):
        frame = open_dataset.Frame()
        frame.ParseFromString(bytearray(data.numpy()))

        timestamp = frame.timestamp_micros
        date = "2026-02-01"  # fixed date for demo
        frame_id = f"frame_{i:06d}"

        base_dir = OUTPUT_ROOT / f"vehicle_id={VEHICLE_ID}" / f"date={date}"
        ensure_dir(base_dir)

        # --- Extract FRONT camera image ---
        front_images = [
            img for img in frame.images
            if img.name == open_dataset.CameraName.FRONT
        ]

        if not front_images:
            continue
        
        img = front_images[0]
        image_path = base_dir / f"{frame_id}_front.jpg"
        tf.io.write_file(str(image_path), img.image)
        T = frame.pose.transform  # length 16 (4x4)

        # --- Metadata ---
        metadata = {
            "vehicle_id": VEHICLE_ID,
            "frame_id": frame_id,
            "timestamp_micros": timestamp,
            "date": date,
            "camera_name": "FRONT",
            "image_path": str(image_path),
            "pose": {
                "tx": float(T[3]),
                "ty": float(T[7]),
                "tz": float(T[11]),
                "T": list(map(float, T)),
            },
            "lidar_count": len(frame.lasers),
            "has_lidar": len(frame.lasers) > 0,
        }

        json_path = base_dir / f"{frame_id}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"Uploaded {frame_id}")

    print("Mock upload complete.")


if __name__ == "__main__":
    main()
