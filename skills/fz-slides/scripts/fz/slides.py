"""Stage 3a: Slides. One editable slide per Segment, built on the Fuzentrix Slide Master with native
PowerPoint shapes (standard library only). The bottom-right presenter area stays empty, and text that
would not fit its box is rejected with the limit instead of being shrunk."""
from __future__ import annotations

import math
import re
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from . import naming, settings
from .bundle import read_json
from .problems import Rejected

ASSETS = Path(__file__).parent / "assets"
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
PT = 12700  # EMU per point
BRAND = {
    "navy": "062858", "blue": "0A59C8", "dark_blue": "033476", "slate": "52657D",
    "light": "E5EFFD", "border": "DCE7F4", "white": "FFFFFF",
    "font": "Aptos", "font_bold": "Aptos", "code_font": "Consolas",
}
# Content region, as fractions of the slide. Everything stays left of x = 0.86, so nothing can reach the
# presenter area (bottom-right 10% × 20%).
X0, X1, Y_LABEL, Y_TITLE, Y0, Y1 = 0.06, 0.86, 0.065, 0.11, 0.34, 0.90
CHAR_W = {"regular": 0.52, "bold": 0.56, "mono": 0.60}  # average glyph width in ems, for fit estimates
_LEAD = re.compile(r"^\s*(?:[✔✓•\-*➔→>]\s*)+")


class Slide:
    """Collects the shapes of one slide and the text-fit problems found while placing them."""

    def __init__(self, sid: str, W: int, H: int, brand: dict):
        self.sid, self.W, self.H, self.b = sid, W, H, brand
        self.shapes, self.problems, self._id = [], [], 2

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def box(self, x, y, w, h):
        return int(x * self.W), int(y * self.H), int(w * self.W), int(h * self.H)

    # --- fit -----------------------------------------------------------------------
    def lines_needed(self, text: str, size: float, w_emu: int, kind: str) -> int:
        per_line = max(1, int((w_emu / PT) / (size * CHAR_W[kind])))
        total = 0
        for para in str(text).split("\n"):
            line, count = 0, 1
            for word in para.split():
                need = len(word) + (1 if line else 0)
                if line + need > per_line and line:
                    count += 1
                    line = len(word)
                else:
                    line += need
            total += count
        return total

    def fits(self, label: str, text: str, size: float, w_emu: int, h_emu: int, kind: str = "regular") -> bool:
        lines = self.lines_needed(text, size, w_emu, kind)
        if lines * size * 1.2 * PT > h_emu:
            per_line = max(1, int((w_emu / PT) / (size * CHAR_W[kind])))
            capacity = per_line * max(1, int(h_emu / (size * 1.2 * PT)))
            self.problems.append(f"{self.sid} {label} is too long for its box: about {capacity} characters fit, it has {len(str(text))}. Shorten it in the Master Script.")
            return False
        return True

    # --- shapes ----------------------------------------------------------------------
    def _run(self, text, size, color, bold=False, font=None):
        font = font or (self.b["font_bold"] if bold else self.b["font"])
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
            f'<a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom><a:ln w="38100"><a:solidFill><a:srgbClr val="{self.b["blue"]}"/></a:solidFill>'
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
    b = s.b
    s.text("Label", X0, Y_LABEL if not big else 0.20, 0.6, 0.03, [[(f"FUZENTRIX EDUCATION · {course}", 16, b["blue"], True)]])
    words = title.upper().split()
    k = math.ceil(len(words) / 2) if len(words) > 1 else len(words)
    lines = [" ".join(words[:k]), " ".join(words[k:])]
    size = 66 if big else 48
    y = 0.26 if big else Y_TITLE
    w_emu = int((X1 - X0) * s.W)
    for line in lines:
        if line:
            s.fits("title", line, size, w_emu, int(size * 1.25 * PT), "bold")
    paras = [[(lines[0], size, b["navy"], True)]] + ([[(lines[1], size, b["blue"], True)]] if lines[1] else [])
    s.text("Title", X0, y, X1 - X0, (0.30 if big else 0.20), paras)


