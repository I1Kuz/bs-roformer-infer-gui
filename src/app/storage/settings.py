import json
from dataclasses import dataclass, asdict
from typing import Optional
from app.core.paths import get_settings_dir
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AppSettings:
    input_folder: str = ""
    output_folder: str = ""
    create_subfolder_per_track: bool = False
    device: str = "auto"
    vram_limit: int = 0
    selected_model: str = ""
    chunk_size_preset: str = "Auto"
    overlap: int = 4
    export_format: str = "WAV 32-bit (Float)"
    backend: str = "torch"
    overwrite_existing: bool = False
    theme: str = "dark"

class SettingsManager:
    def __init__(self):
        self.settings_file = get_settings_dir() / "settings.json"
        self.settings = AppSettings()
        self.load()

    def load(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Update fields that exist in AppSettings
                    for key, value in data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
                logger.info("Settings loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
        else:
            logger.info("No settings file found. Using defaults.")
            self.save()

    def save(self):
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.settings), f, indent=4)
            logger.info("Settings saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
