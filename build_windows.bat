@echo off
setlocal

echo ========================================================
echo   Building BS-RoFormer Infer Studio Executable
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please run install_windows.bat first.
    pause
    exit /b 1
)

where.exe uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Syncing build dependencies via uv sync...
    uv sync
) else (
    echo Installing build dependencies...
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
)
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install build dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo Running PyInstaller...
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed ^
    --name "BS-RoFormer-Infer Studio" ^
    --icon="resources\icons\app.ico" ^
    --paths src ^
    --add-data "resources;resources" ^
    --add-data "src\app;app" ^
    --collect-data sv_ttk ^
    src\app\main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] PyInstaller build failed with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Build finished! Output directory: dist\BS-RoFormer-Infer Studio
