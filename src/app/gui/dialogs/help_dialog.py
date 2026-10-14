from __future__ import annotations

import re
import sys
import tkinter as tk
import webbrowser
from tkinter import ttk
from typing import Any, final

from app.core.i18n import get_translations
from app.core.paths import get_app_data_dir
from app.gui.styles import COLOR_BG_DARK, COLOR_BG_INPUT, COLOR_TEXT_LIGHT
from app.gui.utils import apply_dark_titlebar


@final
class HelpDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel) -> None:
        super().__init__(parent)
        self.withdraw()
        t = get_translations()
        self.title(t.help_dialog.title)

        parent.update_idletasks()
        pw = max(640, parent.winfo_width())
        ph = max(500, parent.winfo_height())
        width = min(780, max(560, int(pw * 0.85)))
        height = min(680, max(460, int(ph * 0.82)))
        x = max(0, parent.winfo_x() + (pw - width) // 2)
        y = max(0, parent.winfo_y() + (ph - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(540, width), min(420, height))
        self.transient(parent)
        _ = self.grab_set()

        apply_dark_titlebar(self)
        _ = self.configure(bg=COLOR_BG_DARK)

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
            text=t.help_dialog.subtitle,
            font=("TkDefaultFont", 9),
            foreground="gray",
        ).pack(anchor="w")

        btn_box = ttk.Frame(header_frame)
        btn_box.pack(side="right")

        ttk.Button(
            btn_box,
            text=t.queue.action_open_folder,
            style="Action.TButton",
            command=self._open_prog_folder,
        ).pack(side="left")

        # Bottom row with Close button (anchored to bottom)
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=(12, 0))

        ttk.Button(
            bottom_frame,
            text=t.help_dialog.btn_close,
            style="Action.TButton",
            command=self.destroy,
        ).pack(side="right")

        # Tabbed Notebook (takes remaining vertical space)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        self._add_tab(self.notebook, t.help_dialog.tab_quickstart, t.help_dialog.quickstart_content)
        self._add_tab(self.notebook, t.help_dialog.tab_settings, t.help_dialog.settings_content)
        self._add_tab(self.notebook, t.help_dialog.tab_models, t.help_dialog.models_content)
        self._add_tab(self.notebook, t.help_dialog.tab_about, t.help_dialog.about_content)

        self.deiconify()

    def _add_tab(self, notebook: ttk.Notebook, tab_title: str, content: str) -> None:
        tab_frame = ttk.Frame(notebook, padding=12)
        notebook.add(tab_frame, text=tab_title)

        text_widget = tk.Text(
            tab_frame,
            wrap="word",
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_LIGHT,
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

        # Highlight URLs and make them clickable
        _ = text_widget.tag_configure("hyperlink", foreground="#4cc2ff", underline=True)

        url_pattern = re.compile(r"https?://[^\s)]+")
        url_map: dict[str, str] = {}
        for idx, match in enumerate(url_pattern.finditer(content)):
            raw_url = match.group(0).rstrip(".,;")
            tag_name = f"link_{idx}"
            start_pos = f"1.0 + {match.start()} chars"
            end_pos = f"1.0 + {match.start() + len(raw_url)} chars"
            text_widget.tag_add(tag_name, start_pos, end_pos)
            text_widget.tag_add("hyperlink", start_pos, end_pos)
            url_map[tag_name] = raw_url

        if url_map:
            def _on_click(event: tk.Event[Any]) -> None:
                index = text_widget.index(f"@{event.x},{event.y}")
                for tag in text_widget.tag_names(index):
                    if tag in url_map:
                        _ = webbrowser.open(url_map[tag])
                        break

            def _on_motion(event: tk.Event[Any]) -> None:
                index = text_widget.index(f"@{event.x},{event.y}")
                has_link = any(tag in url_map for tag in text_widget.tag_names(index))
                _ = text_widget.configure(cursor="hand2" if has_link else "")

            _ = text_widget.bind("<Button-1>", _on_click)
            _ = text_widget.bind("<Motion>", _on_motion)

        _ = text_widget.configure(state="disabled")

    def _open_prog_folder(self) -> None:
        folder = get_app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            import os
            _ = os.startfile(folder)  # type: ignore[attr-defined]
