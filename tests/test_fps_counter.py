import time
from unittest.mock import patch

from cam_recorder.fps_counter import FpsCounter


def test_fps_returns_zero_with_no_ticks():
    """FPS is 0.0 when no frames have been recorded."""
    counter = FpsCounter()
    assert counter.fps() == 0.0


def test_fps_returns_zero_with_single_tick():
    """FPS is 0.0 with only one tick (need at least two for a span)."""
    counter = FpsCounter()
    counter.tick()
    assert counter.fps() == 0.0


def test_fps_computes_correct_rate():
    """FPS matches the expected rate for evenly spaced ticks."""
    counter = FpsCounter(window=5.0)
    mock_time = 100.0
    with patch("cam_recorder.fps_counter.time.monotonic") as mock_monotonic:
        for i in range(11):
            mock_monotonic.return_value = mock_time + i * 0.1
            counter.tick()
    assert abs(counter.fps() - 10.0) < 0.1


def test_fps_window_discards_old_timestamps():
    """Old timestamps outside the window are pruned on tick."""
    counter = FpsCounter(window=1.0)
    mock_time = 100.0
    with patch("cam_recorder.fps_counter.time.monotonic") as mock_monotonic:
        for i in range(5):
            mock_monotonic.return_value = mock_time + i * 0.1
            counter.tick()
        mock_monotonic.return_value = mock_time + 5.0
        counter.tick()
    assert len(counter._timestamps) == 1


def test_fps_with_custom_window():
    """Custom window size is respected for pruning."""
    counter = FpsCounter(window=0.5)
    mock_time = 100.0
    with patch("cam_recorder.fps_counter.time.monotonic") as mock_monotonic:
        for i in range(10):
            mock_monotonic.return_value = mock_time + i * 0.1
            counter.tick()
    assert len(counter._timestamps) == 5
