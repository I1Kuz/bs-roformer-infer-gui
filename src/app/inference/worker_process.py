# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingImports=false, reportOptionalMemberAccess=false
#
# Rationale: torch, numpy, yaml, soundfile and ml_collections are runtime-only
# dependencies installed in the portable Python runtime, not in the dev venv.
# Suppressing import and unknown-type rules file-wide avoids noise while keeping
# all structural and logic checks active.
import argparse
import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, final

from app.inference.protocol import (
    AudioExportFormat,
    ProgressType,
    RpcStatus,
    WorkerCommand,
    WorkerEvent,
)

# Ensure ffmpeg.exe (which sits next to python.exe) is in PATH
os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

@dataclass
class SessionState:
    """Holds all mutable state for a single worker serve session."""
    model: Any = None
    config: Any = None
    device: Any = None
    vram_limit: float = 0.0

    @property
    def is_loaded(self) -> bool:
        return self.model is not None and self.config is not None and self.device is not None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _get_hop_length(config: Any) -> int:
    """Extracts the STFT hop length from a model config dict."""
    if hasattr(config, "model") and hasattr(config.model, "stft_hop_length"):
        return int(config.model.stft_hop_length)
    if hasattr(config, "audio") and hasattr(config.audio, "hop_length"):
        return int(config.audio.hop_length)
    if hasattr(config, "model") and hasattr(config.model, "hop_length"):
        return int(config.model.hop_length)
    if hasattr(config, "inference") and hasattr(config.inference, "hop_length"):
        return int(config.inference.hop_length)
    return 512  # BS-RoFormer default


