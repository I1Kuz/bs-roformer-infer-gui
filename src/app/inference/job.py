from dataclasses import dataclass
from enum import Enum


class JobStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    FINISHED = "Finished"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


@dataclass(slots=True)
class Job:
    id: str
    input_file: str
    output_dir: str
    model_id: str
    status: JobStatus = JobStatus.PENDING
    status_text: str | None = None
    progress: float = 0.0
    progress_str: str = ""
    error: str | None = None


@dataclass(slots=True)
class LoadModelCommand:
    model_id: str
    device: str = "auto"
    backend: str = "torch"
    vram_limit: float = 0.0


@dataclass(slots=True)
class InferCommand:
    input_file: str
    store_dir: str
    chunk_size_preset: str = "Auto"
    overlap: int = 4
    export_format: str = "WAV 32-bit (Float)"


# Alias for semantic clarity
InferenceJob = Job
