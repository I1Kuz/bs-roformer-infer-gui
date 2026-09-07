import tkinter as tk
from tkinter import ttk
import webbrowser
import os
from app.core.paths import get_app_data_dir

class HelpDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("Help & Information")
        
        # Center the window on the parent
        width, height = 700, 650

        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.maxsize(width, height)
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
        
        # --- Content ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        lbl_title = ttk.Label(main_frame, text="(BS-RoFormer-Infer) Studio", font=("-size", 16, "-weight", "bold"))
        lbl_title.pack(anchor="w", pady=(0, 5))
        
        lbl_subtitle = ttk.Label(main_frame, text="An intuitive interface for audio separation using BS-RoFormer models.", foreground="gray")
        lbl_subtitle.pack(anchor="w", pady=(0, 20))
        
        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 20))
        
        btn_github = ttk.Button(btn_frame, text="View on GitHub", command=lambda: webbrowser.open("https://github.com/openmirlab/bs-roformer-infer"))
        btn_github.pack(side="left", padx=(0, 10))
        
        btn_open_prog_folder = ttk.Button(btn_frame, text="Open Program Folder", command=self._open_prog_folder)
        btn_open_prog_folder.pack(side="left")
        
        # Text documentation
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)
        
        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side="right", fill="y")
        
        self.text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scroll.set, bg="#2b2b2b", fg="white", borderwidth=0, padx=10, pady=10, font=("-size", 10))
        self.text_widget.pack(fill="both", expand=True)
        scroll.config(command=self.text_widget.yview)
        
        self._insert_help_text()
        self.text_widget.configure(state="disabled")
        
        close_btn = ttk.Button(main_frame, text="Close", command=self.destroy)
        close_btn.pack(pady=(15, 0), anchor="e")
        
        self.deiconify()

    def _open_prog_folder(self):
        folder = get_app_data_dir()
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    def _insert_help_text(self):
        help_content = """# How it Works
This program separates audio files (like extracting vocals and instruments) using state-of-the-art BS-RoFormer models. 
Your source code and program files are stored wherever you launched the app, but all downloaded models and the Python environment are safely stored in your user App Data folder.

# Interface Guide
- Input / Output Folders: Select where your audio files are located and where the separated stems should be saved.
- Create a subfolder per track: Keeps output organized if you process multiple tracks at once.
- Change Model: Browse and select different models from the registry.

# Advanced Settings
- Device: Which hardware to run on. 'auto' selects your GPU if available (CUDA). 'cpu' is extremely slow.
- VRAM Limit: If you have a small GPU and it crashes with Out of Memory errors, set a hard limit (e.g., 4) to force PyTorch to respect your memory boundary.
- Chunk Size: How much audio is processed at once. Larger chunks are faster but use more VRAM. The 'Auto' setting and the dropdown will automatically limit choices to what fits in your GPU memory.
- Export Format: Choose how to save your stems. FLAC and WAV provide lossless quality, while MP3 saves space.
- Overlap (Speed / Quality): Controls how many times the audio is re-processed to smooth out boundaries. Lower overlap (left) is much faster. Higher overlap (right) gives better quality but takes significantly longer.

# Queue
- Processing: You can stop a running track via its right-click context menu ("Cancel Transform").
- PENDING tracks can be removed or reordered via right-click.
- FINISHED tracks can have their output folder opened directly from the context menu ("Reveal Output").
"""
        self.text_widget.insert("1.0", help_content)
