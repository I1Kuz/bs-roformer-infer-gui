import json
import os
import subprocess
import threading
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, final

from app.core.logging import get_logger
from app.core.paths import get_runtime_dir, get_worker_script_path
from app.inference.job import InferCommand, LoadModelCommand

logger = get_logger(__name__)


@dataclass(slots=True)
class WorkerResponse:
    id: str
    status: str
    data: Any = None
    error: str | None = None


@dataclass(slots=True)
class WorkerEvent:
    event: str
    payload: dict[str, Any]


@final
class WorkerClient:
    """Client to communicate with the background worker process."""

    def __init__(self, on_event: Callable[[WorkerEvent], None]) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.on_event: Callable[[WorkerEvent], None] = on_event
        self.pending_requests: dict[str, Callable[[WorkerResponse], None]] = {}
        self.lock: threading.Lock = threading.Lock()
        self.running: bool = False
        self.python_exe: Path = get_runtime_dir() / "python.exe"
        self.worker_script: Path = get_worker_script_path()

    def start(self) -> bool:
        if not self.python_exe.exists():
            logger.error("Python runtime not found. Cannot start worker.")
            return False

        logger.info("Starting worker process: %s", self.worker_script)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        self.process = subprocess.Popen(
            [str(self.python_exe), str(self.worker_script), "--serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env,
        )
        self.running = True

        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        return True

    def _read_stdout(self) -> None:
        while self.running and self.process and self.process.poll() is None:
            try:
                if not self.process.stdout:
                    break
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue

                data: dict[str, Any] = json.loads(line)
                logger.debug("[worker stdout] %s", data)

                if "event" in data:
                    self.on_event(WorkerEvent(event=str(data["event"]), payload=data.get("payload", {})))
                elif "id" in data:
                    req_id = str(data["id"])
                    callback = None
                    with self.lock:
                        if req_id in self.pending_requests:
                            callback = self.pending_requests.pop(req_id)

                    if callback:
                        callback(
                            WorkerResponse(
                                id=req_id,
                                status=str(data.get("status", "error")),
                                error=data.get("error"),
                                data=data.get("data"),
                            )
                        )
            except Exception as e:
                logger.error("Error reading from worker stdout: %s", e)

    def _read_stderr(self) -> None:
        while self.running and self.process and self.process.poll() is None:
            try:
                if not self.process.stderr:
                    break
                line = self.process.stderr.readline()
                if not line:
                    break
                stripped = line.strip()
                if stripped:
                    logger.info("[worker stderr] %s", stripped)
            except Exception:
                pass

    def send_command(
        self,
        command: str,
        payload: dict[str, Any] | LoadModelCommand | InferCommand,
        callback: Callable[[WorkerResponse], None] | None = None,
    ) -> None:
        if not self.process or self.process.poll() is not None or not self.process.stdin:
            logger.error("Worker process is not running.")
            if callback:
                callback(WorkerResponse(id="", status="error", error="Worker not running"))
            return

        req_id = str(uuid.uuid4())
        if is_dataclass(payload) and not isinstance(payload, type):
            payload_dict: dict[str, Any] = asdict(payload)
        elif isinstance(payload, dict):
            payload_dict = dict(payload)
        else:
            payload_dict = {}
        msg: dict[str, Any] = {"id": req_id, "command": command}
        msg.update(payload_dict)

        if callback:
            with self.lock:
                self.pending_requests[req_id] = callback

        try:
            _ = self.process.stdin.write(json.dumps(msg) + "\n")
            self.process.stdin.flush()
        except Exception as e:
            logger.error("Failed to send command to worker: %s", e)
            if callback:
                with self.lock:
                    _ = self.pending_requests.pop(req_id, None)
                callback(WorkerResponse(id=req_id, status="error", error=str(e)))

    def stop(self) -> None:
        self.running = False
        if self.process:
            try:
                self.send_command("exit", {})
                _ = self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            self.process = None
