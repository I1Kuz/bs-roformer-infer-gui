import subprocess
import json
import threading
import uuid
from typing import Callable, Optional
from pathlib import Path
from app.core.paths import get_runtime_dir, get_application_dir, get_worker_script_path
from app.core.logging import get_logger

logger = get_logger(__name__)

class WorkerClient:
    """Client to communicate with the background worker process."""
    def __init__(self, on_event: Callable[[str, dict], None]):
        self.process: Optional[subprocess.Popen] = None
        self.on_event = on_event
        self.pending_requests = {}
        self.lock = threading.Lock()
        self.running = False
        self.python_exe = get_runtime_dir() / "python.exe"
        self.worker_script = get_worker_script_path()

    def start(self):
        if not self.python_exe.exists():
            logger.error("Python runtime not found. Cannot start worker.")
            return False
            
        logger.info(f"Starting worker process: {self.worker_script}")
        import os
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
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=env
        )
        self.running = True
        
        # Start read threads
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        return True

    def _read_stdout(self):
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                    
                data = json.loads(line)
                logger.info(f"[ENGINE STDOUT] Received data: {data}")
                
                # Check if it's an event or a response
                if "event" in data:
                    self.on_event(data["event"], data.get("payload", {}))
                elif "id" in data:
                    req_id = data["id"]
                    callback = None
                    with self.lock:
                        if req_id in self.pending_requests:
                            callback = self.pending_requests.pop(req_id)
                    
                    if callback:
                        callback(data)
            except Exception as e:
                logger.error(f"Error reading from worker stdout: {e}")

    def _read_stderr(self):
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break
                logger.info(f"[WORKER STDERR] {line.strip()}")
            except Exception:
                pass

    def send_command(self, command: str, payload: dict, callback: Callable[[dict], None] = None):
        if not self.process or self.process.poll() is not None:
            logger.error("Worker process is not running.")
            if callback:
                callback({"status": "error", "error": "Worker not running"})
            return

        req_id = str(uuid.uuid4())
        msg = {"id": req_id, "command": command}
        msg.update(payload)
        
        if callback:
            with self.lock:
                self.pending_requests[req_id] = callback
                
        try:
            self.process.stdin.write(json.dumps(msg) + "\n")
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"Failed to send command to worker: {e}")
            if callback:
                with self.lock:
                    if req_id in self.pending_requests:
                        del self.pending_requests[req_id]
                callback({"status": "error", "error": str(e)})

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.send_command("exit", {})
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            self.process = None
