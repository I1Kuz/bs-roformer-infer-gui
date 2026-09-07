import os
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import final

from app.audio.scanner import scan_audio_files
from app.core.bootstrap import EnvironmentBootstrap
from app.core.hardware import HardwareDetector
from app.core.logging import get_logger
from app.core.paths import get_resources_dir
from app.gui.dialogs.help_dialog import HelpDialog
from app.gui.dialogs.model_selector import ModelSelectorDialog
from app.gui.styles import apply_theme
from app.gui.widgets.queue_panel import QueuePanel
from app.inference.job import Job
from app.inference.queue_manager import QueueManager
from app.models.manager import ModelManager
from app.storage.settings import SettingsManager

logger = get_logger(__name__)


@final
class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("(BS-RoFormer-Infer) Studio")
        self.geometry("900x800")
        self.minsize(950, 850)

        # Set application icon
        icon_path = get_resources_dir() / "icons" / "app.ico"
        if icon_path.exists():
            set_icon: Callable[..., object] = getattr(self, "iconbitmap")
            _ = set_icon(default=str(icon_path))

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
        except Exception as e:
            logger.warning("Failed to apply titlebar theme: %s", e)

        apply_theme()
        _ = self.configure(bg="#1c1c1c")

        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings

        self.model_manager = ModelManager()
        self.hardware = HardwareDetector()
        self.queue_manager = QueueManager(self._on_job_updated)

        # Loading screen
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.pack(fill="both", expand=True)

        self.center_frame = ttk.Frame(self.loading_frame)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.loading_pb = ttk.Progressbar(self.center_frame, mode="indeterminate", length=300)
        self.loading_pb.pack(fill="x", pady=(0, 5))
        self.loading_pb.start(10)

        self.loading_lbl_var = tk.StringVar(value="Initializing...")
        self.loading_lbl = ttk.Label(
            self.center_frame,
            textvariable=self.loading_lbl_var,
            wraplength=400,
            justify="center",
        )
        self.loading_lbl.pack()

        self.setup_frame: ttk.Frame | None = None
        self.install_progress_frame: ttk.Frame | None = None
        self.bootstrap: EnvironmentBootstrap | None = None

        _ = self.after(100, self._startup_check)

    def _poll_queue(self) -> None:
        self.queue_manager.process_ui_events()
        _ = self.after(100, self._poll_queue)

    def _startup_check(self) -> None:
        def check_env_bg() -> None:
            _ = self.after(0, lambda: self.loading_lbl_var.set("Checking environment and dependencies..."))
            bs = EnvironmentBootstrap(lambda p, s: None, lambda s, m: None)
            exists = bs.check_environment_exists()
            _ = self.after(0, lambda: self._on_env_checked(exists))

        threading.Thread(target=check_env_bg, daemon=True).start()

    def _on_env_checked(self, exists: bool) -> None:
        if not exists:
            self.loading_pb.stop()
            self.loading_pb.pack_forget()
            self.loading_lbl.pack_forget()

            self.setup_frame = ttk.Frame(self.center_frame)
            self.setup_frame.pack(fill="both", expand=True)

            title_lbl = ttk.Label(
                self.setup_frame,
                text="First-Time Environment Setup",
                font=("TkDefaultFont", 13, "bold"),
                justify="center",
            )
            title_lbl.pack(pady=(0, 8))

            desc_lbl = ttk.Label(
                self.setup_frame,
                text="BS-RoFormer requires PyTorch runtime and inference dependencies to be installed.",
                justify="center",
                wraplength=420,
            )
            desc_lbl.pack(pady=(0, 16))

            self.btn_install = ttk.Button(
                self.setup_frame,
                text="Install",
                style="Accent.TButton",
                command=self._start_first_time_install,
                width=16,
            )
            self.btn_install.pack(pady=(0, 8))

            self.lbl_note = ttk.Label(
                self.setup_frame,
                text="Installation will take approximately 5 GB of disk space.",
                font=("TkDefaultFont", 9),
                foreground="gray",
                justify="center",
            )
            self.lbl_note.pack(pady=(0, 5))
        else:
            self._start_background_init()

    def _start_first_time_install(self) -> None:
        if self.setup_frame and self.setup_frame.winfo_exists():
            self.setup_frame.destroy()

        self.install_progress_frame = ttk.Frame(self.center_frame)
        self.install_progress_frame.pack(fill="both", expand=True)

        self.install_title_lbl = ttk.Label(
            self.install_progress_frame,
            text="Installing PyTorch Environment...",
            font=("TkDefaultFont", 12, "bold"),
            justify="center",
        )
        self.install_title_lbl.pack(pady=(0, 12))

        self.setup_pb_var = tk.DoubleVar(value=0)
        self.setup_pb = ttk.Progressbar(
            self.install_progress_frame,
            variable=self.setup_pb_var,
            maximum=100,
            length=360,
        )
        self.setup_pb.pack(fill="x", pady=(0, 10))

        self.setup_status_var = tk.StringVar(value="Starting installation...")
        self.setup_status_lbl = ttk.Label(
            self.install_progress_frame,
            textvariable=self.setup_status_var,
            font=("TkDefaultFont", 9),
            foreground="gray",
            justify="center",
        )
        self.setup_status_lbl.pack(pady=5)

        self.bootstrap = EnvironmentBootstrap(self._on_setup_progress, self._on_setup_done)
        self.bootstrap.start_setup()

    def _on_setup_progress(self, percent: int, status: str) -> None:
        _ = self.after(0, self._update_setup_progress, percent, status)

    def _update_setup_progress(self, percent: int, status: str) -> None:
        if hasattr(self, "setup_pb_var"):
            self.setup_pb_var.set(percent)
        if hasattr(self, "setup_status_var"):
            self.setup_status_var.set(status)

    def _on_setup_done(self, success: bool, message: str) -> None:
        _ = self.after(0, self._update_setup_done, success, message)

    def _update_setup_done(self, success: bool, message: str) -> None:
        if success:
            if self.install_progress_frame and self.install_progress_frame.winfo_exists():
                self.install_progress_frame.destroy()
            self.loading_pb.pack(fill="x", pady=(0, 5))
            self.loading_pb.start(10)
            self.loading_lbl.pack()
            self._start_background_init()
        else:
            if hasattr(self, "install_title_lbl"):
                _ = self.install_title_lbl.config(text="Installation Failed")
            if hasattr(self, "setup_status_var"):
                self.setup_status_var.set(f"Error: {message}")
            if self.install_progress_frame:
                btn_retry = ttk.Button(
                    self.install_progress_frame,
                    text="Retry",
                    style="Accent.TButton",
                    command=self._start_first_time_install,
                    width=12,
                )
                btn_retry.pack(pady=10)

    def _start_background_init(self) -> None:
        def background_init() -> None:
            _ = self.after(0, lambda: self.loading_lbl_var.set("Starting inference worker process..."))
            success = self.queue_manager.start()
            if success:
                _ = self.after(0, lambda: self.loading_lbl_var.set("Detecting hardware capabilities..."))
                _ = self.hardware.detect()
                _ = self.after(0, lambda: self.loading_lbl_var.set("Fetching model registry..."))
                _ = self.model_manager.fetch_registry()
            _ = self.after(0, lambda: self._on_startup_complete(success))

        threading.Thread(target=background_init, daemon=True).start()

    def _on_startup_complete(self, success: bool) -> None:
        if not success:
            _ = messagebox.showerror("Error", "Failed to start background worker process.")
            self.destroy()
            return

        self.loading_pb.stop()
        self.loading_frame.destroy()

        self._build_ui()
        _ = self.hw_label.config(text=self.hardware.get_display_string())
        self._update_chunk_size_options()
        self._update_model_label()

        self.status_var.set("Ready")
        _ = self.after(100, self._poll_queue)

    def _update_chunk_size_options(self) -> None:
        vram = self.hardware.vram_gb
        limit = getattr(self.settings, "vram_limit", 0)
        if 0 < limit < vram:
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

        self.chunk_combo["values"] = options
        if self.settings.chunk_size_preset not in options:
            self.settings.chunk_size_preset = "Auto"
            self.chunk_var.set("Auto")

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Folders section
        io_frame = ttk.LabelFrame(main_frame, text="Folders", padding=10)
        io_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(io_frame, text="Input Folder:").grid(row=0, column=0, sticky="w", pady=5)
        self.in_var = tk.StringVar(value=self.settings.input_folder)
        ttk.Entry(io_frame, textvariable=self.in_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )
        ttk.Button(io_frame, text="Browse...", width=15, command=self._browse_in).grid(row=0, column=2, pady=5)

        ttk.Label(io_frame, text="Output Folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.out_var = tk.StringVar(value=self.settings.output_folder)
        ttk.Entry(io_frame, textvariable=self.out_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(io_frame, text="Browse...", width=15, command=self._browse_out).grid(row=1, column=2, pady=5)

        _ = io_frame.columnconfigure(1, weight=1)

        self.subfolder_var = tk.BooleanVar(value=self.settings.create_subfolder_per_track)
        ttk.Checkbutton(
            io_frame,
            text="Create a subfolder per track",
            variable=self.subfolder_var,
            command=self._save_settings,
        ).grid(row=2, column=1, sticky="w", pady=5)

        # Model section
        model_frame = ttk.LabelFrame(main_frame, text="Model", padding=10)
        model_frame.pack(fill="x", pady=(0, 15))

        self.model_lbl_var = tk.StringVar(value="")
        ttk.Label(model_frame, textvariable=self.model_lbl_var, font=("TkDefaultFont", 10, "bold")).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(model_frame, text="Change Model...", width=15, command=self._change_model).pack(side="right")

        # Advanced settings section
        adv_frame = ttk.LabelFrame(main_frame, text="Advanced Settings", padding=10)
        adv_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(adv_frame, text="Device:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.device_var = tk.StringVar(value=self.settings.device)
        device_combo = ttk.Combobox(
            adv_frame,
            textvariable=self.device_var,
            state="readonly",
            values=["auto", "cpu", "cuda", "mps"],
            width=10,
        )
        device_combo.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        _ = device_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        ttk.Label(adv_frame, text="VRAM Limit (GB, 0=auto):").grid(row=0, column=2, sticky="w", pady=2, padx=5)
        self.vram_var = tk.StringVar(value=str(self.settings.vram_limit))
        vram_entry = ttk.Entry(adv_frame, textvariable=self.vram_var, width=8)
        vram_entry.grid(row=0, column=3, sticky="w", pady=2, padx=5)
        _ = vram_entry.bind("<FocusOut>", lambda e: self._save_settings())

        ttk.Label(adv_frame, text="Chunk Size:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.chunk_var = tk.StringVar(value=getattr(self.settings, "chunk_size_preset", "Auto"))
        self.chunk_combo = ttk.Combobox(adv_frame, textvariable=self.chunk_var, state="readonly", width=22)
        self.chunk_combo.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        _ = self.chunk_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        ttk.Label(adv_frame, text="Export Format:").grid(row=1, column=2, sticky="w", pady=2, padx=5)
        self.format_var = tk.StringVar(value=getattr(self.settings, "export_format", "WAV 32-bit (Float)"))
        format_combo = ttk.Combobox(
            adv_frame,
            textvariable=self.format_var,
            state="readonly",
            values=["MP3 320kbps", "WAV 16-bit", "WAV 24-bit", "WAV 32-bit (Float)", "FLAC"],
            width=18,
        )
        format_combo.grid(row=1, column=3, sticky="w", pady=2, padx=5)
        _ = format_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        ttk.Label(adv_frame, text="Overlap:").grid(row=2, column=0, sticky="w", pady=(10, 2), padx=5)
        overlap_frame = ttk.Frame(adv_frame)
        overlap_frame.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(10, 2), padx=5)

        ttk.Label(overlap_frame, text="Speed", font=("TkDefaultFont", 8)).pack(side="left")
        self.overlap_var = tk.IntVar(value=getattr(self.settings, "overlap", 4))
        self.overlap_scale = ttk.Scale(
            overlap_frame,
            from_=2,
            to=8,
            variable=self.overlap_var,
            command=self._on_overlap_change,
        )
        self.overlap_scale.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(overlap_frame, text="Quality", font=("TkDefaultFont", 8)).pack(side="right")

        self.overlap_val_lbl = ttk.Label(adv_frame, text=f"{self.overlap_var.get()}")
        self.overlap_val_lbl.grid(row=2, column=4, sticky="w", pady=(10, 2))

        _ = adv_frame.columnconfigure(4, weight=1)
        ttk.Button(adv_frame, text="Help", width=15, command=self._show_help).grid(
            row=0, column=5, rowspan=3, sticky="e", padx=(10, 0)
        )

        # Queue section
        self.queue_panel = QueuePanel(main_frame)
        self.queue_panel.queue_manager = self.queue_manager
        self.queue_panel.pack(fill="both", expand=True, pady=(0, 15))

        self.btn_start = ttk.Button(
            main_frame,
            text="Start Transform",
            command=self._start_stop_toggle,
            style="Accent.TButton",
        )
        self.btn_start.pack(side="right")

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        self.hw_label = ttk.Label(status_frame, text="GPU: Detecting...")
        self.hw_label.pack(side="left", padx=10)

        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _on_overlap_change(self, val: str) -> None:
        v = int(float(val))
        self.overlap_var.set(v)
        _ = self.overlap_val_lbl.config(text=f"{v}")
        self._save_settings()

    def _browse_in(self) -> None:
        d = filedialog.askdirectory(initialdir=self.settings.input_folder)
        if d:
            self.in_var.set(d)
            self.settings.input_folder = d
            self._save_settings()

    def _browse_out(self) -> None:
        d = filedialog.askdirectory(initialdir=self.settings.output_folder)
        if d:
            self.out_var.set(d)
            self.settings.output_folder = d
            self._save_settings()

    def _save_settings(self) -> None:
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

    def _change_model(self) -> None:
        dlg = ModelSelectorDialog(self, self.model_manager, self.settings.selected_model)
        self.wait_window(dlg)
        if dlg.selected_model_id != self.settings.selected_model:
            self.settings.selected_model = dlg.selected_model_id
            self._save_settings()
            self._update_model_label()

    def _update_model_label(self) -> None:
        model = self.model_manager.get_model(self.settings.selected_model)
        if model:
            stems_count = len(model.stems) if model.stems else "?"
            self.model_lbl_var.set(f"{model.name} ({stems_count} stems)")
        else:
            self.model_lbl_var.set(self.settings.selected_model)

    def _show_help(self) -> None:
        dlg = HelpDialog(self)
        self.wait_window(dlg)

    def _start_stop_toggle(self) -> None:
        if self.queue_manager.is_running:
            self.queue_manager.cancel_all()
            self._update_start_button()
        else:
            if not self.settings.input_folder or not self.settings.output_folder:
                _ = messagebox.showwarning("Warning", "Please select input and output folders.")
                return

            files = scan_audio_files(self.settings.input_folder)
            if not files:
                _ = messagebox.showinfo("Info", "No supported audio files found in the input folder.")
                return

            self.queue_manager.clear_jobs()
            self.queue_panel.clear_all()

            for f in files:
                out_d = self.settings.output_folder
                if self.settings.create_subfolder_per_track:
                    basename = Path(f).stem
                    out_d = str(Path(out_d) / basename)
                    os.makedirs(out_d, exist_ok=True)

                self.queue_manager.add_job(f, out_d, self.settings.selected_model)

            self._update_start_button()

    def _update_start_button(self) -> None:
        if self.queue_manager.is_running:
            _ = self.btn_start.config(text="Cancel Transform")
            try:
                style = ttk.Style()
                if not style.lookup("Red.TButton", "background"):
                    _ = style.configure("Red.TButton", foreground="red")
                _ = self.btn_start.config(style="Red.TButton")
            except Exception:
                pass
        else:
            _ = self.btn_start.config(text="Start Transform", style="Accent.TButton")

    def _on_job_updated(self, job: Job) -> None:
        self.queue_panel.update_job(job)
        self._update_start_button()

    def destroy(self) -> None:
        self.queue_manager.stop()
        super().destroy()
