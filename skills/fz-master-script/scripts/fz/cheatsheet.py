"""fz-cheatsheet: a revision page for a Topic, as LMS-ready HTML plus its images.

The Host App writes the content as typed blocks; the builder checks it (sources, key terms, images,
voice) and renders consistent HTML. 'semantic' HTML (the default) needs no CSS or JavaScript, so it
survives strict LMS editors; 'styled' adds a scoped style block for LMSs that allow it.
"""
from __future__ import annotations

import html
import re
import shutil

from . import settings
from .bundle import read_json, write_json
from .problems import Rejected

BLOCKS = ("paragraph", "bullets", "table", "code", "key_idea", "example", "mistakes", "image", "reveal")
IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")
FILLER = (
    "in today's", "fast-paced", "delve", "it is important to note", "it's important to note", "in conclusion",
    "in summary", "embark", "unlock the", "game-changer", "game changer", "seamless", "leverage", "landscape",
    "realm", "tapestry", "navigate the", "moreover", "furthermore", "dive deep", "dive into", "let's dive",
    "plays a crucial role", "plays a vital role", "a testament to", "ever-evolving", "cutting-edge",
)


# --- draft ----------------------------------------------------------------------------

def draft(bundle) -> dict:
    from .topic import masters

    sections, terms = [], []
    for vid, m in masters(bundle).items():
        teach = [s["id"] for s in m["segments"] if s["section"] in ("explanation", "teaser")] or [s["id"] for s in m["segments"]]
        sections.append({"heading": m["video"].get("title", vid), "source": [{"video": vid, "segments": teach}], "blocks": []})
        terms += [{"term": t["term"], "video": vid} for t in m.get("key_terms") or []]
    return {"title": bundle.manifest["topic"]["title"], "intro": "", "sections": sections, "quick_revision": [],
            "key_terms_to_cover": terms}


# --- checks ---------------------------------------------------------------------------

def _texts(data: dict):
    """Every piece of prose in the cheatsheet, with a label saying where it is."""
    yield "title", data.get("title", "")
    yield "intro", data.get("intro", "")
    for i, s in enumerate(data.get("sections") or [], 1):
        where = f"section {i} ({s.get('heading', '')})"
        yield f"{where} heading", s.get("heading", "")
        for j, b in enumerate(s.get("blocks") or [], 1):
            label = f"{where} block {j}"
            for key in ("text", "title", "question", "answer", "caption", "alt"):
                if b.get(key):
                    yield label, b[key]
            for item in b.get("items") or []:
                yield label, item
            for row in [b.get("columns") or []] + (b.get("rows") or []):
                for cell in row:
                    yield label, cell
    for item in data.get("quick_revision") or []:
        yield "quick revision", item


def submit(bundle, data: dict) -> None:
    from .topic import masters

    all_masters = masters(bundle)
    images = bundle.path("cheatsheet", "images")
    banned = FILLER + tuple(p.lower() for p in settings.get(bundle, "cheatsheet_banned_phrases"))
    problems = []
    if not str(data.get("title", "")).strip():
        problems.append("'title' is empty.")
    sections = data.get("sections") or []
    if not sections:
        problems.append("'sections' is empty.")
    for i, s in enumerate(sections, 1):
        where = f"section {i} ({s.get('heading', '')})"
        if not str(s.get("heading", "")).strip():
            problems.append(f"section {i}: 'heading' is empty.")
        if not s.get("source"):
            problems.append(f"{where}: 'source' must name the Video and Segments it summarises.")
        for src in s.get("source") or []:
            vid = src.get("video")
            if vid not in all_masters:
                problems.append(f"{where}: {vid} is not in this Topic ({', '.join(all_masters)}).")
                continue
            known = {seg["id"] for seg in all_masters[vid]["segments"]}
            for sid in src.get("segments") or []:
                if sid not in known:
                    problems.append(f"{where}: segment {sid} is not in {vid}.")
        if not s.get("blocks"):
            problems.append(f"{where}: has no blocks.")
        for j, b in enumerate(s.get("blocks") or [], 1):
            problems += _check_block(f"{where} block {j}", b, images)
    if not data.get("quick_revision"):
        problems.append("'quick_revision' must list the few lines a student should remember.")
    if settings.get(bundle, "cheatsheet_require_mistakes") and not any(
            b.get("type") == "mistakes" for s in sections for b in s.get("blocks") or []):
        problems.append("Add at least one 'mistakes' block: the misconceptions students actually have.")
    text = " ".join(str(t) for _, t in _texts(data)).lower()
    for vid, m in all_masters.items():
        for t in m.get("key_terms") or []:
            if t["term"].lower() not in text:
                problems.append(f"Key term '{t['term']}' from {vid} is not covered.")
    for label, t in _texts(data):
        low = str(t).lower()
        for phrase in banned:
            if phrase in low:
                problems.append(f"{label}: \"{phrase}\" reads as filler; say the fact directly, the way the Instructor would.")
    if problems:
        raise Rejected(problems)
    data = {k: v for k, v in data.items() if k != "key_terms_to_cover"}
    write_json(bundle.path("cheatsheet", "cheatsheet.json"), data)
    bundle.manifest["stages"]["cheatsheet"] = {"status": "in_progress"}
    bundle.manifest["gates"].get("3", {}).pop("cheatsheet", None)


def _check_block(label: str, b: dict, images) -> list:
    kind = b.get("type")
    if kind not in BLOCKS:
        return [f"{label}: type must be one of {', '.join(BLOCKS)}."]
    need = {"paragraph": ["text"], "key_idea": ["text"], "example": ["text"], "code": ["code"],
            "bullets": ["items"], "mistakes": ["items"], "table": ["columns", "rows"],
            "image": ["file", "alt"], "reveal": ["question", "answer"]}[kind]
    problems = [f"{label} ({kind}): '{k}' is empty." for k in need if not b.get(k)]
    if kind == "table" and b.get("columns") and any(len(r) != len(b["columns"]) for r in b.get("rows") or []):
        problems.append(f"{label} (table): every row needs {len(b['columns'])} cells.")
    if kind == "image" and b.get("file"):
        name = str(b["file"])
        if "/" in name or "\\" in name or not name.lower().endswith(IMAGE_TYPES):
            problems.append(f"{label} (image): 'file' must be a file name in cheatsheet/images/ ({', '.join(IMAGE_TYPES)}).")
        elif not (images / name).exists():
            problems.append(f"{label} (image): {name} is not in cheatsheet/images/; save the generated image there first.")
        if len(str(b.get("alt", "")).split()) < 3:
            problems.append(f"{label} (image): alt text must describe the image in a few words, for students using screen readers.")
    return problems


# --- rendering ----------------------------------------------------------------------------

def _inline(text: str) -> str:
    out = html.escape(str(text))
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def _block(b: dict, base: str, styled: bool) -> str:
    kind = b["type"]
    cls = (lambda name: f' class="fz-{name}"') if styled else (lambda name: "")
    if kind == "paragraph":
        return f"<p>{_inline(b['text'])}</p>"
    if kind == "bullets":
        return "<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in b["items"]) + "</ul>"
    if kind == "table":
        head = "".join(f"<th>{_inline(c)}</th>" for c in b["columns"])
        rows = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in b["rows"])
        return f"<table{cls('table')}><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"
    if kind == "code":
        return f"<pre><code>{html.escape(b['code'])}</code></pre>"
    if kind == "key_idea":
        return f"<p{cls('key')}><strong>Key idea:</strong> {_inline(b['text'])}</p>"
    if kind == "example":
        title = f" {_inline(b['title'])}" if b.get("title") else ""
        return f"<p{cls('example')}><strong>Example:{title}</strong> {_inline(b['text'])}</p>"
    if kind == "mistakes":
        return f"<p{cls('mistakes-title')}><strong>Common mistakes</strong></p><ul{cls('mistakes')}>" + \
               "".join(f"<li>{_inline(i)}</li>" for i in b["items"]) + "</ul>"
    if kind == "image":
        caption = f"<figcaption>{_inline(b['caption'])}</figcaption>" if b.get("caption") else ""
        return f'<figure><img src="{html.escape(base + b["file"])}" alt="{html.escape(b["alt"])}">{caption}</figure>'
    if kind == "reveal":
        return f"<details{cls('reveal')}><summary>{_inline(b['question'])}</summary><p>{_inline(b['answer'])}</p></details>"
    raise ValueError(kind)


