"""fz-cheatsheet: a revision page for a Topic, as LMS-ready HTML plus its images.

The Host App writes the content as typed blocks; the builder checks it (sources, key terms, images, voice) and
renders HTML that keeps to the LMS HTML Policy's cheatsheet_page rules, in the Brand Kit's colours as far as
those rules let colour through:
- where the LMS keeps inline styles: styled elements, using only the allowed properties;
- where it keeps fz-* classes: those classes, plus <topic>_theme.css for the LMS team to install once;
- otherwise: structure and the Brand Kit's icons only, and the build says so.
Reveals become <details> where the LMS keeps it, else a question-and-answer block. Images are written as
placeholders; they are generated separately and attached when uploading (insertion_map.md).
"""
from __future__ import annotations

import fnmatch
import html
import re

from . import brandkit, lmspolicy, markup, settings
from .bundle import read_json, write_json
from .problems import Rejected

BLOCKS = ("paragraph", "bullets", "table", "code", "key_idea", "example", "mistakes", "image", "reveal")
FILLER = (
    "in today's", "fast-paced", "delve", "it is important to note", "it's important to note", "in conclusion",
    "in summary", "embark", "unlock the", "game-changer", "game changer", "seamless", "leverage", "landscape",
    "realm", "tapestry", "navigate the", "moreover", "furthermore", "dive deep", "dive into", "let's dive",
    "plays a crucial role", "plays a vital role", "a testament to", "ever-evolving", "cutting-edge",
)
CONTEXT = "cheatsheet_page"


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
    banned = FILLER + tuple(p.lower() for p in settings.get(bundle, "cheatsheet_banned_phrases"))
    problems = []
    if not str(data.get("title", "")).strip():
        problems.append("'title' is empty.")
    sections = data.get("sections") or []
    if not sections:
        problems.append("'sections' is empty.")
    image_ids = []
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
            problems += _check_block(f"{where} block {j}", b, image_ids)
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


def _check_block(label: str, b: dict, image_ids: list) -> list:
    kind = b.get("type")
    if kind not in BLOCKS:
        return [f"{label}: type must be one of {', '.join(BLOCKS)}."]
    need = {"paragraph": ["text"], "key_idea": ["text"], "example": ["text"], "code": ["code"],
            "bullets": ["items"], "mistakes": ["items"], "table": ["columns", "rows"],
            "image": ["id", "alt", "prompt"], "reveal": ["question", "answer"]}[kind]
    problems = [f"{label} ({kind}): '{k}' is empty." for k in need if not b.get(k)]
    if kind == "table" and b.get("columns") and any(len(r) != len(b["columns"]) for r in b.get("rows") or []):
        problems.append(f"{label} (table): every row needs {len(b['columns'])} cells.")
    if kind == "image":
        if b.get("id"):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(b["id"])):
                problems.append(f"{label} (image): 'id' must be short lowercase words joined by hyphens, like data-vs-information.")
            elif b["id"] in image_ids:
                problems.append(f"{label} (image): the id '{b['id']}' is used twice.")
            image_ids.append(b["id"])
        if len(str(b.get("alt", "")).split()) < 3:
            problems.append(f"{label} (image): alt text must describe the image in a few words, for students using screen readers.")
    return problems


# --- images ------------------------------------------------------------------------------

def images(data: dict) -> list:
    return [(s["heading"], b) for s in data["sections"] for b in s["blocks"] if b["type"] == "image"]


def image_file(bundle, image_id: str):
    return bundle.path("cheatsheet", "images", f"{bundle.manifest['topic']['id']}_{image_id}.png")


def missing_images(bundle) -> list:
    path = bundle.path("cheatsheet", "cheatsheet.json")
    if not path.exists():
        return []
    return [b for _, b in images(read_json(path)) if not image_file(bundle, b["id"]).exists()]


def prompts(bundle) -> str:
    from .visuals import house_style, image_size_wanted

    path = bundle.path("cheatsheet", "cheatsheet.json")
    if not path.exists():
        raise Rejected("Submit the Cheatsheet first; its image blocks say what each image shows.")
    brand = brandkit.load(bundle)
    style, size = house_style(brand), image_size_wanted(brand)
    data = read_json(path)
    rows = [f"{len(images(data))} cheatsheet image(s). Generate each with the image tool at {size[0]}×{size[1]}, save it under the "
            "path shown, then run `fz.py build <bundle> cheatsheet`.", ""]
    for heading, b in images(data):
        rows += [f"{b['id']} → {image_file(bundle, b['id']).relative_to(bundle.root).as_posix()} · section \"{heading}\"",
                 f"  Prompt: {style} For a student revision page: {b['prompt']}. Clear and simple; labels spelled exactly.", ""]
    return "\n".join(rows)


# --- rendering ----------------------------------------------------------------------------

