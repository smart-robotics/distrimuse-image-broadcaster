import argparse
import sys
import time
from datetime import datetime

import cv2
import rclpy
import rclpy.serialization
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import CompressedImage
import rosbag2_py

from cam_recorder.camera_capture import CameraCapture
from cam_recorder.config import DEFAULT_CAMERAS, DEFAULT_FPS, TOPIC_TEMPLATE
from cam_recorder.fps_counter import FpsCounter


class CameraBroadcasterNode(Node):
    def __init__(self, cameras, fps, collect_bag, bag_path):
        super().__init__("camera_broadcaster")
        self._encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
        self._start_time = time.monotonic()
        self.captures = []
        self._pubs = {}
        self._publish_fps: dict[str, FpsCounter] = {}
        self.bag_writer = None
        self.topic_names = {}

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        for cam in cameras:
            name = cam["name"]
            topic = TOPIC_TEMPLATE.format(name=name)
            self.topic_names[name] = topic

            capture = CameraCapture(name, cam["rtsp_url"], fps)
            capture.start()
            self.captures.append(capture)

            pub = self.create_publisher(CompressedImage, topic, sensor_qos)
            self._pubs[name] = pub
            self._publish_fps[name] = FpsCounter()
            self.get_logger().info(f"Publishing {name} on {topic}")

        if collect_bag:
            self._init_bag_writer(bag_path)

        period = 1.0 / fps
        self.timer = self.create_timer(period, self._timer_callback)
        self.create_timer(5.0, self._log_fps)

    def _init_bag_writer(self, bag_path):
        self.bag_writer = rosbag2_py.SequentialWriter()
        storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id="mcap")
        converter_options = rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        )
        self.bag_writer.open(storage_options, converter_options)

        for name, topic in self.topic_names.items():
            topic_info = rosbag2_py.TopicMetadata(
                id=0,
                name=topic,
                type="sensor_msgs/msg/CompressedImage",
                serialization_format="cdr",
            )
            self.bag_writer.create_topic(topic_info)
            self.get_logger().info(f"Recording {topic} to bag")

    def _timer_callback(self):
        for capture in self.captures:
            frame = capture.get_frame()
            if frame is None:
                continue

            _, encoded = cv2.imencode(".jpg", frame, self._encode_params)
            msg = CompressedImage()
            # Note: this is the publish time, not the actual capture time. RTSP
            # streams (Dahua cameras) don't expose per-frame capture timestamps.
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = capture.name
            msg.format = "jpeg"
            msg.data = encoded.tobytes()

            self._pubs[capture.name].publish(msg)
            self._publish_fps[capture.name].tick()

            if self.bag_writer is not None:
                topic = self.topic_names[capture.name]
                timestamp = self.get_clock().now().nanoseconds
                serialized = rclpy.serialization.serialize_message(msg)
                self.bag_writer.write(topic, serialized, timestamp)

    def _log_fps(self):
        parts = []
        for capture in self.captures:
            name = capture.name
            in_fps = capture.capture_fps
            out_fps = self._publish_fps[name].fps()
            parts.append(f"{name}: {in_fps:.1f}/{out_fps:.1f}")
        elapsed = int(time.monotonic() - self._start_time)
        h, m, s = elapsed // 3600, elapsed % 3600 // 60, elapsed % 60
        duration = f"\033[38;5;33m{h:02d}:{m:02d}:{s:02d}\033[0m"
        line = "FPS (in/out) | " + " | ".join(parts) + " | " + duration
        print(f"\r{line:<90}", end="", flush=True)

    def shutdown(self):
        self.get_logger().info("Shutting down...")
        for capture in self.captures:
            capture.stop()
        if self.bag_writer is not None:
            del self.bag_writer
            self.bag_writer = None


def parse_camera_arg(value):
    parts = value.split("=", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Expected name=rtsp://..., got: {value}")
    return {"name": parts[0], "rtsp_url": parts[1]}


def main():
    parser = argparse.ArgumentParser(description="ROS2 Camera Broadcaster")
    parser.add_argument(
        "--camera",
        type=parse_camera_arg,
        action="append",
        default=None,
        help="Camera in format name=rtsp://... (repeatable)",
    )
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument("--collect-bag", action="store_true", help="Record to rosbag")
    parser.add_argument(
        "--bag-path",
        default=None,
        help="Bag output path (default: ./bags/recording_<timestamp>)",
    )

    args, ros_args = parser.parse_known_args()

    cameras = args.camera if args.camera else DEFAULT_CAMERAS
    bag_path = args.bag_path
    if bag_path is None:
        bag_path = f"./bags/recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    rclpy.init(args=ros_args)
    node = CameraBroadcasterNode(cameras, args.fps, args.collect_bag, bag_path)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
