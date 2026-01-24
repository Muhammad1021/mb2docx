# Build a Windows GUI executable (no console window) using PyInstaller.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot\..

Write-Host "==> Syncing dependencies (includes dev group by default)"
uv sync

Write-Host "==> Building EXE via PyInstaller"
uv run pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name mb2docx-gui `
    --noconsole `
    --add-data "src/mb2docx;mb2docx" `
    launcher.py

Write-Host "==> Done. Output in .\dist\mb2docx-gui.exe"

Pop-Location
