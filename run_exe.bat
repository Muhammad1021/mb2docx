@echo off
cd /d "%~dp0"
if exist "dist\mb2docx-gui.exe" (
    start "" "dist\mb2docx-gui.exe"
) else (
    echo EXE not found. Build it first with: build_exe.bat
    pause
)
