import threading
import uuid
from typing import List, Callable, Optional
from queue import Queue, Empty
from app.inference.job import Job, JobStatus
from app.inference.engine import WorkerClient
from app.core.logging import get_logger

logger = get_logger(__name__)

class QueueManager:
    def __init__(self, on_job_updated: Callable[[Job], None]):
        self.jobs: List[Job] = []
        self.client = WorkerClient(self._on_worker_event)
        self.on_job_updated = on_job_updated
        self.is_running = False
        self.current_job: Optional[Job] = None
        self.ui_event_queue = Queue()

        # Engine settings
        self.device = "auto"
        self.backend = "torch"
        self.loaded_model_id = None

    def start(self):
        return self.client.start()

    def stop(self):
        self.is_running = False
        self.client.stop()

    def add_job(self, input_file: str, output_dir: str, model_id: str):
        job = Job(
            id=str(uuid.uuid4()),
            input_file=input_file,
            output_dir=output_dir,
            model_id=model_id
        )
        self.jobs.append(job)
        self.on_job_updated(job)
        self._process_next_job()

    def remove_job(self, job_id: str):
        self.jobs = [j for j in self.jobs if j.id != job_id]

    def prioritize_job(self, job_id: str):
        job = next((j for j in self.jobs if j.id == job_id), None)
        if job and job.status == JobStatus.PENDING:
            self.jobs.remove(job)
            # Insert at the beginning of pending jobs
            first_pending_idx = next((i for i, j in enumerate(self.jobs) if j.status == JobStatus.PENDING), len(self.jobs))
            self.jobs.insert(first_pending_idx, job)
            
    def cancel_current(self):
        if self.is_running and self.current_job:
            self.current_job.status = JobStatus.CANCELLED
            self.current_job.status_text = "Cancelled"
            self.current_job.progress_str = ""
            self._schedule_ui_update(self.current_job)
            self.loaded_model_id = None
            self.client.stop()
            self.client.start()
            self._job_finished()
            
    def cancel_all(self):
        for job in self.jobs:
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.status_text = "Cancelled"
                job.progress_str = ""
                self._schedule_ui_update(job)
        self.cancel_current()
            
    def clear_jobs(self):
        self.jobs.clear()

    def _process_next_job(self):
        if self.is_running:
            return # Already processing

        # Find next pending
        next_job = next((j for j in self.jobs if j.status == JobStatus.PENDING), None)
        if not next_job:
            # Maybe unload model if idle? We can implement timeout later
            return

        self.is_running = True
        self.current_job = next_job
        self.current_job.status = JobStatus.PROCESSING
        self.on_job_updated(self.current_job)

        # 1. Check if model needs loading
        if self.loaded_model_id != self.current_job.model_id:
            logger.info(f"Loading model {self.current_job.model_id} for job {self.current_job.id}")
            from app.storage.settings import SettingsManager
            settings = SettingsManager().settings
            
            self.client.send_command("load", {
                "model_id": self.current_job.model_id,
                "device": self.device,
                "backend": self.backend,
                "vram_limit": settings.vram_limit
            }, self._on_model_load_response)
        else:
            self._start_inference()

    def _on_model_load_response(self, response: dict):
        if response.get("status") == "success":
            self.loaded_model_id = self.current_job.model_id
            self._start_inference()
        else:
            self.current_job.status = JobStatus.FAILED
            self.current_job.error = response.get("error", "Unknown model load error")
            self._schedule_ui_update(self.current_job)
            self._job_finished()

    def _start_inference(self):
        logger.info(f"Starting inference for job {self.current_job.id}")
        
        # Get settings from global singleton (or passed down if preferred, but we can import it)
        from app.storage.settings import SettingsManager
        settings = SettingsManager().settings
        
        # We also pass vram_limit in 'load' command, let's just make sure we send chunk_size in infer
        self.client.send_command("infer", {
            "input_file": self.current_job.input_file,
            "store_dir": self.current_job.output_dir,
            "chunk_size_preset": settings.chunk_size_preset,
            "overlap": settings.overlap,
            "export_format": settings.export_format
        }, self._on_infer_response)

    def _on_infer_response(self, response: dict):
        if response.get("status") == "success":
            self.current_job.status = JobStatus.FINISHED
            self.current_job.status_text = "Finished"
            self.current_job.progress_str = ""
            self.current_job.progress = 1.0
        else:
            self.current_job.status = JobStatus.FAILED
            self.current_job.error = response.get("error", "Unknown inference error")
            
        self._schedule_ui_update(self.current_job)
        self._job_finished()

    def _job_finished(self):
        self.current_job = None
        self.is_running = False
        # Process next
        self._process_next_job()

    def _on_worker_event(self, event_type: str, payload: dict):
        if self.current_job:
            if self.current_job.status == JobStatus.CANCELLED:
                return # Ignore events from stopping worker
                
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
                prog_val = payload.get("progress", 0.0)
                text_val = payload.get("text", "")
                prog_type = payload.get("type", "unknown")
                
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
                text = payload.get("text", "")
                self.current_job.status_text = text
                logger.info(f"Status: {text}")
                self._schedule_ui_update(self.current_job)
            elif event_type == "infer_done":
                pass

    def _schedule_ui_update(self, job: Job):
        self.ui_event_queue.put(("update", job))
        
    def process_ui_events(self):
        # Called from Tkinter after() loop
        while True:
            try:
                event_type, job = self.ui_event_queue.get_nowait()
                if event_type == "update":
                    self.on_job_updated(job)
            except Empty:
                break
