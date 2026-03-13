import threading
import time

import cv2

from cam_recorder.fps_counter import FpsCounter


class CameraCapture:
    def __init__(self, name: str, rtsp_url: str, fps: int = 15):
        self.name = name
        self.rtsp_url = rtsp_url
        self.fps = fps
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._fps_counter = FpsCounter()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def get_frame(self):
        with self._lock:
            return self._frame

    def _capture_loop(self):
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                print(f"[{self.name}] Failed to open {self.rtsp_url}, retrying in {backoff:.1f}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                continue

            print(f"[{self.name}] Connected to {self.rtsp_url}")
            backoff = 1.0

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    print(f"[{self.name}] Lost connection, reconnecting...")
                    break
                self._fps_counter.tick()
                with self._lock:
                    self._frame = frame

            cap.release()

    @property
    def capture_fps(self) -> float:
        return self._fps_counter.fps()
