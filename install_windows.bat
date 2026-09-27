@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   BS-RoFormer Infer Studio - Windows Setup
echo ========================================================
echo.

:: 1. Check for Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in your PATH.
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: 2. Create virtual environment if missing
if not exist ".venv" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Existing virtual environment (.venv) found.
)

:: 3. Upgrade pip
echo [2/4] Upgrading pip...
.\.venv\Scripts\python.exe -m pip install --upgrade pip

:: 4. Install PyTorch with CUDA 12.1 acceleration
echo [3/4] Installing PyTorch with CUDA 12.1 support...
.\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 5. Install GUI dependencies and core bs-roformer-infer
echo [4/4] Installing application dependencies...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if exist "bs-roformer-infer" (
    echo Installing local bs-roformer-infer module...
    .\.venv\Scripts\python.exe -m pip install -e bs-roformer-infer
)

echo.
echo ========================================================
echo   Setup completed successfully!
echo   You can now launch the app with: run_windows.bat
echo ========================================================
pause
