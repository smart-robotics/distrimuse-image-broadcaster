from pathlib import Path

import yaml

from cam_recorder.config import DEFAULT_CAMERAS, TOPIC_TEMPLATE


def test_config_yaml_exists_and_has_expected_keys():
    """Verify config.yaml exists at project root and contains required keys."""
    config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    assert config_path.exists(), f"config.yaml not found at {config_path}"
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    assert "cameras" in cfg
    assert "fps" in cfg
    assert "topic_template" in cfg


def test_default_cameras_count():
    """Verify there are exactly 3 default cameras."""
    assert len(DEFAULT_CAMERAS) == 3


def test_default_cameras_have_expected_ips():
    """Verify default cameras contain the correct IP addresses."""
    ips = [cam["rtsp_url"] for cam in DEFAULT_CAMERAS]
    assert any("10.82.6.67" in url for url in ips)
    assert any("10.82.6.65" in url for url in ips)
    assert any("10.82.6.66" in url for url in ips)


def test_default_cameras_have_names():
    """Verify each default camera has a name field."""
    for cam in DEFAULT_CAMERAS:
        assert "name" in cam
        assert "rtsp_url" in cam


def test_topic_template_produces_expected_names():
    """Verify the topic template formats correctly for each camera."""
    for cam in DEFAULT_CAMERAS:
        topic = TOPIC_TEMPLATE.format(name=cam["name"])
        assert topic.startswith("/camera/")
        assert topic.endswith("/image_raw")
        assert cam["name"] in topic
