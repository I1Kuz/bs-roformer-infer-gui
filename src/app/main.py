import contextlib
import os
import sys
from pathlib import Path

# Ensure src/ is in the PYTHONPATH so imports like `from app.core...` work
current_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(current_dir))

from app.core.logging import setup_logging
from app.core.paths import ensure_directories, get_models_dir
from app.gui.main_window import MainWindow


def _enable_dpi_awareness() -> None:
    """Enables Per-Monitor V2 DPI awareness on Windows to prevent UI blurriness."""
    if sys.platform != "win32":
        return
    import ctypes

    with contextlib.suppress(Exception):
        # PROCESS_PER_MONITOR_DPI_AWARE_V2 = 2 (Windows 10 1703+)
        _ = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    with contextlib.suppress(Exception):
        # Fallback for Windows 8.1 / older Windows 10
        _ = ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    with contextlib.suppress(Exception):
        # Fallback for older Windows
        _ = ctypes.windll.user32.SetProcessDPIAware()


def main() -> None:
    _enable_dpi_awareness()
    ensure_directories()
    # Force the library to use our appdata models directory
    os.environ["BS_ROFORMER_MODELS_PATH"] = str(get_models_dir())

    _ = setup_logging()

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
