from dataclasses import dataclass
from enum import StrEnum

from app.inference.protocol import AudioExportFormat, InferenceDevice


class JobStatus(StrEnum):
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
    device: str = InferenceDevice.AUTO.value
    backend: str = "torch"
    vram_limit: float = 0.0


@dataclass(slots=True)
class InferCommand:
    input_file: str
    store_dir: str
    chunk_size_preset: str = "Auto"
    overlap: int = 4
    export_format: str = AudioExportFormat.WAV_32_FLOAT.value


@dataclass(frozen=True, slots=True)
class ChunkPreset:
    """A chunk size preset for audio inference.

    Attributes:
        key: Internal identifier used in settings and IPC (e.g. "Small").
        label: Human-readable label shown in the GUI combobox.
        min_vram_gb: Minimum GPU VRAM (in GB) needed for this preset.
              0 means always available.
        samples: Number of audio samples per chunk. 0 means "use native
              model chunk size from config".
    """
    key: str
    label: str
    min_vram_gb: float
    samples: int


CHUNK_PRESETS: tuple[ChunkPreset, ...] = (
    ChunkPreset(key="Auto",   label="Auto",              min_vram_gb=0.0, samples=0),
    ChunkPreset(key="Small",  label="Small (~3GB VRAM)", min_vram_gb=0.0, samples=352800),
    ChunkPreset(key="Medium", label="Medium (~4GB VRAM)", min_vram_gb=4.0, samples=470400),
    ChunkPreset(key="Big",    label="Big (~6GB VRAM)",   min_vram_gb=5.5, samples=0),
    ChunkPreset(key="Huge",   label="Huge (~8+ GB VRAM)", min_vram_gb=7.5, samples=705600),
)
