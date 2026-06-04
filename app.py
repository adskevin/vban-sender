import os
import sys
from pathlib import Path

def _stubs_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "_stubs"
    return Path(__file__).resolve().parent / "_stubs"


_stubs = _stubs_dir()
if _stubs.is_dir():
    sys.path.insert(0, str(_stubs))

if getattr(sys, "frozen", False) and sys.platform == "win32":
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        path = os.environ.get("PATH", "")
        parts = path.split(os.pathsep) if path else []
        if meipass not in parts:
            parts.append(meipass)
            os.environ["PATH"] = os.pathsep.join(parts)

from ui.main_window import MainWindow

if __name__ == "__main__":
    MainWindow().mainloop()
