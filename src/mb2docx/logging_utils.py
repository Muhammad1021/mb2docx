"""Logging configuration with rotating file handler."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_dir: Path, *, verbose: bool = False) -> None:
    """Configure logging with console and rotating file handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "mb2docx.log"

    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()

    # Clear existing handlers
    root.handlers.clear()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)
