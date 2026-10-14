@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   BS-RoFormer Infer Studio - Windows Setup
echo ========================================================
echo.

:: 1. Check for Python virtual environment or compatible Python installation
if exist ".venv\Scripts\python.exe" (
    echo [1/4] Existing virtual environment (.venv) found.
) else (
    set "PYTHON_CMD="

    :: Check py launcher for Python 3.12 or 3.13
    where py >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        py -3.12 -c "import sys; exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
        if !ERRORLEVEL! equ 0 (
            set "PYTHON_CMD=py -3.12"
        ) else (
            py -3.13 -c "import sys; exit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>nul
            if !ERRORLEVEL! equ 0 set "PYTHON_CMD=py -3.13"
        )
    )

    :: Check default python in PATH
    if not defined PYTHON_CMD (
        where python >nul 2>nul
        if !ERRORLEVEL! equ 0 (
            python -c "import sys; exit(0 if (3, 12) <= sys.version_info < (3, 14) else 1)" >nul 2>nul
            if !ERRORLEVEL! equ 0 set "PYTHON_CMD=python"
        )
    )

    if not defined PYTHON_CMD (
        echo [ERROR] Compatible 64-bit Python 3.12 or 3.13 was not found.
        echo BS-RoFormer Infer Studio requires Python 3.12 or 3.13 (PyTorch does not support Python 3.14+ yet).
        echo Please install Python 3.12 from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )

    echo [1/4] Creating virtual environment (.venv) using !PYTHON_CMD!...
    !PYTHON_CMD! -m venv .venv
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 2. Upgrade pip
echo [2/4] Upgrading pip...
.\.venv\Scripts\python.exe -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Install PyTorch with CUDA 12.1 acceleration
echo [3/4] Installing PyTorch with CUDA 12.1 support...
.\.venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install PyTorch with CUDA 12.1 support.
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Install GUI dependencies and bs-roformer-infer
echo [4/4] Installing application dependencies...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install application dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo   Setup completed successfully!
echo   You can now launch the app with: run_windows.bat
echo ========================================================
pause
