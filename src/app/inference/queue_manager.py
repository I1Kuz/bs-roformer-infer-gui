import uuid
from collections.abc import Callable
from dataclasses import dataclass
from queue import Empty, Queue

from app.core.logging import get_logger
from app.inference.engine import (
    InferCommand,
    LoadModelCommand,
    WorkerClient,
    WorkerEvent,
    WorkerResponse,
)
from app.inference.job import Job, JobStatus
from app.storage.settings import SettingsManager

logger = get_logger(__name__)


@dataclass(slots=True)
class UIEvent:
    event_type: str
    job: Job


class QueueManager:
    def __init__(self, on_job_updated: Callable[[Job], None]) -> None:
        self.jobs: list[Job] = []
        self.client: WorkerClient = WorkerClient(self._on_worker_event)
        self.on_job_updated: Callable[[Job], None] = on_job_updated
        self.is_running: bool = False
        self.current_job: Job | None = None
        self.ui_event_queue: Queue[UIEvent] = Queue()

        # Engine settings
        self.device: str = "auto"
        self.backend: str = "torch"
        self.loaded_model_id: str | None = None

    def start(self) -> bool:
        return self.client.start()

    def stop(self) -> None:
        self.is_running = False
        self.client.stop()

    def add_job(self, input_file: str, output_dir: str, model_id: str) -> None:
        job = Job(
            id=str(uuid.uuid4()),
            input_file=input_file,
            output_dir=output_dir,
            model_id=model_id,
        )
        self.jobs.append(job)
        self.on_job_updated(job)
        self._process_next_job()

    def remove_job(self, job_id: str) -> None:
        self.jobs = [j for j in self.jobs if j.id != job_id]

    def prioritize_job(self, job_id: str) -> None:
        job = next((j for j in self.jobs if j.id == job_id), None)
        if job and job.status == JobStatus.PENDING:
            self.jobs.remove(job)
            first_pending_idx = next(
                (i for i, j in enumerate(self.jobs) if j.status == JobStatus.PENDING),
                len(self.jobs),
            )
            self.jobs.insert(first_pending_idx, job)

    def cancel_current(self) -> None:
        if self.is_running and self.current_job:
            self.current_job.status = JobStatus.CANCELLED
            self.current_job.status_text = "Cancelled"
            self.current_job.progress_str = ""
            self._schedule_ui_update(self.current_job)
            self.loaded_model_id = None
            self.client.stop()
            _ = self.client.start()
            self._job_finished()

    def cancel_all(self) -> None:
        for job in self.jobs:
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.status_text = "Cancelled"
                job.progress_str = ""
                self._schedule_ui_update(job)
        self.cancel_current()

    def clear_jobs(self) -> None:
        self.jobs.clear()

    def _process_next_job(self) -> None:
        if self.is_running:
            return

        next_job = next((j for j in self.jobs if j.status == JobStatus.PENDING), None)
        if not next_job:
            return

        self.is_running = True
        self.current_job = next_job
        self.current_job.status = JobStatus.PROCESSING
        self.on_job_updated(self.current_job)

        if self.loaded_model_id != self.current_job.model_id:
            logger.info("Loading model %s for job %s", self.current_job.model_id, self.current_job.id)
            settings = SettingsManager().settings

            cmd = LoadModelCommand(
                model_id=self.current_job.model_id,
                device=self.device,
                backend=self.backend,
                vram_limit=float(settings.vram_limit),
            )
            self.client.send_command("load", cmd, self._on_model_load_response)
        else:
            self._start_inference()

    def _on_model_load_response(self, response: WorkerResponse) -> None:
        if not self.current_job:
            return

        if response.status == "success":
            self.loaded_model_id = self.current_job.model_id
            self._start_inference()
        else:
            self.current_job.status = JobStatus.FAILED
            self.current_job.error = response.error or "Unknown model load error"
            self._schedule_ui_update(self.current_job)
            self._job_finished()

    def _start_inference(self) -> None:
        if not self.current_job:
            return

        logger.info("Starting inference for job %s", self.current_job.id)
        settings = SettingsManager().settings

        cmd = InferCommand(
            input_file=self.current_job.input_file,
            store_dir=self.current_job.output_dir,
            chunk_size_preset=settings.chunk_size_preset,
            overlap=settings.overlap,
            export_format=settings.export_format,
        )
        self.client.send_command("infer", cmd, self._on_infer_response)

    def _on_infer_response(self, response: WorkerResponse) -> None:
        if not self.current_job:
            return

        if response.status == "success":
            self.current_job.status = JobStatus.FINISHED
            self.current_job.status_text = "Finished"
            self.current_job.progress_str = ""
            self.current_job.progress = 1.0
        else:
            self.current_job.status = JobStatus.FAILED
            self.current_job.error = response.error or "Unknown inference error"

        self._schedule_ui_update(self.current_job)
        self._job_finished()

    def _job_finished(self) -> None:
        self.current_job = None
        self.is_running = False
        self._process_next_job()

    def _on_worker_event(self, event: WorkerEvent) -> None:
        if not self.current_job:
            return

        if self.current_job.status == JobStatus.CANCELLED:
            return

        event_type = event.event
        payload = event.payload

        if event_type == "model_loading":
            self.current_job.status_text = "Downloading / Loading Model..."
            self._schedule_ui_update(self.current_job)
        elif event_type == "model_loaded":
            self.current_job.status_text = None
            self.current_job.status = JobStatus.PROCESSING
            self._schedule_ui_update(self.current_job)
        elif event_type == "infer_start":
            self.current_job.status_text = "Processing (Transforming)..."
            self._schedule_ui_update(self.current_job)
        elif event_type == "progress":
            prog_val = float(payload.get("progress", 0.0))
            text_val = str(payload.get("text", ""))
            prog_type = str(payload.get("type", "unknown"))

            self.current_job.progress = prog_val
            if prog_type == "download":
                self.current_job.status_text = "Downloading"
                self.current_job.progress_str = text_val
            elif prog_type == "transform":
                self.current_job.status_text = "Transforming"
                self.current_job.progress_str = text_val
            else:
                self.current_job.status_text = text_val
                self.current_job.progress_str = f"{int(prog_val * 100)}%"

            self._schedule_ui_update(self.current_job)
        elif event_type == "progress_text":
            text = str(payload.get("text", ""))
            self.current_job.status_text = text
            logger.info("Job status update: %s", text)
            self._schedule_ui_update(self.current_job)
        elif event_type == "infer_done":
            pass

    def _schedule_ui_update(self, job: Job) -> None:
        self.ui_event_queue.put(UIEvent(event_type="update", job=job))

    def process_ui_events(self) -> None:
        """Called from Tkinter after() poll loop on main thread."""
        while True:
            try:
                event = self.ui_event_queue.get_nowait()
                if event.event_type == "update":
                    self.on_job_updated(event.job)
            except Empty:
                break
