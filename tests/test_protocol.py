from app.inference.job import InferCommand, Job, JobStatus, LoadModelCommand
from app.inference.protocol import (
    AudioExportFormat,
    InferenceDevice,
    ProgressType,
    RpcStatus,
    WorkerCommand,
    WorkerEventType,
)


def test_protocol_enums() -> None:
    assert WorkerCommand.LOAD == "load"
    assert WorkerCommand.INFER == "infer"
    assert WorkerCommand.EXIT == "exit"

    assert WorkerEventType.MODEL_LOADING == "model_loading"
    assert WorkerEventType.MODEL_LOADED == "model_loaded"
    assert WorkerEventType.INFER_START == "infer_start"
    assert WorkerEventType.PROGRESS == "progress"
    assert WorkerEventType.PROGRESS_TEXT == "progress_text"
    assert WorkerEventType.INFER_DONE == "infer_done"

    assert ProgressType.DOWNLOAD == "download"
    assert ProgressType.TRANSFORM == "transform"

    assert RpcStatus.SUCCESS == "success"
    assert RpcStatus.ERROR == "error"

    assert InferenceDevice.AUTO == "auto"
    assert InferenceDevice.CPU == "cpu"
    assert InferenceDevice.CUDA == "cuda"

    assert AudioExportFormat.MP3_320 == "MP3 320kbps"
    assert AudioExportFormat.WAV_16 == "WAV 16-bit"
    assert AudioExportFormat.WAV_24 == "WAV 24-bit"
    assert AudioExportFormat.WAV_32_FLOAT == "WAV 32-bit (Float)"
    assert AudioExportFormat.FLAC == "FLAC"


def test_job_lifecycle() -> None:
    job = Job(
        id="job-1",
        input_file="/path/to/song.mp3",
        output_dir="/path/to/output",
        model_id="bs_roformer_vocals",
    )

    assert job.status == JobStatus.PENDING
    assert job.progress == 0.0
    assert job.progress_str == ""
    assert job.error is None

    # Transition to PROCESSING
    job.status = JobStatus.PROCESSING
    job.progress = 0.5
    job.progress_str = "50%"
    assert job.status == JobStatus.PROCESSING
    assert job.progress == 0.5

    # Transition to FINISHED
    job.status = JobStatus.FINISHED
    job.progress = 1.0
    assert job.status == JobStatus.FINISHED


def test_command_dataclasses() -> None:
    load_cmd = LoadModelCommand(
        model_id="bs_roformer_vocals",
        device="cuda",
        vram_limit=6.0,
    )
    assert load_cmd.model_id == "bs_roformer_vocals"
    assert load_cmd.device == "cuda"
    assert load_cmd.vram_limit == 6.0

    infer_cmd = InferCommand(
        input_file="test.wav",
        store_dir="out/",
        chunk_size_preset="Small",
        overlap=6,
        export_format=AudioExportFormat.FLAC.value,
        overwrite_existing=False,
    )
    assert infer_cmd.input_file == "test.wav"
    assert infer_cmd.chunk_size_preset == "Small"
    assert infer_cmd.overlap == 6
    assert infer_cmd.export_format == "FLAC"
    assert infer_cmd.overwrite_existing is False
