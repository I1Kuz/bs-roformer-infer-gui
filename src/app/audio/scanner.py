from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
})
SUPPORTED_AUDIO_PATTERNS: str = "*.wav;*.flac;*.mp3;*.ogg;*.m4a;*.aac;*.wma;*.aiff"


def scan_audio_files(directory: str | Path) -> list[str]:
    """Scans a directory recursively for supported audio files.

    Uses a single rglob("*") pass with suffix filtering instead of one pass
    per extension — significantly faster on large directory trees.
    """
    path = Path(directory)
    if not path.is_dir():
        return []

    return sorted(
        str(f.resolve())
        for f in path.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )
