from enum import StrEnum


class WorkerCommand(StrEnum):
    LOAD = "load"
    INFER = "infer"
    RELEASE = "release"
    EXIT = "exit"


class WorkerEvent(StrEnum):
    MODEL_LOADING = "model_loading"
    MODEL_LOADED = "model_loaded"
    INFER_START = "infer_start"
    PROGRESS = "progress"
    PROGRESS_TEXT = "progress_text"
    INFER_DONE = "infer_done"


class ProgressType(StrEnum):
    DOWNLOAD = "download"
    TRANSFORM = "transform"
    UNKNOWN = "unknown"


class RpcStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class InferenceDevice(StrEnum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


class AudioExportFormat(StrEnum):
    MP3_320 = "MP3 320kbps"
    WAV_16 = "WAV 16-bit"
    WAV_24 = "WAV 24-bit"
    WAV_32_FLOAT = "WAV 32-bit (Float)"
    FLAC = "FLAC"
