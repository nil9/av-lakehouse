import tensorflow as tf
import matplotlib.pyplot as plt
from waymo_open_dataset import dataset_pb2
from pathlib import Path

tfrecord_path = "waymo-open-dataset/tutorial/frames"

dataset = tf.data.TFRecordDataset(tfrecord_path, compression_type="")

for data in dataset.take(1):
    frame = dataset_pb2.Frame()
    frame.ParseFromString(bytearray(data.numpy()))
    print("Context:", frame.context.name)
    print("Timestamp:", frame.timestamp_micros)
    print("Cameras:", len(frame.images))
    print("LiDARs:", len(frame.lasers))

    # pick first camera image in the frame
    img_bytes = frame.images[1].image
    image = tf.io.decode_jpeg(img_bytes)
    plt.imshow(image.numpy())
    plt.axis("off")
    out_path = Path(__file__).parent / "out_frame0_cam1.png"
    plt.savefig(out_path, bbox_inches="tight", pad_inches=0)
    print("Saved:", out_path.resolve())
