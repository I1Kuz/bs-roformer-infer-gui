"""GUI utility helpers shared across all windows and dialogs."""

import sys
import tkinter as tk

from app.core.logging import get_logger

logger = get_logger(__name__)


def apply_dark_titlebar(window: tk.Tk | tk.Toplevel) -> None:
    """Applies a dark titlebar to a Windows 10/11 window via pywinstyles.

    Background: tkinter has no built-in way to theme the OS titlebar on
    Windows — it always renders white regardless of the app's colour scheme.
    pywinstyles patches this via the DwmSetWindowAttribute Win32 API call:
    - Windows 11 (build ≥ 22000): changes the caption colour directly.
    - Windows 10: applies the "dark" window style and briefly toggles alpha
      to force a repaint.

    Silently does nothing if pywinstyles is unavailable or the OS is not Windows.
    """
    if sys.platform != "win32":
        return
    try:
        import pywinstyles  # type: ignore[import-untyped]

        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:
            _ = pywinstyles.change_header_color(window, "#1c1c1c")
        elif version.major == 10:
            _ = pywinstyles.apply_style(window, "dark")
            _ = window.wm_attributes("-alpha", 0.99)  # type: ignore[attr-defined]
            _ = window.wm_attributes("-alpha", 1.0)   # type: ignore[attr-defined]
    except Exception as e:
        logger.warning("Failed to apply dark titlebar: %s", e)
