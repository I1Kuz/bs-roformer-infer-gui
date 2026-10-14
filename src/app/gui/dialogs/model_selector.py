import tkinter as tk
from tkinter import ttk
from typing import final

from app.core.i18n import get_translations
from app.gui.styles import COLOR_BG_DARK
from app.gui.utils import apply_dark_titlebar
from app.models.manager import ModelManager


@final
class ModelSelectorDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, model_manager: ModelManager, current_model_id: str) -> None:
        super().__init__(parent)
        self.withdraw()
        t = get_translations()
        self.title(t.model_dialog.title)

        parent.update_idletasks()
        pw = max(600, parent.winfo_width())
        ph = max(450, parent.winfo_height())
        width = min(820, max(580, int(pw * 0.85)))
        height = min(520, max(360, int(ph * 0.65)))
        x = max(0, parent.winfo_x() + (pw - width) // 2)
        y = max(0, parent.winfo_y() + (ph - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(560, width), min(340, height))

        self.transient(parent)
        _ = self.grab_set()

        apply_dark_titlebar(self)
        _ = self.configure(bg=COLOR_BG_DARK)

        self.model_manager: ModelManager = model_manager
        self.selected_model_id: str = current_model_id

        lbl = ttk.Label(self, text=t.model_dialog.title, font=("-size", 12, "-weight", "bold"))
        lbl.pack(pady=10)

        self.tree: ttk.Treeview = ttk.Treeview(
            self, columns=("Name", "Category", "Installed"), show="headings"
        )
        self.tree.heading("Name", text=t.model_dialog.col_name)
        self.tree.heading("Category", text=t.model_dialog.col_category)
        self.tree.heading("Installed", text=t.model_dialog.col_installed)

        _ = self.tree.column("Name", stretch=True)
        _ = self.tree.column("Category", stretch=False, width=140)
        _ = self.tree.column("Installed", stretch=False, width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text=t.model_dialog.btn_select,
            command=self._on_select,
            style="Action.TButton",
        ).pack(side="right", padx=(5, 0))
        ttk.Button(
            btn_frame,
            text=t.model_dialog.btn_cancel,
            command=self.destroy,
            style="Action.TButton",
        ).pack(side="right")

        self._populate()

    def _populate(self) -> None:
        t = get_translations()
        for m in self.model_manager.get_all_models():
            installed_str = t.model_dialog.installed_yes if m.installed else t.model_dialog.installed_no
            iid = self.tree.insert("", "end", iid=m.id, values=(m.name, m.category, installed_str))
            if m.id == self.selected_model_id:
                _ = self.tree.selection_set(iid)
                _ = self.tree.see(iid)

        self.deiconify()

    def _on_select(self) -> None:
        selected = self.tree.selection()
        if selected:
            self.selected_model_id = selected[0]
            self.destroy()
