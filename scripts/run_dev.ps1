Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
uv sync
uv run mb2docx-gui
