import os
import sys
from pathlib import Path

from app.core.constants import APP_DATA_DIRNAME


def get_app_data_dir() -> Path:
    """Returns the writable application data directory.

    On Windows uses %LOCALAPPDATA%; falls back to ~/.bsroformer_studio
    on other platforms or if the environment variable is missing.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_DATA_DIRNAME
    return Path.home() / ".bsroformer_studio"


def get_models_dir() -> Path:
    return get_app_data_dir() / "models"


def get_settings_dir() -> Path:
    return get_app_data_dir() / "settings"


def get_logs_dir() -> Path:
    return get_app_data_dir() / "logs"


def ensure_directories() -> None:
    """Creates all necessary writable directories."""
    dirs = [
        get_app_data_dir(),
        get_models_dir(),
        get_settings_dir(),
        get_logs_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_application_dir() -> Path:
    """Returns the directory where the application executable/script is located.

    In production the app is distributed as an installed application or PyInstaller .exe —
    this returns the directory containing that executable.
    In development (running from source) it returns the repository root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent.parent


def get_src_dir() -> Path:
    """Returns the directory containing the 'app' package root."""
    if getattr(sys, "frozen", False):
        meipass: str = getattr(sys, "_MEIPASS", ".")
        candidate = Path(meipass)
        if (candidate / "app").exists():
            return candidate
        if (candidate / "_internal" / "app").exists():
            return candidate / "_internal"
        app_dir = get_application_dir()
        if (app_dir / "app").exists():
            return app_dir
        if (app_dir / "_internal" / "app").exists():
            return app_dir / "_internal"
        return app_dir / "src"
    return get_application_dir() / "src"


def get_python_exe() -> Path:
    """Returns the Python executable to run the worker process.

    1. In an installed Inno Setup distribution, prefers {app}/runtime/python.exe.
    2. In user AppData runtime (if installed previously with CUDA support).
    3. Otherwise (in development or virtualenv), uses the current sys.executable.
    """
    installed_runtime = get_application_dir() / "runtime" / "python.exe"
    if installed_runtime.exists():
        return installed_runtime

    appdata_runtime = get_app_data_dir() / "runtime" / "python.exe"
    if appdata_runtime.exists():
        return appdata_runtime

    return Path(sys.executable)


def get_resources_dir() -> Path:
    """Returns the resources directory (icons, themes)."""
    if getattr(sys, "frozen", False):
        meipass: str = getattr(sys, "_MEIPASS", ".")
        return Path(meipass) / "resources"
    return get_application_dir() / "resources"


def get_worker_script_path() -> Path:
    """Returns the absolute path to worker_process.py, handling PyInstaller packaging."""
    return get_src_dir() / "app" / "inference" / "worker_process.py"
