@echo off
setlocal

echo ========================================================
echo   BS-RoFormer Infer Studio - Setup (uv)
echo ========================================================
echo.

where.exe uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv is required but could not be found.
    echo Please install uv: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo Synchronizing dependencies via uv sync (Python 3.12 with CUDA acceleration)...
uv sync --python 3.12 --no-dev
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to synchronize dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo   Setup completed successfully with uv!
echo   You can now launch the app with: run_windows.bat
echo ========================================================
pause
