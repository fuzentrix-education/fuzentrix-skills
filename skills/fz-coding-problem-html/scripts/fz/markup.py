"""Fuzentrix markup: the light marks content is written in, turned into LMS HTML in the form the LMS HTML Policy
requires. Marks: `code`, **bold**, [text](https://link), fenced code blocks (```python … ```), lists ("- " or
"1. " at the start of each line), and tables (| a | b | with a |---| line under the header). Blank lines separate
paragraphs; a single line break stays a line break."""
from __future__ import annotations

import html
import re

from . import lmspolicy

FENCE = re.compile(r"```([A-Za-z0-9+#-]*)[ \t]*\n(.*?)\n?```", re.S)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)")
BULLET = re.compile(r"^\s*[-*] ")
NUMBER = re.compile(r"^\s*\d+[.)] ")


def inline(text: str) -> str:
    """One line of marks as HTML: escaped text with <code>, <strong> and <a>."""
    parts, pos = [], 0
    for m in INLINE_CODE.finditer(str(text)):  # code first, so marks inside code stay literal
        parts.append(_marks(str(text)[pos:m.start()]))
        parts.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        pos = m.end()
    parts.append(_marks(str(text)[pos:]))
    return "".join(parts)


def _marks(text: str) -> str:
    out = html.escape(text, quote=False)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    return LINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', out)


def render(text: str, policy: dict) -> str:
    """A whole field of marked text as block HTML (paragraphs, lists, tables, code blocks)."""
    text = str(text).replace("\r\n", "\n")
    out, pos = [], 0
    for m in FENCE.finditer(text):
        out += _blocks(text[pos:m.start()])
        out.append(lmspolicy.code_block(policy, html.escape(m.group(2), quote=False), m.group(1)))
        pos = m.end()
    out += _blocks(text[pos:])
    return "".join(out)


def _blocks(text: str) -> list:
    out = []
    for para in [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()] if text.strip() else []:
        lines = [l.rstrip() for l in para.split("\n")]
        if all(BULLET.match(l) for l in lines):
            out.append("<ul>" + "".join("<li>" + inline(BULLET.sub("", l)) + "</li>" for l in lines) + "</ul>")
        elif all(NUMBER.match(l) for l in lines):
            out.append("<ol>" + "".join("<li>" + inline(NUMBER.sub("", l)) + "</li>" for l in lines) + "</ol>")
        elif len(lines) >= 2 and all(l.strip().startswith("|") for l in lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[1]):
            cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells(lines[0]))
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(l)) + "</tr>" for l in lines[2:])
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in lines) + "</p>")
    return out


def unmark(text: str) -> str:
    """The words without the marks a formatting pass may add (code ticks and fences, bold), for checking
    that formatting changed no words."""
    text = str(text).replace("\r\n", "\n")
    text = FENCE.sub(lambda m: m.group(2), text)
    text = INLINE_CODE.sub(r"\1", text)
    text = BOLD.sub(r"\1", text)
    return "\n".join(l.rstrip() for l in text.strip().split("\n"))
