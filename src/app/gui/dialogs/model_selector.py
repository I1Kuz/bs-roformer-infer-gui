import sys
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import final

from app.models.manager import ModelManager


@final
class ModelSelectorDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, model_manager: ModelManager, current_model_id: str) -> None:
        super().__init__(parent)
        self.withdraw()
        self.title("Select Model")

        width, height = 800, 450
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(width, height)

        self.transient(parent)
        _ = self.grab_set()

        self.model_manager: ModelManager = model_manager
        self.selected_model_id: str = current_model_id

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

        lbl = ttk.Label(self, text="Available Models", font=("-size", 12, "-weight", "bold"))
        lbl.pack(pady=10)

        self.tree: ttk.Treeview = ttk.Treeview(self, columns=("Name", "Category", "Stems", "Installed"), show="headings")
        self.tree.heading("Name", text="Model Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Stems", text="Stems")
        self.tree.heading("Installed", text="Installed")

        _ = self.tree.column("Name", width=260)
        _ = self.tree.column("Category", width=100)
        _ = self.tree.column("Stems", width=20)
        _ = self.tree.column("Installed", width=60)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        btn_select = ttk.Button(btn_frame, text="Select", command=self._on_select)
        btn_select.pack(side="right", padx=5)

        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side="right")

        self._populate()

    def _populate(self) -> None:
        models = self.model_manager.get_all_models()
        for m in models:
            stems_str = str(len(m.stems)) if m.stems else "?"
            installed_str = "Yes" if m.installed else "No"
            iid = self.tree.insert("", "end", iid=m.id, values=(m.name, m.category, stems_str, installed_str))
            if m.id == self.selected_model_id:
                _ = self.tree.selection_set(iid)
                _ = self.tree.see(iid)

        self.deiconify()

    def _on_select(self) -> None:
        selected = self.tree.selection()
        if selected:
            self.selected_model_id = selected[0]
            self.destroy()
