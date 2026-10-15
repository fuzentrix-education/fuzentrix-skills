"""Stage 0: read an Instructor Script file into numbered lines."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .problems import Rejected

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

MARKERS = [
    ("slide", re.compile(r"^slide\s*(?:[-–—:]|\d)", re.IGNORECASE)),
    ("animation-start", re.compile(r"^animation\s+start\b", re.IGNORECASE)),
    ("animation-end", re.compile(r"^animation\s+end\b", re.IGNORECASE)),
    ("visual", re.compile(r"^\[\s*visual\s*:", re.IGNORECASE)),
]


def read_script(path) -> list:
    """Return the script as a list of paragraphs, in order, without blank lines.

    Each paragraph is {"text": str, "bold": bool, "marker": str|None}.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        raw = path.read_text(encoding="utf-8-sig")
        paragraphs = [{"text": line} for line in raw.splitlines()]
    elif suffix == ".docx":
        paragraphs = _read_docx(path)
    elif suffix == ".pdf":
        paragraphs = _read_pdf(path)
    else:
        raise Rejected(f"Unsupported Instructor Script format '{suffix}'. Use .docx, .pdf, .md or .txt (convert old .doc files to .docx first).")
    return [p for p in (_clean(p) for p in paragraphs) if _has_content(p["text"])]


def _has_content(text: str) -> bool:
    """Lines with no letters or digits (separators, a stray '>') carry nothing to say or show."""
    return any(ch.isalnum() for ch in text)


def _clean(paragraph: dict) -> dict:
    text = " ".join(paragraph["text"].split())
    marker = next((name for name, rx in MARKERS if rx.match(text)), None)
    return {"text": text, "bold": bool(paragraph.get("bold")), "marker": marker}


def tags(line: dict) -> list:
    out = []
    if line.get("bold"):
        out.append("bold")
    if line.get("marker"):
        out.append(line["marker"])
    return out


def number_lines(paragraphs: list) -> list:
    return [dict(p, id=f"L{i}") for i, p in enumerate(paragraphs, 1)]


# --- .pdf -------------------------------------------------------------------

_SENTENCE_END = tuple(".?!:;\"'”’)]…")


def _read_pdf(path: Path) -> list:
    """PDFs wrap long sentences onto several lines. A line is a wrap (and is joined to the
    next) when it is nearly full-width and doesn't end like a sentence."""
    try:
        from pypdf import PdfReader
        raw = [line.rstrip() for page in PdfReader(str(path)).pages for line in (page.extract_text() or "").split("\n")]
    except Exception as e:  # pypdf raises many types for damaged files
        raise Rejected(f"{path.name} is not a readable PDF ({e.__class__.__name__}).")
    lengths = sorted(len(l) for l in raw if l.strip())
    if not lengths:
        return []
    full_width = 0.8 * lengths[int(0.9 * (len(lengths) - 1))]
    paragraphs, current, wraps = [], None, False
    for line in raw:
        if not line.strip():
            current, wraps = None, False
            continue
        if current is not None and wraps:
            current["text"] += " " + line.strip()
        else:
            current = {"text": line.strip(), "bold": False}
            paragraphs.append(current)
        wraps = len(line) >= full_width and not line.strip().endswith(_SENTENCE_END)
    return paragraphs


# --- .docx ------------------------------------------------------------------

def _read_docx(path: Path) -> list:
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError):
        raise Rejected(f"{path.name} is not a readable .docx file.")
    body = ElementTree.fromstring(xml).find(f"{W}body")
    out = []
    for block in body:
        if block.tag == f"{W}p":
            out.extend(_docx_paragraph(block))
        elif block.tag == f"{W}tbl":
            for row in block.iter(f"{W}tr"):
                cells = []
                for cell in row.iter(f"{W}tc"):
                    cells.append(" ".join(p["text"] for para in cell.iter(f"{W}p") for p in _docx_paragraph(para)))
                if any(c.strip() for c in cells):
                    out.append({"text": " | ".join(c.strip() for c in cells), "bold": False})
    return out


def _docx_paragraph(p) -> list:
    """One w:p can hold several visual lines separated by soft breaks (w:br)."""
    pieces = [[]]  # list of (text, bold) runs per visual line
    for run in p.iter(f"{W}r"):
        bold = _run_is_bold(run)
        for child in run:
            if child.tag == f"{W}t":
                pieces[-1].append((child.text or "", bold))
            elif child.tag == f"{W}tab":
                pieces[-1].append((" ", bold))
            elif child.tag in (f"{W}br", f"{W}cr"):
                pieces.append([])
    out = []
    for runs in pieces:
        text = "".join(t for t, _ in runs)
        visible = [b for t, b in runs if t.strip()]
        out.append({"text": text, "bold": bool(visible) and all(visible)})
    return out


def _run_is_bold(run) -> bool:
    rpr = run.find(f"{W}rPr")
    if rpr is None:
        return False
    b = rpr.find(f"{W}b")
    if b is None:
        return False
    return b.get(f"{W}val", "true").lower() not in ("0", "false", "off")
