from pathlib import Path

from app.audio.scanner import SUPPORTED_EXTENSIONS, scan_audio_files


def test_scan_non_existent_and_empty(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist"
    assert scan_audio_files(non_existent) == []

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert scan_audio_files(empty_dir) == []


def test_scan_audio_formats(tmp_path: Path) -> None:
    # Create files for all supported extensions
    for ext in SUPPORTED_EXTENSIONS:
        (tmp_path / f"track{ext}").write_bytes(b"dummy")

    # Add uppercase and mixed-case extensions
    (tmp_path / "track_upper.WAV").write_bytes(b"dummy")
    (tmp_path / "track_mixed.Mp3").write_bytes(b"dummy")

    # Add non-audio files
    (tmp_path / "notes.txt").write_text("not audio", encoding="utf-8")
    (tmp_path / "cover.jpg").write_bytes(b"image")
    (tmp_path / "script.py").write_text("print('hello')", encoding="utf-8")

    results = scan_audio_files(tmp_path)
    result_paths = [Path(p) for p in results]

    # Every supported extension plus the two case-variants should be found
    expected_count = len(SUPPORTED_EXTENSIONS) + 2
    assert len(results) == expected_count

    # Non-audio files must be excluded
    result_names = {p.name for p in result_paths}
    assert "notes.txt" not in result_names
    assert "cover.jpg" not in result_names
    assert "script.py" not in result_names
    assert "track_upper.WAV" in result_names
    assert "track_mixed.Mp3" in result_names


def test_scan_recursive_and_sorted(tmp_path: Path) -> None:
    sub1 = tmp_path / "album1"
    sub2 = tmp_path / "album2" / "cd1"
    sub1.mkdir(parents=True)
    sub2.mkdir(parents=True)

    (tmp_path / "z_root.wav").write_bytes(b"dummy")
    (sub1 / "b_track.flac").write_bytes(b"dummy")
    (sub2 / "a_track.mp3").write_bytes(b"dummy")

    results = scan_audio_files(tmp_path)
    assert len(results) == 3
    # Result must be sorted alphabetically
    assert results == sorted(results)
