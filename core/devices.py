import re
import sys
from dataclasses import dataclass
from typing import Literal

import sounddevice as sd

DeviceKind = Literal["input", "output"]

_MONITOR_PATTERNS = re.compile(r"monitor|loopback", re.IGNORECASE)
_INPUT_PREFIX = "[Entrada] "
_OUTPUT_PREFIX = "[Saída] "
_SEPARATOR_INPUT = "── Entrada ──"
_SEPARATOR_OUTPUT = "── Saída ──"


@dataclass(frozen=True)
class DeviceOption:
    index: int
    name: str
    kind: DeviceKind
    display_name: str
    is_separator: bool = False


def _all_input_devices() -> list[tuple[int, str]]:
    devices: list[tuple[int, str]] = []
    try:
        for index, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append((index, dev["name"]))
    except Exception:
        pass
    return devices


def _all_output_devices() -> list[tuple[int, str]]:
    devices: list[tuple[int, str]] = []
    try:
        for index, dev in enumerate(sd.query_devices()):
            if dev["max_output_channels"] > 0:
                devices.append((index, dev["name"]))
    except Exception:
        pass
    return devices


def _make_separator(label: str) -> DeviceOption:
    return DeviceOption(
        index=-1,
        name="",
        kind="input",
        display_name=label,
        is_separator=True,
    )


def _make_option(index: int, name: str, kind: DeviceKind) -> DeviceOption:
    prefix = _INPUT_PREFIX if kind == "input" else _OUTPUT_PREFIX
    return DeviceOption(
        index=index,
        name=name,
        kind=kind,
        display_name=f"{prefix}{name}",
    )


def build_grouped_device_options() -> list[DeviceOption]:
    options: list[DeviceOption] = []

    inputs = _all_input_devices()
    if inputs:
        options.append(_make_separator(_SEPARATOR_INPUT))
        for index, name in inputs:
            options.append(_make_option(index, name, "input"))

    outputs = _all_output_devices()
    if outputs:
        options.append(_make_separator(_SEPARATOR_OUTPUT))
        for index, name in outputs:
            options.append(_make_option(index, name, "output"))

    return options


def combo_values(options: list[DeviceOption]) -> list[str]:
    return [opt.display_name for opt in options]


def selectable_options(options: list[DeviceOption]) -> list[DeviceOption]:
    return [opt for opt in options if not opt.is_separator]


def resolve_device_option(
    display_name: str, options: list[DeviceOption]
) -> DeviceOption | None:
    for opt in options:
        if opt.is_separator:
            continue
        if opt.display_name == display_name:
            return opt
    # Migração: config antigo sem prefixo
    for opt in options:
        if opt.is_separator:
            continue
        if opt.name == display_name:
            return opt
    return None


def _find_monitor_for_output(output_name: str) -> int | None:
    output_lower = output_name.lower()
    for index, name in _all_input_devices():
        if not _MONITOR_PATTERNS.search(name):
            continue
        monitor_lower = name.lower()
        if output_lower in monitor_lower:
            return index
        # "Monitor of Built-in Audio" vs "Built-in Audio Analog Stereo"
        output_stem = output_lower.replace(" analog stereo", "").strip()
        if output_stem and output_stem in monitor_lower:
            return index
    return None


def capture_index_for_option(option: DeviceOption) -> int:
    if option.kind == "input":
        return option.index

    if sys.platform == "win32":
        return option.index

    monitor_index = _find_monitor_for_output(option.name)
    if monitor_index is not None:
        return monitor_index

    raise ValueError(
        f"Não foi encontrado monitor para a saída \"{option.name}\". "
        "Escolha um dispositivo na seção Entrada (ex.: Monitor of …)."
    )


def default_desktop_option(options: list[DeviceOption]) -> DeviceOption | None:
    selectable = selectable_options(options)
    if not selectable:
        return None

    for opt in selectable:
        if opt.kind == "input" and _MONITOR_PATTERNS.search(opt.name):
            return opt

    try:
        _, default_out = sd.default.device
        for opt in selectable:
            if opt.kind == "output" and opt.index == default_out:
                return opt
    except Exception:
        pass

    for opt in selectable:
        if opt.kind == "output":
            return opt

    return selectable[0]


def default_mic_option(options: list[DeviceOption]) -> DeviceOption | None:
    selectable = selectable_options(options)
    if not selectable:
        return None

    try:
        default_in, _ = sd.default.device
        for opt in selectable:
            if opt.kind == "input" and opt.index == default_in:
                return opt
    except Exception:
        pass

    for opt in selectable:
        if opt.kind == "input" and not _MONITOR_PATTERNS.search(opt.name):
            return opt

    for opt in selectable:
        if opt.kind == "input":
            return opt

    return selectable[0]


def device_hint() -> str:
    if sys.platform == "win32":
        return (
            "Lista setorizada: Entrada (microfones, Stereo Mix) e Saída (alto-falantes). "
            "Na seção Saída, pode ser necessário habilitar Stereo Mix."
        )
    return (
        "Lista setorizada: Entrada (microfones, Monitor of …) e Saída (alto-falantes). "
        "Ao escolher Saída, o app usa o monitor correspondente automaticamente."
    )


# Alias para compatibilidade com imports antigos
desktop_device_hint = device_hint
