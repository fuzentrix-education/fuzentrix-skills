"""Stage 3a: Slides. One editable slide per Segment, built with native PowerPoint shapes (standard library
only) on the Brand Kit's slide template and background, in its colours, fonts and sizes. Content stays
inside the kit's content area, clear of the presenter area, and text that would not fit its box is
rejected with the limit instead of being shrunk."""
from __future__ import annotations

import math
import re
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from . import brandkit, naming
from .problems import Rejected

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
PT = 12700  # EMU per point
_LEAD = re.compile(r"^\s*(?:[✔✓•\-*➔→>]\s*)+")
ROLE = {"regular": "body", "bold": "heading", "mono": "code"}   # text kind → Brand Kit font role


class Area:
    """The Brand Kit's slide regions, as fractions of the slide."""

    def __init__(self, brand):
        a, t = brand.get("slides.content_area"), brand.get("slides.title_slide")
        self.x0, self.x1, self.y0, self.y1 = a["left"], a["right"], a["top"], a["bottom"]
        self.label_y, self.title_y = a["label_y"], a["title_y"]
        self.big_label_y, self.big_title_y, self.subtitle_y = t["label_y"], t["title_y"], t["subtitle_y"]


class Slide:
    """Collects the shapes of one slide and the text-fit problems found while placing them."""

    def __init__(self, sid: str, W: int, H: int, brand):
        self.sid, self.W, self.H, self.brand = sid, W, H, brand
        self.a = Area(brand)
        self.shapes, self.problems, self._id = [], [], 2

    def c(self, role: str) -> str:
        """The colour (RRGGBB) the Brand Kit gives a slide element."""
        return self.brand.rgb(self.brand.get(f"slides.colors.{role}"))

    def z(self, role: str) -> float:
        """The text size the Brand Kit gives a slide element."""
        return self.brand.get(f"slides.sizes.{role}")

    def word(self, key: str) -> str:
        return self.brand.get(f"slides.words.{key}")

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def box(self, x, y, w, h):
        return int(x * self.W), int(y * self.H), int(w * self.W), int(h * self.H)

    # --- fit -----------------------------------------------------------------------
    def lines_needed(self, text: str, size: float, w_emu: int, kind: str) -> int:
        m, width = self.brand.measure(ROLE[kind]), w_emu / PT
        total = 0
        for para in str(text).split("\n"):
            line, count = "", 1
            for word in para.split():
                candidate = f"{line} {word}" if line else word
                if line and not m.fits(candidate, size, width):
                    count += 1
                    line = word
                else:
                    line = candidate
            total += count
        return total

    def fits(self, label: str, text: str, size: float, w_emu: int, h_emu: int, kind: str = "regular") -> bool:
        lines = self.lines_needed(text, size, w_emu, kind)
        if lines * size * 1.2 * PT > h_emu:
            per_line = self.brand.measure(ROLE[kind]).capacity(size, w_emu / PT)
            capacity = per_line * max(1, int(h_emu / (size * 1.2 * PT)))
            self.problems.append(f"{self.sid} {label} is too long for its box: about {capacity} characters fit, it has {len(str(text))}. Shorten it in the Master Script.")
            return False
        return True

    # --- shapes ----------------------------------------------------------------------
    def _run(self, text, size, color, bold=False, font=None):
        font = font or self.brand.family("heading" if bold else "body")
        return (f'<a:r><a:rPr lang="en-US" sz="{int(size * 100)}" b="{1 if bold else 0}" dirty="0">'
                f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{escape(font)}"/><a:cs typeface="{escape(font)}"/></a:rPr>'
                f"<a:t>{escape(str(text))}</a:t></a:r>")

    def text(self, name, x, y, w, h, paragraphs, anchor="t", align="l", inset=0, fill=None, line=None, geom="rect", radius=0):
        """paragraphs: list of runs-lists, each run (text, size, color, bold, font)."""
        X, Y, CX, CY = self.box(x, y, w, h)
        ins = int(inset * PT)
        paras = "".join(
            f'<a:p><a:pPr algn="{align}"/>' + "".join(self._run(*r) for r in runs) + "</a:p>" for runs in paragraphs)
        sp_fill = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        sp_line = f'<a:ln w="19050"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line else "<a:ln><a:noFill/></a:ln>"
        av = f'<a:avLst><a:gd name="adj" fmla="val {radius}"/></a:avLst>' if geom == "roundRect" else "<a:avLst/>"
        txbox = ' txBox="1"' if not fill and not line else ""
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{self.next_id()}" name="{escape(name)}"/><p:cNvSpPr{txbox}/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{X}" y="{Y}"/><a:ext cx="{CX}" cy="{CY}"/></a:xfrm><a:prstGeom prst="{geom}">{av}</a:prstGeom>{sp_fill}{sp_line}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="{ins}" tIns="{ins}" rIns="{ins}" bIns="{ins}" anchor="{anchor}"><a:noAutofit/></a:bodyPr><a:lstStyle/>{paras or "<a:p/>"}</p:txBody></p:sp>')
        return X, Y, CX, CY

    def card(self, name, x, y, w, h, fill, line=None, radius=6000):
        self.text(name, x, y, w, h, [], fill=fill, line=line, geom="roundRect", radius=radius)

    def arrow(self, name, x1, y1, x2, y2):
        X1, Y1, X2, Y2 = int(x1 * self.W), int(y1 * self.H), int(x2 * self.W), int(y2 * self.H)
        self.shapes.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{self.next_id()}" name="{escape(name)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{min(X1, X2)}" y="{min(Y1, Y2)}"/><a:ext cx="{abs(X2 - X1)}" cy="{abs(Y2 - Y1)}"/></a:xfrm>'
            f'<a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom><a:ln w="38100"><a:solidFill><a:srgbClr val="{self.c("connector")}"/></a:solidFill>'
            f'<a:tailEnd type="triangle"/></a:ln></p:spPr></p:cxnSp>')

    def picture(self, name, rid, x, y, w, h):
        X, Y, CX, CY = self.box(x, y, w, h) if (w, h) != (1, 1) else (0, 0, self.W, self.H)
        self.shapes.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{self.next_id()}" name="{escape(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{X}" y="{Y}"/><a:ext cx="{CX}" cy="{CY}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def xml(self) -> str:
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld {NS}><p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                + "".join(self.shapes) + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


# --- layouts ---------------------------------------------------------------------------

def _header(s: Slide, course: str, title: str, big: bool = False) -> None:
    a, label, t = s.a, s.brand.get("slides.label"), s.brand.get("slides.title")
    if label.get("text"):
        s.text("Label", a.x0, a.big_label_y if big else a.label_y, 0.6, 0.03,
               [[(label["text"].format(course=course), label["size"], s.brand.rgb(label["color"]), True)]])
    text = title.upper() if t.get("case") == "upper" else title
    colors = [s.brand.rgb(c) for c in t["colors"]]
    words = text.split()
    if len(colors) > 1:
        k = math.ceil(len(words) / 2) if len(words) > 1 else len(words)
        lines = [" ".join(words[:k]), " ".join(words[k:])]
    else:
        lines = [text, ""]
    size = t["title_slide_size"] if big else t["size"]
    y = a.big_title_y if big else a.title_y
    w_emu = int((a.x1 - a.x0) * s.W)
    for line in lines:
        if line:
            s.fits("title", line, size, w_emu, int(size * 1.25 * PT * (1 if len(colors) > 1 else 2)), "bold")
    paras = [[(lines[0], size, colors[0], True)]] + ([[(lines[1], size, colors[-1], True)]] if lines[1] else [])
    s.text("Title", a.x0, y, a.x1 - a.x0, (0.30 if big else 0.20), paras)


def _bullets(s: Slide, items, y0=None, y1=None, x0=None, x1=None, size=None, marker=None) -> None:
    a = s.a
    y0, y1 = a.y0 if y0 is None else y0, a.y1 if y1 is None else y1
    x0, x1 = a.x0 if x0 is None else x0, a.x1 if x1 is None else x1
    size = size or s.z("body")
    marker = marker or s.brand.get("slides.bullets.marker")
    max_lines = s.brand.get("slides.bullets.max_lines")
    items = [_LEAD.sub("", str(i)) for i in items]  # the slide draws its own markers
    gap = 0.018
    y = y0
    text_x = x0 + 0.03
    w_emu = int((x1 - text_x) * s.W)
    for i, item in enumerate(items, 1):
        lines = min(max_lines, s.lines_needed(item, size, w_emu, "regular"))
        h = lines * size * 1.2 * PT / s.H
        if y + h > y1:
            s.problems.append(f"{s.sid} has too many bullets for one slide (bullet {i} does not fit); keep at most {i - 1}, or split the Segment.")
            return
        if not s.fits(f"bullet {i}", item, size, w_emu, int(min(max_lines * size * 1.2 * PT, (y1 - y) * s.H)) + 1):
            return  # on screen, a bullet is at most max_lines lines
        if marker == "check":
            s.text(f"Check {i}", x0, y + 0.004, 0.02, 0.036, [[("✓", s.z("check"), s.c("marker_text"), True)]], anchor="ctr", align="ctr",
                   fill=s.c("marker"), geom="roundRect", radius=12000)
        else:
            s.card(f"Bullet {i}", x0 + 0.004, y + 0.016, 0.009, 0.016, s.c("marker"), radius=0)
        s.text(f"Text {i}", text_x, y, x1 - text_x, h + 0.01, [[(item, size, s.c("body"), False)]])
        y += h + gap


def _title_layout(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"], big=True)
    y = a.subtitle_y
    for i, item in enumerate(slide.get("bullets") or [], 1):
        if s.fits(f"bullet {i}", item, s.z("subtitle"), int((a.x1 - a.x0) * s.W), int(0.065 * s.H)):
            s.text(f"Subtitle {i}", a.x0, y, a.x1 - a.x0, 0.065, [[(item, s.z("subtitle"), s.c("subtitle"), False)]])
        y += 0.07


def _agenda(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    if len(items) > 6:
        s.problems.append(f"{s.sid} agenda has {len(items)} items; keep at most 6.")
        items = items[:6]
    col_w, row_h = (a.x1 - a.x0 - 0.02) / 2, 0.15
    for i, item in enumerate(items):
        col, row = i // 3, i % 3
        x, y = a.x0 + col * (col_w + 0.02), a.y0 + row * (row_h + 0.035)
        s.card(f"Agenda card {i + 1}", x, y, col_w, row_h, s.c("card"), s.c("card_border"))
        s.text(f"Agenda number {i + 1}", x + 0.02, y + 0.04, 0.045, 0.07, [[(f"{i + 1:02d}", s.z("agenda_number"), s.c("marker_text"), True)]],
               anchor="ctr", align="ctr", fill=s.c("marker"), geom="roundRect", radius=10000)
        tx, tw = x + 0.08, col_w - 0.10
        if s.fits(f"agenda item {i + 1}", item, s.z("agenda_item"), int(tw * s.W), int((row_h - 0.03) * s.H), "bold"):
            s.text(f"Agenda item {i + 1}", tx, y + 0.015, tw, row_h - 0.03, [[(item, s.z("agenda_item"), s.c("body"), True)]], anchor="ctr")


def _definition(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    definition = _LEAD.sub("", items[0]) if items else slide["title"]
    size = s.z("definition")
    w = a.x1 - a.x0 - 0.06
    lines = min(3, s.lines_needed(definition, size, int(w * s.W), "regular"))
    text_h = lines * size * 1.25 * PT / s.H
    card_h = 0.095 + text_h
    s.card("Definition card", a.x0, a.y0, a.x1 - a.x0, card_h, s.c("card_alt"))
    s.card("Definition accent", a.x0, a.y0, 0.008, card_h, s.c("accent"), radius=0)
    s.text("Definition label", a.x0 + 0.03, a.y0 + 0.025, 0.5, 0.04, [[(s.word("definition"), s.z("definition_label"), s.c("definition_label"), True)]])
    if s.fits("definition", definition, size, int(w * s.W), int(3 * size * 1.25 * PT)):
        s.text("Definition text", a.x0 + 0.03, a.y0 + 0.075, w, text_h + 0.01, [[(definition, size, s.c("body"), False)]])
    if items[1:]:
        _bullets(s, items[1:], y0=a.y0 + card_h + 0.05)


def _code(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    code = str(slide.get("code") or "\n".join(slide.get("bullets") or []))
    lines = code.split("\n")
    size, mono = s.z("code"), s.brand.family("code")
    w = a.x1 - a.x0
    h = min(0.36, 0.06 + len(lines) * size * 1.25 * PT / s.H)
    for i, line in enumerate(lines, 1):
        s.fits(f"code line {i}", line, size, int((w - 0.06) * s.W), int(size * 1.3 * PT), "mono")
    s.card("Code card", a.x0, a.y0, w, h, s.c("code_bg"))
    s.text("Code", a.x0 + 0.03, a.y0 + 0.025, w - 0.06, h - 0.04,
           [[(line or " ", size, s.c("code_text"), False, mono)] for line in lines])
    if slide.get("output") is not None:
        y = a.y0 + h + 0.03
        out = str(slide["output"])
        s.card("Output card", a.x0, y, w, 0.12, s.c("card_alt"))
        s.text("Output label", a.x0 + 0.03, y + 0.015, 0.3, 0.03, [[(s.word("output"), s.z("output_label"), s.c("output_label"), True)]])
        if s.fits("output", out, size, int((w - 0.06) * s.W), int(0.06 * s.H), "mono"):
            s.text("Output", a.x0 + 0.03, y + 0.05, w - 0.06, 0.06, [[(out, size, s.c("output_text"), True, mono)]])


def _comparison(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    columns = slide.get("columns")
    if not columns:
        items = slide.get("bullets") or []
        half = math.ceil(len(items) / 2)
        columns = [{"title": "", "bullets": items[:half]}, {"title": "", "bullets": items[half:]}]
    col_w = (a.x1 - a.x0 - 0.03) / 2
    for i, col in enumerate(columns[:2]):
        x = a.x0 + i * (col_w + 0.03)
        s.card(f"Column {i + 1}", x, a.y0, col_w, a.y1 - a.y0, s.c("card"), s.c("card_border"))
        y = a.y0 + 0.03
        if col.get("title"):
            if s.fits(f"column {i + 1} title", col["title"], s.z("column_title"), int((col_w - 0.04) * s.W), int(0.05 * s.H), "bold"):
                s.text(f"Column {i + 1} title", x + 0.02, y, col_w - 0.04, 0.05, [[(col["title"], s.z("column_title"), s.c("column_title"), True)]])
            y += 0.07
        _bullets(s, col.get("bullets") or [], y0=y, y1=a.y1 - 0.02, x0=x + 0.02, x1=x + col_w - 0.02, size=s.z("column_body"))


def _diagram(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    flow = next((i for i in items if re.search(r"→|->|➔", i)), None)
    nodes = [n.strip() for n in re.split(r"→|->|➔", flow)] if flow else items[:4]
    nodes = [n for n in nodes if n][:5]
    rest = [i for i in items if i is not flow] if flow else items[4:]
    if nodes:
        gap = 0.06
        box_w = (a.x1 - a.x0 - gap * (len(nodes) - 1)) / len(nodes)
        y, box_h = a.y0 + 0.02, 0.14
        for i, node in enumerate(nodes):
            x = a.x0 + i * (box_w + gap)
            if s.fits(f"diagram box {i + 1}", node, s.z("diagram_box"), int((box_w - 0.02) * s.W), int((box_h - 0.02) * s.H), "bold"):
                s.text(node, x, y, box_w, box_h, [[(node, s.z("diagram_box"), s.c("box_text"), True)]], anchor="ctr", align="ctr",
                       inset=6, fill=s.c("box"), geom="roundRect", radius=12000)
            if i:
                s.arrow(f"Connector {i}", x - gap + 0.008, y + box_h / 2, x - 0.008, y + box_h / 2)
    if rest:
        _bullets(s, rest, y0=a.y0 + 0.22)


def _quote(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    statement = _LEAD.sub("", items[0]) if items else slide["title"]
    size = s.z("quote")
    w = a.x1 - a.x0 - 0.06
    lines = min(3, s.lines_needed(statement, size, int(w * s.W), "bold"))
    text_h = lines * size * 1.25 * PT / s.H
    card_h = 0.06 + text_h
    s.card("Statement card", a.x0, a.y0, a.x1 - a.x0, card_h, s.c("card_alt"))
    if s.fits("statement", statement, size, int(w * s.W), int(3 * size * 1.25 * PT), "bold"):
        s.text("Statement", a.x0 + 0.03, a.y0 + 0.03, w, text_h + 0.01, [[(statement, size, s.c("body"), True)]], anchor="ctr")
    if items[1:]:
        _bullets(s, items[1:], y0=a.y0 + card_h + 0.05)


def _image(s, slide, course, extras):
    a = s.a
    _header(s, course, slide["title"])
    half = (a.x1 - a.x0) / 2
    if slide.get("bullets"):
        _bullets(s, slide["bullets"], x1=a.x0 + half - 0.02)
    x, w, h = a.x0 + half + 0.01, half - 0.01, a.y1 - a.y0
    if extras.get("image_rid"):
        iw, ih = extras["image_size"]
        scale = min(w * s.W / iw, h * s.H / ih)
        pw, ph = iw * scale / s.W, ih * scale / s.H
        s.picture("Visual", extras["image_rid"], x + (w - pw) / 2, a.y0 + (h - ph) / 2, pw, ph)
    else:
        s.card("Image placeholder", x, a.y0, w, h, s.c("card"), s.c("card_border"))
        s.text("Image placeholder text", x + 0.02, a.y0 + 0.02, w - 0.04, h - 0.04,
               [[(s.word("image_placeholder"), s.z("placeholder_label"), s.c("placeholder_label"), True)],
                [(extras.get("image_description") or slide["title"], s.z("placeholder_text"), s.c("placeholder_text"), False)]],
               anchor="ctr", align="ctr")


def _summary(s, slide, course, extras):
    _header(s, course, slide["title"])
    _bullets(s, slide.get("bullets") or [], marker="check")


LAYOUTS = {"title": _title_layout, "agenda": _agenda, "bullets": lambda s, sl, c, e: (_header(s, c, sl["title"]), _bullets(s, sl.get("bullets") or [])),
           "definition": _definition, "code": _code, "comparison": _comparison, "diagram": _diagram,
           "quote": _quote, "image": _image, "summary": _summary}


# --- package -----------------------------------------------------------------------------

def _png_size(data: bytes):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    return None


def build(bundle) -> dict:
    from . import editor
    from .visuals import _found, image_size, require_final

    master = require_final(bundle, "Slides")
    brand = brandkit.load(bundle)
    template = brand.file(brand.get("slides.template"))
    bg_rel = brand.get("slides.background")
    background = brand.file(bg_rel)
    bg_name = "fz_background" + (Path(bg_rel).suffix.lower() or ".png")
    course = master["video"]["id"].split("-")[0].upper()

    import io

    with zipfile.ZipFile(io.BytesIO(template)) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    pres = parts["ppt/presentation.xml"].decode("utf-8")
    m = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    W, H = int(m.group(1)), int(m.group(2))
    blank = next((n for n, d in parts.items() if n.startswith("ppt/slideLayouts/slideLayout") and n.endswith(".xml") and b'type="blank"' in d), None)
    if blank is None:
        raise Rejected("The Brand Kit's slide template has no Blank layout.")

    slides, problems, media = [], [], {f"ppt/media/{bg_name}": background}
    for seg in master["segments"]:
        sl = seg["slide"]
        s = Slide(sl["id"], W, H, brand)
        s.picture("Background", "rId2", 0, 0, 1, 1)
        extras = {}
        images = [e for e in seg.get("visual_events", []) if e.get("kind") == "image"]
        if sl["layout"] == "image" and images:
            extras["image_description"] = images[0]["description"]
            f = _found(naming.asset_path(bundle, images[0], "image", "png"))
            size = image_size(f.read_bytes()) if f else None
            if size:
                name = f"fz_{images[0]['id']}{f.suffix.lower()}"
                media[f"ppt/media/{name}"] = f.read_bytes()
                extras.update(image_rid="rId3", image_file=name, image_size=size)
        LAYOUTS.get(sl["layout"], LAYOUTS["bullets"])(s, sl, course, extras)
        problems += s.problems
        slides.append((s, extras))
    if problems:
        raise Rejected(problems)

    rels = parts["ppt/_rels/presentation.xml.rels"].decode("utf-8")
    types = parts["[Content_Types].xml"].decode("utf-8")
    ids, layout_target = [], "../slideLayouts/" + blank.split("/")[-1]
    for i, (s, extras) in enumerate(slides, 1):
        parts[f"ppt/slides/slide{i}.xml"] = s.xml().encode("utf-8")
        srels = (f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="{layout_target}"/>'
                 f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{bg_name}"/>')
        if extras.get("image_rid"):
            srels += f'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{extras["image_file"]}"/>'
        parts[f"ppt/slides/_rels/slide{i}.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + srels + "</Relationships>").encode("utf-8")
        rels = rels.replace("</Relationships>", f'<Relationship Id="rIdFz{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/></Relationships>')
        types = types.replace("</Types>", f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
        ids.append(f'<p:sldId id="{255 + i}" r:id="rIdFz{i}"/>')
    slide_list = "<p:sldIdLst>" + "".join(ids) + "</p:sldIdLst>"
    if re.search(r"<p:sldIdLst\b", pres):
        pres = re.sub(r"<p:sldIdLst\s*/>|<p:sldIdLst>.*?</p:sldIdLst>", slide_list, pres, flags=re.S)
    else:  # a template with no slides at all has no list yet; it goes just before the slide size
        pres = pres.replace("<p:sldSz", slide_list + "<p:sldSz", 1)
    parts["ppt/presentation.xml"] = pres.encode("utf-8")
    parts["ppt/_rels/presentation.xml.rels"] = rels.encode("utf-8")
    for ext, ctype in (("png", "image/png"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg")):
        if f'Extension="{ext}"' not in types:
            types = types.replace("<Default ", f'<Default Extension="{ext}" ContentType="{ctype}"/><Default ', 1)
    parts["[Content_Types].xml"] = types.encode("utf-8")
    if "docProps/app.xml" in parts:
        parts["docProps/app.xml"] = re.sub(rb"<Slides>\d+</Slides>", f"<Slides>{len(slides)}</Slides>".encode(), parts["docProps/app.xml"])
    parts.update(media)

    out = naming.slides_file(bundle)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", parts.pop("[Content_Types].xml"))
        for name, data in parts.items():
            z.writestr(name, data)
    outline = [f"# Slides: {master['video'].get('title') or master['video']['id']}", "",
               f"{len(slides)} slides in `{out.name}`. Export slide images from PowerPoint (File → Export) if the Video Editor needs PNGs.", ""]
    for seg in master["segments"]:
        sl = seg["slide"]
        outline.append(f"- **{sl['id']}** · {sl['layout']} · {sl['title']} ({seg['id']})")
    (out.parent / "slides.md").write_text("\n".join(outline) + "\n", encoding="utf-8")
    bundle.manifest["stages"]["slides"] = {"status": "built", "slides": len(slides)}
    bundle.log("slides built")
    editor.build(bundle)
    return {"slides": len(slides), "path": out}
