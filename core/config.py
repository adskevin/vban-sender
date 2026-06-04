import json
import os
import sys
from pathlib import Path
from typing import Any, TypedDict

DEFAULT_PORT = 6980
DEFAULT_STREAM_NAME = "Stream1"
DEFAULT_DESKTOP_STREAM = "Desktop"
DEFAULT_MIC_STREAM = "Mic"


class TrackConfig(TypedDict):
    enabled: bool
    device_name: str
    stream_name: str


class AppConfig(TypedDict):
    receiver_ip: str
    port: int
    desktop: TrackConfig
    mic: TrackConfig


def _config_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "vban-sender"
    return Path.home() / ".config" / "vban-sender"


def config_path() -> Path:
    return _config_dir() / "config.json"


def _default_track(
    enabled: bool = True,
    device_name: str = "",
    stream_name: str = "",
) -> TrackConfig:
    return {
        "enabled": enabled,
        "device_name": device_name,
        "stream_name": stream_name,
    }


def default_config() -> AppConfig:
    return {
        "receiver_ip": "",
        "port": DEFAULT_PORT,
        "desktop": _default_track(True, "", DEFAULT_DESKTOP_STREAM),
        "mic": _default_track(True, "", DEFAULT_MIC_STREAM),
    }


def _normalize_track(raw: Any, fallback: TrackConfig) -> TrackConfig:
    if not isinstance(raw, dict):
        return fallback
    return {
        "enabled": bool(raw.get("enabled", fallback["enabled"])),
        "device_name": str(raw.get("device_name", fallback["device_name"])),
        "stream_name": str(raw.get("stream_name", fallback["stream_name"])),
    }


def _migrate_legacy(data: dict[str, Any]) -> AppConfig:
    cfg = default_config()
    if data.get("receiver_ip"):
        cfg["receiver_ip"] = str(data["receiver_ip"])
    if data.get("port") is not None:
        cfg["port"] = int(data["port"])

    legacy_device = data.get("device_name", "")
    legacy_stream = data.get("stream_name", DEFAULT_STREAM_NAME)

    cfg["mic"]["device_name"] = str(legacy_device) if legacy_device else ""
    cfg["mic"]["stream_name"] = (
        str(legacy_stream) if legacy_stream else DEFAULT_MIC_STREAM
    )
    cfg["mic"]["enabled"] = True
    cfg["desktop"]["enabled"] = False
    return cfg


def load_config() -> AppConfig:
    path = config_path()
    if not path.is_file():
        return default_config()
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return default_config()
    except (OSError, json.JSONDecodeError):
        return default_config()

    if "desktop" in data or "mic" in data:
        base = default_config()
        if data.get("receiver_ip"):
            base["receiver_ip"] = str(data["receiver_ip"])
        if data.get("port") is not None:
            base["port"] = int(data["port"])
        base["desktop"] = _normalize_track(data.get("desktop"), base["desktop"])
        base["mic"] = _normalize_track(data.get("mic"), base["mic"])
        return base

    return _migrate_legacy(data)


def save_config(cfg: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
