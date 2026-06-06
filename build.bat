@echo off
echo Installing PyInstaller...
pip install pyinstaller
echo.
echo Building PCAS...
pyinstaller --noconfirm --onefile --windowed --name "PCAS" --icon="icon.ico" --add-data "style.qss;." --add-data "tick.svg;." --add-data "icon.ico;." main.py
echo.
echo ==============================================
echo Build Complete! 
echo Your new executable is located in the "dist" folder.
echo You can copy "dist\PCAS.exe" to your Network Shared Folder.
echo ==============================================
pause
