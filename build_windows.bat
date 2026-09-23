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

echo Installing build dependencies...
.\.venv\Scripts\python.exe -m pip install -r dev-requirements.txt
.\.venv\Scripts\python.exe -m pip install pyinstaller

echo Running PyInstaller...
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed ^
    --name "BS-RoFormer-Infer Studio" ^
    --icon="resources\icons\app.ico" ^
    --paths src ^
    --add-data "resources;resources" ^
    --add-data "src\app;app" ^
    --collect-data sv_ttk ^
    --collect-data tkinter ^
    src\app\main.py

echo.
echo Build finished! Output directory: dist\BS-RoFormer-Infer Studio
