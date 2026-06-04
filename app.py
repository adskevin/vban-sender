import os
import sys

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
