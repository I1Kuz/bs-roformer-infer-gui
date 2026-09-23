import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """Returns the writable application data directory.

    On Windows uses %LOCALAPPDATA%; falls back to ~/.bsroformer_studio
    on other platforms or if the environment variable is missing.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "BSRoFormer Studio"
    return Path.home() / ".bsroformer_studio"


def get_runtime_dir() -> Path:
    return get_app_data_dir() / "runtime"


def get_models_dir() -> Path:
    return get_app_data_dir() / "models"


def get_settings_dir() -> Path:
    return get_app_data_dir() / "settings"


def get_logs_dir() -> Path:
    return get_app_data_dir() / "logs"


def get_temp_dir() -> Path:
    return get_app_data_dir() / "temp"


def get_history_dir() -> Path:
    return get_app_data_dir() / "history"


def ensure_directories() -> None:
    """Creates all necessary writable directories."""
    dirs = [
        get_app_data_dir(),
        get_runtime_dir(),
        get_models_dir(),
        get_settings_dir(),
        get_logs_dir(),
        get_temp_dir(),
        get_history_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_application_dir() -> Path:
    """Returns the directory where the application executable/script is located.

    In production the app is distributed as a PyInstaller .exe — this branch
    returns the directory containing that executable.
    In development (running from source) it returns the repository root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent.parent


def get_resources_dir() -> Path:
    """Returns the resources directory (icons, themes)."""
    if getattr(sys, "frozen", False):
        meipass: str = getattr(sys, "_MEIPASS", ".")
        return Path(meipass) / "resources"
    return get_application_dir() / "resources"


def get_worker_script_path() -> Path:
    """Returns the absolute path to worker_process.py, handling PyInstaller packaging."""
    if getattr(sys, "frozen", False):
        meipass: str = getattr(sys, "_MEIPASS", ".")
        return Path(meipass) / "app" / "inference" / "worker_process.py"
    return get_application_dir() / "src" / "app" / "inference" / "worker_process.py"
