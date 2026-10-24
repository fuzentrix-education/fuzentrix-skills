"""Readable views. Every JSON file a person might need gets a Markdown twin and an HTML page
generated from it, so the readable version always matches the data."""
from __future__ import annotations

import html
import re
from pathlib import Path


def config_note(bundle) -> str:
    config = bundle.manifest.get("config", {})
    if config.get("draft"):
        return "_DRAFT: built with minimal skill defaults, not the Fuzentrix Configuration Pack._"
    return f"_Configuration Pack {config.get('version')}_"


def bullet_list(items) -> str:
    items = [str(i) for i in items if str(i).strip()]
    return "\n".join(f"- {i}" for i in items) if items else "- None"


def as_spoken(bundle):
    """How a script line is said: the same clean-up the Teleprompter Script uses (no bullets, ✔ or '>')."""
    from . import settings
    from .teleprompter import clean

    symbols = settings.get(bundle, "teleprompter_symbols")
    return lambda text: clean(text, symbols)


# --- Markdown → HTML for the subset these views use ------------------------------

def gallery_page(title: str, body: str) -> str:
    """A review page of images (internal, so in the report style, not the brand)."""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>" + html.escape(title) + "</title><style>"
            "body{font-family:system-ui,sans-serif;margin:2rem;color:#13213c}figure{display:inline-block;width:46%;margin:1%;vertical-align:top}"
            "img{width:100%;border:1px solid #dce7f4;border-radius:8px;background:#fff}figcaption{font-size:14px;margin-top:.4rem}</style></head>"
            f"<body><h1>{html.escape(title)}</h1>{body}</body></html>\n")


def write_pair(stem: Path, markdown: str, title: str) -> None:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".md").write_text(markdown, encoding="utf-8")
    stem.with_suffix(".html").write_text(to_html(markdown, title), encoding="utf-8")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", text)
    return text


def to_html(markdown: str, title: str) -> str:
    body, in_list, table = [], False, []
    lines = markdown.splitlines() + [""]
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                table.append(cells)
            continue
        if table:
            head, rows = table[0], table[1:]
            body.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                        + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table>")
            table = []
        if line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_inline(line[2:])}</li>")
            continue
        if in_list:
            body.append("</ul>")
            in_list = False
        m = re.match(r"^(#{1,4}) (.*)", line)
        if m:
            n = len(m.group(1))
            body.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif line.startswith("> "):
            body.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
        elif line:
            body.append(f"<p>{_inline(line)}</p>")
    if in_list:
        body.append("</ul>")
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title><style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#1d2433}"
        "h1,h2,h3{color:#0b3d91}blockquote{margin:.5rem 0;padding:.5rem 1rem;border-left:4px solid #2f6fde;background:#eef4ff}"
        "code{background:#f2f4f7;padding:0 .25rem;border-radius:3px}li{margin:.2rem 0}"
        "table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dce7f4;padding:.35rem .5rem;text-align:left;vertical-align:top}th{background:#eef4ff}"
        "</style></head><body>\n" + "\n".join(body) + "\n</body></html>\n"
    )
