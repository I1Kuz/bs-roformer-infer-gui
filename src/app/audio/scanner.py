from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aiff"}


def scan_audio_files(directory: str | Path) -> list[str]:
    """Scans a directory recursively for supported audio files."""
    path = Path(directory)
    if not path.is_dir():
        return []

    found_files: set[str] = set()
    for ext in SUPPORTED_EXTENSIONS:
        for file_path in path.rglob(f"*{ext}"):
            found_files.add(str(file_path.resolve()))

    return sorted(found_files)
