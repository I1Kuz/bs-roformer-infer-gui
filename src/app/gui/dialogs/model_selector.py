import tkinter as tk
from tkinter import ttk
from typing import List
from app.models.manager import ModelManager, ModelMetadata

class ModelSelectorDialog(tk.Toplevel):
    def __init__(self, parent, model_manager: ModelManager, current_model_id: str):
        super().__init__(parent)
        self.withdraw() # Hide immediately to prevent flash
        self.title("Select Model")
        
        # Center the window on the parent
        width, height = 800, 400
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        self.model_manager = model_manager
        self.selected_model_id = current_model_id
        
        try:
            import pywinstyles, sys
            import sv_ttk
            version = sys.getwindowsversion()
            if version.major == 10 and version.build >= 22000:
                pywinstyles.change_header_color(self, "#1c1c1c")
            elif version.major == 10:
                pywinstyles.apply_style(self, "dark")
                self.wm_attributes("-alpha", 0.99)
                self.wm_attributes("-alpha", 1)
        except Exception:
            pass
        
        self.configure(bg="#1c1c1c")
        
        # UI Setup
        lbl = ttk.Label(self, text="Available Models", font=("-size", 12, "-weight", "bold"))
        lbl.pack(pady=10)
        
        self.tree = ttk.Treeview(self, columns=("Name", "Category", "Stems", "Installed"), show="headings")
        self.tree.heading("Name", text="Model Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Stems", text="Stems")
        self.tree.heading("Installed", text="Installed")
        
        self.tree.column("Name", width=260)
        self.tree.column("Category", width=100)
        self.tree.column("Stems", width=20)
        self.tree.column("Installed", width=60)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        btn_select = ttk.Button(btn_frame, text="Select", command=self._on_select)
        btn_select.pack(side="right", padx=5)
        
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side="right")
        
        self._populate()
        
    def _populate(self):
        models = self.model_manager.get_all_models()
        for m in models:
            stems_str = str(len(m.stems)) if m.stems else "?"
            installed_str = "Yes" if m.installed else "No"
            iid = self.tree.insert("", "end", iid=m.id, values=(m.name, m.category, stems_str, installed_str))
            if m.id == self.selected_model_id:
                self.tree.selection_set(iid)
                self.tree.see(iid)
        
        # Finally, show the window after everything is styled and positioned
        self.deiconify()
                
    def _on_select(self):
        selected = self.tree.selection()
        if selected:
            self.selected_model_id = selected[0]
            self.destroy()
