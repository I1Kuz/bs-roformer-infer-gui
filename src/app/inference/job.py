from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class JobStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    FINISHED = "Finished"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

@dataclass
class Job:
    id: str
    input_file: str
    output_dir: str
    model_id: str
    status: JobStatus = JobStatus.PENDING
    status_text: Optional[str] = None
    progress: float = 0.0
    progress_str: str = ""
    error: Optional[str] = None
