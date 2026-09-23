import sys
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import final

from app.core.i18n import get_translations
from app.core.paths import get_app_data_dir
from app.gui.utils import apply_dark_titlebar


@final
class HelpDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel) -> None:
        super().__init__(parent)
        self.withdraw()
        t = get_translations()
        self.title(t.help_dialog.title)

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
            main_frame, text=t.app_title, font=("-size", 16, "-weight", "bold")
        ).pack(anchor="w", pady=(0, 5))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 20))

        ttk.Button(
            btn_frame,
            text="GitHub",
            command=lambda: webbrowser.open("https://github.com/openmirlab/bs-roformer-infer"),
        ).pack(side="left", padx=(0, 10))

        ttk.Button(btn_frame, text=t.queue.action_open_folder, command=self._open_prog_folder).pack(side="left")

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

        ttk.Button(main_frame, text=t.help_dialog.btn_close, command=self.destroy).pack(pady=(15, 0), anchor="e")

        self.deiconify()

    def _open_prog_folder(self) -> None:
        folder = get_app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            import os
            _ = os.startfile(folder)

    def _insert_help_text(self) -> None:
        t = get_translations()
        self.text_widget.insert("1.0", t.help_dialog.content)
