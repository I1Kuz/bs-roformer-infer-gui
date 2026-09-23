@echo off
echo Building (BS-RoFormer-Infer) Studio...
.\venv\Scripts\python.exe -m pip install -r dev-requirements.txt
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name "BS-RoFormer-Infer Studio" --icon="resources\icons\app.ico" --paths src --add-data "resources;resources" --add-data "src\app\inference\worker_process.py;app\inference" --collect-data sv_ttk --collect-data tkinter src\app\main.py
echo Build finished!
