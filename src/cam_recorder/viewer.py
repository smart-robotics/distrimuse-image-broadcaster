import argparse
import threading
import time
from datetime import datetime

import cv2
import numpy as np
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import CompressedImage

from cam_recorder.fps_counter import FpsCounter


class CameraViewerNode(Node):
    def __init__(self, topics, headless=False):
        super().__init__("camera_viewer")
        self._headless = headless
        self._start_time = time.monotonic()
        self._fps_counters: dict[str, FpsCounter] = {}
        self._latest_frames: dict[str, object] = {}

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        for topic in topics:
            self._fps_counters[topic] = FpsCounter()
            self.create_subscription(
                CompressedImage,
                topic,
                lambda msg, t=topic: self._image_callback(t, msg),
                sensor_qos,
            )
            self.get_logger().info(f"Subscribing to {topic}")

        self.create_timer(5.0, self._log_fps)

    def _image_callback(self, topic, msg):
        self._fps_counters[topic].tick()
        self._latest_frames[topic] = msg

    def display_once(self):
        if self._headless:
            time.sleep(0.03)
            return

        for topic, msg in list(self._latest_frames.items()):
            if msg is None:
                continue
            frame = cv2.imdecode(
                np.frombuffer(msg.data, dtype=np.uint8), cv2.IMREAD_COLOR
            )
            if frame is None:
                continue

            stamp = msg.header.stamp
            dt = datetime.fromtimestamp(stamp.sec + stamp.nanosec * 1e-9)
            timestamp_text = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            fps_text = f"{self._fps_counters[topic].fps():.1f} FPS"

            cv2.putText(
                frame,
                timestamp_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                timestamp_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                fps_text,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 0),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                fps_text,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

            parts = topic.strip("/").split("/")
            window_name = parts[1] if len(parts) > 1 else topic
            cv2.imshow(window_name, frame)

        cv2.waitKey(5)

    def _log_fps(self):
        parts = []
        for topic, counter in self._fps_counters.items():
            segments = topic.strip("/").split("/")
            name = segments[1] if len(segments) > 1 else topic
            parts.append(f"{name}: {counter.fps():.1f}")
        elapsed = int(time.monotonic() - self._start_time)
        h, m, s = elapsed // 3600, elapsed % 3600 // 60, elapsed % 60
        duration = f"\033[38;5;33m{h:02d}:{m:02d}:{s:02d}\033[0m"
        line = "FPS (recv) | " + " | ".join(parts) + " | " + duration
        print(f"\r{line:<90}", end="", flush=True)

    def shutdown(self):
        if not self._headless:
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="View camera image topics")
    parser.add_argument(
        "--topic",
        action="append",
        default=None,
        help="Topic to subscribe to (repeatable; defaults to all default cameras)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without display, only print received FPS",
    )

    args, ros_args = parser.parse_known_args()

    topics = args.topic
    if not topics:
        from cam_recorder.config import DEFAULT_CAMERAS, TOPIC_TEMPLATE

        topics = [TOPIC_TEMPLATE.format(name=cam["name"]) for cam in DEFAULT_CAMERAS]

    rclpy.init(args=ros_args)
    node = CameraViewerNode(topics, headless=args.headless)
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        while spin_thread.is_alive():
            node.display_once()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
