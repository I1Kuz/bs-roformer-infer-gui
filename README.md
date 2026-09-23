# BS-RoFormer-Infer Studio

A lightweight desktop GUI for AI-powered audio source separation using [BS-RoFormer](https://github.com/openmirlab/bs-roformer-infer) models.

![License](https://img.shields.io/github/license/openmirlab/bs-roformer-infer-gui)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## Features

- **Batch processing** — drop an entire folder and process all tracks in a queue
- **Auto VRAM management** — chunk size adapts to your GPU automatically
- **Multiple export formats** — WAV 16/24/32-bit, FLAC, MP3 320kbps
- **No bundled PyTorch** — the GUI executable is tiny; PyTorch is downloaded once into a portable runtime
- **Fully responsive UI** — inference runs in a separate process, the GUI never freezes

## Architecture

```
bs-roformer-infer-gui/
├── src/app/
│   ├── audio/          # Audio file scanner
│   ├── core/           # Paths, logging, hardware detection, bootstrap
│   ├── gui/            # Tkinter windows, dialogs, widgets
│   ├── inference/      # Worker process client, job queue, job dataclasses
│   ├── models/         # Model registry manager
│   └── storage/        # Settings persistence
└── bs-roformer-infer/  # git submodule — inference engine
```

**Key design decisions:**
- The GUI runs as a standalone `.exe` built with PyInstaller — no Python installation required for end users.
- Inference runs in a **separate portable Python process** (`worker_process.py`) that communicates over JSON-RPC via stdio. This keeps the GUI responsive and allows the heavy ML runtime to be independently updated.
- On first launch the app bootstraps a portable Python 3.11 environment with PyTorch and `bs-roformer-infer` into `%LOCALAPPDATA%\BSRoFormer Studio\runtime\`.

## Requirements

- Windows 10 or 11
- An NVIDIA GPU with CUDA support is strongly recommended for practical performance; CPU fallback is supported but slow

## Development Setup

```bat
git clone https://github.com/your-username/bs-roformer-infer-gui
cd bs-roformer-infer-gui

:: Pull the inference engine submodule
git submodule update --init --recursive

:: Create a virtual environment and install dev dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

:: Run from source
python src/app/main.py
```

## Linting & Type Checking

```bat
:: Linter
.venv\Scripts\ruff check src/

:: Type checker (strict basedpyright)
.venv\Scripts\basedpyright
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
3. Ensure `ruff check src/` and `basedpyright` both pass with zero errors
4. Open a pull request

## License

[GPL-3.0](LICENSE)
