"""Montagem de pacotes VBAN audio (compatível com pyVBAN, sem importar o pacote)."""

import enum
import struct
from dataclasses import dataclass

VBAN_PROTOCOL_MAX_SIZE = 1464

VBAN_PROTOCOL_MASK = 0xE0


class VBANProtocols(enum.Enum):
    VBAN_PROTOCOL_AUDIO = 0x00


class VBANSampleRates(enum.Enum):
    RATE_48000 = 3


class VBANBitResolution(enum.Enum):
    VBAN_BITFMT_16_INT = 1


class VBANCodec(enum.Enum):
    VBAN_CODEC_PCM = 0x00


@dataclass
class VBANAudioHeader:
    sample_rate: VBANSampleRates
    samples_per_frame: int
    channels: int
    format: VBANBitResolution
    codec: VBANCodec
    stream_name: str
    frame_counter: int

    def to_bytes(self) -> bytes:
        header = b"VBAN"
        header += bytes(
            [self.sample_rate.value | VBANProtocols.VBAN_PROTOCOL_AUDIO.value]
        )
        header += bytes([self.samples_per_frame - 1])
        header += bytes([self.channels - 1])
        header += bytes([self.format.value | self.codec.value])
        header += bytes(
            self.stream_name + "\x00" * (16 - len(self.stream_name)), "utf-8"
        )
        header += struct.pack("<L", self.frame_counter)
        return header
