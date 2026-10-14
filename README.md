# BS-RoFormer-Infer Studio

A lightweight desktop GUI for AI-powered audio source separation using [BS-RoFormer](https://github.com/openmirlab/bs-roformer-infer) models.

[![License](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)

---

## Features

- **Batch processing** — drop audio files or an entire folder and process all tracks in a queue
- **Auto VRAM management** — chunk size adapts to your GPU automatically
- **Multiple export formats** — WAV 16/24/32-bit, FLAC, MP3 320kbps
- **No bundled PyTorch in GUI** — lightweight GUI executable; PyTorch runs in a separate runtime
- **Fully responsive UI** — inference runs in a separate background process, the GUI never freezes

## Architecture

```
bs-roformer-infer-gui/
├── src/app/
│   ├── audio/          # Audio file scanner
│   ├── core/           # Paths, logging, hardware detection
│   ├── gui/            # Tkinter windows, dialogs, widgets
│   ├── inference/      # Worker process client, job queue, protocol
│   ├── models/         # Model registry manager
│   └── storage/        # Settings persistence
```

**Key design decisions:**
- The GUI runs as a standalone `.exe` built with PyInstaller or directly from Python.
- Inference runs in a **separate Python process** (`worker_process.py`) powered by `bs-roformer-infer` communicating over JSON-RPC via stdio. This ensures the GUI stays responsive during heavy model operations.
- Model checkpoints are downloaded automatically on first use into `%LOCALAPPDATA%\BSRoFormer Studio\models\`.

## Requirements

- Windows 10 or 11
- Python 3.12 (3.12.15 standardized for PyTorch CUDA support)
- An NVIDIA GPU with CUDA support is strongly recommended for practical performance; CPU fallback is supported but slow

## Development Setup

```bat
git clone https://github.com/I1Kuz/bs-roformer-infer-gui
cd bs-roformer-infer-gui

:: Sync dependencies using uv (automatically configures Python 3.12 and PyTorch CUDA)
uv sync

:: Run from source
run_windows.bat
```

## Testing & Quality Assurance

```bat
:: Linter
.venv\Scripts\ruff check src/ tests/

:: Type checker (strict basedpyright)
.venv\Scripts\basedpyright

:: Unit tests
.venv\Scripts\pytest
```

## Build Executable

```bat
build_windows.bat
```

The compiled `.exe` will be in the `dist/` directory.

## Data Storage

| Path | Contents |
|---|---|
| `%LOCALAPPDATA%\BSRoFormer Studio\runtime\` | Portable Python + PyTorch |
| `%LOCALAPPDATA%\BSRoFormer Studio\models\` | Downloaded model checkpoints |
| `%LOCALAPPDATA%\BSRoFormer Studio\settings\` | `settings.json` |
| `%LOCALAPPDATA%\BSRoFormer Studio\logs\` | Application logs |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Ensure `ruff check`, `basedpyright`, and `pytest` all pass with zero errors
4. Open a pull request

## Credits & Acknowledgments

- **[Band-Split RoFormer](https://github.com/lucidrains/BS-RoFormer)** — Original architecture by Wei-Tsung Lu et al., implemented by Phil Wang ([@lucidrains](https://github.com/lucidrains)).
- **[bs-roformer-infer](https://github.com/openmirlab/bs-roformer-infer)** — High-performance inference engine by [OpenMirLab](https://github.com/openmirlab).
- **[Sun Valley ttk Theme](https://github.com/rdbende/Sun-Valley-ttk-theme)** — Modern dark theme for Tkinter by [@rdbende](https://github.com/rdbende).

## License

[GPL-3.0](LICENSE)
