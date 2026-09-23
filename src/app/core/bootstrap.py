import json
import subprocess
import threading
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import final

from app.core.logging import get_logger
from app.core.paths import get_runtime_dir

logger = get_logger(__name__)

# Embedded Python version used for the portable runtime.
# If you change the URL, update _PYTHON_PTH_FILENAME to match the new version.
_PYTHON_VERSION = "3.11.9"
_PYTHON_URL = f"https://www.python.org/ftp/python/{_PYTHON_VERSION}/python-{_PYTHON_VERSION}-embed-amd64.zip"
_PYTHON_PTH_FILENAME = "python311._pth"

_GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


@final
class EnvironmentBootstrap:
    def __init__(
        self,
        callback_progress: Callable[[int, str], None],
        callback_done: Callable[[bool, str], None],
    ) -> None:
        self.runtime_dir: Path = get_runtime_dir()
        self.python_exe: Path = self.runtime_dir / "python.exe"
        self.callback_progress: Callable[[int, str], None] = callback_progress
        self.callback_done: Callable[[bool, str], None] = callback_done

    def check_environment_exists(self) -> bool:
        """Returns True if the required environment is already set up."""
        if not self.python_exe.exists():
            return False
        try:
            result = subprocess.run(
                [str(self.python_exe), "-c", "import bs_roformer"],
                capture_output=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return result.returncode == 0
        except Exception:
            return False

    def start_setup(self) -> None:
        """Starts the setup process in a background thread."""
        thread = threading.Thread(target=self._run_setup, daemon=True)
        thread.start()

    def _report_progress(self, percent: int, status: str) -> None:
        logger.info("Bootstrap progress: %d%% - %s", percent, status)
        self.callback_progress(percent, status)

    def _run_setup(self) -> None:
        try:
            if not self.python_exe.exists():
                self.runtime_dir.mkdir(parents=True, exist_ok=True)

                # 1. Download Python
                self._report_progress(10, "Downloading portable Python...")
                zip_path = self.runtime_dir / "python-embed.zip"
                _ = urllib.request.urlretrieve(_PYTHON_URL, zip_path)

                # 2. Extract Python
                self._report_progress(20, "Extracting Python...")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(self.runtime_dir)
                zip_path.unlink()

                # 3. Enable site-packages by uncommenting "import site" in the .pth file
                self._report_progress(30, "Configuring Python...")
                pth_file = self.runtime_dir / _PYTHON_PTH_FILENAME
                if pth_file.exists():
                    content = pth_file.read_text(encoding="utf-8")
                    content = content.replace("#import site", "import site")
                    _ = pth_file.write_text(content, encoding="utf-8")

            # 4. Install pip
            pip_path = self.runtime_dir / "Scripts" / "pip.exe"
            if not pip_path.exists():
                self._report_progress(40, "Downloading pip...")
                get_pip_path = self.runtime_dir / "get-pip.py"
                _ = urllib.request.urlretrieve(_GET_PIP_URL, get_pip_path)

                self._report_progress(50, "Installing pip...")
                _ = subprocess.run(
                    [str(self.python_exe), str(get_pip_path)],
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                get_pip_path.unlink()

            # 5. Install torch
            self._report_progress(60, "Installing PyTorch (this may take a while)...")
            _ = subprocess.run(
                [
                    str(self.python_exe),
                    "-m",
                    "pip",
                    "install",
                    "torch",
                    "torchaudio",
                    "--index-url",
                    "https://download.pytorch.org/whl/cu121",
                ],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # 6. Install bs-roformer-infer
            self._report_progress(80, "Installing bs-roformer-infer...")
            _ = subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "bs-roformer-infer"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # 7. Install ffmpeg via imageio-ffmpeg and copy the binary next to python.exe
            #    so that worker_process.py can find it via PATH.
            # TODO: use static-ffmpeg instead
            self._report_progress(95, "Installing ffmpeg...")
            _ = subprocess.run(
                [str(self.python_exe), "-m", "pip", "install", "imageio-ffmpeg"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            ffmpeg_dest = json.dumps(str(self.runtime_dir / "ffmpeg.exe"))
            copy_script = (
                f"import imageio_ffmpeg, shutil; shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), {ffmpeg_dest})"
            )
            _ = subprocess.run(
                [str(self.python_exe), "-c", copy_script],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            self._report_progress(100, "Setup complete")
            self.callback_done(True, "Success")

        except Exception as e:
            logger.error("Setup failed: %s", e, exc_info=True)
            self.callback_done(False, str(e))
