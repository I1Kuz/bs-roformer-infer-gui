# Audio Separation Studio (BS-RoFormer-Infer)

A beautiful, lightweight, production-ready desktop UI for audio source separation based on `bs-roformer-infer`.

## Architecture
- **Lightweight GUI:** The UI is packaged as a tiny standalone executable without bundling PyTorch.
- **Smart Bootstrap:** On the first launch, the GUI will automatically download and set up a portable Python environment with PyTorch and `bs-roformer-infer` into `%LOCALAPPDATA%\BSRoFormer Studio\runtime`.
- **Background Inference:** Separation is performed asynchronously in a background worker process, keeping the UI completely responsive.

## Requirements
- Windows 10/11
- A CUDA-compatible NVIDIA GPU is highly recommended for optimal performance, though CPU fallback is supported.

## Development Setup
```bat
# Clone repository
git clone <your-repo>
cd bs-roformer-infer-gui

# Create virtual environment and install requirements
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run from source
python src/app/main.py
```

## Build Executable
To package the app into a standalone Windows `.exe` using PyInstaller:
```bat
build_windows.bat
```
The compiled executable will be located in the `dist/` directory.

## Data Storage Paths
- **Executable Location:** `C:\Program Files\BSRoFormer Studio\` (if using installer)
- **Runtime Environment:** `%LOCALAPPDATA%\BSRoFormer Studio\runtime\`
- **Model Checkpoints:** `%LOCALAPPDATA%\BSRoFormer Studio\models\`
- **Settings & Logs:** `%LOCALAPPDATA%\BSRoFormer Studio\settings\` and `logs\`
