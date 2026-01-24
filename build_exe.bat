@echo off
cd /d "%~dp0"
echo Building standalone EXE...
uv run python -m PyInstaller --onefile --windowed --name mb2docx-gui --add-data "src/mb2docx;mb2docx" launcher.py
echo.
echo Build complete! Check dist/mb2docx-gui.exe
pause
