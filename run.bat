@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo First run: Setting up environment...
    uv sync
)
uv run mb2docx-gui
pause
