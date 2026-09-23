import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import final

from app.audio.scanner import scan_audio_files
from app.core.bootstrap import EnvironmentBootstrap
from app.core.hardware import HardwareDetector
from app.core.i18n import (
    LANGUAGE_DISPLAY_NAMES,
    AppLanguage,
    get_translations,
    set_current_language,
)
from app.core.logging import get_logger
from app.core.paths import get_resources_dir
from app.gui.dialogs.help_dialog import HelpDialog
from app.gui.dialogs.model_selector import ModelSelectorDialog
from app.gui.styles import apply_theme
from app.gui.utils import apply_dark_titlebar
from app.gui.widgets.queue_panel import QueuePanel
from app.inference.job import CHUNK_PRESETS, Job
from app.inference.protocol import AudioExportFormat, InferenceDevice
from app.inference.queue_manager import QueueManager
from app.models.manager import ModelManager
from app.storage.settings import SettingsManager

logger = get_logger(__name__)


@final
class MainWindow(tk.Tk):
    def __init__(self) -> None:
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings
        set_current_language(self.settings.language)
        t = get_translations()

        super().__init__()
        self.title(t.app_title)
        self.geometry("900x800")
        self.minsize(950, 850)

        # Set application icon
        icon_path = get_resources_dir() / "icons" / "app.ico"
        if icon_path.exists():
            self.iconbitmap(default=str(icon_path))  # type: ignore[attr-defined]

        apply_dark_titlebar(self)
        apply_theme()
        _ = self.configure(bg="#1c1c1c")

        self.model_manager = ModelManager()
        self.hardware = HardwareDetector()
        self.queue_manager = QueueManager(self.settings, self._on_job_updated)

        # Loading screen
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.pack(fill="both", expand=True)

        self.center_frame = ttk.Frame(self.loading_frame)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.loading_pb = ttk.Progressbar(self.center_frame, mode="indeterminate", length=300)
        self.loading_pb.pack(fill="x", pady=(0, 5))
        self.loading_pb.start(10)

        self.loading_lbl_var = tk.StringVar(value=t.loading.initializing)
        self.loading_lbl = ttk.Label(
            self.center_frame,
            textvariable=self.loading_lbl_var,
            wraplength=400,
            justify="center",
        )
        self.loading_lbl.pack()

        # Optional widgets created during first-time install flow
        self.setup_frame: ttk.Frame | None = None
        self.install_progress_frame: ttk.Frame | None = None
        self.setup_pb_var: tk.DoubleVar | None = None
        self.setup_pb: ttk.Progressbar | None = None
        self.setup_status_var: tk.StringVar | None = None
        self.install_title_lbl: ttk.Label | None = None
        self.bootstrap: EnvironmentBootstrap | None = None

        _ = self.after(100, self._startup_check)

    # ------------------------------------------------------------------
    # Queue polling
    # ------------------------------------------------------------------

    def _poll_queue(self) -> None:
        self.queue_manager.process_ui_events()
        _ = self.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # Startup sequence
    # ------------------------------------------------------------------

    def _startup_check(self) -> None:
        def check_env_bg() -> None:
            t = get_translations()
            _ = self.after(0, lambda: self.loading_lbl_var.set(t.loading.checking_env))
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

            ttk.Label(
                self.setup_frame,
                text="First-Time Environment Setup",
                font=("TkDefaultFont", 13, "bold"),
                justify="center",
            ).pack(pady=(0, 8))

            ttk.Label(
                self.setup_frame,
                text="BS-RoFormer requires PyTorch runtime and inference dependencies to be installed.",
                justify="center",
                wraplength=420,
            ).pack(pady=(0, 16))

            ttk.Button(
                self.setup_frame,
                text="Install",
                style="Accent.TButton",
                command=self._start_first_time_install,
                width=16,
            ).pack(pady=(0, 8))

            ttk.Label(
                self.setup_frame,
                text="Installation will take approximately 5 GB of disk space.",
                font=("TkDefaultFont", 9),
                foreground="gray",
                justify="center",
            ).pack(pady=(0, 5))
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
        ttk.Label(
            self.install_progress_frame,
            textvariable=self.setup_status_var,
            font=("TkDefaultFont", 9),
            foreground="gray",
            justify="center",
        ).pack(pady=5)

        self.bootstrap = EnvironmentBootstrap(self._on_setup_progress, self._on_setup_done)
        self.bootstrap.start_setup()

    def _on_setup_progress(self, percent: int, status: str) -> None:
        _ = self.after(0, self._update_setup_progress, percent, status)

    def _update_setup_progress(self, percent: int, status: str) -> None:
        if self.setup_pb_var is not None:
            self.setup_pb_var.set(percent)
        if self.setup_status_var is not None:
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
            t = get_translations()
            if self.install_title_lbl is not None:
                _ = self.install_title_lbl.config(text=t.setup.install_failed)
            if self.setup_status_var is not None:
                self.setup_status_var.set(f"{t.setup.error_prefix}{message}")
            if self.install_progress_frame:
                ttk.Button(
                    self.install_progress_frame,
                    text=t.setup.retry,
                    style="Accent.TButton",
                    command=self._start_first_time_install,
                    width=12,
                ).pack(pady=10)

    def _start_background_init(self) -> None:
        def background_init() -> None:
            t = get_translations()
            _ = self.after(0, lambda: self.loading_lbl_var.set(t.loading.starting_worker))
            success = self.queue_manager.start()
            if success:
                _ = self.after(0, lambda: self.loading_lbl_var.set(t.loading.detecting_hw))
                _ = self.hardware.detect()
                _ = self.after(0, lambda: self.loading_lbl_var.set(t.loading.fetching_registry))
                _ = self.model_manager.fetch_registry()
            _ = self.after(0, lambda: self._on_startup_complete(success))

        threading.Thread(target=background_init, daemon=True).start()

    def _on_startup_complete(self, success: bool) -> None:
        t = get_translations()
        if not success:
            _ = messagebox.showerror(t.setup.install_failed, t.loading.worker_start_failed)
            self.destroy()
            return

        self.loading_pb.stop()
        self.loading_frame.destroy()

        self._build_ui()
        _ = self.hw_label.config(text=self.hardware.get_display_string())
        self._update_chunk_size_options()
        self._update_model_label()

        self.status_var.set(t.queue.ready)
        _ = self.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        t = get_translations()
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Folders section
        self.io_frame = ttk.LabelFrame(main_frame, text=t.folders.frame_title, padding=10)
        self.io_frame.pack(fill="x", pady=(0, 15))

        self.lbl_in_folder = ttk.Label(self.io_frame, text=t.folders.input_folder)
        self.lbl_in_folder.grid(row=0, column=0, sticky="w", pady=5)
        self.in_var = tk.StringVar(value=self.settings.input_folder)
        ttk.Entry(self.io_frame, textvariable=self.in_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=5, pady=5
        )
        self.btn_browse_in = ttk.Button(self.io_frame, text=t.folders.browse, width=15, command=self._browse_in)
        self.btn_browse_in.grid(row=0, column=2, pady=5)

        self.lbl_out_folder = ttk.Label(self.io_frame, text=t.folders.output_folder)
        self.lbl_out_folder.grid(row=1, column=0, sticky="w", pady=5)
        self.out_var = tk.StringVar(value=self.settings.output_folder)
        ttk.Entry(self.io_frame, textvariable=self.out_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.btn_browse_out = ttk.Button(self.io_frame, text=t.folders.browse, width=15, command=self._browse_out)
        self.btn_browse_out.grid(row=1, column=2, pady=5)

        _ = self.io_frame.columnconfigure(1, weight=1)

        self.subfolder_var = tk.BooleanVar(value=self.settings.create_subfolder_per_track)
        self.chk_subfolder = ttk.Checkbutton(
            self.io_frame,
            text=t.folders.subfolder_per_track,
            variable=self.subfolder_var,
            command=self._save_settings,
        )
        self.chk_subfolder.grid(row=2, column=1, sticky="w", pady=5)

        # Model section
        self.model_frame = ttk.LabelFrame(main_frame, text=t.model.frame_title, padding=10)
        self.model_frame.pack(fill="x", pady=(0, 15))

        self.model_lbl_var = tk.StringVar(value="")
        ttk.Label(self.model_frame, textvariable=self.model_lbl_var, font=("TkDefaultFont", 10, "bold")).pack(
            side="left", padx=(0, 10)
        )
        self.btn_change_model = ttk.Button(
            self.model_frame, text=t.model.change_model, width=18, command=self._change_model
        )
        self.btn_change_model.pack(side="right")

        # Advanced settings section
        self.adv_frame = ttk.LabelFrame(main_frame, text=t.settings.frame_title, padding=10)
        self.adv_frame.pack(fill="x", pady=(0, 15))

        self.lbl_device = ttk.Label(self.adv_frame, text=t.settings.device)
        self.lbl_device.grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.device_var = tk.StringVar(value=self.settings.device)
        device_combo = ttk.Combobox(
            self.adv_frame,
            textvariable=self.device_var,
            state="readonly",
            values=[d.value for d in InferenceDevice],
            width=10,
        )
        device_combo.grid(row=0, column=1, sticky="w", pady=2, padx=5)
        _ = device_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        self.lbl_vram = ttk.Label(self.adv_frame, text=t.settings.vram_limit)
        self.lbl_vram.grid(row=0, column=2, sticky="w", pady=2, padx=5)
        self.vram_var = tk.StringVar(value=str(self.settings.vram_limit))
        vram_entry = ttk.Entry(self.adv_frame, textvariable=self.vram_var, width=8)
        vram_entry.grid(row=0, column=3, sticky="w", pady=2, padx=5)
        _ = vram_entry.bind("<FocusOut>", lambda e: self._save_settings())

        self.lbl_lang = ttk.Label(self.adv_frame, text=t.settings.language)
        self.lbl_lang.grid(row=0, column=4, sticky="w", pady=2, padx=5)
        current_lang_display = LANGUAGE_DISPLAY_NAMES.get(self.settings.language, "English")
        self.lang_var = tk.StringVar(value=current_lang_display)
        self.lang_combo = ttk.Combobox(
            self.adv_frame,
            textvariable=self.lang_var,
            state="readonly",
            values=list(LANGUAGE_DISPLAY_NAMES.values()),
            width=14,
        )
        self.lang_combo.grid(row=0, column=5, sticky="w", pady=2, padx=5)
        _ = self.lang_combo.bind("<<ComboboxSelected>>", lambda e: self._on_language_change())

        self.lbl_chunk = ttk.Label(self.adv_frame, text=t.settings.chunk_size)
        self.lbl_chunk.grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.chunk_var = tk.StringVar(value=self.settings.chunk_size_preset)
        self.chunk_combo = ttk.Combobox(self.adv_frame, textvariable=self.chunk_var, state="readonly", width=22)
        self.chunk_combo.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        _ = self.chunk_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        self.lbl_format = ttk.Label(self.adv_frame, text=t.settings.export_format)
        self.lbl_format.grid(row=1, column=2, sticky="w", pady=2, padx=5)
        self.format_var = tk.StringVar(value=self.settings.export_format)
        format_combo = ttk.Combobox(
            self.adv_frame,
            textvariable=self.format_var,
            state="readonly",
            values=[f.value for f in AudioExportFormat],
            width=18,
        )
        format_combo.grid(row=1, column=3, sticky="w", pady=2, padx=5)
        _ = format_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        self.btn_help = ttk.Button(self.adv_frame, text=t.settings.help, width=15, command=self._show_help)
        self.btn_help.grid(row=1, column=5, sticky="e", padx=(5, 0))

        self.lbl_overlap = ttk.Label(self.adv_frame, text=t.settings.overlap)
        self.lbl_overlap.grid(row=2, column=0, sticky="w", pady=(10, 2), padx=5)
        overlap_frame = ttk.Frame(self.adv_frame)
        overlap_frame.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(10, 2), padx=5)

        self.lbl_speed = ttk.Label(overlap_frame, text=t.settings.speed, font=("TkDefaultFont", 8))
        self.lbl_speed.pack(side="left")
        self.overlap_var = tk.IntVar(value=self.settings.overlap)
        self.overlap_scale = ttk.Scale(
            overlap_frame,
            from_=2,
            to=8,
            variable=self.overlap_var,
            command=self._on_overlap_change,
        )
        self.overlap_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_quality = ttk.Label(overlap_frame, text=t.settings.quality, font=("TkDefaultFont", 8))
        self.lbl_quality.pack(side="right")

        self.overlap_val_lbl = ttk.Label(self.adv_frame, text=f"{self.overlap_var.get()}")
        self.overlap_val_lbl.grid(row=2, column=4, sticky="w", pady=(10, 2))

        _ = self.adv_frame.columnconfigure(5, weight=1)

        # Queue section
        self.queue_panel = QueuePanel(main_frame)
        self.queue_panel.queue_manager = self.queue_manager
        self.queue_panel.pack(fill="both", expand=True, pady=(0, 15))

        self.btn_start = ttk.Button(
            main_frame,
            text=t.queue.start_transform,
            command=self._start_stop_toggle,
            style="Accent.TButton",
        )
        self.btn_start.pack(side="right")

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        self.status_var = tk.StringVar(value=t.queue.ready)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left")
        self.hw_label = ttk.Label(status_frame, text=t.queue.gpu_detecting)
        self.hw_label.pack(side="left", padx=10)

        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 0))

    # ------------------------------------------------------------------
    # Settings & Localization
    # ------------------------------------------------------------------

    def _on_language_change(self) -> None:
        display_name = self.lang_var.get()
        code = next((k for k, v in LANGUAGE_DISPLAY_NAMES.items() if v == display_name), AppLanguage.EN)
        self.settings.language = code
        set_current_language(code)
        self._save_settings()
        self._refresh_ui_translations()

    def _refresh_ui_translations(self) -> None:
        t = get_translations()
        self.title(t.app_title)
        _ = self.io_frame.config(text=t.folders.frame_title)
        _ = self.lbl_in_folder.config(text=t.folders.input_folder)
        _ = self.btn_browse_in.config(text=t.folders.browse)
        _ = self.lbl_out_folder.config(text=t.folders.output_folder)
        _ = self.btn_browse_out.config(text=t.folders.browse)
        _ = self.chk_subfolder.config(text=t.folders.subfolder_per_track)
        _ = self.model_frame.config(text=t.model.frame_title)
        _ = self.btn_change_model.config(text=t.model.change_model)
        _ = self.adv_frame.config(text=t.settings.frame_title)
        _ = self.lbl_device.config(text=t.settings.device)
        _ = self.lbl_vram.config(text=t.settings.vram_limit)
        _ = self.lbl_chunk.config(text=t.settings.chunk_size)
        _ = self.lbl_format.config(text=t.settings.export_format)
        _ = self.lbl_lang.config(text=t.settings.language)
        _ = self.btn_help.config(text=t.settings.help)
        _ = self.lbl_overlap.config(text=t.settings.overlap)
        _ = self.lbl_speed.config(text=t.settings.speed)
        _ = self.lbl_quality.config(text=t.settings.quality)
        self.queue_panel.refresh_translations()
        self._update_start_button()
        self._update_model_label()
        if self.status_var.get() in ("Ready", "Готово"):
            self.status_var.set(t.queue.ready)

    def _update_chunk_size_options(self) -> None:
        vram = self.hardware.vram_gb
        limit = self.settings.vram_limit
        if 0 < limit < vram:
            vram = float(limit)

        # When vram is 0 (no GPU detected / CPU mode), show all presets
        options = [p.label for p in CHUNK_PRESETS if vram == 0 or p.min_vram_gb <= vram]

        self.chunk_combo["values"] = options
        if self.settings.chunk_size_preset not in options:
            self.settings.chunk_size_preset = "Auto"
            self.chunk_var.set("Auto")

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
        # Keep QueueManager in sync with the latest settings
        self.queue_manager.settings = self.settings
        self.queue_manager.device = self.settings.device

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------

    def _change_model(self) -> None:
        dlg = ModelSelectorDialog(self, self.model_manager, self.settings.selected_model)
        self.wait_window(dlg)
        if dlg.selected_model_id != self.settings.selected_model:
            self.settings.selected_model = dlg.selected_model_id
            self._save_settings()
            self._update_model_label()

    def _update_model_label(self) -> None:
        t = get_translations()
        model = self.model_manager.get_model(self.settings.selected_model)
        if model:
            self.model_lbl_var.set(model.name)
        elif self.settings.selected_model:
            self.model_lbl_var.set(self.settings.selected_model)
        else:
            self.model_lbl_var.set(t.model.no_model)

    # ------------------------------------------------------------------
    # Queue control
    # ------------------------------------------------------------------

    def _show_help(self) -> None:
        dlg = HelpDialog(self)
        self.wait_window(dlg)

    def _start_stop_toggle(self) -> None:
        t = get_translations()
        if self.queue_manager.is_running:
            self.queue_manager.cancel_all()
            self._update_start_button()
            return

        if not self.settings.input_folder or not self.settings.output_folder:
            _ = messagebox.showwarning(t.folders.frame_title, f"{t.folders.input_folder} / {t.folders.output_folder}")
            return

        files = scan_audio_files(self.settings.input_folder)
        if not files:
            _ = messagebox.showinfo(t.queue.frame_title, "No audio files found")
            return

        self.queue_manager.clear_jobs()
        self.queue_panel.clear_all()

        for f in files:
            out_d = self.settings.output_folder
            if self.settings.create_subfolder_per_track:
                track_folder = Path(out_d) / Path(f).stem
                track_folder.mkdir(parents=True, exist_ok=True)
                out_d = str(track_folder)
            self.queue_manager.add_job(f, out_d, self.settings.selected_model)

        self._update_start_button()

    def _update_start_button(self) -> None:
        t = get_translations()
        if self.queue_manager.is_running:
            _ = self.btn_start.config(text=t.queue.stop)
            try:
                style = ttk.Style()
                if not style.lookup("Red.TButton", "background"):
                    _ = style.configure("Red.TButton", foreground="red")
                _ = self.btn_start.config(style="Red.TButton")
            except Exception:
                pass
        else:
            _ = self.btn_start.config(text=t.queue.start_transform, style="Accent.TButton")

    def _on_job_updated(self, job: Job) -> None:
        self.queue_panel.update_job(job)
        self._update_start_button()

    def destroy(self) -> None:
        self.queue_manager.stop()
        super().destroy()
