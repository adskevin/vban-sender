import queue
import socket
import threading
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import sounddevice as sd

from core.vban_packet import (
    VBAN_PROTOCOL_MAX_SIZE,
    VBANAudioHeader,
    VBANBitResolution,
    VBANCodec,
    VBANSampleRates,
)

SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLES_PER_FRAME = 128
DTYPE = "int16"
METER_INTERVAL_SEC = 1.0 / 30.0


class VBANEmitter:
    def __init__(
        self,
        device_index: int,
        receiver_ip: str,
        receiver_port: int,
        stream_name: str,
        track_label: str = "",
        on_error: Callable[[str], None] | None = None,
        on_level: Callable[[float], None] | None = None,
    ) -> None:
        self._device_index = device_index
        self._receiver_ip = receiver_ip
        self._receiver_port = receiver_port
        self._stream_name = stream_name[:16]
        self._track_label = track_label
        self._on_error = on_error
        self._on_level = on_level

        self._running = False
        self._thread: threading.Thread | None = None
        self._stream: sd.InputStream | None = None
        self._sock: socket.socket | None = None
        self._counter = 0
        self._lock = threading.Lock()
        self._error_queue: queue.Queue[str] = queue.Queue()
        self._last_meter_time = 0.0
        self._input_channels = CHANNELS

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._counter = 0

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False

        stream = self._stream
        if stream is not None:
            try:
                stream.abort()
            except Exception:
                try:
                    stream.stop()
                except Exception:
                    pass
            try:
                stream.close()
            except Exception:
                pass
            self._stream = None

        sock = self._sock
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
            self._sock = None

        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def _report_error(self, message: str) -> None:
        if self._on_error:
            prefix = f"{self._track_label}: " if self._track_label else ""
            self._on_error(f"{prefix}{message}")

    def _queue_error(self, message: str) -> None:
        try:
            self._error_queue.put_nowait(message)
        except queue.Full:
            pass
        with self._lock:
            self._running = False

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: Any,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            self._queue_error(str(status))
            return

        if not self._running or self._sock is None:
            return

        pcm = indata.tobytes()
        header = VBANAudioHeader(
            sample_rate=VBANSampleRates.RATE_48000,
            samples_per_frame=SAMPLES_PER_FRAME,
            channels=self._input_channels,
            format=VBANBitResolution.VBAN_BITFMT_16_INT,
            codec=VBANCodec.VBAN_CODEC_PCM,
            stream_name=self._stream_name,
            frame_counter=self._counter,
        )
        packet = (header.to_bytes() + pcm)[:VBAN_PROTOCOL_MAX_SIZE]
        try:
            self._sock.sendto(packet, (self._receiver_ip, self._receiver_port))
        except OSError as exc:
            self._queue_error(str(exc))
            return

        self._counter += 1

        if self._on_level is not None:
            now = time.monotonic()
            if now - self._last_meter_time >= METER_INTERVAL_SEC:
                self._last_meter_time = now
                rms = float(np.sqrt(np.mean(indata.astype(np.float64) ** 2)))
                level = min(1.0, rms / 32768.0)
                self._on_level(level)

    def _resolve_channels(self) -> int:
        try:
            dev = sd.query_devices(self._device_index)
            max_in = int(dev["max_input_channels"])
        except Exception:
            return CHANNELS
        if max_in < 1:
            raise ValueError("Dispositivo sem canais de entrada")
        return min(CHANNELS, max_in)

    def _run(self) -> None:
        try:
            self._input_channels = self._resolve_channels()
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._stream = sd.InputStream(
                device=self._device_index,
                channels=self._input_channels,
                samplerate=SAMPLE_RATE,
                dtype=DTYPE,
                blocksize=SAMPLES_PER_FRAME,
                callback=self._audio_callback,
            )
            self._stream.start()
            wait = threading.Event()
            while self._running:
                try:
                    err = self._error_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    self._report_error(err)
                    break
                wait.wait(0.05)
        except Exception as exc:
            self._report_error(str(exc))
        finally:
            with self._lock:
                self._running = False
            stream = self._stream
            if stream is not None:
                try:
                    stream.abort()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
                self._stream = None
            sock = self._sock
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass
                self._sock = None
