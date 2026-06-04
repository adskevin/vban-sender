# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None


def _sounddevice_datas():
    try:
        import sounddevice

        sd_dir = Path(sounddevice.__file__).resolve().parent
        data_dir = sd_dir / "_sounddevice_data"
        if data_dir.is_dir():
            return [(str(data_dir), "_sounddevice_data")]
    except ImportError:
        pass
    return []


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=_sounddevice_datas(),
    hiddenimports=[
        "customtkinter",
        "numpy",
        "sounddevice",
        "_sounddevice_data",
        "core.vban_packet",
        "core.devices",
        "core.session",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pyaudio", "pyvban"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VBANSender",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
