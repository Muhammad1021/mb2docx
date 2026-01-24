#!/usr/bin/env python3
"""Direct launcher for the GUI application."""
import sys
import traceback
from pathlib import Path

def write_error_log(msg: str) -> None:
    """Write error to a log file in the same directory as the executable."""
    try:
        if getattr(sys, 'frozen', False):
            log_path = Path(sys.executable).parent / 'mb2docx_error.log'
        else:
            log_path = Path(__file__).parent / 'mb2docx_error.log'
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(msg)
    except Exception:
        pass

if __name__ == "__main__":
    try:
        from mb2docx.gui import main
        main()
    except Exception as e:
        error_msg = f"Error: {e}\n\n{traceback.format_exc()}"
        write_error_log(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
