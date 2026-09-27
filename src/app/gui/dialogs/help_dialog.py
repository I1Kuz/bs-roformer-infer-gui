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

        width, height = 720, 620
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(640, 500)
        self.transient(parent)
        _ = self.grab_set()

        apply_dark_titlebar(self)
        _ = self.configure(bg="#1c1c1c")

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Header with branding and quick links
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        title_box = ttk.Frame(header_frame)
        title_box.pack(side="left")

        ttk.Label(
            title_box,
            text=t.app_title,
            font=("TkDefaultFont", 15, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            title_box,
            text="Band-Split RoFormer Audio Source Separation Studio",
            font=("TkDefaultFont", 9),
            foreground="gray",
        ).pack(anchor="w")

        btn_box = ttk.Frame(header_frame)
        btn_box.pack(side="right")

        ttk.Button(
            btn_box,
            text="GitHub",
            command=lambda: webbrowser.open("https://github.com/I1Kuz/bs-roformer-infer-gui"),
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_box,
            text=t.queue.action_open_folder,
            command=self._open_prog_folder,
        ).pack(side="left")

        # Tabbed Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self._add_tab(self.notebook, t.help_dialog.tab_quickstart, t.help_dialog.quickstart_content)
        self._add_tab(self.notebook, t.help_dialog.tab_settings, t.help_dialog.settings_content)
        self._add_tab(self.notebook, t.help_dialog.tab_models, t.help_dialog.models_content)

        # Bottom row with Close button
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(bottom_frame, text=t.help_dialog.btn_close, command=self.destroy).pack(side="right")

        self.deiconify()

    def _add_tab(self, notebook: ttk.Notebook, tab_title: str, content: str) -> None:
        tab_frame = ttk.Frame(notebook, padding=12)
        notebook.add(tab_frame, text=tab_title)

        text_widget = tk.Text(
            tab_frame,
            wrap="word",
            bg="#222222",
            fg="#eaeaea",
            insertbackground="white",
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=14,
            font=("Segoe UI", 10),
        )
        scroll = ttk.Scrollbar(
            tab_frame,
            orient="vertical",
            command=lambda *args: getattr(text_widget, "yview")(*args),
        )
        _ = text_widget.configure(yscrollcommand=scroll.set)  # type: ignore[arg-type]

        text_widget.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        text_widget.insert("1.0", content)
        _ = text_widget.configure(state="disabled")

    def _open_prog_folder(self) -> None:
        folder = get_app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            import os
            _ = os.startfile(folder)  # type: ignore[attr-defined]
