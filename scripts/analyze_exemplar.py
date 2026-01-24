#!/usr/bin/env python3
"""
DOCX Exemplar Analyzer - V9 Forensic Analysis
==============================================
Extracts EXACT formatting values from a gold-standard DOCX file and generates
ready-to-paste Python configuration code.

Usage:
    python analyze_exemplar.py path/to/exemplar.docx [--type cv|cl]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

from docx import Document
from docx.oxml.ns import qn


def twips_to_pt(twips: Optional[str]) -> Optional[float]:
    """Convert twips string to points (20 twips = 1 point)."""
    if twips is None:
        return None
    try:
        return int(twips) / 20.0
    except (ValueError, TypeError):
        return None


def safe_pt(length_obj) -> Optional[float]:
    """Safely extract points from a Length object."""
    if length_obj is None:
        return None
    if hasattr(length_obj, 'pt'):
        return round(length_obj.pt, 1)
    return None


def safe_inches(length_obj) -> Optional[float]:
    """Safely extract inches from a Length object."""
    if length_obj is None:
        return None
    if hasattr(length_obj, 'inches'):
        return round(length_obj.inches, 3)
    return None


def resolve_effective_font_size(paragraph, run) -> float:
    """Traverse style hierarchy to find actual font size."""
    if run.font.size is not None:
        return run.font.size.pt
    style = paragraph.style
    while style:
        if style.font.size is not None:
            return style.font.size.pt
        style = style.base_style
    return 11.0


def resolve_effective_bold(paragraph, run) -> bool:
    """Resolve tri-state bold through inheritance."""
    if run.font.bold is not None:
        return run.font.bold
    style = paragraph.style
    while style:
        if style.font.bold is not None:
            return style.font.bold
        style = style.base_style
    return False


def resolve_effective_italic(paragraph, run) -> bool:
    """Resolve tri-state italic through inheritance."""
    if run.font.italic is not None:
        return run.font.italic
    style = paragraph.style
    while style:
        if style.font.italic is not None:
            return style.font.italic
        style = style.base_style
    return False


def analyze_separator_pattern(paragraph) -> Literal["TAB", "PIPE", "NONE"]:
    """Distinguish 'Title [TAB] Date' from 'Title | Date' patterns."""
    text = paragraph.text
    tab_stops = paragraph.paragraph_format.tab_stops

    has_tab_chars = '\t' in text
    has_tab_stops = len(tab_stops) > 0
    has_pipes = '|' in text

    if has_tab_chars and has_tab_stops:
        return "TAB"
    elif has_pipes:
        return "PIPE"
    else:
        return "NONE"


def detect_paragraph_role(para, idx: int) -> str:
    """Infer paragraph role from formatting and position."""
    text = para.text.strip()
    if not text:
        return "empty"

    pf = para.paragraph_format
    alignment = str(pf.alignment) if pf.alignment else "LEFT"

    font_size = 11.0
    is_bold = False
    is_italic = False
    if para.runs:
        font_size = resolve_effective_font_size(para, para.runs[0])
        is_bold = resolve_effective_bold(para, para.runs[0])
        is_italic = resolve_effective_italic(para, para.runs[0])

    pPr = para._element.pPr
    is_list = pPr is not None and pPr.numPr is not None

    if idx == 0 and font_size >= 14 and is_bold and "CENTER" in alignment:
        return "name"
    if idx == 1 and "CENTER" in alignment and ('|' in text or '@' in text):
        return "contact"
    if text.isupper() and is_bold and 1 <= len(text.split()) <= 6 and not is_list:
        return "section_heading"
    if is_bold and not is_italic and '|' in text:
        return "job_entry"
    if is_italic and '|' in text:
        return "institution"
    if is_list:
        return "bullet"
    return "body"


def analyze_document(docx_path: Path) -> Dict[str, Any]:
    """Perform full forensic analysis of a DOCX file."""
    doc = Document(docx_path)
    section = doc.sections[0]

    result = {
        'page_width_inches': safe_inches(section.page_width) or 8.5,
        'page_height_inches': safe_inches(section.page_height) or 11.0,
        'margin_top_inches': safe_inches(section.top_margin) or 1.0,
        'margin_bottom_inches': safe_inches(section.bottom_margin) or 1.0,
        'margin_left_inches': safe_inches(section.left_margin) or 1.0,
        'margin_right_inches': safe_inches(section.right_margin) or 1.0,
        'job_entry_separator': 'NONE',
        'paragraphs': []
    }

    for i, para in enumerate(doc.paragraphs):
        role = detect_paragraph_role(para, i)

        pf = para.paragraph_format
        space_before = None
        space_after = None
        pPr = para._element.pPr
        if pPr is not None:
            spacing = pPr.find(qn('w:spacing'))
            if spacing is not None:
                space_before = twips_to_pt(spacing.get(qn('w:before')))
                space_after = twips_to_pt(spacing.get(qn('w:after')))

        font_size = 11.0
        is_bold = False
        is_italic = False
        font_name = "Calibri"
        if para.runs:
            run = para.runs[0]
            font_size = resolve_effective_font_size(para, run)
            is_bold = resolve_effective_bold(para, run)
            is_italic = resolve_effective_italic(para, run)
            if run.font.name:
                font_name = run.font.name

        separator = analyze_separator_pattern(para)
        if role == 'job_entry' and separator != 'NONE':
            result['job_entry_separator'] = separator

        result['paragraphs'].append({
            'index': i,
            'role': role,
            'text_preview': para.text[:50] if para.text else '',
            'font_size_pt': font_size,
            'bold': is_bold,
            'italic': is_italic,
            'space_before_pt': space_before,
            'space_after_pt': space_after,
            'separator': separator,
        })

    return result


def generate_config_code(analysis: Dict[str, Any], var_name: str = "CV_STYLE") -> str:
    """Generate ready-to-paste Python configuration code."""
    paragraphs = analysis['paragraphs']

    def get_first_by_role(role):
        for p in paragraphs:
            if p['role'] == role:
                return p
        return None

    name = get_first_by_role('name')
    contact = get_first_by_role('contact')
    section = get_first_by_role('section_heading')
    job = get_first_by_role('job_entry')
    inst = get_first_by_role('institution')
    body = get_first_by_role('body')
    bullet = get_first_by_role('bullet')

    content_width = analysis['page_width_inches'] - analysis['margin_left_inches'] - analysis['margin_right_inches']

    return f'''# ============================================================================
# GENERATED BY analyze_exemplar.py
# Job Entry Separator: {analysis['job_entry_separator']}
# Margins: {analysis['margin_left_inches']}" all sides
# ============================================================================

{var_name} = DocxStyleConfig(
    font_name="Calibri",
    name_size_pt={int(name['font_size_pt']) if name else 18},
    contact_size_pt={int(contact['font_size_pt']) if contact else 10},
    section_heading_size_pt={int(section['font_size_pt']) if section else 12},
    body_size_pt={int(body['font_size_pt']) if body else 11},
    margin_inches={analysis['margin_left_inches']:.2f},
    tab_stop_inches={content_width:.1f},
    job_entry_separator="{analysis['job_entry_separator']}",
    space_after_name_pt={int(name['space_after_pt'] or 0) if name else 0},
    space_after_contact_pt={int(contact['space_after_pt'] or 10) if contact else 10},
    space_before_section_pt={int(section['space_before_pt'] or 12) if section else 12},
    space_after_section_pt={int(section['space_after_pt'] or 6) if section else 6},
    space_after_job_entry_pt={int(job['space_after_pt'] or 0) if job else 0},
    space_after_institution_pt={int(inst['space_after_pt'] or 5) if inst else 5},
    space_after_paragraph_pt={int(body['space_after_pt'] or 10) if body else 10},
    space_after_bullet_pt={int(bullet['space_after_pt'] or 0) if bullet else 0},
    space_after_last_bullet_pt=10,
)
'''


def main():
    parser = argparse.ArgumentParser(description="Analyze DOCX exemplar")
    parser.add_argument("docx_path", type=Path, help="Path to gold-standard DOCX")
    parser.add_argument("--type", choices=["cv", "cl"], default="cv")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.docx_path.exists():
        print(f"ERROR: File not found: {args.docx_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing: {args.docx_path}")
    print("=" * 60)

    analysis = analyze_document(args.docx_path)

    print(f"\nPAGE SETUP:")
    print(f"  Margins: {analysis['margin_left_inches']}\" all sides")
    print(f"\nJOB ENTRY FORMAT:")
    print(f"  Separator: {analysis['job_entry_separator']}")

    if args.json:
        print("\n" + json.dumps(analysis, indent=2))
    else:
        var_name = "CV_STYLE" if args.type == "cv" else "CL_STYLE"
        print("\n" + "=" * 60)
        print("COPY THIS INTO src/mb2docx/config.py")
        print("=" * 60)
        print(generate_config_code(analysis, var_name))


if __name__ == "__main__":
    main()
