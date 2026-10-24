"""The Brand Kit: how Fuzentrix content looks (slide template, backgrounds, fonts, colours, logos, styles,
characters). Skills take every brand value from here; their code holds none.

Where a value comes from, in order: an override the user gave in the prompt (recorded with its source),
the Brand Kit attached to the bundle, then the Default Brand Kit shipped with the skill (defaults/brand/).
A bundle has no Brand Kit until one is chosen: the skill asks the user for theirs and, if they have none,
attaches the default."""
from __future__ import annotations

import copy
import re
import shutil
from pathlib import Path

from . import SKILL_VERSION, kits
from .bundle import now
from .problems import Rejected

DEFAULT = Path(__file__).parent / "defaults" / "brand"
STAGES = ("slides", "visuals", "editor_kit", "cheatsheet")   # built from the Brand Kit; stale when it changes
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
ASK = ("Next: choose a Brand Kit. Ask the user for theirs (the Brand Kit release .zip, attached or added from Google Drive), "
       "then `fz.py attach <bundle> brand <zip>`; if they have none, `fz.py attach <bundle> brand default`.")


def _check(files: dict) -> list:
    data = kits.load_yaml(files["brand.yaml"].decode("utf-8"))
    return check_data(data, files.get)


BRAND = kits.KitType(
    name="Brand Kit", key="brand", version_key="brand_version", schema_key="brand_schema_version", schema_version=1,
    zip_prefix="fuzentrix-brand", snapshot="_brand_snapshot", folder_hint="Fuzentrix Brand Kit",
    suffixes=frozenset({".yaml", ".yml", ".md", ".txt", ".json", ".pptx", ".potx", ".png", ".jpg", ".jpeg", ".svg",
                        ".ttf", ".otf", ".woff"}),
    required=("brand.yaml",), affects={"brand.yaml": list(STAGES)}, check=_check)


class Brand:
    """One resolved Brand Kit: its data, its files, and where it came from."""

    def __init__(self, data: dict, read, info: dict):
        self.data, self._read, self.info = data, read, info
        self._measures = {}

    def get(self, path: str, default=None):
        node = self.data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def color(self, value: str) -> str:
        """'#RRGGBB' for a colour token name or a hex value."""
        value = str(value)
        if HEX.match(value):
            return value.upper()
        colors = self.data.get("colors", {})
        if value not in colors:
            raise Rejected(f"The Brand Kit has no colour '{value}' (colors: {', '.join(colors)}).")
        return str(colors[value]).upper()

    def rgb(self, value: str) -> str:
        """'RRGGBB', as PowerPoint wants it."""
        return self.color(value)[1:]

    def font(self, role: str) -> dict:
        return dict(self.data["fonts"][role])

    def family(self, role: str) -> str:
        return self.data["fonts"][role]["family"]

    def file(self, rel: str) -> bytes:
        data = self._read(rel) if rel else None
        if data is None:
            raise Rejected(f"The Brand Kit names {rel}, but the file is not in the kit.")
        return data

    def measure(self, role: str):
        """Text width for a font role: exact from the kit's font file, or from avg_char_width."""
        from .fonts import Measure

        if role not in self._measures:
            f = self.font(role)
            self._measures[role] = Measure(self.file(f["file"]) if f.get("file") else None, f.get("avg_char_width", 0.55))
        return self._measures[role]

    @property
    def label(self) -> str:
        return f"{self.info.get('id')} {self.info.get('version')}" + (" (default)" if self.info.get("source") == "default" else "")


# --- loading -------------------------------------------------------------------------------

def _default_data() -> dict:
    return kits.load_yaml((DEFAULT / "brand.yaml").read_text(encoding="utf-8"))


def _read_dir(folder: Path):
    def read(rel):
        p = folder / rel
        return p.read_bytes() if p.is_file() else None
    return read


def default() -> Brand:
    data = _default_data()
    return Brand(data, _read_dir(DEFAULT), {"source": "default", "id": data["brand"]["id"], "version": default_version()})


def default_version() -> str:
    return f"default-{SKILL_VERSION}"


