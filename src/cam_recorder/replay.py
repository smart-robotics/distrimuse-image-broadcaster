import argparse
import subprocess
import sys
import threading

import cv2
import rclpy
from rclpy.executors import MultiThreadedExecutor
import rosbag2_py
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import CompressedImage

from cam_recorder.viewer import CameraViewerNode


def get_bag_image_topics(bag_path):
    """Read topic metadata from a bag and return image topic names."""
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id="mcap")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="",
        output_serialization_format="",
    )
    reader.open(storage_options, converter_options)
    topics = [
        t.name
        for t in reader.get_all_topics_and_types()
        if t.type == "sensor_msgs/msg/CompressedImage"
    ]
    del reader
    return topics


def main():
    parser = argparse.ArgumentParser(description="Replay a rosbag recording")
    parser.add_argument("bag_path", help="Path to the bag directory")
    parser.add_argument("--loop", action="store_true", help="Loop playback")
    parser.add_argument("--rate", type=float, default=1.0, help="Playback rate")
    parser.add_argument(
        "--no-display", action="store_true", help="Skip image display"
    )

    args = parser.parse_args()

    cmd = ["ros2", "bag", "play", args.bag_path]
    if args.loop:
        cmd.append("--loop")
    if args.rate != 1.0:
        cmd.extend(["--rate", str(args.rate)])

    if args.no_display:
        sys.exit(subprocess.call(cmd))

    topics = get_bag_image_topics(args.bag_path)
    if not topics:
        print("No image topics found in bag, playing without display.")
        sys.exit(subprocess.call(cmd))

    bag_proc = subprocess.Popen(cmd)

    rclpy.init()
    node = CameraViewerNode(topics)
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        while bag_proc.poll() is None:
            node.display_once()
    except KeyboardInterrupt:
        bag_proc.terminate()
    finally:
        executor.shutdown()
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()
        bag_proc.wait()

    sys.exit(bag_proc.returncode)


if __name__ == "__main__":
    main()
