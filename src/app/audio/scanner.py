from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aiff'}

def scan_audio_files(directory: str) -> List[str]:
    """Scans a directory for supported audio files."""
    path = Path(directory)
    if not path.is_dir():
        return []
        
    found_files = []
    for ext in SUPPORTED_EXTENSIONS:
        # Scan case-insensitive if possible, using simple matching for now
        # Path.rglob is case-sensitive on Linux, but case-insensitive on Windows.
        # Since this is a Windows app, rglob is fine.
        found_files.extend([str(p.resolve()) for p in path.rglob(f"*{ext}")])
        
    return list(set(found_files)) # Remove duplicates if any
