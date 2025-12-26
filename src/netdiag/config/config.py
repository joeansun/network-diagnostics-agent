# config.py is used for loading configurations from config.toml

import subprocess
from dataclasses import dataclass
from loader import ensure_config_dir, ensure_config_file
from pathlib import Path
import tomllib
from loader import ensure_config_dir, ensure_config_file


# subprocess.run(
#     ["route", "-n", "get", "default"],
#     capture_output=True,
#     text=True,
#     check=False,
# )

@dataclass(frozen=True)
class Config:
    enabled : bool

@dataclass(frozen=True)
class PingConfig(Config):
    targets: list[str]
    count: int
    timeout_ms: int
    interval_s: int

@dataclass(frozen=True)
class AppConfig:
    ping: PingConfig
    # dns: DnsConfig


def parse_ping_config(raw: dict) -> PingConfig:
    try:
        enabled = raw["enabled"]
        targets = raw["targets"]
        count = raw["count"]
        timeout_ms = raw["timeout_ms"]
        interval_s = raw["interval_s"]    
    except KeyError as e:
        raise ValueError(f"Missing ping config key: {e}") from None
    
    if not isinstance(enabled, bool):
        raise ValueError("ping.enabled must be a boolean")
    
    if not isinstance(targets, list) or not all(isinstance(t, str) for t in targets):
        raise ValueError("ping.targets must be a list of strings")
    
    if not isinstance(count, int) or count <= 0:
        raise ValueError("ping.count must be a positive integer")

    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        raise ValueError("ping.timeout_ms must be a positive integer")

    if not isinstance(interval_s, int) or interval_s <= 0:
        raise ValueError("ping.interval_s must be a positive integer")

    return PingConfig(
        enabled=enabled,
        targets=targets,
        count=count,
        timeout_ms=timeout_ms,
        interval_s=interval_s,
    )
    
# Currently only load ping_config 
# TODO: modify the function to integrate for further config file uses
def load_config() -> AppConfig:
    config_file_path = ensure_config_file()
    with config_file_path.open("rb") as f:
        config_raw = tomllib.load(f)
    ping_config = parse_ping_config(config_raw)
    return AppConfig(
        ping=ping_config
    )