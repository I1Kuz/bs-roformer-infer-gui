import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from app.core.bootstrap import EnvironmentBootstrap
from app.core.hardware import HardwareDetector
from app.storage.settings import SettingsManager
from app.models.manager import ModelManager
from app.inference.queue_manager import QueueManager
from app.audio.scanner import scan_audio_files
from app.gui.styles import apply_theme
from app.gui.dialogs.setup_dialog import SetupDialog
from app.gui.dialogs.model_selector import ModelSelectorDialog
from app.gui.widgets.queue_panel import QueuePanel

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("(BS-RoFormer-Infer) Studio")
        self.geometry("900x800")
        self.minsize(900, 800)
        
        # Set app icon
        from app.core.paths import get_resources_dir
        icon_path = get_resources_dir() / "icons" / "app.ico"
        if icon_path.exists():
            self.iconbitmap(default=str(icon_path))
        
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
        except Exception as e:
            print("Failed to apply titlebar theme:", e)
            
        apply_theme()
        
        # Force background color to sv_ttk dark background to fix Windows 10 style resetting it
        self.configure(bg="#1c1c1c")
        
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings
        
        self.model_manager = ModelManager()
        self.hardware = HardwareDetector()
        self.queue_manager = QueueManager(self._on_job_updated)
        
        # Loading Screen
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.pack(fill="both", expand=True)
        
        center_frame = ttk.Frame(self.loading_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.loading_pb = ttk.Progressbar(center_frame, mode="indeterminate", length=300)
        self.loading_pb.pack(fill="x", pady=(0, 5))
        self.loading_pb.start(10)
        
        self.loading_lbl_var = tk.StringVar(value="Initializing...")
        lbl = ttk.Label(center_frame, textvariable=self.loading_lbl_var, wraplength=300, justify="center")
        lbl.pack()
        
        self.after(100, self._startup_check)
        
    def _poll_queue(self):
        self.queue_manager.process_ui_events()
        self.after(100, self._poll_queue)
        
    def _startup_check(self):
        # Check if python env exists in background to prevent UI freeze
        def check_env_bg():
            self.after(0, lambda: self.loading_lbl_var.set("Checking environment and dependencies..."))
            bs = EnvironmentBootstrap(lambda p, s: None, lambda s, m: None)
            exists = bs.check_environment_exists()
            self.after(0, lambda: self._on_env_checked(exists))
            
        import threading
        threading.Thread(target=check_env_bg, daemon=True).start()
        
    def _on_env_checked(self, exists):
        if not exists:
            self.loading_lbl_var.set("Running first-time setup...")
            dlg = SetupDialog(self)
            self.wait_window(dlg)
            if not dlg.success:
                from tkinter import messagebox
                messagebox.showerror("Setup Failed", "Environment setup failed. Cannot continue.")
                self.destroy()
                return
                
        # Run heavy init in background thread to prevent GUI freeze
        def background_init():
            self.after(0, lambda: self.loading_lbl_var.set("Starting inference worker process..."))
            success = self.queue_manager.start()
            if success:
                self.after(0, lambda: self.loading_lbl_var.set("Detecting hardware capabilities..."))
                self.hardware.detect()
                self.after(0, lambda: self.loading_lbl_var.set("Fetching model registry..."))
                self.model_manager.fetch_registry()
            self.after(0, lambda: self._on_startup_complete(success))
            
        import threading
        threading.Thread(target=background_init, daemon=True).start()
        
    def _on_startup_complete(self, success):
        if not success:
            from tkinter import messagebox
            messagebox.showerror("Error", "Failed to start background worker.")
            self.destroy()
            return
            
        # Transition to main UI
        self.loading_pb.stop()
        self.loading_frame.destroy()
        
        self._build_ui()
        
        self.hw_label.config(text=self.hardware.get_display_string())
        self._update_chunk_size_options()
        self._update_model_label()
        
        self.status_var.set("Ready")
        self.after(100, self._poll_queue)
        
    def _update_chunk_size_options(self):
        vram = self.hardware.vram_gb
        limit = getattr(self.settings, 'vram_limit', 0)
        if limit > 0 and limit < vram:
            vram = float(limit)
            
        options = ["Auto"]
        if vram > 0:
            options.append("Small (~3GB VRAM)")
            if vram >= 4.0:
                options.append("Medium (~4GB VRAM)")
            if vram >= 5.5:
                options.append("Big (~6GB VRAM)")
            if vram >= 7.5:
                options.append("Huge (~8+ GB VRAM)")
        else:
            options.extend(["Small (~3GB VRAM)", "Medium (~4GB VRAM)", "Big (~6GB VRAM)", "Huge (~8+ GB VRAM)"])
            
        self.chunk_combo['values'] = options
        if self.settings.chunk_size_preset not in options:
            self.settings.chunk_size_preset = "Auto"
            self.chunk_var.set("Auto")
        
    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # --- IO Section ---
        io_frame = ttk.LabelFrame(main_frame, text="Folders", padding=10)
        io_frame.pack(fill="x", pady=(0, 15))
        
        # Input
        ttk.Label(io_frame, text="Input Folder:").grid(row=0, column=0, sticky="w", pady=5)
        self.in_var = tk.StringVar(value=self.settings.input_folder)
        ttk.Entry(io_frame, textvariable=self.in_var, state="readonly").grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(io_frame, text="Browse...", width=15, command=self._browse_in).grid(row=0, column=2, pady=5)
        
        # Output
        ttk.Label(io_frame, text="Output Folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.out_var = tk.StringVar(value=self.settings.output_folder)
        ttk.Entry(io_frame, textvariable=self.out_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(io_frame, text="Browse...", width=15, command=self._browse_out).grid(row=1, column=2, pady=5)
        
        io_frame.columnconfigure(1, weight=1)
        
        # Settings Checkbox
        self.subfolder_var = tk.BooleanVar(value=self.settings.create_subfolder_per_track)
        ttk.Checkbutton(io_frame, text="Create a subfolder per track", variable=self.subfolder_var, command=self._save_settings).grid(row=2, column=1, sticky="w", pady=5)
        
        # --- Model Section ---
        model_frame = ttk.LabelFrame(main_frame, text="Model", padding=10)
        model_frame.pack(fill="x", pady=(0, 15))
        
        self.model_lbl_var = tk.StringVar(value="")
        ttk.Label(model_frame, textvariable=self.model_lbl_var, font=("-weight", "bold")).pack(side="left", padx=(0, 10))
        ttk.Button(model_frame, text="Change Model...", width=15, command=self._change_model).pack(side="right")
        
        # --- Advanced Settings Section ---
        adv_frame = ttk.LabelFrame(main_frame, text="Advanced Settings", padding=10)
        adv_frame.pack(fill="x", pady=(0, 15))
        
        # Row 0: Device & VRAM
        ttk.Label(adv_frame, text="Device:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.device_var = tk.StringVar(value=self.settings.device)
        device_combo = ttk.Combobox(adv_frame, textvariable=self.device_var, state="readonly", values=["auto", "cpu", "cuda", "mps"], width=10)
        device_combo.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        device_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())
        
        ttk.Label(adv_frame, text="VRAM Limit (GB, 0=auto):").grid(row=0, column=2, sticky="w", pady=2, padx=5)
        self.vram_var = tk.StringVar(value=str(self.settings.vram_limit))
        vram_entry = ttk.Entry(adv_frame, textvariable=self.vram_var, width=8)
        vram_entry.grid(row=0, column=3, sticky="w", pady=2, padx=5)
        vram_entry.bind("<FocusOut>", lambda e: self._save_settings())

        # Row 1: Chunk Size & Format
        ttk.Label(adv_frame, text="Chunk Size:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.chunk_var = tk.StringVar(value=getattr(self.settings, 'chunk_size_preset', 'Auto'))
        self.chunk_combo = ttk.Combobox(adv_frame, textvariable=self.chunk_var, state="readonly", width=22)
        self.chunk_combo.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        self.chunk_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        ttk.Label(adv_frame, text="Export Format:").grid(row=1, column=2, sticky="w", pady=2, padx=5)
        self.format_var = tk.StringVar(value=getattr(self.settings, 'export_format', 'WAV 32-bit (Float)'))
        format_combo = ttk.Combobox(adv_frame, textvariable=self.format_var, state="readonly", 
            values=["MP3 320kbps", "WAV 16-bit", "WAV 24-bit", "WAV 32-bit (Float)", "FLAC"], width=18)
        format_combo.grid(row=1, column=3, sticky="w", pady=2, padx=5)
        format_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        # Row 2: Overlap Slider
        ttk.Label(adv_frame, text="Overlap:").grid(row=2, column=0, sticky="w", pady=(10, 2), padx=5)
        overlap_frame = ttk.Frame(adv_frame)
        overlap_frame.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(10, 2), padx=5)
        
        ttk.Label(overlap_frame, text="Speed", font=("", 8)).pack(side="left")
        self.overlap_var = tk.IntVar(value=getattr(self.settings, 'overlap', 4))
        self.overlap_scale = ttk.Scale(overlap_frame, from_=2, to=8, variable=self.overlap_var, command=self._on_overlap_change)
        self.overlap_scale.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(overlap_frame, text="Quality", font=("", 8)).pack(side="right")
        
        self.overlap_val_lbl = ttk.Label(adv_frame, text=f"{self.overlap_var.get()}")
        self.overlap_val_lbl.grid(row=2, column=4, sticky="w", pady=(10, 2))
        
        # Help Button inside Advanced Settings
        adv_frame.columnconfigure(4, weight=1)
        ttk.Button(adv_frame, text="Help", width=15, command=self._show_help).grid(row=0, column=5, rowspan=3, sticky="e", padx=(10, 0))
        
        # --- Queue Section ---
        self.queue_panel = QueuePanel(main_frame)
        self.queue_panel.queue_manager = self.queue_manager
        self.queue_panel.pack(fill="both", expand=True, pady=(0, 15))
        
        # Start button inside QueuePanel's btn_frame
        self.btn_start = ttk.Button(main_frame, text="Start Transform", command=self._start_stop_toggle, style="Accent.TButton")
        self.btn_start.pack(side="right")
        
        # --- Status Bar ---
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        self.hw_label = ttk.Label(status_frame, text="GPU: Detecting...")
        self.hw_label.pack(side="left", padx=10)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _on_overlap_change(self, val):
        v = int(float(val))
        self.overlap_var.set(v)
        self.overlap_val_lbl.config(text=f"{v}")
        self._save_settings()

    def _browse_in(self):
        d = filedialog.askdirectory(initialdir=self.settings.input_folder)
        if d:
            self.in_var.set(d)
            self.settings.input_folder = d
            self._save_settings()
            
    def _browse_out(self):
        d = filedialog.askdirectory(initialdir=self.settings.output_folder)
        if d:
            self.out_var.set(d)
            self.settings.output_folder = d
            self._save_settings()
            
    def _save_settings(self):
        self.settings.create_subfolder_per_track = self.subfolder_var.get()
        self.settings.device = self.device_var.get()
        self.settings.chunk_size_preset = self.chunk_var.get()
        self.settings.overlap = self.overlap_var.get()
        self.settings.export_format = self.format_var.get()
        try:
            old_limit = self.settings.vram_limit
            new_limit = int(self.vram_var.get())
            self.settings.vram_limit = new_limit
            if old_limit != new_limit:
                self._update_chunk_size_options()
        except ValueError:
            self.settings.vram_limit = 0
            self.vram_var.set("0")
        self.settings_manager.save()
        self.queue_manager.device = self.settings.device
        
    def _change_model(self):
        dlg = ModelSelectorDialog(self, self.model_manager, self.settings.selected_model)
        self.wait_window(dlg)
        if dlg.selected_model_id != self.settings.selected_model:
            self.settings.selected_model = dlg.selected_model_id
            self._save_settings()
            self._update_model_label()
            
    def _update_model_label(self):
        model = self.model_manager.get_model(self.settings.selected_model)
        if model:
            stems_count = len(model.stems) if model.stems else "?"
            self.model_lbl_var.set(f"{model.name} ({stems_count} stems)")
        else:
            self.model_lbl_var.set(self.settings.selected_model)
            
    def _show_help(self):
        from app.gui.dialogs.help_dialog import HelpDialog
        dlg = HelpDialog(self)
        self.wait_window(dlg)

    def _start_stop_toggle(self):
        if self.queue_manager.is_running:
            self.queue_manager.cancel_all()
            self._update_start_button()
        else:
            if not self.settings.input_folder or not self.settings.output_folder:
                messagebox.showwarning("Warning", "Please select input and output folders.")
                return
                
            files = scan_audio_files(self.settings.input_folder)
            if not files:
                messagebox.showinfo("Info", "No supported audio files found in the input folder.")
                return
                
            self.queue_manager.clear_jobs()
            self.queue_panel.clear_all()
                
            for f in files:
                out_d = self.settings.output_folder
                if self.settings.create_subfolder_per_track:
                    basename = os.path.splitext(os.path.basename(f))[0]
                    out_d = os.path.join(out_d, basename)
                    os.makedirs(out_d, exist_ok=True)
                    
                self.queue_manager.add_job(f, out_d, self.settings.selected_model)
                
            self._update_start_button()

    def _update_start_button(self):
        if self.queue_manager.is_running:
            self.btn_start.config(text="Cancel Transform")
            try:
                style = ttk.Style()
                if not style.lookup("Red.TButton", "background"):
                    style.configure("Red.TButton", foreground="red")
                self.btn_start.config(style="Red.TButton")
            except:
                pass
        else:
            self.btn_start.config(text="Start Transform", style="Accent.TButton")

    def _on_job_updated(self, job):
        self.queue_panel.update_job(job)
        self._update_start_button()
        
    def destroy(self):
        self.queue_manager.stop()
        super().destroy()
