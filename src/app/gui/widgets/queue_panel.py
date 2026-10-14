from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING, Any, final

from app.core.i18n import get_translations
from app.gui.utils import enable_file_drop
from app.inference.job import Job, JobStatus

if TYPE_CHECKING:
    from app.inference.queue_manager import QueueManager


@final
class QueuePanel(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget) -> None:
        t = get_translations()
        super().__init__(parent, text=t.queue.frame_title, padding=10)
        self.jobs: dict[str, Job] = {}
        self.queue_manager: QueueManager | None = None

        self.on_files_dropped: Callable[[list[str]], None] | None = None

        # -------------------------------------------------------------
        # Action Toolbar
        # -------------------------------------------------------------
        self.toolbar: ttk.Frame = ttk.Frame(self)
        self.toolbar.pack(fill="x", pady=(0, 8))

        self.btn_clear_all = ttk.Button(
            self.toolbar,
            text=t.queue.btn_clear_all,
            command=self.clear_all,
            style="Action.TButton",
        )
        self.btn_clear_all.pack(side="right", padx=(6, 0))

        self.btn_clear_finished = ttk.Button(
            self.toolbar,
            text=t.queue.btn_clear_finished,
            command=self.clear_completed,
            style="Action.TButton",
        )
        self.btn_clear_finished.pack(side="right")

        # -------------------------------------------------------------
        # Treeview Area
        # -------------------------------------------------------------
        self.tree_container: ttk.Frame = ttk.Frame(self)
        self.tree_container.pack(fill="both", expand=True)

        self.tree: ttk.Treeview = ttk.Treeview(
            self.tree_container,
            columns=("File", "Model", "Status", "Progress"),
            show="headings",
            height=6,
        )
        self._setup_headings()

        _ = self.tree.column("File", stretch=True, minwidth=150)
        _ = self.tree.column("Model", stretch=False, width=170, minwidth=120)
        _ = self.tree.column("Status", stretch=False, width=140, minwidth=100)
        _ = self.tree.column("Progress", stretch=False, width=90, minwidth=70, anchor="center")

        enable_file_drop(self.tree, self._on_tree_drop)
        enable_file_drop(self.tree_container, self._on_tree_drop)

        scroll_y = ttk.Scrollbar(self.tree_container, orient="vertical", command=self._on_scroll)
        _ = self.tree.configure(yscrollcommand=scroll_y.set)  # type: ignore[arg-type]

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Empty state overlay
        self.empty_frame: ttk.Frame = ttk.Frame(self.tree_container)
        self.empty_title_lbl = ttk.Label(
            self.empty_frame,
            text=t.queue.empty_title,
            font=("TkDefaultFont", 11, "bold"),
            justify="center",
        )
        self.empty_title_lbl.pack()
        self.empty_hint_lbl = ttk.Label(
            self.empty_frame,
            text=t.queue.empty_hint,
            font=("TkDefaultFont", 9),
            foreground="gray",
            justify="center",
        )
        self.empty_hint_lbl.pack(pady=(2, 0))

        # -------------------------------------------------------------
        # Summary footer
        # -------------------------------------------------------------
        self.footer_frame: ttk.Frame = ttk.Frame(self)
        self.footer_frame.pack(fill="x", pady=(8, 0))

        self.summary_var: tk.StringVar = tk.StringVar(value="")
        self.summary_lbl: ttk.Label = ttk.Label(
            self.footer_frame,
            textvariable=self.summary_var,
            font=("TkDefaultFont", 9),
            foreground="gray",
        )
        self.summary_lbl.pack(side="left")

        # Context Menu & shortcuts
        self.context_menu: tk.Menu = tk.Menu(self, tearoff=0)
        _ = self.tree.bind("<Button-3>", self._show_context_menu)
        _ = self.tree.bind("<Delete>", lambda _: self._on_remove())

        self._update_empty_state()

    def _on_scroll(self, *args: Any) -> None:
        _ = getattr(self.tree, "yview")(*args)

    def _setup_headings(self) -> None:
        t = get_translations()
        self.tree.heading("File", text=t.queue.col_file)
        self.tree.heading("Model", text=t.queue.col_model)
        self.tree.heading("Status", text=t.queue.col_status)
        self.tree.heading("Progress", text=t.queue.col_progress)

    def _on_tree_drop(self, paths: list[str]) -> None:
        if self.on_files_dropped:
            self.on_files_dropped(paths)

    def _update_empty_state(self) -> None:
        if len(self.jobs) == 0:
            self.empty_frame.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_frame.place_forget()
        self._update_summary()

    def _update_summary(self) -> None:
        t = get_translations()
        total = len(self.jobs)
        done = sum(1 for j in self.jobs.values() if j.status == JobStatus.FINISHED)
        proc = sum(1 for j in self.jobs.values() if j.status == JobStatus.PROCESSING)
        pending = sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING)

        if total == 0:
            self.summary_var.set("")
        else:
            self.summary_var.set(
                t.queue.summary_fmt.format(total=total, done=done, proc=proc, pending=pending)
            )

    def refresh_translations(self) -> None:
        t = get_translations()
        _ = self.config(text=t.queue.frame_title)
        self._setup_headings()
        _ = self.btn_clear_finished.config(text=t.queue.btn_clear_finished)
        _ = self.btn_clear_all.config(text=t.queue.btn_clear_all)
        _ = self.empty_title_lbl.config(text=t.queue.empty_title)
        _ = self.empty_hint_lbl.config(text=t.queue.empty_hint)
        self._update_summary()

    def _show_context_menu(self, event: tk.Event[Any]) -> None:
        iid = self.tree.identify_row(event.y)
        if iid:
            _ = self.tree.selection_set(iid)
            job = self.jobs.get(iid)
            if job:
                t = get_translations()
                self.context_menu.delete(0, "end")

                if job.status == JobStatus.PENDING:
                    self.context_menu.add_command(label=t.queue.action_remove, command=self._on_remove)
                    self.context_menu.add_command(label=t.queue.action_prioritize, command=self._on_process_next)

                if job.status == JobStatus.PROCESSING:
                    self.context_menu.add_command(label=t.queue.stop, command=self._on_cancel_transform)

                if self.context_menu.index("end") is not None:
                    self.context_menu.add_separator()

                self.context_menu.add_command(label=t.queue.action_open_file, command=self._on_open_file)
                self.context_menu.add_command(label=t.queue.action_reveal_input, command=self._on_reveal)

                if job.status == JobStatus.FINISHED:
                    self.context_menu.add_command(label=t.queue.action_open_output, command=self._on_reveal_output)

                self.context_menu.post(event.x_root, event.y_root)

    def _on_cancel_transform(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job_id = selection[0]
        if self.queue_manager and self.queue_manager.current_job and self.queue_manager.current_job.id == job_id:
            self.queue_manager.cancel_current()

    def _on_reveal_output(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job = self.jobs.get(selection[0])
        if job and sys.platform == "win32":
            import os
            _ = os.startfile(job.output_dir)  # type: ignore[attr-defined]

    def _on_remove(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job_id = selection[0]
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.PROCESSING:
            return
        if self.queue_manager:
            self.queue_manager.remove_job(job_id)
        if self.tree.exists(job_id):
            self.tree.delete(job_id)
        _ = self.jobs.pop(job_id, None)
        self._update_empty_state()

    def _on_process_next(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job_id = selection[0]
        if self.queue_manager:
            self.queue_manager.prioritize_job(job_id)
            target_idx = 0
            for child in self.tree.get_children():
                child_job = self.jobs.get(child)
                if child_job and child_job.status == JobStatus.PROCESSING:
                    target_idx = 1
                    break
            self.tree.move(job_id, "", target_idx)

    def _on_open_file(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job = self.jobs.get(selection[0])
        if job and sys.platform == "win32":
            import os
            _ = os.startfile(job.input_file)  # type: ignore[attr-defined]

    def _on_reveal(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job = self.jobs.get(selection[0])
        if job:
            _ = subprocess.run(
                ["explorer", f"/select,{job.input_file}"],
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

    def update_job(self, job: Job) -> None:
        if self.queue_manager and not any(j.id == job.id for j in self.queue_manager.jobs):
            if self.tree.exists(job.id):
                self.tree.delete(job.id)
            _ = self.jobs.pop(job.id, None)
            self._update_empty_state()
            return

        t = get_translations()
        filename = Path(job.input_file).name
        if job.status_text:
            status_str = job.status_text
        elif job.status == JobStatus.PENDING:
            status_str = t.status.pending
        elif job.status == JobStatus.PROCESSING:
            status_str = t.status.processing
        elif job.status == JobStatus.FINISHED:
            status_str = t.status.finished
        elif job.status == JobStatus.CANCELLED:
            status_str = t.status.cancelled
        elif job.status == JobStatus.FAILED:
            status_str = f"{t.status.failed}: {job.error}" if job.error else t.status.failed
        else:
            status_str = job.status.value

        if job.status == JobStatus.PROCESSING:
            prog_str = job.progress_str if job.progress_str else f"{int(job.progress * 100)}%"
        elif job.status == JobStatus.FINISHED:
            prog_str = "100%"
        else:
            prog_str = ""

        if self.tree.exists(job.id):
            self.tree.item(
                job.id,
                values=(
                    filename,
                    job.model_id,
                    status_str,
                    prog_str,
                ),
            )
            self.jobs[job.id] = job
        else:
            _ = self.tree.insert(
                "",
                "end",
                iid=job.id,
                values=(
                    filename,
                    job.model_id,
                    status_str,
                    prog_str,
                ),
            )
            self.jobs[job.id] = job

        self._update_empty_state()

    def clear_completed(self) -> None:
        for job_id, job in list(self.jobs.items()):
            if job.status in (JobStatus.FINISHED, JobStatus.CANCELLED, JobStatus.FAILED):
                if self.tree.exists(job_id):
                    self.tree.delete(job_id)
                _ = self.jobs.pop(job_id, None)
        if self.queue_manager:
            self.queue_manager.clear_finished_jobs()
        self._update_empty_state()

    def clear_all(self) -> None:
        if self.queue_manager and self.queue_manager.is_running:
            self.queue_manager.cancel_all()
        for job_id in list(self.jobs.keys()):
            if self.tree.exists(job_id):
                self.tree.delete(job_id)
            _ = self.jobs.pop(job_id, None)
        if self.queue_manager:
            self.queue_manager.clear_jobs()
        self._update_empty_state()