class Theme:
    """How the Brand Kit's cheatsheet look reaches the page, given what the LMS keeps (the policy context)."""

    def __init__(self, brand, policy: dict):
        self.brand, self.policy, self.rules = brand, policy, lmspolicy.context(policy, CONTEXT)
        self.cs = brand.get("cheatsheet")
        self.mode = "style" if self.rules["style"] and self._attr_ok("p", "style") else \
            "class" if self._attr_ok("p", "class") and self._class_ok("p", "fz-key-idea") else "structure"

    def _attr_ok(self, tag, attr):
        a = self.rules["attributes"]
        return attr in (a.get(tag) or []) or attr in (a.get("*") or [])

    def _class_ok(self, tag, name):
        c = self.rules["classes"]
        return any(fnmatch.fnmatch(name, p) for p in list(c.get(tag) or []) + list(c.get("*") or []))

    def c(self, value) -> str:
        return self.brand.color(value)

    def declarations(self, role: str) -> list:
        cs, c = self.cs, self.c
        return {
            "h2": [("color", c(cs["heading"]))],
            "h3": [("color", c(cs["subheading"]))],
            "key-idea": [("background-color", c(cs["key_idea"]["background"])), ("border-left", f"4px solid {c(cs['key_idea']['border'])}"),
                         ("padding", "8px 12px"), ("border-radius", "6px")],
            "key-label": [("color", c(cs["key_idea"]["label"]))],
            "example": [("background-color", c(cs["example"]["background"])), ("padding", "8px 12px"), ("border-radius", "6px")],
            "example-label": [("color", c(cs["example"]["label"]))],
            "mistakes-title": [("color", c(cs["mistakes"]["color"]))],
            "mistake": [("color", c(cs["text"]))],
            "th": [("background-color", c(cs["table"]["header_background"])), ("border", f"1px solid {c(cs['table']['border'])}"), ("padding", "6px 10px")],
            "td": [("border", f"1px solid {c(cs['table']['border'])}"), ("padding", "6px 10px")],
            "code": [("background-color", c(cs["code"]["background"])), ("color", c(cs["code"]["text"])), ("padding", "0 4px"), ("border-radius", "3px")],
            "pre": [("background-color", c(cs["code"]["background"])), ("padding", "12px"), ("border-radius", "6px")],
            "reveal": [("border", f"1px solid {c(cs['reveal']['border'])}"), ("padding", "8px 12px"), ("border-radius", "6px")],
            "question": [("color", c(cs["reveal"]["question"]))],
        }[role]

    def attrs(self, tag: str, role: str) -> str:
        """The attribute string that gives this element its brand look, if the LMS keeps it."""
        if self.mode == "style" and self._attr_ok(tag, "style"):
            decl = [f"{k}:{v}" for k, v in self.declarations(role) if k in self.rules["style"]]
            return f' style="{";".join(decl)}"' if decl else ""
        if self.mode == "class" and self._attr_ok(tag, "class") and self._class_ok(tag, f"fz-{role}"):
            return f' class="fz-{role}"'
        return ""

    def css(self) -> str:
        family = f"{self.brand.family('body')}, {self.brand.get('fonts.fallback')}"
        out = [f".fz-cheatsheet{{font-family:{family};color:{self.c(self.cs['text'])}}}"]
        roles = ("h2", "h3", "key-idea", "key-label", "example", "example-label", "mistakes-title", "mistake", "th", "td", "code", "pre",
                 "reveal", "question")
        out += [f".fz-{r}{{" + ";".join(f"{k}:{v}" for k, v in self.declarations(r)) + "}" for r in roles]
        return "\n".join(out) + "\n"

    def icon(self, key: str) -> str:
        return (self.cs.get("icons") or {}).get(key, "")

    def label(self, key: str) -> str:
        return (self.cs.get("labels") or {}).get(key, key)


def _inline(text: str, t: Theme) -> str:
    out = markup.inline(text)
    code_attrs = t.attrs("code", "code")
    return out.replace("<code>", f"<code{code_attrs}>") if code_attrs else out


