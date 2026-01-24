@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo First run: Setting up environment...
    uv sync
)
uv run mb2docx --help
echo.
echo Type: uv run mb2docx [OPTIONS] to use CLI
cmd /k