def _bullets(s: Slide, items, y0=Y0, y1=Y1, x0=X0, x1=X1, size=32, marker="square") -> None:
    b = s.b
    items = [_LEAD.sub("", str(i)) for i in items]  # the slide draws its own markers
    gap = 0.018
    y = y0
    text_x = x0 + 0.03
    w_emu = int((x1 - text_x) * s.W)
    for i, item in enumerate(items, 1):
        lines = min(2, s.lines_needed(item, size, w_emu, "regular"))
        h = lines * size * 1.2 * PT / s.H
        if y + h > y1:
            s.problems.append(f"{s.sid} has too many bullets for one slide (bullet {i} does not fit); keep at most {i - 1}, or split the Segment.")
            return
        if not s.fits(f"bullet {i}", item, size, w_emu, int(min(2 * size * 1.2 * PT, (y1 - y) * s.H)) + 1):
            return  # on screen, a bullet is at most 2 lines
        if marker == "check":
            s.text(f"Check {i}", x0, y + 0.004, 0.02, 0.036, [[("✓", 18, b["white"], True)]], anchor="ctr", align="ctr", fill=b["blue"], geom="roundRect", radius=12000)
        else:
            s.card(f"Bullet {i}", x0 + 0.004, y + 0.016, 0.009, 0.016, b["blue"], radius=0)
        s.text(f"Text {i}", text_x, y, x1 - text_x, h + 0.01, [[(item, size, b["navy"], False)]])
        y += h + gap


def _title_layout(s, slide, course, extras):
    _header(s, course, slide["title"], big=True)
    y = 0.62
    for i, item in enumerate(slide.get("bullets") or [], 1):
        if s.fits(f"bullet {i}", item, 34, int((X1 - X0) * s.W), int(0.065 * s.H)):
            s.text(f"Subtitle {i}", X0, y, X1 - X0, 0.065, [[(item, 34, s.b["slate"], False)]])
        y += 0.07


def _agenda(s, slide, course, extras):
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    if len(items) > 6:
        s.problems.append(f"{s.sid} agenda has {len(items)} items; keep at most 6.")
        items = items[:6]
    col_w, row_h = 0.39, 0.15
    for i, item in enumerate(items):
        col, row = i // 3, i % 3
        x, y = X0 + col * (col_w + 0.02), Y0 + row * (row_h + 0.035)
        s.card(f"Agenda card {i + 1}", x, y, col_w, row_h, s.b["white"], s.b["border"])
        s.text(f"Agenda number {i + 1}", x + 0.02, y + 0.04, 0.045, 0.07, [[(f"{i + 1:02d}", 24, s.b["white"], True)]],
               anchor="ctr", align="ctr", fill=s.b["blue"], geom="roundRect", radius=10000)
        tx, tw = x + 0.08, col_w - 0.10
        if s.fits(f"agenda item {i + 1}", item, 30, int(tw * s.W), int((row_h - 0.03) * s.H), "bold"):
            s.text(f"Agenda item {i + 1}", tx, y + 0.015, tw, row_h - 0.03, [[(item, 30, s.b["navy"], True)]], anchor="ctr")


def _definition(s, slide, course, extras):
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    definition = _LEAD.sub("", items[0]) if items else slide["title"]
    w = X1 - X0 - 0.06
    lines = min(3, s.lines_needed(definition, 36, int(w * s.W), "regular"))
    text_h = lines * 36 * 1.25 * PT / s.H
    card_h = 0.095 + text_h
    s.card("Definition card", X0, Y0, X1 - X0, card_h, s.b["light"])
    s.card("Definition accent", X0, Y0, 0.008, card_h, s.b["blue"], radius=0)
    s.text("Definition label", X0 + 0.03, Y0 + 0.025, 0.5, 0.04, [[("DEFINITION", 18, s.b["dark_blue"], True)]])
    if s.fits("definition", definition, 36, int(w * s.W), int(3 * 36 * 1.25 * PT)):
        s.text("Definition text", X0 + 0.03, Y0 + 0.075, w, text_h + 0.01, [[(definition, 36, s.b["navy"], False)]])
    if items[1:]:
        _bullets(s, items[1:], y0=Y0 + card_h + 0.05)