def _block(b: dict, t: Theme) -> str:
    kind = b["type"]
    allows = lambda tag: tag in t.rules["tags"]
    if kind == "paragraph":
        return f"<p>{_inline(b['text'], t)}</p>"
    if kind == "bullets":
        return "<ul>" + "".join(f"<li>{_inline(i, t)}</li>" for i in b["items"]) + "</ul>"
    if kind == "table":
        head = "".join(f"<th{t.attrs('th', 'th')}>{_inline(c, t)}</th>" for c in b["columns"])
        rows = "".join("<tr>" + "".join(f"<td{t.attrs('td', 'td')}>{_inline(c, t)}</td>" for c in r) + "</tr>" for r in b["rows"])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"
    if kind == "code":
        block = lmspolicy.code_block(t.policy, html.escape(b["code"], quote=False), b.get("language", ""))
        pre = t.attrs("pre", "pre")
        return block.replace("<pre>", f"<pre{pre}>", 1) if pre else block
    if kind == "key_idea":
        return (f"<p{t.attrs('p', 'key-idea')}><strong{t.attrs('strong', 'key-label')}>{t.icon('key_idea')} {t.label('key_idea')}:</strong> "
                f"{_inline(b['text'], t)}</p>")
    if kind == "example":
        title = f" {_inline(b['title'], t)}" if b.get("title") else ""
        return (f"<p{t.attrs('p', 'example')}><strong{t.attrs('strong', 'example-label')}>{t.icon('example')} {t.label('example')}:{title}</strong> "
                f"{_inline(b['text'], t)}</p>")
    if kind == "mistakes":
        mark = t.icon("mistake_item")
        return (f"<p><strong{t.attrs('strong', 'mistakes-title')}>{t.icon('mistakes')} {t.label('mistakes')}</strong></p><ul>"
                + "".join(f"<li{t.attrs('li', 'mistake')}>{mark} {_inline(i, t)}</li>" for i in b["items"]) + "</ul>")
    if kind == "image":
        img = f'<img src="{html.escape(lmspolicy.placeholder(t.policy, b["id"]))}" alt="{html.escape(b["alt"])}">'
        caption = f"<p><em>{_inline(b['caption'], t)}</em></p>" if b.get("caption") else ""
        return f"<p>{img}</p>{caption}"
    if kind == "reveal":
        q = f"{t.icon('reveal')} {_inline(b['question'], t)}"
        if allows("details") and allows("summary"):
            return (f"<details{t.attrs('details', 'reveal')}><summary{t.attrs('summary', 'question')}>{q}</summary>"
                    f"<p>{_inline(b['answer'], t)}</p></details>")
        wrap = "blockquote" if allows("blockquote") else None
        inner = f"<p><strong>{q}</strong></p><p><em>{t.label('answer')}:</em> {_inline(b['answer'], t)}</p>"
        return f"<{wrap}>{inner}</{wrap}>" if wrap else inner
    raise ValueError(kind)


def render(data: dict, t: Theme) -> str:
    parts = [f"<h2{t.attrs('h2', 'h2')}>{_inline(data['title'], t)}</h2>"]
    if data.get("intro"):
        parts.append(f"<p>{_inline(data['intro'], t)}</p>")
    for s in data["sections"]:
        parts.append(f"<h3{t.attrs('h3', 'h3')}>{_inline(s['heading'], t)}</h3>")
        parts += [_block(b, t) for b in s["blocks"]]
    parts.append(f"<h3{t.attrs('h3', 'h3')}>{t.icon('quick_revision')} {t.label('quick_revision')}</h3><ul>"
                 + "".join(f"<li>{_inline(i, t)}</li>" for i in data["quick_revision"]) + "</ul>")
    return "\n".join(parts) + "\n"


def build(bundle) -> dict:
    path = bundle.path("cheatsheet", "cheatsheet.json")
    if not path.exists():
        raise Rejected("Submit the Cheatsheet first (`fz.py submit <bundle> cheatsheet <file>`).")
    data = read_json(path)
    policy = lmspolicy.load(bundle)
    t = Theme(brandkit.load(bundle), policy)
    fragment = render(data, t)
    problems = lmspolicy.check(fragment, policy, CONTEXT)
    if problems:
        raise Rejected([f"The cheatsheet HTML would not survive the LMS: {p}" for p in problems])
    tid = bundle.manifest["topic"]["id"]
    folder = bundle.path("cheatsheet")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{tid}_cheatsheet.html").write_text(fragment, encoding="utf-8")
    if t.mode == "class":
        (folder / f"{tid}_theme.css").write_text(t.css(), encoding="utf-8")
    preview = fragment
    for _, b in images(data):
        if image_file(bundle, b["id"]).exists():
            preview = preview.replace(html.escape(lmspolicy.placeholder(policy, b["id"])), f"images/{image_file(bundle, b['id']).name}")
    css = f"<style>{t.css()}</style>" if t.mode == "class" else ""
    (folder / "preview.html").write_text(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>Cheatsheet: {html.escape(data['title'])}</title>{css}</head>"
        f"<body style=\"max-width:860px;margin:2rem auto;padding:0 1rem\"><div class=\"fz-cheatsheet\">\n{preview}</div></body></html>\n",
        encoding="utf-8")
    lines = [f"# Image insertion map: {tid}", "",
             "The cheatsheet HTML holds a placeholder where each image goes. When uploading to the LMS, attach the image file and put "
             "it where its placeholder is.", "",
             "| Placeholder | File | Section | Alt text | Ready |", "|---|---|---|---|---|"]
    for heading, b in images(data):
        f = image_file(bundle, b["id"])
        lines.append(f"| `{lmspolicy.placeholder(policy, b['id'])}` | `images/{f.name}` | {heading} | {b['alt']} | {'yes' if f.exists() else 'not yet'} |")
    if not images(data):
        lines.append("| (none) | | | | |")
    (folder / "insertion_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    bundle.manifest["stages"]["cheatsheet"] = {"status": "built", "mode": t.mode, "policy": policy["_source"]}
    bundle.manifest["gates"].get("3", {}).pop("cheatsheet", None)
    bundle.log("cheatsheet built")
    return {"sections": len(data["sections"]), "images": len(images(data)), "mode": t.mode, "policy": policy["_source"],
            "interactive": "details" in t.rules["tags"] and "summary" in t.rules["tags"], "missing": len(missing_images(bundle))}
