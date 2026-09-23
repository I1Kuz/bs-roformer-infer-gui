@echo off
if not exist ".venv\Scripts\python.exe" goto no_venv

set PYTHONPATH=src
start "" ".\.venv\Scripts\pythonw.exe" -m app.main
goto :eof

:no_venv
echo [ERROR] Virtual environment (.venv) not found.
echo Please run 'install_windows.bat' first to set up the environment.
pause
