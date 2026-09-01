@echo off
echo Building (BS-RoFormer-Infer) Studio...
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "BS-RoFormer-Infer Studio" --icon="resources\icons\app.ico" --paths src --add-data "resources;resources" --add-data "src\app\inference\worker_process.py;app\inference" --collect-data sv_ttk --collect-data tkinter src\app\main.py
echo Build finished! The executable is in the dist/ folder.
