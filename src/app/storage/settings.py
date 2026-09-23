import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import cast, final

from app.core.logging import get_logger
from app.core.paths import get_settings_dir
from app.inference.protocol import AudioExportFormat, InferenceDevice

logger = get_logger(__name__)


@dataclass(slots=True)
class AppSettings:
    input_folder: str = ""
    output_folder: str = ""
    create_subfolder_per_track: bool = False
    device: str = InferenceDevice.AUTO.value
    vram_limit: int = 0
    selected_model: str = ""
    chunk_size_preset: str = "Auto"
    overlap: int = 4
    export_format: str = AudioExportFormat.WAV_32_FLOAT.value
    backend: str = "torch"
    overwrite_existing: bool = False
    theme: str = "dark"
    language: str = "en"


@final
class SettingsManager:
    def __init__(self) -> None:
        self.settings_file: Path = get_settings_dir() / "settings.json"
        self.settings: AppSettings = AppSettings()
        self.load()

    def load(self) -> None:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, encoding="utf-8") as f:
                    raw_data: object = json.load(f)

                if isinstance(raw_data, dict):
                    raw_dict = cast(dict[str, object], raw_data)
                    defaults = AppSettings()
                    for field in fields(AppSettings):
                        if field.name not in raw_dict:
                            continue
                        val = raw_dict[field.name]
                        # Strict type check (not isinstance) to avoid the
                        # bool-is-subclass-of-int trap.
                        if type(val) is type(getattr(defaults, field.name)):
                            object.__setattr__(self.settings, field.name, val)

                logger.info("Settings loaded successfully")
            except Exception as e:
                logger.error("Failed to load settings: %s", e)
        else:
            logger.info("No settings file found, using defaults")
            self.save()

    def save(self) -> None:
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=4)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
