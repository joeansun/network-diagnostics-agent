from pathlib import Path

from default import DEFAULT_CONFIG
from platformdirs import user_config_dir


def ensure_config_dir() -> Path:
    config_dir = Path(user_config_dir("netdiag"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir 

def ensure_config_file() -> Path:
    config_dir = ensure_config_dir()
    config_file = config_dir / "config.toml"

    if not config_file.exists():
        config_file.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return config_file