def _code(s, slide, course, extras):
    _header(s, course, slide["title"])
    code = str(slide.get("code") or "\n".join(slide.get("bullets") or []))
    lines = code.split("\n")
    w = X1 - X0
    h = min(0.36, 0.06 + len(lines) * 22 * 1.25 * PT / s.H)
    for i, line in enumerate(lines, 1):
        s.fits(f"code line {i}", line, 22, int((w - 0.06) * s.W), int(22 * 1.3 * PT), "mono")
    s.card("Code card", X0, Y0, w, h, s.b["navy"])
    s.text("Code", X0 + 0.03, Y0 + 0.025, w - 0.06, h - 0.04,
           [[(line or " ", 22, s.b["white"], False, s.b["code_font"])] for line in lines])
    if slide.get("output") is not None:
        y = Y0 + h + 0.03
        out = str(slide["output"])
        s.card("Output card", X0, y, w, 0.12, s.b["light"])
        s.text("Output label", X0 + 0.03, y + 0.015, 0.3, 0.03, [[("OUTPUT", 16, s.b["blue"], True)]])
        if s.fits("output", out, 22, int((w - 0.06) * s.W), int(0.06 * s.H), "mono"):
            s.text("Output", X0 + 0.03, y + 0.05, w - 0.06, 0.06, [[(out, 22, s.b["dark_blue"], True, s.b["code_font"])]])


def _comparison(s, slide, course, extras):
    _header(s, course, slide["title"])
    columns = slide.get("columns")
    if not columns:
        items = slide.get("bullets") or []
        half = math.ceil(len(items) / 2)
        columns = [{"title": "", "bullets": items[:half]}, {"title": "", "bullets": items[half:]}]
    col_w = (X1 - X0 - 0.03) / 2
    for i, col in enumerate(columns[:2]):
        x = X0 + i * (col_w + 0.03)
        s.card(f"Column {i + 1}", x, Y0, col_w, Y1 - Y0, s.b["white"], s.b["border"])
        y = Y0 + 0.03
        if col.get("title"):
            if s.fits(f"column {i + 1} title", col["title"], 28, int((col_w - 0.04) * s.W), int(0.05 * s.H), "bold"):
                s.text(f"Column {i + 1} title", x + 0.02, y, col_w - 0.04, 0.05, [[(col["title"], 28, s.b["blue"], True)]])
            y += 0.07
        _bullets(s, col.get("bullets") or [], y0=y, y1=Y1 - 0.02, x0=x + 0.02, x1=x + col_w - 0.02, size=24)


def _diagram(s, slide, course, extras):
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    flow = next((i for i in items if re.search(r"→|->|➔", i)), None)
    nodes = [n.strip() for n in re.split(r"→|->|➔", flow)] if flow else items[:4]
    nodes = [n for n in nodes if n][:5]
    rest = [i for i in items if i is not flow] if flow else items[4:]
    if nodes:
        gap = 0.06
        box_w = (X1 - X0 - gap * (len(nodes) - 1)) / len(nodes)
        y, box_h = Y0 + 0.02, 0.14
        for i, node in enumerate(nodes):
            x = X0 + i * (box_w + gap)
            if s.fits(f"diagram box {i + 1}", node, 28, int((box_w - 0.02) * s.W), int((box_h - 0.02) * s.H), "bold"):
                s.text(node, x, y, box_w, box_h, [[(node, 28, s.b["white"], True)]], anchor="ctr", align="ctr",
                       inset=6, fill=s.b["blue"], geom="roundRect", radius=12000)
            if i:
                s.arrow(f"Connector {i}", x - gap + 0.008, y + box_h / 2, x - 0.008, y + box_h / 2)
    if rest:
        _bullets(s, rest, y0=Y0 + 0.22)


