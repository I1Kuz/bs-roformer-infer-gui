import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import final

from app.core.bootstrap import EnvironmentBootstrap


@final
class SetupDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel) -> None:
        super().__init__(parent)
        self.withdraw()
        self.title("(BS-RoFormer-Infer) Studio - First Time Setup")

        width, height = 400, 200
        parent.update_idletasks()

        p_width = parent.winfo_width()
        p_height = parent.winfo_height()

        if p_width > 100 and p_height > 100:
            x = parent.winfo_x() + (p_width - width) // 2
            y = parent.winfo_y() + (p_height - height) // 2
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(width, height)
        self.resizable(False, False)
        self.transient(parent)
        _ = self.grab_set()

        try:
            import pywinstyles  # type: ignore[import-untyped]

            version = sys.getwindowsversion()
            if version.major == 10 and version.build >= 22000:
                _ = pywinstyles.change_header_color(self, "#1c1c1c")
            elif version.major == 10:
                _ = pywinstyles.apply_style(self, "dark")
                set_attr: Callable[..., object] = getattr(self, "wm_attributes")
                _ = set_attr("-alpha", 0.99)
                _ = set_attr("-alpha", 1.0)
        except Exception:
            pass

        _ = self.configure(bg="#1c1c1c")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.success: bool = False

        lbl = ttk.Label(
            self,
            text="Setting up PyTorch environment for the first time.\nThis will download ~2GB of data. Please wait...",
            justify="center",
        )
        lbl.pack(pady=20)

        self.progress_var: tk.DoubleVar = tk.DoubleVar()
        self.progress: ttk.Progressbar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=20, pady=10)

        self.status_var: tk.StringVar = tk.StringVar(value="Initializing...")
        self.status_lbl: ttk.Label = ttk.Label(self, textvariable=self.status_var, font=("-size", 9))
        self.status_lbl.pack(pady=5)

        self.bootstrap: EnvironmentBootstrap = EnvironmentBootstrap(self._on_progress, self._on_done)
        self.bootstrap.start_setup()

        self.deiconify()

    def _on_progress(self, percent: int, status: str) -> None:
        _ = self.after(0, self._update_ui_progress, percent, status)

    def _update_ui_progress(self, percent: int, status: str) -> None:
        self.progress_var.set(percent)
        self.status_var.set(status)

    def _on_done(self, success: bool, message: str) -> None:
        _ = self.after(0, self._update_ui_done, success, message)

    def _update_ui_done(self, success: bool, message: str) -> None:
        self.success = success
        if success:
            self.destroy()
        else:
            self.status_var.set(f"Error: {message}")
            btn = ttk.Button(self, text="Close", command=self.destroy)
            btn.pack(pady=5)

    def _on_close(self) -> None:
        pass
