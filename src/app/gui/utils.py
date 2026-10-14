"""GUI utility helpers shared across all windows and dialogs."""

import sys
import tkinter as tk
from collections.abc import Callable

from app.core.logging import get_logger
from app.gui.styles import COLOR_BG_DARK

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
            _ = pywinstyles.change_header_color(window, COLOR_BG_DARK)
        elif version.major == 10:
            _ = pywinstyles.apply_style(window, "dark")
            _ = window.wm_attributes("-alpha", 0.99)  # type: ignore[attr-defined]
            _ = window.wm_attributes("-alpha", 1.0)   # type: ignore[attr-defined]
    except Exception as e:
        logger.warning("Failed to apply dark titlebar: %s", e)


def enable_file_drop(widget: tk.Widget, on_drop: Callable[[list[str]], None]) -> None:
    """Enables native Windows Explorer drag-and-drop of files and folders onto the given widget."""
    if sys.platform != "win32":
        return

    try:
        import ctypes
        from ctypes import wintypes

        if not callable(on_drop):
            return

        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32

        widget.update_idletasks()
        hwnd: int = widget.winfo_id()

        _ = shell32.DragAcceptFiles(hwnd, True)

        gwl_wndproc: int = -4
        wm_dropfiles: int = 0x0233

        wndproc_proto = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        try:
            get_wndproc = user32.GetWindowLongPtrW
            set_wndproc = user32.SetWindowLongPtrW
        except AttributeError:
            get_wndproc = user32.GetWindowLongW
            set_wndproc = user32.SetWindowLongW

        get_wndproc.restype = ctypes.c_ssize_t
        get_wndproc.argtypes = [wintypes.HWND, ctypes.c_int]
        set_wndproc.restype = ctypes.c_ssize_t
        set_wndproc.argtypes = [wintypes.HWND, ctypes.c_int, wndproc_proto]

        user32.CallWindowProcW.restype = ctypes.c_ssize_t
        user32.CallWindowProcW.argtypes = [
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]

        shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
        shell32.DragAcceptFiles.restype = None

        shell32.DragFinish.argtypes = [wintypes.WPARAM]
        shell32.DragFinish.restype = None

        shell32.DragQueryFileW.argtypes = [wintypes.WPARAM, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        shell32.DragQueryFileW.restype = wintypes.UINT

        old_proc_addr: int = get_wndproc(hwnd, gwl_wndproc)
        if not old_proc_addr:
            return

        def drop_wndproc(
            h_wnd: int,
            msg: int,
            w_param: int,
            l_param: int,
        ) -> int:
            if msg == wm_dropfiles:
                h_drop = w_param
                count: int = shell32.DragQueryFileW(h_drop, 0xFFFFFFFF, None, 0)
                paths: list[str] = []
                buf = ctypes.create_unicode_buffer(1024)
                for i in range(count):
                    _ = shell32.DragQueryFileW(h_drop, i, buf, 1024)
                    paths.append(buf.value)
                _ = shell32.DragFinish(h_drop)
                if paths:
                    _ = widget.after(0, lambda: on_drop(paths))
                return 0
            return int(user32.CallWindowProcW(old_proc_addr, h_wnd, msg, w_param, l_param))

        new_proc = wndproc_proto(drop_wndproc)
        object.__setattr__(widget, "_drop_wndproc_ref", new_proc)
        _ = set_wndproc(hwnd, gwl_wndproc, new_proc)
    except Exception as e:
        logger.warning("Failed to enable drag and drop: %s", e)

