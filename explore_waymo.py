import tensorflow.compat.v1 as tf
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

tf.enable_eager_execution()

from waymo_open_dataset import dataset_pb2 as open_dataset

FILENAME = "waymo-open-dataset/tutorial/frames"

dataset = tf.data.TFRecordDataset(FILENAME, compression_type="")
for data in dataset.take(1):
    frame = open_dataset.Frame()
    frame.ParseFromString(bytearray(data.numpy()))
    print("Context:", frame.context.name)
    print("Timestamp:", frame.timestamp_micros)
    print("Cameras:", len(frame.images))
    print("LiDARs:", len(frame.lasers))