def merged(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merged(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _get(data: dict, path: str):
    node = data
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _set(data: dict, path: str, value) -> None:
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def load(bundle) -> Brand:
    """The bundle's Brand Kit, with prompt overrides applied. Rejected with the next step if none is chosen."""
    rec = bundle.manifest.get("brand")
    if not rec:
        raise Rejected(ASK.replace("Next: choose", "Choose", 1))
    data = _default_data()
    read = _read_dir(DEFAULT)
    snap = kits.snapshot_dir(BRAND, bundle.root)
    if rec.get("source") != "default":
        if not (snap / "brand.yaml").exists():
            raise Rejected(f"The bundle's Brand Kit {rec.get('version')} is missing from {BRAND.snapshot}/; attach it again.")
        data = merged(data, kits.load_yaml((snap / "brand.yaml").read_text(encoding="utf-8")))
        kit_read, base_read = _read_dir(snap), read
        read = lambda rel: kit_read(rel) if kit_read(rel) is not None else base_read(rel)
    for path, o in (rec.get("overrides") or {}).items():
        _set(data, path, o["value"])
    return Brand(data, read, dict(rec))


def publish_main(argv=None) -> int:
    return kits.publish_main(BRAND, argv)


# --- checks ----------------------------------------------------------------------------------

def house_style(brand) -> str:
    """The Brand Kit's illustration style plus its characters, as one prompt preface."""
    style = " ".join(str(brand.get("illustration.style") or "").split())
    people = " ".join(f"When {c['use_when']}, use {c['description']}." for c in brand.get("characters") or [])
    refs = [r for c in brand.get("characters") or [] for r in c.get("references") or []] + list(brand.get("illustration.references") or [])
    avoid = brand.get("illustration.negative") or []
    avoid = f"Avoid: {', '.join(avoid)}." if avoid else ""
    attach = f" Reference images in the Brand Kit ({', '.join(refs)}): attach them to the image tool when it accepts images." if refs else ""
    return " ".join(x for x in (style, avoid, people) if x) + attach


def image_size_wanted(brand) -> tuple:
    w, h = brand.get("illustration.size") or (1536, 1024)
    return int(w), int(h)


def check_data(data: dict, read) -> list:
    """Problems with a Brand Kit's brand.yaml and the files it names. read(rel) → bytes or None."""
    if not isinstance(data, dict):
        return ["brand.yaml must be a mapping."]
    full = merged(_default_data(), data)
    default_read = _read_dir(DEFAULT)
    problems = []
    if data.get("schema") != 1:
        problems.append("brand.yaml: 'schema' must be 1.")
    if not str((data.get("brand") or {}).get("id", "")).strip():
        problems.append("brand.yaml: brand.id is required (a short name such as fuzentrix).")
    colors = full.get("colors") or {}
    for name, value in colors.items():
        if not HEX.match(str(value)):
            problems.append(f"brand.yaml: colors.{name} must be a hex colour like \"#0A59C8\" (is {value!r}).")
    if problems:
        return problems
    tokens = set(colors)

    def color_ok(where, value):
        if not (HEX.match(str(value)) or value in tokens):
            problems.append(f"brand.yaml: {where} is '{value}', which is neither a colour token ({', '.join(sorted(tokens))}) nor \"#RRGGBB\".")
    for section in ("slides", "diagrams"):
        for k, v in ((full.get(section) or {}).get("colors") or {}).items():
            color_ok(f"{section}.colors.{k}", v)
    color_ok("slides.label.color", full["slides"]["label"]["color"])
    def walk(prefix, node):
        for k, v in node.items():
            if k in ("icons", "labels"):
                continue
            if isinstance(v, dict):
                walk(f"{prefix}.{k}", v)
            else:
                color_ok(f"{prefix}.{k}", v)
    walk("cheatsheet", full.get("cheatsheet") or {})
    keys = (full.get("illustration") or {}).get("key_colors") or []
    if not keys or not all(HEX.match(str(k)) for k in keys):
        problems.append("brand.yaml: illustration.key_colors must list hex colours like \"#00FF00\".")
    from .vocab import ENTRANCES

    for role, how in ((full.get("motion") or {}).get("entrances") or {}).items():
        if how not in ENTRANCES:
            problems.append(f"brand.yaml: motion.entrances.{role} must be one of {', '.join(ENTRANCES)}.")
    negative = (full.get("illustration") or {}).get("negative") or []
    if not isinstance(negative, list) or not all(isinstance(n, str) and n.strip() for n in negative):
        problems.append("brand.yaml: illustration.negative must list short phrases, e.g. [photorealism, clutter].")
    for i, c in enumerate(full["slides"]["title"]["colors"]):
        color_ok(f"slides.title.colors[{i}]", c)

    def reader(path):
        """Files the kit itself names must be in the kit; values it leaves out come from the Default Brand Kit."""
        return read if _get(data, path) is not None else default_read

    def need(where, path, rel):
        """True if the file is here to check. A file the kit leaves to the Default Brand Kit may be missing from this
        skill (only fz-slides carries the default slide template); the default kit is checked when it is published."""
        if rel and reader(path)(rel) is None:
            if _get(data, path) is None:
                return False
            problems.append(f"brand.yaml: {where} names {rel}, which is not in the kit.")
            return False
        return bool(rel)
    for role, f in (full.get("fonts") or {}).items():
        if isinstance(f, dict) and need(f"fonts.{role}.file", f"fonts.{role}.file", f.get("file")):
            from .fonts import Font
            try:
                Font(reader(f"fonts.{role}.file")(f["file"]))
            except Exception as e:
                problems.append(f"fonts.{role}.file ({f['file']}) can't be read as a font: {e}.")
    for name, rel in (full.get("logos") or {}).items():
        need(f"logos.{name}", f"logos.{name}", rel)
    for i, ref in enumerate((full.get("illustration") or {}).get("references") or []):
        need(f"illustration.references[{i}]", "illustration.references", ref)
    for c in full.get("characters") or []:
        for ref in c.get("references") or []:
            need(f"characters.{c.get('id')}.references", "characters", ref)
    slides = full["slides"]
    from .vocab import SLIDE_LAYOUTS as LAYOUTS

    backgrounds = {}
    if need("slides.background", "slides.background", slides.get("background")):
        backgrounds["slides.background"] = reader("slides.background")(slides["background"])
    for layout, rel in (slides.get("backgrounds") or {}).items():
        if layout not in LAYOUTS:
            problems.append(f"brand.yaml: slides.backgrounds: '{layout}' is not a slide layout ({', '.join(LAYOUTS)}).")
        elif need(f"slides.backgrounds.{layout}", f"slides.backgrounds.{layout}", rel):
            backgrounds[f"slides.backgrounds.{layout}"] = reader(f"slides.backgrounds.{layout}")(rel)
    if need("slides.template", "slides.template", slides.get("template")) and backgrounds:
        problems += _check_template(reader("slides.template")(slides["template"]), backgrounds)
    problems += _check_areas(slides)
    for fg, bg in (("on_primary", "primary"), ("ink", "surface"), ("ink", "surface_alt"), ("code_text", "code_bg")):
        if fg in colors and bg in colors:
            ratio = contrast(colors[fg], colors[bg])
            if ratio < 4.5:
                problems.append(f"colors.{fg} on colors.{bg} has contrast {ratio:.1f}:1; text needs at least 4.5:1 to be readable.")
    return problems


def _check_template(template: bytes, backgrounds: dict) -> list:
    """backgrounds: {"slides.background": bytes, "slides.backgrounds.title": bytes, …}, each checked against the slide shape."""
    import io
    import zipfile

    from .png import size as image_size

    try:
        with zipfile.ZipFile(io.BytesIO(template)) as z:
            pres = z.read("ppt/presentation.xml").decode("utf-8")
            layouts = [z.read(n) for n in z.namelist() if n.startswith("ppt/slideLayouts/slideLayout") and n.endswith(".xml")]
    except Exception:
        return ["slides.template is not a readable PowerPoint file."]
    problems = []
    if not any(b'type="blank"' in d for d in layouts):
        problems.append("slides.template needs a Blank layout (slides are drawn on it).")
    m = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    for where, background in backgrounds.items():
        size = image_size(background)
        if size is None:
            problems.append(f"{where} must be a PNG or JPEG.")
        elif m and abs(size[0] / size[1] - int(m.group(1)) / int(m.group(2))) > 0.02:
            problems.append(f"{where} is {size[0]}×{size[1]}, which doesn't match the template's slide shape; it would be stretched.")
    return problems


def _check_areas(slides: dict) -> list:
    a, p = slides["content_area"], slides["presenter_area"]
    overlap_x = a["left"] < p["x"] + p["w"] and p["x"] < a["right"]
    overlap_y = a["top"] < p["y"] + p["h"] and p["y"] < a["bottom"]
    if overlap_x and overlap_y:
        return ["slides.content_area overlaps slides.presenter_area; the presenter would cover slide content."]
    return []


def contrast(a: str, b: str) -> float:
    def lum(hex_):
        rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# --- choosing a Brand Kit for a bundle --------------------------------------------------------

def attach(bundle, source) -> dict:
    """Snapshot a Brand Kit release (or choose the default) for this bundle. Stages built from the old one go stale."""
    snap = kits.snapshot_dir(BRAND, bundle.root)
    if str(source) == "default":
        data = _default_data()
        rec = {"source": "default", "id": data["brand"]["id"], "version": default_version()}
        if snap.exists():
            shutil.rmtree(snap)
    else:
        manifest, files = kits.read_release(BRAND, source)
        data = kits.load_yaml(files["brand.yaml"].decode("utf-8"))
        kits.snapshot(BRAND, bundle.root, manifest, files)
        rec = {"source": "attached", "id": data["brand"]["id"], "version": manifest[BRAND.version_key],
               "origin": Path(source).name}
    rec.update(attached_at=now(), overrides={})
    bundle.manifest["brand"] = rec
    stale = mark_stale(bundle)
    bundle.log(f"brand kit {rec['id']} {rec['version']} ({rec['source']})")
    return dict(rec, stale=stale)


def signature(bundle) -> str:
    """The Brand Kit a stage is built from, as people read it: "acme 2026.10.21.1 + colors.primary=#FF6600"."""
    rec = bundle.manifest.get("brand") or {}
    if not rec:
        return ""
    sig = f"{rec['id']} {rec['version']}"
    overrides = sorted((rec.get("overrides") or {}).items())
    return sig + ("".join(f" + {p}={o['value']}" for p, o in overrides) if overrides else "")


def mark_stale(bundle) -> list:
    """Stages built from another Brand Kit than the bundle's now: kept, marked to rebuild, with the kit they used."""
    now_ = signature(bundle)
    stale = []
    for s in STAGES:
        stage = bundle.manifest.get("stages", {}).get(s)
        if stage and stage.get("status") in ("built", "stale") and stage.get("brand", "") != now_:
            stage.update(status="stale", brand=stage.get("brand") or "none recorded")
            stale.append(s)
    return stale


def stale_note(bundle, stage: str, command: str) -> str:
    """The status line for a stage built with an older Brand Kit, or "" if it is not."""
    st = bundle.manifest.get("stages", {}).get(stage, {})
    if st.get("status") != "stale":
        return ""
    return f"Next: rebuild: built with an older Brand Kit ({st.get('brand')}); now {signature(bundle)}. `{command}`"


def override(bundle, path: str, value, note: str = "") -> dict:
    """Change one Brand Kit value for this bundle only, as the user asked in the prompt."""
    brand = load(bundle)
    current = brand.get(path, None)
    if current is None or isinstance(current, (dict, list)):
        raise Rejected(f"'{path}' is not a single Brand Kit value. See `fz.py show <bundle> brand` for the values you can change.")
    if path.startswith("colors.") and not HEX.match(str(value)):
        raise Rejected(f"{path} must be a hex colour like \"#0A59C8\".")
    if path.startswith("motion.entrances."):
        from .vocab import ENTRANCES

        if value not in ENTRANCES:
            raise Rejected(f"{path} must be one of {', '.join(ENTRANCES)}.")
    rec = bundle.manifest["brand"]
    rec.setdefault("overrides", {})[path] = {"value": value, "was": current, "source": "prompt", "note": note, "at": now()}
    mark_stale(bundle)
    bundle.log(f"brand override {path} = {value}")
    return rec["overrides"][path]


def describe(bundle) -> str:
    rec = bundle.manifest.get("brand")
    if not rec:
        return ASK
    brand = load(bundle)
    out = [f"Brand Kit {rec['id']} {rec['version']} · {rec['source']}" + (f" ({rec['origin']})" if rec.get("origin") else "")]
    for path, o in (rec.get("overrides") or {}).items():
        out.append(f"  override {path} = {o['value']} (was {o['was']}; from the prompt" + (f": {o['note']}" if o.get("note") else "") + ")")
    out.append("Colours: " + ", ".join(f"{k} {v}" for k, v in brand.data["colors"].items()))
    out.append("Fonts: " + ", ".join(f"{r} {f['family']}" + (" (file)" if f.get("file") else "")
                                      for r, f in brand.data["fonts"].items() if isinstance(f, dict)))
    out.append(f"Slides: template {brand.get('slides.template')}, background {brand.get('slides.background')}, "
               f"label \"{brand.get('slides.label.text')}\", titles {brand.get('slides.title.case')}")
    by_layout = brand.get("slides.backgrounds") or {}
    out.append("Slide backgrounds by layout: " + (", ".join(f"{k} {v}" for k, v in by_layout.items()) or "none"))
    out.append("Characters: " + (", ".join(c["id"] for c in brand.data.get("characters") or []) or "none"))
    out.append("Images avoid: " + (", ".join(brand.get("illustration.negative") or []) or "nothing listed"))
    out.append("Animation entrances: " + ", ".join(f"{k} {v}" for k, v in (brand.get("motion.entrances") or {}).items()))
    return "\n".join(out)
