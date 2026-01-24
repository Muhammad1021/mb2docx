"""Clean AI paste artifacts from markdown text."""
from __future__ import annotations

import re
import unicodedata

_FENCE_LINE_RE = re.compile(r"^\s*```(?:\w+)?\s*$")


def clean_ai_paste(text: str) -> str:
    """Normalize typical AI markdown-box paste artifacts.

    - Normalizes newlines
    - Removes code fences (``` / ```md)
    - Removes leading blockquote markers (> )
    - Strips zero-width formatting chars (category Cf)
    - Collapses extreme blank line runs
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove fence lines
    lines = text.split("\n")
    lines = [ln for ln in lines if not _FENCE_LINE_RE.match(ln)]
    text = "\n".join(lines)

    # Remove leading blockquote markers
    text = re.sub(r"(?m)^\s*>\s?", "", text)

    # Remove zero-width / formatting chars
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")

    # Trim trailing whitespace per line
    text = re.sub(r"(?m)[ \t]+$", "", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text.strip()