STYLE = """<style>
.fz-cheatsheet{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#13213c;line-height:1.55}
.fz-cheatsheet h2{color:#0b3d91}.fz-cheatsheet h3{color:#1d5fd6;border-bottom:2px solid #e3ecff;padding-bottom:.2em}
.fz-cheatsheet code{background:#eef3ff;padding:0 .25em;border-radius:3px}
.fz-key{background:#e8f0ff;border-left:4px solid #1d5fd6;padding:.6em .9em;border-radius:6px}
.fz-example{background:#f6f8fb;padding:.6em .9em;border-radius:6px}
.fz-mistakes li::marker{content:"✗  ";color:#c62828}
.fz-table{border-collapse:collapse}.fz-table th,.fz-table td{border:1px solid #d4dcec;padding:.4em .7em}.fz-table th{background:#eef3ff}
.fz-reveal{border:1px solid #d4dcec;border-radius:6px;padding:.5em .8em;margin:.6em 0}.fz-reveal summary{cursor:pointer;font-weight:600;color:#1d5fd6}
</style>"""


def render(bundle, data: dict, styled: bool) -> str:
    base = settings.get(bundle, "cheatsheet_image_base_url")
    parts = [f"<h2>{_inline(data['title'])}</h2>"]
    if data.get("intro"):
        parts.append(f"<p>{_inline(data['intro'])}</p>")
    for s in data["sections"]:
        parts.append(f"<h3>{_inline(s['heading'])}</h3>")
        parts += [_block(b, base, styled) for b in s["blocks"]]
    parts.append("<h3>Quick revision</h3><ul>" + "".join(f"<li>{_inline(i)}</li>" for i in data["quick_revision"]) + "</ul>")
    body = "\n".join(parts)
    return f'{STYLE}\n<section class="fz-cheatsheet">\n{body}\n</section>\n' if styled else body + "\n"


def build(bundle) -> dict:
    path = bundle.path("cheatsheet", "cheatsheet.json")
    if not path.exists():
        raise Rejected("Submit the Cheatsheet first (`fz.py submit <bundle> cheatsheet <file>`).")
    data = read_json(path)
    styled = settings.get(bundle, "cheatsheet_html") == "styled"
    tid = bundle.manifest["topic"]["id"]
    fragment = render(bundle, data, styled)
    folder = bundle.path("cheatsheet")
    (folder / f"{tid}_cheatsheet.html").write_text(fragment, encoding="utf-8")
    preview = render(bundle, data, styled=True)
    (folder / "preview.html").write_text(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>Cheatsheet: {html.escape(data['title'])}</title></head>"
        f"<body style=\"max-width:860px;margin:2rem auto;padding:0 1rem\">\n{preview}</body></html>\n", encoding="utf-8")
    images = [(s["heading"], b) for s in data["sections"] for b in s["blocks"] if b["type"] == "image"]
    base = settings.get(bundle, "cheatsheet_image_base_url")
    lines = [f"# Image insertion map: {tid}", "",
             f"The cheatsheet HTML points to images at `{base}<file>`. Upload each image to the LMS, then replace that address with the uploaded image's address.", ""]
    lines += [f"- **{b['file']}** · section \"{heading}\" · alt: {b['alt']}" + (f" · caption: {b['caption']}" if b.get("caption") else "") for heading, b in images] or ["- No images."]
    (folder / "insertion_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    bundle.manifest["stages"]["cheatsheet"] = {"status": "built", "mode": "styled" if styled else "semantic"}
    bundle.manifest["gates"].get("3", {}).pop("cheatsheet", None)
    bundle.log("cheatsheet built")
    return {"sections": len(data["sections"]), "images": len(images), "mode": "styled" if styled else "semantic"}
