import tkinter as tk
from tkinter import ttk
from app.core.bootstrap import EnvironmentBootstrap

class SetupDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw() # Prevent flash
        self.title("(BS-RoFormer-Infer) Studio - First Time Setup")
        
        # Center the window on the screen or parent
        width, height = 400, 200
        parent.update_idletasks()
        
        p_width = parent.winfo_width()
        p_height = parent.winfo_height()
        
        if p_width > 100 and p_height > 100:
            x = parent.winfo_x() + (p_width - width) // 2
            y = parent.winfo_y() + (p_height - height) // 2
        else:
            # Fallback to screen center if parent isn't fully drawn yet
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
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
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.success = False
        
        lbl = ttk.Label(self, text="Setting up PyTorch environment for the first time.\nThis will download ~2GB of data. Please wait...", justify="center")
        lbl.pack(pady=20)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=20, pady=10)
        
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_lbl = ttk.Label(self, textvariable=self.status_var, font=("-size", 9))
        self.status_lbl.pack(pady=5)
        
        self.bootstrap = EnvironmentBootstrap(self._on_progress, self._on_done)
        self.bootstrap.start_setup()
        
        self.deiconify()
        
    def _on_progress(self, percent: int, status: str):
        self.after(0, self._update_ui_progress, percent, status)
        
    def _update_ui_progress(self, percent: int, status: str):
        self.progress_var.set(percent)
        self.status_var.set(status)
        
    def _on_done(self, success: bool, message: str):
        self.after(0, self._update_ui_done, success, message)
        
    def _update_ui_done(self, success: bool, message: str):
        self.success = success
        if success:
            self.destroy()
        else:
            self.status_var.set(f"Error: {message}")
            btn = ttk.Button(self, text="Close", command=self.destroy)
            btn.pack(pady=5)
            
    def _on_close(self):
        pass # Disable closing manually while installing