def _quote(s, slide, course, extras):
    _header(s, course, slide["title"])
    items = slide.get("bullets") or []
    statement = _LEAD.sub("", items[0]) if items else slide["title"]
    w = X1 - X0 - 0.06
    lines = min(3, s.lines_needed(statement, 40, int(w * s.W), "bold"))
    text_h = lines * 40 * 1.25 * PT / s.H
    card_h = 0.06 + text_h
    s.card("Statement card", X0, Y0, X1 - X0, card_h, s.b["light"])
    if s.fits("statement", statement, 40, int(w * s.W), int(3 * 40 * 1.25 * PT), "bold"):
        s.text("Statement", X0 + 0.03, Y0 + 0.03, w, text_h + 0.01, [[(statement, 40, s.b["navy"], True)]], anchor="ctr")
    if items[1:]:
        _bullets(s, items[1:], y0=Y0 + card_h + 0.05)


def _image(s, slide, course, extras):
    _header(s, course, slide["title"])
    half = (X1 - X0) / 2
    if slide.get("bullets"):
        _bullets(s, slide["bullets"], x1=X0 + half - 0.02)
    x, w, h = X0 + half + 0.01, half - 0.01, Y1 - Y0
    if extras.get("image_rid"):
        iw, ih = extras["image_size"]
        scale = min(w * s.W / iw, h * s.H / ih)
        pw, ph = iw * scale / s.W, ih * scale / s.H
        s.picture("Visual", extras["image_rid"], x + (w - pw) / 2, Y0 + (h - ph) / 2, pw, ph)
    else:
        s.card("Image placeholder", x, Y0, w, h, s.b["white"], s.b["border"])
        s.text("Image placeholder text", x + 0.02, Y0 + 0.02, w - 0.04, h - 0.04,
               [[("IMAGE TO ADD", 16, s.b["blue"], True)], [(extras.get("image_description") or slide["title"], 20, s.b["slate"], False)]],
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


def _brand(bundle) -> dict:
    return dict(BRAND, **settings.get(bundle, "brand"))


def build(bundle) -> dict:
    from . import editor
    from .visuals import _found, image_size, require_final

    master = require_final(bundle, "Slides")
    snap = bundle.path("_config_snapshot", "assets")
    template = snap / "slide_master.pptx" if (snap / "slide_master.pptx").exists() else ASSETS / "slide_master.pptx"
    background = (snap / "slide_background.png" if (snap / "slide_background.png").exists() else ASSETS / "slide_background.png").read_bytes()
    brand = _brand(bundle)
    course = master["video"]["id"].split("-")[0].upper()

    with zipfile.ZipFile(template) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    pres = parts["ppt/presentation.xml"].decode("utf-8")
    m = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    W, H = int(m.group(1)), int(m.group(2))
    blank = next((n for n, d in parts.items() if n.startswith("ppt/slideLayouts/slideLayout") and n.endswith(".xml") and b'type="blank"' in d), None)
    if blank is None:
        raise Rejected("The Slide Master has no Blank layout.")

    slides, problems, media = [], [], {"ppt/media/fz_background.png": background}
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
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/fz_background.png"/>')
        if extras.get("image_rid"):
            srels += f'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{extras["image_file"]}"/>'
        parts[f"ppt/slides/_rels/slide{i}.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + srels + "</Relationships>").encode("utf-8")
        rels = rels.replace("</Relationships>", f'<Relationship Id="rIdFz{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/></Relationships>')
        types = types.replace("</Types>", f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>')
        ids.append(f'<p:sldId id="{255 + i}" r:id="rIdFz{i}"/>')
    pres = re.sub(r"<p:sldIdLst\s*/>|<p:sldIdLst>.*?</p:sldIdLst>", "<p:sldIdLst>" + "".join(ids) + "</p:sldIdLst>", pres, flags=re.S)
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
