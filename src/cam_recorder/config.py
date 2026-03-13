from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"

if not _CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Config not found at {_CONFIG_PATH}. "
        f"Copy config/config.yaml.example to config/config.yaml and fill in your credentials."
    )

with open(_CONFIG_PATH) as f:
    _cfg = yaml.safe_load(f)

DEFAULT_CAMERAS = _cfg["cameras"]
DEFAULT_FPS = _cfg["fps"]
TOPIC_TEMPLATE = _cfg["topic_template"]
