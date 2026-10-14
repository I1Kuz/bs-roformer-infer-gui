import os
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, final

from app.audio.scanner import SUPPORTED_AUDIO_PATTERNS, SUPPORTED_EXTENSIONS, scan_audio_files
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
from app.gui.styles import (
    BTN_WIDTH_PRIMARY,
    COLOR_ACCENT_BLUE,
    COLOR_BG_DARK,
    COLOR_STATUS_SUCCESS,
    COLOR_STATUS_WARNING,
    COLOR_TEXT_MUTED,
    apply_theme,
)
from app.gui.utils import apply_dark_titlebar
from app.gui.widgets.queue_panel import QueuePanel
from app.inference.job import (
    CHUNK_PRESETS,
    Job,
    JobStatus,
    get_chunk_preset_key,
    get_chunk_preset_label,
)
from app.inference.protocol import AudioExportFormat, InferenceDevice
from app.inference.queue_manager import QueueManager
from app.models.manager import ModelManager, ModelMetadata
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

        # Dynamic responsive window geometry based on available screen bounds
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = min(1000, max(800, int(screen_w * 0.70)))
        win_h = min(840, max(600, int(screen_h * 0.85) - 60))
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)

        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(min(800, win_w), min(560, win_h))

        # Set application icon
        icon_path = get_resources_dir() / "icons" / "app.ico"
        if icon_path.exists():
            self.iconbitmap(default=str(icon_path))  # type: ignore[attr-defined]

        apply_dark_titlebar(self)
        apply_theme()
        _ = self.configure(bg=COLOR_BG_DARK)

        self.model_manager = ModelManager()
        self.hardware = HardwareDetector()
        self.queue_manager = QueueManager(self.settings, self._on_job_updated)

        # Loading screen (fluid relative layout)
        self.loading_frame = ttk.Frame(self)
        self.loading_frame.pack(fill="both", expand=True)

        self.center_frame = ttk.Frame(self.loading_frame)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.5)

        self.loading_pb = ttk.Progressbar(self.center_frame, mode="indeterminate")
        self.loading_pb.pack(fill="x", pady=(0, 8))
        self.loading_pb.start(10)

        self.loading_lbl_var = tk.StringVar(value=t.loading.initializing)
        self.loading_lbl = ttk.Label(
            self.center_frame,
            textvariable=self.loading_lbl_var,
            justify="center",
        )
        self.loading_lbl.pack()

        _ = self.after(100, self._start_background_init)

    # ------------------------------------------------------------------
    # Queue polling
    # ------------------------------------------------------------------

    def _poll_queue(self) -> None:
        self.queue_manager.process_ui_events()
        _ = self.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # Startup sequence
    # ------------------------------------------------------------------

    def _safe_after(self, ms: int, func: Callable[..., Any], *args: Any) -> None:
        try:
            if self.winfo_exists():
                _ = self.after(ms, func, *args)
        except Exception:
            pass

    def _start_background_init(self) -> None:
        def background_init() -> None:
            t = get_translations()
            self._safe_after(0, lambda: self.loading_lbl_var.set(t.loading.starting_worker))
            success = self.queue_manager.start()
            if success:
                self._safe_after(0, lambda: self.loading_lbl_var.set(t.loading.detecting_hw))
                _ = self.hardware.detect()
                self._safe_after(0, lambda: self.loading_lbl_var.set(t.loading.fetching_registry))
                _ = self.model_manager.fetch_registry()
            self._safe_after(0, lambda: self._on_startup_complete(success))

        threading.Thread(target=background_init, daemon=True).start()

    def _on_startup_complete(self, success: bool) -> None:
        t = get_translations()
        if not success:
            _ = messagebox.showerror(t.app_title, t.loading.worker_start_failed)
            self.destroy()
            return

        # Auto-configure CUDA if available and device wasn't explicitly pinned
        if self.hardware.cuda_available and self.settings.device in (InferenceDevice.AUTO.value, ""):
            self.settings.device = InferenceDevice.CUDA.value
            self._save_settings()

        self.loading_pb.stop()
        self.loading_frame.destroy()

        self._build_ui()
        _ = self.hw_label.config(text=self.hardware.get_display_string())
        self._update_chunk_size_options()
        self._update_model_card()

        # If an input folder is already saved, pre-populate queue
        if self.settings.input_folder and Path(self.settings.input_folder).exists():
            self._scan_folder_into_queue(self.settings.input_folder, clear_existing=False)

        self.status_var.set(t.queue.ready)
        _ = self.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        t = get_translations()

        # -------------------------------------------------------------
        # Status Bar (always anchored to the bottom of the window)
        # -------------------------------------------------------------
        status_frame = ttk.Frame(self, padding=(10, 4, 10, 6))
        status_frame.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value=t.queue.ready)
        self.status_lbl = ttk.Label(status_frame, textvariable=self.status_var, font=("TkDefaultFont", 9, "bold"))
        self.status_lbl.pack(side="left")

        ttk.Separator(status_frame, orient="vertical").pack(side="left", fill="y", padx=12, pady=2)

        self.hw_label = ttk.Label(status_frame, text=t.queue.gpu_detecting, font=("TkDefaultFont", 9))
        self.hw_label.pack(side="left")

        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.pack(side="right", padx=(10, 0))

        # -------------------------------------------------------------
        # Main Content Frame
        # -------------------------------------------------------------
        main_frame = ttk.Frame(self, padding=(20, 15, 20, 10))
        main_frame.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 1. Top Header Bar (Branding & Global Controls)
        # -------------------------------------------------------------
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 12))

        brand_frame = ttk.Frame(header_frame)
        brand_frame.pack(side="left")

        self.app_title_lbl = ttk.Label(
            brand_frame,
            text=t.app_title,
            font=("TkDefaultFont", 14, "bold"),
        )
        self.app_title_lbl.pack(anchor="w")

        top_actions_frame = ttk.Frame(header_frame)
        top_actions_frame.pack(side="right")

        current_lang_display = LANGUAGE_DISPLAY_NAMES.get(self.settings.language, "English")
        self.lang_var = tk.StringVar(value=current_lang_display)
        self.lang_combo = ttk.Combobox(
            top_actions_frame,
            textvariable=self.lang_var,
            state="readonly",
            values=list(LANGUAGE_DISPLAY_NAMES.values()),
            width=12,
        )
        self.lang_combo.pack(side="left", padx=(0, 8))
        _ = self.lang_combo.bind("<<ComboboxSelected>>", lambda _: self._on_language_change())

        self.btn_help = ttk.Button(
            top_actions_frame,
            text=f"? {t.settings.help}",
            style="Header.TButton",
            command=self._show_help,
        )
        self.btn_help.pack(side="left")

        # -------------------------------------------------------------
        # 2. Files & Folders Section
        # -------------------------------------------------------------
        self.io_frame = ttk.LabelFrame(main_frame, text=t.folders.frame_title, padding=10)
        self.io_frame.pack(fill="x", pady=(0, 10))

        # Input folder row
        self.lbl_in_folder = ttk.Label(self.io_frame, text=t.folders.input_folder)
        self.lbl_in_folder.grid(row=0, column=0, sticky="w", pady=4)

        norm_in = os.path.normpath(self.settings.input_folder) if self.settings.input_folder else ""
        self.in_var = tk.StringVar(value=norm_in)
        self.in_entry = ttk.Entry(self.io_frame, textvariable=self.in_var)
        self.in_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        _ = self.in_entry.bind("<FocusOut>", self._on_in_folder_edited)
        _ = self.in_entry.bind("<Return>", self._on_in_folder_edited)

        in_btns_frame = ttk.Frame(self.io_frame)
        in_btns_frame.grid(row=0, column=2, sticky="e", pady=4)
        self.btn_browse_in = ttk.Button(
            in_btns_frame,
            text=t.folders.browse,
            style="Compact.TButton",
            command=self._browse_in,
        )
        self.btn_browse_in.pack(side="left", padx=(0, 4))
        self.btn_add_files = ttk.Button(
            in_btns_frame,
            text=f"+ {t.folders.add_files}",
            style="Compact.TButton",
            command=self._on_add_files_clicked,
        )
        self.btn_add_files.pack(side="left", padx=(0, 4))
        self.btn_rescan_in = ttk.Button(
            in_btns_frame,
            text="↻",
            style="Icon.TButton",
            command=self._rescan_input_folder,
        )
        self.btn_rescan_in.pack(side="left", padx=(0, 4))
        self.btn_open_in = ttk.Button(
            in_btns_frame,
            text="↗",
            style="Icon.TButton",
            command=lambda: self._open_dir_in_explorer(self.in_var.get()),
        )
        self.btn_open_in.pack(side="left")

        # Output folder row
        self.lbl_out_folder = ttk.Label(self.io_frame, text=t.folders.output_folder)
        self.lbl_out_folder.grid(row=1, column=0, sticky="w", pady=4)

        norm_out = os.path.normpath(self.settings.output_folder) if self.settings.output_folder else ""
        self.out_var = tk.StringVar(value=norm_out)
        self.out_entry = ttk.Entry(self.io_frame, textvariable=self.out_var)
        self.out_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        _ = self.out_entry.bind("<FocusOut>", self._on_out_folder_edited)
        _ = self.out_entry.bind("<Return>", self._on_out_folder_edited)

        out_btns_frame = ttk.Frame(self.io_frame)
        out_btns_frame.grid(row=1, column=2, sticky="ew", pady=4)
        self.btn_browse_out = ttk.Button(
            out_btns_frame,
            text=t.folders.browse,
            style="Compact.TButton",
            command=self._browse_out,
        )
        self.btn_browse_out.pack(side="left")
        self.btn_open_out = ttk.Button(
            out_btns_frame,
            text="↗",
            style="Icon.TButton",
            command=lambda: self._open_dir_in_explorer(self.out_var.get()),
        )
        self.btn_open_out.pack(side="right")

        _ = self.io_frame.columnconfigure(1, weight=1)

        self.subfolder_var = tk.BooleanVar(value=self.settings.create_subfolder_per_track)
        self.chk_subfolder = ttk.Checkbutton(
            self.io_frame,
            text=t.folders.subfolder_per_track,
            variable=self.subfolder_var,
            command=self._on_subfolder_toggle,
        )
        self.chk_subfolder.grid(row=2, column=1, sticky="w", pady=(4, 0))

        # -------------------------------------------------------------
        # 3. Model Information Card
        # -------------------------------------------------------------
        self.model_frame = ttk.LabelFrame(main_frame, text=t.model.frame_title, padding=12)
        self.model_frame.pack(fill="x", pady=(0, 10))

        model_content = ttk.Frame(self.model_frame)
        model_content.pack(fill="x")

        model_info_box = ttk.Frame(model_content)
        model_info_box.pack(side="left", fill="x", expand=True)

        self.model_title_var = tk.StringVar(value="")
        self.model_title_lbl = ttk.Label(
            model_info_box,
            textvariable=self.model_title_var,
            font=("TkDefaultFont", 11, "bold"),
        )
        self.model_title_lbl.pack(anchor="w")

        self.model_badges_frame = ttk.Frame(model_info_box)
        self.model_badges_frame.pack(anchor="w", pady=(4, 0))

        self.badge_category_var = tk.StringVar(value="")
        self.badge_category_lbl = ttk.Label(
            self.model_badges_frame,
            textvariable=self.badge_category_var,
            font=("TkDefaultFont", 9),
            foreground=COLOR_ACCENT_BLUE,
        )
        self.badge_category_lbl.pack(side="left", padx=(0, 12))

        self.badge_stems_var = tk.StringVar(value="")
        self.badge_stems_lbl = ttk.Label(
            self.model_badges_frame,
            textvariable=self.badge_stems_var,
            font=("TkDefaultFont", 9),
            foreground=COLOR_TEXT_MUTED,
        )
        self.badge_stems_lbl.pack(side="left", padx=(0, 12))

        self.badge_status_var = tk.StringVar(value="")
        self.badge_status_lbl = ttk.Label(
            self.model_badges_frame,
            textvariable=self.badge_status_var,
            font=("TkDefaultFont", 9),
        )
        self.badge_status_lbl.pack(side="left")

        self.btn_change_model = ttk.Button(
            model_content,
            text=t.model.change_model,
            style="Action.TButton",
            command=self._change_model,
        )
        self.btn_change_model.pack(side="right", padx=(10, 0))

        # -------------------------------------------------------------
        # 4. Settings Section (2x2 Grid + Overlap Slider)
        # -------------------------------------------------------------
        self.adv_frame = ttk.LabelFrame(main_frame, text=t.settings.frame_title, padding=10)
        self.adv_frame.pack(fill="x", pady=(0, 10))

        # Grid row 0
        self.lbl_device = ttk.Label(self.adv_frame, text=t.settings.device)
        self.lbl_device.grid(row=0, column=0, sticky="w", pady=4, padx=5)
        self.device_var = tk.StringVar(value=self.settings.device)
        device_combo = ttk.Combobox(
            self.adv_frame,
            textvariable=self.device_var,
            state="readonly",
            values=[d.value for d in InferenceDevice],
            width=14,
        )
        device_combo.grid(row=0, column=1, sticky="w", pady=4, padx=5)
        _ = device_combo.bind("<<ComboboxSelected>>", lambda _: self._save_settings())

        self.lbl_vram = ttk.Label(self.adv_frame, text=t.settings.vram_limit)
        self.lbl_vram.grid(row=0, column=2, sticky="w", pady=4, padx=15)
        vram_str = f"{self.settings.vram_limit:.1f}".rstrip("0").rstrip(".") if self.settings.vram_limit > 0 else "0"
        self.vram_var = tk.StringVar(value=vram_str)
        vram_entry = ttk.Entry(self.adv_frame, textvariable=self.vram_var, width=10)
        vram_entry.grid(row=0, column=3, sticky="w", pady=4, padx=5)
        _ = vram_entry.bind("<FocusOut>", lambda _: self._save_settings())

        # Grid row 1
        self.lbl_chunk = ttk.Label(self.adv_frame, text=t.settings.chunk_size)
        self.lbl_chunk.grid(row=1, column=0, sticky="w", pady=4, padx=5)
        self.chunk_var = tk.StringVar(value=get_chunk_preset_label(self.settings.chunk_size_preset))
        self.chunk_combo = ttk.Combobox(
            self.adv_frame, textvariable=self.chunk_var, state="readonly", width=22
        )
        self.chunk_combo.grid(row=1, column=1, sticky="w", pady=4, padx=5)
        _ = self.chunk_combo.bind("<<ComboboxSelected>>", lambda _: self._save_settings())

        self.lbl_format = ttk.Label(self.adv_frame, text=t.settings.export_format)
        self.lbl_format.grid(row=1, column=2, sticky="w", pady=4, padx=15)
        self.format_var = tk.StringVar(value=self.settings.export_format)
        format_combo = ttk.Combobox(
            self.adv_frame,
            textvariable=self.format_var,
            state="readonly",
            values=[f.value for f in AudioExportFormat],
            width=20,
        )
        format_combo.grid(row=1, column=3, sticky="w", pady=4, padx=5)
        _ = format_combo.bind("<<ComboboxSelected>>", lambda _: self._save_settings())

        # Grid row 2: Overlap Slider (strictly in Column 1, proportional to combos, without pixel hardcode)
        self.lbl_overlap = ttk.Label(self.adv_frame, text=t.settings.overlap)
        self.lbl_overlap.grid(row=2, column=0, sticky="w", pady=(10, 4), padx=5)

        overlap_container = ttk.Frame(self.adv_frame)
        overlap_container.grid(row=2, column=1, sticky="ew", pady=(10, 4), padx=5)

        self.lbl_speed = ttk.Label(overlap_container, text=t.settings.speed, font=("TkDefaultFont", 8))
        self.lbl_speed.pack(side="left")

        self.overlap_var = tk.IntVar(value=self.settings.overlap)
        self.overlap_scale = ttk.Scale(
            overlap_container,
            from_=2,
            to=8,
            variable=self.overlap_var,
            command=self._on_overlap_change,
        )
        self.overlap_scale.pack(side="left", fill="x", expand=True, padx=8)
        _ = self.overlap_scale.bind("<ButtonRelease-1>", lambda _: self._save_settings())

        self.lbl_quality = ttk.Label(overlap_container, text=t.settings.quality, font=("TkDefaultFont", 8))
        self.lbl_quality.pack(side="left", padx=(0, 4))

        _ = self.adv_frame.columnconfigure(3, weight=1)

        # -------------------------------------------------------------
        # 6. Action Bar & Transform Control (anchored to bottom of main_frame)
        # -------------------------------------------------------------
        action_bar = ttk.Frame(main_frame)
        action_bar.pack(side="bottom", fill="x", pady=(8, 0))

        self.btn_start = ttk.Button(
            action_bar,
            text=f"▶ {t.queue.start_transform}",
            command=self._start_stop_toggle,
            style="Accent.TButton",
            width=BTN_WIDTH_PRIMARY,
        )
        self.btn_start.pack(side="right")

        # -------------------------------------------------------------
        # 5. Processing Queue Section (takes all remaining space)
        # -------------------------------------------------------------
        self.queue_panel = QueuePanel(main_frame)
        self.queue_panel.queue_manager = self.queue_manager
        self.queue_panel.on_files_dropped = self._on_paths_dropped
        self.queue_panel.pack(fill="both", expand=True, pady=(0, 4))

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
        _ = self.app_title_lbl.config(text=t.app_title)
        _ = self.io_frame.config(text=t.folders.frame_title)
        _ = self.lbl_in_folder.config(text=t.folders.input_folder)
        _ = self.btn_browse_in.config(text=t.folders.browse)
        _ = self.btn_add_files.config(text=f"+ {t.folders.add_files}")
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
        _ = self.btn_help.config(text=f"? {t.settings.help}")
        _ = self.lbl_overlap.config(text=t.settings.overlap)
        _ = self.lbl_speed.config(text=t.settings.speed)
        _ = self.lbl_quality.config(text=t.settings.quality)

        self.queue_panel.refresh_translations()
        self._update_start_button()
        self._update_model_card()
        _ = self.hw_label.config(text=self.hardware.get_display_string())
        if not self.queue_manager.is_running:
            self.status_var.set(t.queue.ready)

    def _update_chunk_size_options(self) -> None:
        vram = self.hardware.vram_gb
        limit = self.settings.vram_limit
        if 0 < limit < vram:
            vram = float(limit)

        options = [p.label for p in CHUNK_PRESETS if vram == 0 or p.min_vram_gb <= vram]
        self.chunk_combo["values"] = options
        curr_label = get_chunk_preset_label(self.settings.chunk_size_preset)
        if curr_label not in options:
            self.settings.chunk_size_preset = "Auto"
            self.chunk_var.set("Auto")
        else:
            self.chunk_var.set(curr_label)

    def _on_overlap_change(self, val: str) -> None:
        v = round(float(val))
        self.overlap_var.set(v)

    def _browse_in(self) -> None:
        d = filedialog.askdirectory(initialdir=self.settings.input_folder)
        if d:
            norm_d = os.path.normpath(d)
            self.in_var.set(norm_d)
            self.settings.input_folder = norm_d
            self._save_settings()
            self._scan_folder_into_queue(norm_d, clear_existing=True)

    def _on_in_folder_edited(self, event: Any = None) -> None:
        val = self.in_var.get().strip()
        norm_d = os.path.normpath(val) if val else ""
        if norm_d != self.settings.input_folder:
            self.settings.input_folder = norm_d
            self._save_settings()
            if norm_d and Path(norm_d).is_dir():
                self._scan_folder_into_queue(norm_d, clear_existing=True)

    def _rescan_input_folder(self) -> None:
        if self.settings.input_folder and Path(self.settings.input_folder).is_dir():
            self._scan_folder_into_queue(self.settings.input_folder, clear_existing=True)

    def _browse_out(self) -> None:
        d = filedialog.askdirectory(initialdir=self.settings.output_folder)
        if d:
            norm_d = os.path.normpath(d)
            self.out_var.set(norm_d)
            self.settings.output_folder = norm_d
            self._save_settings()
            self.queue_manager.update_pending_output_dir(norm_d, self.settings.create_subfolder_per_track)

    def _on_out_folder_edited(self, event: Any = None) -> None:
        val = self.out_var.get().strip()
        norm_d = os.path.normpath(val) if val else ""
        if norm_d != self.settings.output_folder:
            self.settings.output_folder = norm_d
            self._save_settings()
            if norm_d:
                self.queue_manager.update_pending_output_dir(norm_d, self.settings.create_subfolder_per_track)

    def _on_subfolder_toggle(self) -> None:
        self._save_settings()
        out_d = self._get_effective_output_dir()
        self.queue_manager.update_pending_output_dir(out_d, self.settings.create_subfolder_per_track)

    def _open_dir_in_explorer(self, folder_str: str) -> None:
        if not folder_str:
            return
        p = Path(folder_str)
        if p.exists() and sys.platform == "win32":
            _ = os.startfile(p)  # type: ignore[attr-defined]

    def _save_settings(self) -> None:
        self.settings.create_subfolder_per_track = self.subfolder_var.get()
        self.settings.device = self.device_var.get()
        self.settings.chunk_size_preset = get_chunk_preset_key(self.chunk_var.get())
        self.settings.overlap = self.overlap_var.get()
        self.settings.export_format = self.format_var.get()
        try:
            old_limit = self.settings.vram_limit
            new_limit = max(0.0, float(self.vram_var.get()))
            self.settings.vram_limit = new_limit
            if old_limit != new_limit:
                self._update_chunk_size_options()
        except ValueError:
            self.settings.vram_limit = 0.0
            self.vram_var.set("0")
        self.settings_manager.save()
        self.queue_manager.settings = self.settings
        self.queue_manager.device = self.settings.device

    # ------------------------------------------------------------------
    # Model Card
    # ------------------------------------------------------------------

    def _change_model(self) -> None:
        self.model_manager.refresh_installed_status()
        dlg = ModelSelectorDialog(self, self.model_manager, self.settings.selected_model)
        self.wait_window(dlg)
        if dlg.selected_model_id != self.settings.selected_model:
            self.settings.selected_model = dlg.selected_model_id
            self._save_settings()
            self._update_model_card()
            self.queue_manager.update_pending_model(self.settings.selected_model)
            if not self.queue_manager.is_running:
                has_pending = any(j.status == JobStatus.PENDING for j in self.queue_manager.jobs)
                if not has_pending and self.settings.input_folder and Path(self.settings.input_folder).is_dir():
                    self._scan_folder_into_queue(self.settings.input_folder, clear_existing=True)

    def _update_model_card(self) -> None:
        t = get_translations()
        model: ModelMetadata | None = self.model_manager.get_model(self.settings.selected_model)
        if model:
            self.model_title_var.set(model.name)
            self.badge_category_var.set(f"{t.model.category_prefix} [{model.category.upper()}]")
            stems_str = ", ".join(model.stems)
            self.badge_stems_var.set(f"{t.model.stems_prefix} {stems_str}")
            if model.installed:
                self.badge_status_var.set(t.model.status_installed)
                _ = self.badge_status_lbl.config(foreground=COLOR_STATUS_SUCCESS)
            else:
                self.badge_status_var.set(t.model.status_online)
                _ = self.badge_status_lbl.config(foreground=COLOR_STATUS_WARNING)
        elif self.settings.selected_model:
            self.model_title_var.set(self.settings.selected_model)
            self.badge_category_var.set("")
            self.badge_stems_var.set("")
            self.badge_status_var.set("")
        else:
            self.model_title_var.set(t.model.no_model)
            self.badge_category_var.set("")
            self.badge_stems_var.set("")
            self.badge_status_var.set("")

    # ------------------------------------------------------------------
    # Queue Management & Actions
    # ------------------------------------------------------------------

    def _on_add_files_clicked(self) -> None:
        t = get_translations()
        filetypes = [
            (t.queue.file_filter_audio, SUPPORTED_AUDIO_PATTERNS),
            ("All Files", "*.*"),
        ]
        files = filedialog.askopenfilenames(
            title=t.queue.select_files_title,
            filetypes=filetypes,
            initialdir=self.settings.input_folder or None,
        )
        if files:
            out_d = self._get_effective_output_dir()
            for f in files:
                target_out = out_d
                if self.settings.create_subfolder_per_track:
                    target_out = str(Path(target_out) / Path(f).stem)
                self.queue_manager.add_job(f, target_out, self.settings.selected_model)

    def _on_paths_dropped(self, paths: list[str]) -> None:
        audio_files: list[str] = []
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_dir():
                audio_files.extend(scan_audio_files(str(path_obj)))
            elif path_obj.is_file() and path_obj.suffix.lower() in SUPPORTED_EXTENSIONS:
                audio_files.append(str(path_obj))

        if not audio_files:
            return

        out_d = self._get_effective_output_dir()
        existing_files = {j.input_file for j in self.queue_manager.jobs}
        for f in audio_files:
            if f in existing_files:
                continue
            target_out = out_d
            if self.settings.create_subfolder_per_track:
                target_out = str(Path(target_out) / Path(f).stem)
            self.queue_manager.add_job(f, target_out, self.settings.selected_model)
            existing_files.add(f)

    def _get_effective_output_dir(self) -> str:
        if self.settings.output_folder and Path(self.settings.output_folder).exists():
            return self.settings.output_folder
        if self.settings.input_folder and Path(self.settings.input_folder).exists():
            return str(Path(self.settings.input_folder) / "separated")
        return str(Path.home() / "Music" / "separated")

    def _scan_folder_into_queue(self, folder_path: str, clear_existing: bool) -> None:
        files = scan_audio_files(folder_path)
        if not files:
            return

        if clear_existing:
            self.queue_manager.clear_jobs()
            self.queue_panel.clear_all()

        existing_files = {j.input_file for j in self.queue_manager.jobs}
        out_d = self._get_effective_output_dir()
        effective_out_path = Path(out_d).resolve()

        for f in files:
            file_path = Path(f).resolve()
            try:
                if file_path.is_relative_to(effective_out_path):
                    continue
            except (ValueError, AttributeError):
                pass

            if f in existing_files:
                continue

            target_out = out_d
            if self.settings.create_subfolder_per_track:
                target_out = str(Path(target_out) / Path(f).stem)
            self.queue_manager.add_job(f, target_out, self.settings.selected_model)

    def _show_help(self) -> None:
        dlg = HelpDialog(self)
        self.wait_window(dlg)

    def _start_stop_toggle(self) -> None:
        t = get_translations()
        if self.queue_manager.is_running:
            self.queue_manager.cancel_all()
            self._update_start_button()
            self.progress_bar.stop()
            self.status_var.set(t.queue.ready)
            return

        # Check if queue has jobs
        pending_jobs = [j for j in self.queue_manager.jobs if j.status == JobStatus.PENDING]
        if not pending_jobs:
            # If queue has no pending jobs (empty or all finished), re-scan input folder
            if self.settings.input_folder and Path(self.settings.input_folder).is_dir():
                self._scan_folder_into_queue(self.settings.input_folder, clear_existing=True)
                pending_jobs = [j for j in self.queue_manager.jobs if j.status == JobStatus.PENDING]

            if not pending_jobs:
                _ = messagebox.showinfo(t.queue.frame_title, t.queue.empty_hint)
                return

        if not self.settings.output_folder:
            _ = messagebox.showwarning(t.folders.frame_title, t.queue.err_no_output_folder)
            return

        self._update_start_button()
        self.progress_bar.start(15)
        self.status_var.set(t.status.processing)
        self.queue_manager.start_processing()

    def _update_start_button(self) -> None:
        t = get_translations()
        if self.queue_manager.is_running:
            _ = self.btn_start.config(text=f"⏹ {t.queue.stop}", style="Red.TButton")
        else:
            _ = self.btn_start.config(text=f"▶ {t.queue.start_transform}", style="Accent.TButton")
            self.progress_bar.stop()

    def _on_job_updated(self, job: Job) -> None:
        self.queue_panel.update_job(job)
        self._update_start_button()
        if job.status in (JobStatus.FINISHED, JobStatus.PROCESSING):
            self.model_manager.refresh_installed_status()
            self._update_model_card()
        if not self.queue_manager.is_running:
            t = get_translations()
            self.status_var.set(t.queue.ready)

    def destroy(self) -> None:
        self.queue_manager.stop()
        super().destroy()