def _get_native_chunk_size(config: Any, hop: int) -> int:
    """Returns the native chunk size from config, rounded to a hop boundary."""
    native = 588800  # 1150 * 512 — BS-RoFormer default
    if hasattr(config, "inference") and hasattr(config.inference, "chunk_size") and config.inference.chunk_size:
        native = int(config.inference.chunk_size)
    elif hasattr(config, "audio") and hasattr(config.audio, "chunk_size") and config.audio.chunk_size:
        native = int(config.audio.chunk_size)
    return (native // hop) * hop


def _resolve_chunk_size(config: Any, preset: str, vram_limit: float) -> int:
    """Resolves the effective chunk size from a preset string and available VRAM."""
    import torch

    from app.inference.job import CHUNK_PRESETS

    hop = _get_hop_length(config)
    native = _get_native_chunk_size(config, hop)

    # Look up the preset by key (startswith match for backwards compat with labels)
    for p in CHUNK_PRESETS:
        if p.key != "Auto" and preset.startswith(p.key):
            samples = p.samples if p.samples > 0 else native
            return (samples // hop) * hop

    # "Auto" — use native size, downscale if GPU VRAM is too limited
    chunk = native
    if torch.cuda.is_available():
        total_memory = torch.cuda.get_device_properties(0).total_memory
        gb = total_memory / (1024 ** 3)
        if 0 < vram_limit < gb:
            gb = float(vram_limit)
        # Pick the largest preset that fits the available VRAM
        for p in reversed(CHUNK_PRESETS):
            if p.key != "Auto" and p.samples > 0 and p.min_vram_gb > 0 and gb < p.min_vram_gb:
                continue
            if p.key != "Auto" and p.samples > 0:
                chunk = (p.samples // hop) * hop
                break
    return chunk


# ---------------------------------------------------------------------------
# Progress stream — intercepts stderr/stdout of inference libraries
# ---------------------------------------------------------------------------

@final
class ProgressStream:
    """Wraps a stream and translates progress lines into JSON events on real_stdout."""

    def __init__(self, original_stream: Any, real_stdout: Any) -> None:
        self.original_stream: Any = original_stream
        self.real_stdout: Any = real_stdout
        self.buf: str = ""
        self.total_time: float | None = None

    def write(self, text: str) -> None:
        # Replace \r with \n so engine.py's readline() never blocks and causes
        # a pipe buffer deadlock.
        safe_text = text.replace("\r", "\n")
        _ = self.original_stream.write(safe_text)
        _ = self.original_stream.flush()

        self.buf += text

        # Split on any line terminator
        lines = re.split(r"[\r\n]+", self.buf)
        self.buf = lines[-1]  # last element is the remaining incomplete line

        for line in lines[:-1]:
            self._parse_line(line.strip())

        # If the incomplete line already looks like a progress update, emit it
        # immediately rather than waiting for the next \r.
        if self.buf.strip() and ("Estimated" in self.buf or "%" in self.buf):
            self._parse_line(self.buf.strip())
            self.buf = ""

    def _send(self, event: str, payload: dict[str, Any]) -> None:
        msg = json.dumps({"event": event, "payload": payload})
        _ = self.real_stdout.write(msg + "\n")
        _ = self.real_stdout.flush()

    def _parse_line(self, line: str) -> None:
        if not line:
            return

        m = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
        if m:
            val = float(m.group(1)) / 100.0
            self._send(
                WorkerEvent.PROGRESS.value,
                {"progress": val, "text": f"{int(val * 100)}%", "type": ProgressType.DOWNLOAD.value},
            )
            return

        if "Estimated total processing time" in line:
            m_time = re.search(r"([\d\.]+)\s*seconds", line)
            if m_time:
                self.total_time = float(m_time.group(1))
                self._send(
                    WorkerEvent.PROGRESS.value,
                    {"progress": 0.0, "text": "Starting...", "type": ProgressType.TRANSFORM.value},
                )
            return

        if "Estimated time remaining" in line:
            m_time = re.search(r"([\d\.]+)\s*seconds", line)
            if m_time and self.total_time and self.total_time > 0:
                rem = float(m_time.group(1))
                val = max(0.0, min(1.0, (self.total_time - rem) / self.total_time))
                if rem > 60:
                    time_str = f"{int(rem // 60)}m {int(rem % 60)}s left"
                else:
                    time_str = f"{rem:.1f}s left"
                self._send(
                    WorkerEvent.PROGRESS.value,
                    {"progress": val, "text": time_str, "type": ProgressType.TRANSFORM.value},
                )
            return

        if "Estimated" in line or "processing" in line:
            self._send(WorkerEvent.PROGRESS_TEXT.value, {"text": line})

    def flush(self) -> None:
        _ = self.original_stream.flush()


# ---------------------------------------------------------------------------
# Safe model wrapper — pads/trims model output to match the input chunk length
# ---------------------------------------------------------------------------

@final
class SafeModelWrapper:
    """Ensures the model output tensor along the time dimension matches the input chunk length.

    Some BS-RoFormer variants produce outputs that are slightly shorter or longer
    than the input. This wrapper silently corrects that, preventing shape mismatches
    in demix_track().
    """

    def __init__(self, inner: Any) -> None:
        import torch
        # torch.nn.Module.__init__ call is handled by the outer torch.nn.Module wrapper
        self._inner: Any = inner
        self._torch = torch

    def __call__(self, part: Any, *args: Any, **kwargs: Any) -> Any:
        torch = self._torch
        expected_len = part.shape[-1]
        out = self._inner(part, *args, **kwargs)
        if isinstance(out, (list, tuple)):
            res = out[0]
            if torch.is_tensor(res):
                if res.shape[-1] < expected_len:
                    res = torch.nn.functional.pad(res, (0, expected_len - res.shape[-1]))
                elif res.shape[-1] > expected_len:
                    res = res[..., :expected_len]
            return (res, *out[1:])
        if torch.is_tensor(out):
            if out.shape[-1] < expected_len:
                out = torch.nn.functional.pad(out, (0, expected_len - out.shape[-1]))
            elif out.shape[-1] > expected_len:
                out = out[..., :expected_len]
        return out

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _send(real_stdout: Any, event: str, payload: dict[str, Any]) -> None:
    msg = json.dumps({"event": event, "payload": payload})
    _ = real_stdout.write(msg + "\n")
    _ = real_stdout.flush()


def _reply(real_stdout: Any, req_id: Any, status: str, **kwargs: Any) -> None:
    msg: dict[str, Any] = {"id": req_id, "status": status}
    msg.update(kwargs)
    _ = real_stdout.write(json.dumps(msg) + "\n")
    _ = real_stdout.flush()


def _handle_load(req: dict[str, Any], real_stdout: Any, session: SessionState) -> None:
    from typing import cast

    import torch
    import yaml
    from bs_roformer import ensure_model_assets
    from bs_roformer.inference import SafeLoaderWithTuple
    from bs_roformer.utils import get_model_from_config
    from ml_collections import ConfigDict

    req_id = req.get("id")
    model_id = req.get("model_id")
    device_str: str = str(req.get("device", "auto"))
    vram_limit = float(req.get("vram_limit", 0))

    try:
        if not model_id:
            raise ValueError("Missing model_id in load request")

        if vram_limit > 0 and torch.cuda.is_available():
            total_memory = torch.cuda.get_device_properties(0).total_memory
            limit_bytes = vram_limit * 1024 * 1024 * 1024
            if limit_bytes < total_memory:
                try:
                    torch.cuda.set_per_process_memory_fraction(limit_bytes / total_memory, 0)
                except Exception as e:
                    import logging
                    logging.getLogger("worker").error("Failed to set VRAM limit: %s", e)

        _send(real_stdout, WorkerEvent.MODEL_LOADING.value, {"model_id": model_id})

        ckpt_path, config_path = ensure_model_assets(model_id)

        with open(config_path) as f:
            config = ConfigDict(cast(dict[str, Any], yaml.load(f, Loader=SafeLoaderWithTuple)))

        model = get_model_from_config("bs_roformer", config)

        try:
            model.load_state_dict(torch.load(ckpt_path, map_location=torch.device("cpu"), weights_only=False))
        except Exception as load_err:
            err_str = str(load_err).lower()
            if "zip archive" in err_str or "corrupt" in err_str or "invalid" in err_str:
                import contextlib
                with contextlib.suppress(Exception):
                    os.remove(ckpt_path)
                raise RuntimeError(
                    "Model file was corrupted (e.g. from an interrupted download) and has been "
                    "automatically deleted. Please start the transform again to re-download."
                ) from load_err
            raise load_err

        if device_str in ("auto", ""):
            torch_device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
        else:
            torch_device = torch.device(device_str)

        model = model.to(torch_device)
        model.eval()

        session.model = model
        session.config = config
        session.device = torch_device
        session.vram_limit = vram_limit

        _send(real_stdout, WorkerEvent.MODEL_LOADED.value, {"model_id": model_id, "status": RpcStatus.SUCCESS.value})
        _reply(real_stdout, req_id, RpcStatus.SUCCESS.value)

    except Exception as e:
        err_msg = str(e)
        import logging
        logging.getLogger("worker").error("%s", traceback.format_exc())
        _send(real_stdout, WorkerEvent.MODEL_LOADED.value, {"model_id": model_id, "status": RpcStatus.ERROR.value, "error": err_msg})
        _reply(real_stdout, req_id, RpcStatus.ERROR.value, error=err_msg)


def _handle_infer(req: dict[str, Any], real_stdout: Any, session: SessionState) -> None:
    import subprocess as sp

    import numpy as np
    import soundfile as sf
    import torch
    from bs_roformer.utils import demix_track

    req_id = req.get("id")

    if not session.is_loaded:
        _reply(real_stdout, req_id, RpcStatus.ERROR.value, error="No model loaded")
        return

    input_file = Path(str(req.get("input_file", "")))
    store_dir = Path(str(req.get("store_dir", "")))
    chunk_preset: str = str(req.get("chunk_size_preset", "Auto"))
    overlap: int = int(req.get("overlap", 4))
    export_format: str = str(req.get("export_format", AudioExportFormat.WAV_32_FLOAT.value))

    try:
        # Apply config overrides based on chunk preset and available VRAM
        chunk_size = _resolve_chunk_size(session.config, chunk_preset, session.vram_limit)
        hop = _get_hop_length(session.config)

        if hasattr(session.config, "inference"):
            session.config.inference.chunk_size = chunk_size
            session.config.inference.num_overlap = overlap
            if hasattr(session.config.inference, "dim_t") and hop:
                session.config.inference.dim_t = chunk_size // hop

        if hasattr(session.config, "audio"):
            session.config.audio.chunk_size = chunk_size
            if hasattr(session.config.audio, "dim_t") and hop:
                session.config.audio.dim_t = chunk_size // hop
            if hasattr(session.config.audio, "num_overlap"):
                session.config.audio.num_overlap = overlap

        _send(real_stdout, WorkerEvent.INFER_START.value, {"input_file": str(input_file)})
        _send(real_stdout, WorkerEvent.PROGRESS_TEXT.value, {"text": f"Loading audio {input_file.name} into memory..."})

        store_dir.mkdir(parents=True, exist_ok=True)

        mix, sr = sf.read(input_file)
        original_mono = mix.ndim == 1
        if original_mono:
            mix = np.stack([mix, mix], axis=-1)

        mixture = torch.tensor(mix.T, dtype=torch.float32)
        safe_model = SafeModelWrapper(session.model)
        res, _ = demix_track(session.config, safe_model, mixture, session.device, None)

        instruments: list[str] = list(session.config.training.instruments)
        target = getattr(session.config.training, "target_instrument", None)
        if target is not None:
            instruments = [str(target)]

        def save_track(data: Any, name_suffix: str) -> None:
            fmt = export_format.upper()
            base = f"{input_file.stem}_{name_suffix}"
            if export_format == AudioExportFormat.MP3_320 or "MP3" in fmt:
                temp_wav = store_dir / f"{base}.temp.wav"
                final_mp3 = store_dir / f"{base}.mp3"
                sf.write(temp_wav, data, sr, subtype="FLOAT")
                _ = sp.run(
                    ["ffmpeg", "-y", "-i", str(temp_wav), "-b:a", "320k", str(final_mp3)],
                    check=True,
                    stdout=sp.DEVNULL,
                    stderr=sp.DEVNULL,
                )
                temp_wav.unlink(missing_ok=True)
            elif export_format == AudioExportFormat.FLAC or "FLAC" in fmt:
                sf.write(store_dir / f"{base}.flac", data, sr, format="FLAC")
            elif export_format == AudioExportFormat.WAV_16 or "16-BIT" in fmt:
                sf.write(store_dir / f"{base}.wav", data, sr, subtype="PCM_16")
            elif export_format == AudioExportFormat.WAV_24 or "24-BIT" in fmt:
                sf.write(store_dir / f"{base}.wav", data, sr, subtype="PCM_24")
            else:
                sf.write(store_dir / f"{base}.wav", data, sr, subtype="FLOAT")

        for instr in instruments:
            track_output = res[instr].T
            if original_mono:
                track_output = track_output[:, 0]
            save_track(track_output, instr)

        if instruments:
            # Compute instrumental as mixture minus the first (primary) stem
            primary_output = res[instruments[0]].T
            if original_mono:
                primary_output = primary_output[:, 0]
            instrumental = mix - primary_output
            save_track(instrumental, "instrumental")

        _send(real_stdout, WorkerEvent.INFER_DONE.value, {"input_file": str(input_file), "status": RpcStatus.SUCCESS.value})
        _reply(real_stdout, req_id, RpcStatus.SUCCESS.value)

    except Exception as e:
        err_msg = str(e)
        import logging
        logging.getLogger("worker").error("%s", traceback.format_exc())
        _send(real_stdout, WorkerEvent.INFER_DONE.value, {"input_file": str(input_file), "status": RpcStatus.ERROR.value, "error": err_msg})
        _reply(real_stdout, req_id, RpcStatus.ERROR.value, error=err_msg)


def _handle_release(req: dict[str, Any], real_stdout: Any, session: SessionState) -> None:
    import torch

    req_id = req.get("id")
    session.model = None
    session.config = None
    session.device = None
    session.vram_limit = 0.0
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    _reply(real_stdout, req_id, RpcStatus.SUCCESS.value)


# ---------------------------------------------------------------------------
# Top-level entry points
# ---------------------------------------------------------------------------

def handle_registry() -> None:
    from typing import Any

    import bs_roformer
    from bs_roformer.download import default_models_dir

    registry_list: list[dict[str, Any]] = []
    mdir = default_models_dir()
    for category in bs_roformer.MODEL_REGISTRY.categories():
        for model in bs_roformer.MODEL_REGISTRY.list(category):
            ckpt_path = mdir / model.slug / model.checkpoint
            registry_list.append({
                "id": model.slug,
                "name": model.name,
                "category": category,
                "stems": model.default_sources,
                "checkpoint": model.checkpoint,
                "installed": ckpt_path.exists(),
            })

    _ = sys.stdout.write(json.dumps({"status": "success", "data": registry_list}) + "\n")
    _ = sys.stdout.flush()
    sys.exit(0)


def handle_serve() -> None:
    import logging

    # Capture real stdout before redirecting it.
    # All JSON responses go to real_stdout; library prints go to stderr.
    real_stdout = sys.stdout
    original_stderr = sys.stderr

    progress_stream = ProgressStream(original_stderr, real_stdout)
    sys.stdout = progress_stream  # type: ignore[assignment]
    sys.stderr = progress_stream  # type: ignore[assignment]

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logger = logging.getLogger("worker")

    session = SessionState()

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        try:
            req: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue

        cmd = req.get("command")

        if cmd == WorkerCommand.LOAD:
            _handle_load(req, real_stdout, session)
        elif cmd == WorkerCommand.INFER:
            logger.debug("Received infer command: %s", req)
            _handle_infer(req, real_stdout, session)
        elif cmd == WorkerCommand.RELEASE:
            _handle_release(req, real_stdout, session)
        elif cmd == WorkerCommand.EXIT:
            sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--registry", action="store_true", help="Print registry as JSON and exit")
    _ = parser.add_argument("--serve", action="store_true", help="Start JSON-RPC server over stdio")

    args = parser.parse_args()

    if args.registry:
        handle_registry()
    elif args.serve:
        handle_serve()
    else:
        _ = sys.stdout.write(json.dumps({"error": "No action specified"}) + "\n")
        _ = sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
