import re
import sys

import sounddevice as sd

_DESKTOP_PATTERNS = re.compile(
    r"monitor|loopback|stereo\s*mix|what\s*u\s*hear|wave\s*out|mixagem",
    re.IGNORECASE,
)


def _all_input_devices() -> list[tuple[int, str]]:
    devices: list[tuple[int, str]] = []
    try:
        for index, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append((index, dev["name"]))
    except Exception:
        pass
    return devices


def _matches_desktop(name: str) -> bool:
    return _DESKTOP_PATTERNS.search(name) is not None


def list_desktop_devices() -> list[tuple[int, str]]:
    all_inputs = _all_input_devices()
    filtered = [(i, n) for i, n in all_inputs if _matches_desktop(n)]
    if filtered:
        return filtered
    return all_inputs


def list_mic_devices() -> list[tuple[int, str]]:
    return [(i, n) for i, n in _all_input_devices() if not _matches_desktop(n)]


def default_mic_device() -> tuple[int, str] | None:
    mic_list = list_mic_devices()
    if not mic_list:
        return None
    try:
        default_in, _ = sd.default.device
        for index, name in mic_list:
            if index == default_in:
                return index, name
    except Exception:
        pass
    return mic_list[0]


def default_desktop_device() -> tuple[int, str] | None:
    desktop_list = list_desktop_devices()
    return desktop_list[0] if desktop_list else None


def resolve_device_index(
    device_name: str, candidates: list[tuple[int, str]]
) -> int | None:
    for index, name in candidates:
        if name == device_name:
            return index
    return None


def desktop_device_hint() -> str:
    if sys.platform == "win32":
        return "No Windows: habilite Stereo Mix ou escolha um dispositivo (loopback)."
    return "No Linux: escolha um dispositivo Monitor of …"
