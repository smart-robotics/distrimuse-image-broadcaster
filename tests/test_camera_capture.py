from unittest.mock import patch, MagicMock

import cv2

from cam_recorder.camera_capture import CameraCapture


def test_get_frame_returns_none_before_capture():
    """Verify get_frame returns None when no frame has been captured yet."""
    capture = CameraCapture("test", "rtsp://invalid", fps=15)
    assert capture.get_frame() is None


def test_get_frame_returns_frame_after_setting():
    """Verify get_frame returns a frame after one is stored."""
    capture = CameraCapture("test", "rtsp://invalid", fps=15)
    fake_frame = MagicMock()
    capture._frame = fake_frame
    assert capture.get_frame() is fake_frame


@patch("cam_recorder.camera_capture.cv2.VideoCapture")
def test_graceful_handling_of_invalid_url(mock_video_capture):
    """Verify capture handles an invalid RTSP URL without crashing."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_video_capture.return_value = mock_cap

    capture = CameraCapture("test", "rtsp://invalid:554/stream", fps=15)
    capture.start()
    import time
    time.sleep(0.5)
    capture.stop()

    assert capture.get_frame() is None
    mock_video_capture.assert_called_with("rtsp://invalid:554/stream", cv2.CAP_FFMPEG)


def test_stop_without_start():
    """Verify stop can be called safely without start."""
    capture = CameraCapture("test", "rtsp://invalid", fps=15)
    capture.stop()
