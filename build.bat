@echo off
echo Installing Dependencies...
pip install pyinstaller pywin32
echo.
echo Building PROMS...
pyinstaller --noconfirm --onefile --windowed --name "PROMS" --icon="icon.ico" --add-data "style.qss;." --add-data "tick.svg;." --add-data "down_arrow.svg;." --add-data "icon.ico;." main.py
echo.
echo ==============================================
echo Build Complete! 
echo Your new executable is located in the "dist" folder.
echo You can copy "dist\PROMS.exe" to your Network Shared Folder.
echo ==============================================
pause
