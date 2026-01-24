"""Tests for clean.py."""
from mb2docx.clean import clean_ai_paste


def test_clean_removes_fences_and_blockquotes():
    """Test that code fences and blockquotes are removed."""
    raw = """```md
> # TITLE
> - a
> - b
```"""
    cleaned = clean_ai_paste(raw)
    assert "```" not in cleaned
    assert cleaned.startswith("# TITLE")
    assert "- a" in cleaned


def test_clean_removes_zero_width_chars():
    """Test that zero-width characters are removed."""
    raw = "Hello\u200bWorld\u200cTest\u200d"
    cleaned = clean_ai_paste(raw)
    assert "\u200b" not in cleaned
    assert "\u200c" not in cleaned
    assert "\u200d" not in cleaned


def test_clean_normalizes_newlines():
    """Test that Windows newlines are normalized."""
    raw = "Line1\r\nLine2\rLine3\nLine4"
    cleaned = clean_ai_paste(raw)
    assert "\r" not in cleaned
    assert cleaned == "Line1\nLine2\nLine3\nLine4"


def test_clean_collapses_blank_lines():
    """Test that excessive blank lines are collapsed."""
    raw = "Line1\n\n\n\n\n\nLine2"
    cleaned = clean_ai_paste(raw)
    assert "\n\n\n\n" not in cleaned


def test_clean_empty_input():
    """Test that empty input returns empty string."""
    assert clean_ai_paste("") == ""
    assert clean_ai_paste("   ") == ""
