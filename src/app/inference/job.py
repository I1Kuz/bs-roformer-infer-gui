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
    vram_limit: float = 0.0


@dataclass(slots=True)
class InferCommand:
    input_file: str
    store_dir: str
    chunk_size_preset: str = "Auto"
    overlap: int = 4
    export_format: str = AudioExportFormat.WAV_32_FLOAT.value
    overwrite_existing: bool = True


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
    ChunkPreset(key="Auto", label="Auto", min_vram_gb=0.0, samples=0),
    ChunkPreset(key="Small", label="Small (~3GB VRAM)", min_vram_gb=0.0, samples=352800),
    ChunkPreset(key="Medium", label="Medium (~4GB VRAM)", min_vram_gb=4.0, samples=470400),
    ChunkPreset(key="Big", label="Big (~6GB VRAM)", min_vram_gb=5.5, samples=0),
    ChunkPreset(key="Huge", label="Huge (~8+ GB VRAM)", min_vram_gb=7.5, samples=705600),
)

CHUNK_PRESET_KEY_TO_LABEL: dict[str, str] = {p.key: p.label for p in CHUNK_PRESETS}
CHUNK_PRESET_LABEL_TO_KEY: dict[str, str] = {p.label: p.key for p in CHUNK_PRESETS}


def get_chunk_preset_label(key_or_label: str) -> str:
    """Returns the display label for a preset key or returns the string if already a label."""
    return CHUNK_PRESET_KEY_TO_LABEL.get(key_or_label, key_or_label)


def get_chunk_preset_key(label_or_key: str) -> str:
    """Returns the canonical key (e.g. 'Small') for a display label or key."""
    if label_or_key in CHUNK_PRESET_LABEL_TO_KEY:
        return CHUNK_PRESET_LABEL_TO_KEY[label_or_key]
    for p in CHUNK_PRESETS:
        if label_or_key.startswith(p.key):
            return p.key
    return label_or_key
