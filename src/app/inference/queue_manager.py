import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import final

from app.core.i18n import get_translations
from app.core.logging import get_logger
from app.inference.engine import WorkerClient, WorkerEvent, WorkerResponse
from app.inference.job import InferCommand, Job, JobStatus, LoadModelCommand
from app.inference.protocol import ProgressType, RpcStatus, WorkerCommand, WorkerEvent as ProtocolEvent
from app.storage.settings import AppSettings

logger = get_logger(__name__)


@dataclass(slots=True)
class UIEvent:
    event_type: str
    job: Job


@final
class QueueManager:
    def __init__(self, settings: AppSettings, on_job_updated: Callable[[Job], None]) -> None:
        self.settings: AppSettings = settings
        self.jobs: list[Job] = []
        self.client: WorkerClient = WorkerClient(self._on_worker_event)
        self.on_job_updated: Callable[[Job], None] = on_job_updated
        self.is_running: bool = False
        self.current_job: Job | None = None
        self.ui_event_queue: Queue[UIEvent] = Queue()
        self._lock: threading.RLock = threading.RLock()

        # Engine settings
        self.device: str = "auto"
        self.backend: str = "torch"
        self.loaded_model_id: str | None = None

    def start(self) -> bool:
        return self.client.start()

    def stop(self) -> None:
        with self._lock:
            self.is_running = False
        self.client.stop()

    def add_job(self, input_file: str, output_dir: str, model_id: str) -> None:
        with self._lock:
            job = Job(
                id=str(uuid.uuid4()),
                input_file=input_file,
                output_dir=output_dir,
                model_id=model_id,
            )
            self.jobs.append(job)
        self.on_job_updated(job)

    def start_processing(self) -> None:
        self._process_next_job()

    def remove_job(self, job_id: str) -> None:
        with self._lock:
            self.jobs = [j for j in self.jobs if j.id != job_id]

    def prioritize_job(self, job_id: str) -> None:
        with self._lock:
            job = next((j for j in self.jobs if j.id == job_id), None)
            if job and job.status == JobStatus.PENDING:
                self.jobs.remove(job)
                first_pending_idx = next(
                    (i for i, j in enumerate(self.jobs) if j.status == JobStatus.PENDING),
                    len(self.jobs),
                )
                self.jobs.insert(first_pending_idx, job)

    def cancel_current(self) -> None:
        with self._lock:
            if self.is_running and self.current_job:
                self.current_job.status = JobStatus.CANCELLED
                self.current_job.status_text = get_translations().status.cancelled
                self.current_job.progress_str = ""
                self._schedule_ui_update(self.current_job)
                self.loaded_model_id = None
                self.client.stop()
                _ = self.client.start()
                self._job_finished_locked()

    def cancel_all(self) -> None:
        with self._lock:
            for job in self.jobs:
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.CANCELLED
                    job.status_text = get_translations().status.cancelled
                    job.progress_str = ""
                    self._schedule_ui_update(job)
        self.cancel_current()

    def clear_jobs(self) -> None:
        with self._lock:
            self.jobs.clear()

    def clear_finished_jobs(self) -> None:
        with self._lock:
            self.jobs = [
                j for j in self.jobs
                if j.status in (JobStatus.PENDING, JobStatus.PROCESSING)
            ]

    def update_pending_model(self, model_id: str) -> None:
        with self._lock:
            for job in self.jobs:
                if job.status == JobStatus.PENDING:
                    job.model_id = model_id
                    self._schedule_ui_update(job)

    def update_pending_output_dir(self, output_dir: str, subfolder: bool = True) -> None:
        with self._lock:
            base = Path(output_dir)
            for job in self.jobs:
                if job.status == JobStatus.PENDING:
                    target_out = base / Path(job.input_file).stem if subfolder else base
                    job.output_dir = str(target_out)
                    self._schedule_ui_update(job)

    def _process_next_job(self) -> None:
        with self._lock:
            if self.is_running:
                return

            next_job = next((j for j in self.jobs if j.status == JobStatus.PENDING), None)
            if not next_job:
                return

            self.is_running = True
            self.current_job = next_job
            self.current_job.status = JobStatus.PROCESSING
            self._schedule_ui_update(self.current_job)

            # Ensure worker client is running
            if not self.client.process or self.client.process.poll() is not None:
                _ = self.client.start()

            if self.loaded_model_id != self.current_job.model_id:
                logger.info("Loading model %s for job %s", self.current_job.model_id, self.current_job.id)
                cmd = LoadModelCommand(
                    model_id=self.current_job.model_id,
                    device=self.device,
                    backend=self.backend,
                    vram_limit=float(self.settings.vram_limit),
                )
                self.client.send_command(WorkerCommand.LOAD, cmd, self._on_model_load_response)
            else:
                self._start_inference()

    def _on_model_load_response(self, response: WorkerResponse) -> None:
        with self._lock:
            if not self.current_job:
                return

            if response.status == RpcStatus.SUCCESS:
                self.loaded_model_id = self.current_job.model_id
                self._start_inference()
            else:
                self.current_job.status = JobStatus.FAILED
                self.current_job.error = response.error or "Unknown model load error"
                self.current_job.status_text = get_translations().status.failed
                self._schedule_ui_update(self.current_job)
                self._job_finished_locked()

    def _start_inference(self) -> None:
        with self._lock:
            if not self.current_job:
                return

            logger.info("Starting inference for job %s", self.current_job.id)
            cmd = InferCommand(
                input_file=self.current_job.input_file,
                store_dir=self.current_job.output_dir,
                chunk_size_preset=self.settings.chunk_size_preset,
                overlap=self.settings.overlap,
                export_format=self.settings.export_format,
                overwrite_existing=self.settings.overwrite_existing,
            )
            self.client.send_command(WorkerCommand.INFER, cmd, self._on_infer_response)

    def _on_infer_response(self, response: WorkerResponse) -> None:
        with self._lock:
            if not self.current_job:
                return

            if response.status == RpcStatus.SUCCESS:
                self.current_job.status = JobStatus.FINISHED
                self.current_job.status_text = get_translations().status.finished
                self.current_job.progress_str = ""
                self.current_job.progress = 1.0
            else:
                self.current_job.status = JobStatus.FAILED
                self.current_job.error = response.error or "Unknown inference error"
                self.current_job.status_text = get_translations().status.failed

            self._schedule_ui_update(self.current_job)
            self._job_finished_locked()

    def _job_finished_locked(self) -> None:
        self.current_job = None
        self.is_running = False
        self._process_next_job()

    def _on_worker_event(self, event: WorkerEvent) -> None:
        with self._lock:
            if not self.current_job:
                return
            if self.current_job.status == JobStatus.CANCELLED:
                return

            event_type = event.event
            payload = event.payload
            t = get_translations()

            if event_type == "worker_crashed":
                exit_code = payload.get("exit_code")
                self.current_job.status = JobStatus.FAILED
                self.current_job.error = f"Worker process crashed (exit code: {exit_code})"
                self.current_job.status_text = t.status.failed
                self._schedule_ui_update(self.current_job)
                self.loaded_model_id = None
                self._job_finished_locked()
            elif event_type == ProtocolEvent.MODEL_LOADING:
                self.current_job.status_text = t.status.downloading_model
                self._schedule_ui_update(self.current_job)
            elif event_type == ProtocolEvent.MODEL_LOADED:
                self.current_job.status_text = None
                self.current_job.status = JobStatus.PROCESSING
                self._schedule_ui_update(self.current_job)
            elif event_type == ProtocolEvent.INFER_START:
                self.current_job.status_text = t.status.transforming
                self._schedule_ui_update(self.current_job)
            elif event_type == ProtocolEvent.PROGRESS:
                prog_val = float(payload.get("progress", 0.0))  # type: ignore[arg-type]
                text_val = str(payload.get("text", ""))
                prog_type = str(payload.get("type", ProgressType.UNKNOWN.value))

                self.current_job.progress = prog_val
                if prog_type == ProgressType.DOWNLOAD:
                    self.current_job.status_text = t.status.downloading
                    self.current_job.progress_str = text_val
                elif prog_type == ProgressType.TRANSFORM:
                    self.current_job.status_text = t.status.transforming
                    self.current_job.progress_str = text_val
                else:
                    self.current_job.status_text = text_val
                    self.current_job.progress_str = f"{int(prog_val * 100)}%"

                self._schedule_ui_update(self.current_job)
            elif event_type == ProtocolEvent.PROGRESS_TEXT:
                text = str(payload.get("text", ""))
                if "Loading audio" in text:
                    self.current_job.status_text = t.status.starting
                else:
                    self.current_job.status_text = text
                logger.info("Job status update: %s", text)
                self._schedule_ui_update(self.current_job)
            elif event_type == ProtocolEvent.INFER_DONE:
                pass

    def _schedule_ui_update(self, job: Job) -> None:
        self.ui_event_queue.put(UIEvent(event_type="update", job=job))

    def process_ui_events(self) -> None:
        """Called from Tkinter after() poll loop on the main thread."""
        while True:
            try:
                event = self.ui_event_queue.get_nowait()
                if event.event_type == "update":
                    self.on_job_updated(event.job)
            except Empty:
                break
