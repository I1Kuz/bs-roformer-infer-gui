import sys
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import final

from app.core.paths import get_app_data_dir
from app.gui.utils import apply_dark_titlebar


@final
class HelpDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel) -> None:
        super().__init__(parent)
        self.withdraw()
        self.title("Help & Information")

        width, height = 700, 650
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.maxsize(width, height)
        self.transient(parent)
        _ = self.grab_set()

        apply_dark_titlebar(self)
        _ = self.configure(bg="#1c1c1c")

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(
            main_frame, text="(BS-RoFormer-Infer) Studio", font=("-size", 16, "-weight", "bold")
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            main_frame,
            text="An intuitive interface for audio separation using BS-RoFormer models.",
            foreground="gray",
        ).pack(anchor="w", pady=(0, 20))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 20))

        ttk.Button(
            btn_frame,
            text="View on GitHub",
            command=lambda: webbrowser.open("https://github.com/openmirlab/bs-roformer-infer"),
        ).pack(side="left", padx=(0, 10))

        ttk.Button(btn_frame, text="Open Program Folder", command=self._open_prog_folder).pack(side="left")

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side="right", fill="y")

        self.text_widget: tk.Text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scroll.set,
            bg="#2b2b2b",
            fg="white",
            borderwidth=0,
            padx=10,
            pady=10,
            font=("-size", 10),
        )
        self.text_widget.pack(fill="both", expand=True)
        _ = scroll.config(command=self.text_widget.yview)  # type: ignore[arg-type]

        self._insert_help_text()
        _ = self.text_widget.configure(state="disabled")

        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=(15, 0), anchor="e")

        self.deiconify()

    def _open_prog_folder(self) -> None:
        folder = get_app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            import os
            _ = os.startfile(folder)

    def _insert_help_text(self) -> None:
        help_content = """\
This program separates audio files (like extracting vocals and instruments) using state-of-the-art BS-RoFormer models.
All downloaded models and runtime files are stored in your local application data directory.

# Interface Guide
- Input / Output Folders: Select where your audio files are located and where the separated stems should be saved.
- Create a subfolder per track: Keeps output organized when batch processing multiple tracks.
- Change Model: Browse and select different models from the registry.

# Advanced Settings
- Device: Which hardware to run on. 'auto' selects your GPU if available (CUDA). 'cpu' runs on CPU.
- VRAM Limit: Set a memory fraction limit to prevent GPU out-of-memory errors on limited hardware.
- Chunk Size: How much audio is processed at once. Larger chunks are faster but use more VRAM. 'Auto' defaults to the native model size (588800) and scales down for smaller GPUs.
- Export Format: Choose how to save your stems (FLAC, WAV 16/24/32-bit float, or MP3).
- Overlap (Speed / Quality): Controls how many times the audio is re-processed to smooth boundaries. Lower overlap is faster; higher overlap improves quality.

# Queue
- Right-click jobs in the queue to cancel, remove, prioritize, or open the resulting files.
"""
        self.text_widget.insert("1.0", help_content)
