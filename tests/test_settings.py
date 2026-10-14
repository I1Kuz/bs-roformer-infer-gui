import json
from pathlib import Path
from unittest.mock import patch

from app.inference.protocol import AudioExportFormat, InferenceDevice
from app.storage.settings import AppSettings, SettingsManager


def test_default_settings() -> None:
    settings = AppSettings()
    assert settings.input_folder == ""
    assert settings.output_folder == ""
    assert settings.create_subfolder_per_track is False
    assert settings.device == InferenceDevice.AUTO.value
    assert settings.vram_limit == 0.0
    assert settings.chunk_size_preset == "Auto"
    assert settings.overlap == 4
    assert settings.export_format == AudioExportFormat.WAV_32_FLOAT.value
    assert settings.overwrite_existing is False
    assert settings.language == "en"


def test_settings_save_and_load(tmp_path: Path) -> None:
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)

    with patch("app.storage.settings.get_settings_dir", return_value=settings_dir):
        manager = SettingsManager()
        manager.settings.input_folder = "C:/Music/In"
        manager.settings.output_folder = "C:/Music/Out"
        manager.settings.overlap = 6
        manager.settings.vram_limit = 6.5
        manager.settings.language = "uk"
        manager.save()

        # Re-load in a new manager
        manager2 = SettingsManager()
        assert manager2.settings.input_folder == "C:/Music/In"
        assert manager2.settings.output_folder == "C:/Music/Out"
        assert manager2.settings.overlap == 6
        assert manager2.settings.vram_limit == 6.5
        assert manager2.settings.language == "uk"


def test_settings_backward_compat_int_vram_limit(tmp_path: Path) -> None:
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    json_path = settings_dir / "settings.json"

    # Simulate legacy settings saved with int vram_limit
    legacy_data = {
        "device": "cuda",
        "vram_limit": 12,
        "overlap": 4,
        "language": "en",
    }
    json_path.write_text(json.dumps(legacy_data), encoding="utf-8")

    with patch("app.storage.settings.get_settings_dir", return_value=settings_dir):
        manager = SettingsManager()
        assert isinstance(manager.settings.vram_limit, float)
        assert manager.settings.vram_limit == 12.0
        assert manager.settings.device == "cuda"


def test_settings_corrupt_file_handling(tmp_path: Path) -> None:
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    json_path = settings_dir / "settings.json"
    json_path.write_text("{corrupt-json", encoding="utf-8")

    with patch("app.storage.settings.get_settings_dir", return_value=settings_dir):
        manager = SettingsManager()
        # Should gracefully retain defaults
        assert manager.settings.overlap == 4
        assert manager.settings.vram_limit == 0.0
