import os
import sys
import zipfile
import urllib.request
import subprocess
import threading
from pathlib import Path
from typing import Callable
from app.core.paths import get_runtime_dir
from app.core.logging import get_logger

logger = get_logger(__name__)

PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

class EnvironmentBootstrap:
    def __init__(self, callback_progress: Callable[[int, str], None], callback_done: Callable[[bool, str], None]):
        self.runtime_dir = get_runtime_dir()
        self.python_exe = self.runtime_dir / "python.exe"
        self.callback_progress = callback_progress
        self.callback_done = callback_done

    def check_environment_exists(self) -> bool:
        """Returns True if the required environment is already set up."""
        if not self.python_exe.exists():
            return False
        # Also check if bs_roformer is installed
        try:
            result = subprocess.run(
                [str(self.python_exe), "-c", "import bs_roformer"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception:
            return False

    def start_setup(self):
        """Starts the setup process in a background thread."""
        thread = threading.Thread(target=self._run_setup, daemon=True)
        thread.start()

    def _report_progress(self, percent: int, status: str):
        logger.info(f"Bootstrap progress: {percent}% - {status}")
        self.callback_progress(percent, status)

    def _run_setup(self):
        try:
            if not self.python_exe.exists():
                self.runtime_dir.mkdir(parents=True, exist_ok=True)
                
                # 1. Download Python
                self._report_progress(10, "Downloading portable Python...")
                zip_path = self.runtime_dir / "python-embed.zip"
                urllib.request.urlretrieve(PYTHON_URL, zip_path)
                
                # 2. Extract Python
                self._report_progress(20, "Extracting Python...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.runtime_dir)
                zip_path.unlink()

                # 3. Enable site-packages
                self._report_progress(30, "Configuring Python...")
                pth_file = self.runtime_dir / "python311._pth"
                if pth_file.exists():
                    content = pth_file.read_text()
                    content = content.replace("#import site", "import site")
                    pth_file.write_text(content)

            # 4. Install pip
            pip_path = self.runtime_dir / "Scripts" / "pip.exe"
            if not pip_path.exists():
                self._report_progress(40, "Downloading pip...")
                get_pip_path = self.runtime_dir / "get-pip.py"
                urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)
                
                self._report_progress(50, "Installing pip...")
                subprocess.run(
                    [str(self.python_exe), str(get_pip_path)],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                get_pip_path.unlink()

            # 5. Install torch
            self._report_progress(60, "Installing PyTorch (this may take a while)...")
            subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 6. Install bs-roformer-infer
            self._report_progress(80, "Installing bs-roformer-infer...")
            subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "bs-roformer-infer"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 7. Install ffmpeg
            self._report_progress(95, "Installing ffmpeg...")
            subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "imageio-ffmpeg"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            copy_script = f"import imageio_ffmpeg, shutil; shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), r'{str(self.runtime_dir / 'ffmpeg.exe')}')"
            subprocess.run(
                [str(self.python_exe), "-c", copy_script],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self._report_progress(100, "Setup complete!")
            self.callback_done(True, "Success")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            self.callback_done(False, str(e))

    def run_worker(self, worker_script_path: Path):
        """Runs the worker script using the bundled python."""
        # Ensure we set PYTHONPATH so the worker can import `app` if needed
        # Or better yet, write a small standalone worker script.
        pass
