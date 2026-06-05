from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from core.emitter import VBANEmitter

DeviceKind = Literal["input", "output"]


@dataclass
class TrackSettings:
    enabled: bool
    device_index: int
    device_kind: DeviceKind
    stream_name: str
    label: str
    track_id: str


class TransmissionSession:
    def __init__(
        self,
        receiver_ip: str,
        receiver_port: int,
        tracks: list[TrackSettings],
        on_error: Callable[[str, str], None] | None = None,
        on_level: Callable[[str, float], None] | None = None,
    ) -> None:
        self._receiver_ip = receiver_ip
        self._receiver_port = receiver_port
        self._tracks = tracks
        self._on_error = on_error
        self._on_level = on_level
        self._emitters: dict[str, VBANEmitter] = {}

    @property
    def is_running(self) -> bool:
        return bool(self._emitters)

    def start(self) -> None:
        if self._emitters:
            return
        for track in self._tracks:
            if not track.enabled:
                continue
            emitter = VBANEmitter(
                device_index=track.device_index,
                device_kind=track.device_kind,
                receiver_ip=self._receiver_ip,
                receiver_port=self._receiver_port,
                stream_name=track.stream_name,
                track_label=track.label,
                on_error=lambda msg, tid=track.track_id: self._handle_error(tid, msg),
                on_level=lambda level, tid=track.track_id: self._handle_level(
                    tid, level
                ),
            )
            emitter.start()
            self._emitters[track.track_id] = emitter

    def stop(self) -> None:
        for emitter in self._emitters.values():
            emitter.stop()
        self._emitters.clear()

    def _handle_error(self, track_id: str, message: str) -> None:
        if self._on_error:
            self._on_error(track_id, message)

    def _handle_level(self, track_id: str, level: float) -> None:
        if self._on_level:
            self._on_level(track_id, level)
