import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING, Any, final

from app.core.i18n import get_translations
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

        self.btn_frame: ttk.Frame = ttk.Frame(self)
        self.btn_frame.pack(side="bottom", fill="x", pady=(10, 0))

        self.tree: ttk.Treeview = ttk.Treeview(
            self,
            columns=("File", "Model", "Status", "Progress"),
            show="headings",
            height=8,
        )
        self._setup_headings()

        _ = self.tree.column("File", width=200)
        _ = self.tree.column("Model", width=150)
        _ = self.tree.column("Status", width=150)
        _ = self.tree.column("Progress", width=80)

        self.tree.pack(fill="both", expand=True)

        # Context Menu
        self.context_menu: tk.Menu = tk.Menu(self, tearoff=0)
        _ = self.tree.bind("<Button-3>", self._show_context_menu)

    def _setup_headings(self) -> None:
        t = get_translations()
        self.tree.heading("File", text=t.queue.col_file)
        self.tree.heading("Model", text=t.queue.col_model)
        self.tree.heading("Status", text=t.queue.col_status)
        self.tree.heading("Progress", text=t.queue.col_progress)

    def refresh_translations(self) -> None:
        t = get_translations()
        _ = self.config(text=t.queue.frame_title)
        self._setup_headings()

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
                self.context_menu.add_command(label=t.queue.action_open_folder, command=self._on_reveal)

                if job.status == JobStatus.FINISHED:
                    self.context_menu.add_command(label=t.queue.action_open_folder, command=self._on_reveal_output)

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
        if self.queue_manager:
            self.queue_manager.remove_job(job_id)
        self.tree.delete(job_id)
        _ = self.jobs.pop(job_id, None)

    def _on_process_next(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        job_id = selection[0]
        if self.queue_manager:
            self.queue_manager.prioritize_job(job_id)
            self.tree.move(job_id, "", 0)

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
        filename = Path(job.input_file).name
        status_str = job.status_text if job.status_text else job.status.value
        if job.status == JobStatus.FAILED and job.error:
            status_str = f"Failed: {job.error}"

        if job.status == JobStatus.PROCESSING:
            prog_str = job.progress_str if job.progress_str else f"{int(job.progress * 100)}%"
        else:
            prog_str = ""

        if job.id in self.jobs:
            self.tree.item(
                job.id,
                values=(
                    filename,
                    job.model_id,
                    status_str,
                    prog_str,
                ),
            )
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

    def clear_completed(self) -> None:
        for job_id, job in list(self.jobs.items()):
            if job.status == JobStatus.FINISHED:
                self.tree.delete(job_id)
                _ = self.jobs.pop(job_id, None)

    def clear_all(self) -> None:
        for job_id in list(self.jobs.keys()):
            self.tree.delete(job_id)
            _ = self.jobs.pop(job_id, None)
