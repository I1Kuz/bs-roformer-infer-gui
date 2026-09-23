import tkinter as tk
from tkinter import ttk
from typing import final

from app.gui.utils import apply_dark_titlebar
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

        apply_dark_titlebar(self)
        _ = self.configure(bg="#1c1c1c")

        self.model_manager: ModelManager = model_manager
        self.selected_model_id: str = current_model_id

        lbl = ttk.Label(self, text="Available Models", font=("-size", 12, "-weight", "bold"))
        lbl.pack(pady=10)

        self.tree: ttk.Treeview = ttk.Treeview(
            self, columns=("Name", "Category", "Installed"), show="headings"
        )
        self.tree.heading("Name", text="Model Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Installed", text="Installed")

        _ = self.tree.column("Name", width=300)
        _ = self.tree.column("Category", width=120)
        _ = self.tree.column("Installed", width=60)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Select", command=self._on_select).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right")

        self._populate()

    def _populate(self) -> None:
        for m in self.model_manager.get_all_models():
            installed_str = "Yes" if m.installed else "No"
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
