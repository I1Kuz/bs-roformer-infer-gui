from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.inference.job import (
    CHUNK_PRESETS,
    get_chunk_preset_key,
    get_chunk_preset_label,
)
from app.inference.worker_process import _resolve_chunk_size


def test_chunk_preset_bidirectional_mapping() -> None:
    for preset in CHUNK_PRESETS:
        label = get_chunk_preset_label(preset.key)
        assert label == preset.label
        resolved_key = get_chunk_preset_key(label)
        assert resolved_key == preset.key

    # Test fallback behavior
    assert get_chunk_preset_label("NonExistentPreset") == "NonExistentPreset"
    assert get_chunk_preset_key("NonExistentLabel") == "NonExistentLabel"


def test_resolve_chunk_size_explicit_presets() -> None:
    config = SimpleNamespace(
        audio=SimpleNamespace(hop_length=1024, chunk_size=500000),
    )

    hop = 1024
    small_expected = (352800 // hop) * hop
    medium_expected = (470400 // hop) * hop
    huge_expected = (705600 // hop) * hop
    native_expected = (500000 // hop) * hop

    assert _resolve_chunk_size(config, "Small", vram_limit=0.0) == small_expected
    assert _resolve_chunk_size(config, "Medium", vram_limit=0.0) == medium_expected
    assert _resolve_chunk_size(config, "Big", vram_limit=0.0) == native_expected
    assert _resolve_chunk_size(config, "Huge", vram_limit=0.0) == huge_expected


def test_resolve_chunk_size_auto_cpu() -> None:
    config = SimpleNamespace(
        audio=SimpleNamespace(hop_length=1024, chunk_size=500000),
    )
    native_expected = (500000 // 1024) * 1024

    with patch("torch.cuda.is_available", return_value=False):
        resolved = _resolve_chunk_size(config, "Auto", vram_limit=0.0)
        assert resolved == native_expected


def test_resolve_chunk_size_auto_gpu_scaling() -> None:
    config = SimpleNamespace(
        audio=SimpleNamespace(hop_length=1024, chunk_size=500000),
    )
    hop = 1024
    small_expected = (352800 // hop) * hop
    medium_expected = (470400 // hop) * hop
    native_expected = (500000 // hop) * hop

    def mock_gpu_properties(total_gb: float) -> MagicMock:
        prop = MagicMock()
        prop.total_memory = int(total_gb * (1024**3))
        return prop

    with patch("torch.cuda.is_available", return_value=True):
        # 3GB GPU -> Small
        with patch("torch.cuda.get_device_properties", return_value=mock_gpu_properties(3.0)):
            assert _resolve_chunk_size(config, "Auto", vram_limit=0.0) == small_expected

        # 4.5GB GPU -> Medium
        with patch("torch.cuda.get_device_properties", return_value=mock_gpu_properties(4.5)):
            assert _resolve_chunk_size(config, "Auto", vram_limit=0.0) == medium_expected

        # 8GB GPU -> Native
        with patch("torch.cuda.get_device_properties", return_value=mock_gpu_properties(8.0)):
            assert _resolve_chunk_size(config, "Auto", vram_limit=0.0) == native_expected

        # 16GB GPU with user vram_limit=3.0 -> throttled to Small
        with patch("torch.cuda.get_device_properties", return_value=mock_gpu_properties(16.0)):
            assert _resolve_chunk_size(config, "Auto", vram_limit=3.0) == small_expected
