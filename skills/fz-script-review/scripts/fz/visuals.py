"""fz-visuals: images, diagrams and storyboards for the Video's Visual Events, saved into the Editor Pack.

Images: every image Visual Event gets a ready prompt in the Fuzentrix house style; the Host App's own image
tool makes it and saves it under the given name. Storyboards (optional) work the same way for animations.
This checks every required file is there and large enough, and writes a gallery for review."""
from __future__ import annotations

import html
import struct

from . import diagrams, naming, settings
from .bundle import read_json, write_json
from .problems import Rejected

SIZE = (1536, 1024)
MIN_WIDTH = 1024
HOUSE_STYLE = (
    "Clean 2D vector educational illustration on a pure white background. Thick navy outlines, vivid "
    "royal-blue accents, pale-blue fills and soft blue gradients; rounded, friendly shapes. No photorealism, "
    "3D, anime or heavy texture. When a person helps explain the idea, use one friendly young learner: dark "
    "navy hair, simple light face, blue shirt, rounded proportions. One clear hero object, minimal props, no "
    "background rooms or clutter. Short, large, correctly spelled English labels only where they help. Keep "
    "wide empty margins at the edges (the video crops and overlays here). If a caption fits, put one short "
    "sentence in a pale-blue rounded box at the bottom."
)


def image_events(master: dict) -> list:
    return [(seg, e) for seg in master["segments"] for e in seg.get("visual_events", []) if e.get("kind") == "image"]


def image_size(data: bytes):
    """(width, height) of a PNG or JPEG, from its header (standard library only)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def require_final(bundle, what: str) -> dict:
    if bundle.manifest["stages"].get("master", {}).get("status") != "final":
        raise Rejected(f"{what} are built only from the Final Master Script. Approve it at Gate 2 first (fz-master-script).")
    return read_json(bundle.path("02_master", "master.json"))


def storyboard_events(master: dict) -> list:
    return [(seg, e) for seg in master["segments"] for e in seg.get("visual_events", []) if e.get("kind") == "animation"]


def missing_images(bundle, master: dict) -> list:
    return [e for _, e in image_events(master) if _found(naming.asset_path(bundle, e, "image", "png")) is None]


# --- diagrams ----------------------------------------------------------------------------

def diagram_events(master: dict) -> list:
    return [(seg, e) for seg in master["segments"] for e in seg.get("visual_events", []) if e.get("kind") == "diagram"]


def diagram_specs(bundle) -> dict:
    path = bundle.path("visuals", "diagrams.json")
    return {d["event"]: d for d in read_json(path)["diagrams"]} if path.exists() else {}


def diagrams_to_draw(bundle, master: dict) -> list:
    """Diagram events with no spec yet, or whose image-model fallback hasn't been saved."""
    specs = diagram_specs(bundle)
    out = []
    for _, e in diagram_events(master):
        spec = specs.get(e["id"])
        if spec is None or (spec["type"] == "image" and _found(naming.asset_path(bundle, e, "diagram", "png")) is None):
            out.append(e)
    return out


def draft_diagrams(bundle) -> dict:
    master = require_final(bundle, "Diagrams")
    specs = diagram_specs(bundle)
    return {"diagrams": [specs.get(e["id"]) or {"event": e["id"], "description": e["description"], "trigger": e["trigger"], "type": "", "title": ""}
                         for _, e in diagram_events(master)]}


def submit_diagrams(bundle, data: dict) -> int:
    master = require_final(bundle, "Diagrams")
    events = {e["id"]: e for _, e in diagram_events(master)}
    specs = [{k: v for k, v in d.items() if k not in ("description", "trigger")} for d in data.get("diagrams") or []]
    problems = diagrams.validate_all(specs, events)
    if problems:
        raise Rejected(problems)
    merged = dict(diagram_specs(bundle), **{d["event"]: d for d in specs})
    write_json(bundle.path("visuals", "diagrams.json"), {"diagrams": list(merged.values())})
    bundle.manifest["stages"].pop("visuals", None)
    return len(specs)


def _found(path):
    """The saved file for this asset: .png, or the same name as .jpg/.jpeg."""
    for candidate in (path, path.with_suffix(".jpg"), path.with_suffix(".jpeg")):
        if candidate.exists():
            return candidate
    return None


def prompts(bundle) -> str:
    master = require_final(bundle, "Images")
    style = settings.get(bundle, "illustration_style") or HOUSE_STYLE
    events = image_events(master)
    specs = diagram_specs(bundle)
    fallbacks = [(seg, e) for seg, e in diagram_events(master) if specs.get(e["id"], {}).get("type") == "image"]
    if not events and not fallbacks:
        return "This Master Script has no image Visual Events."
    out = [f"{len(events) + len(fallbacks)} image(s). Generate each with the image tool at {SIZE[0]}×{SIZE[1]} (landscape), "
           "save it under the path shown, then run `fz.py build <bundle> visuals`.", "", f"House style (for every image): {style}", ""]
    for seg, e in events:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'image', 'png'))} ({SIZE[0]}×{SIZE[1]})",
                f"  Segment {seg['id']} · {seg['title']} · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} Scene: {e['description']} It illustrates: {seg.get('meaning_en', '')}", ""]
    for seg, e in fallbacks:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'diagram', 'png'))} ({SIZE[0]}×{SIZE[1]}, diagram)",
                f"  Segment {seg['id']} · {seg['title']} · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} A clear explanatory diagram: {specs[e['id']]['prompt']} Labels must be spelled exactly.", ""]
    return "\n".join(out)


def storyboard_prompts(bundle) -> str:
    master = require_final(bundle, "Storyboards")
    style = settings.get(bundle, "illustration_style") or HOUSE_STYLE
    events = storyboard_events(master)
    if not events:
        return "This Master Script has no animation Visual Events to storyboard."
    out = [f"{len(events)} animation(s). Storyboards are optional: each is ONE image with 4 numbered panels (2×2) showing how the "
           f"animation unfolds. Generate at {SIZE[0]}×{SIZE[1]}, save under the path shown, then run `fz.py build <bundle> visuals`.", ""]
    for seg, e in events:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'storyboard', 'png'))}",
                f"  Animation Template: {e.get('template') or 'custom'} · {e.get('duration_sec') or 3} s · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} A 4-panel storyboard, panels numbered 1–4, showing step by step: {e['description']}", ""]
    return "\n".join(out)


def build(bundle) -> dict:
    from . import editor

    master = require_final(bundle, "Visuals")
    problems, rows = [], []
    for kind, events, required in (("image", image_events(master), True), ("storyboard", storyboard_events(master), False)):
        for seg, e in events:
            path = naming.asset_path(bundle, e, kind, "png")
            f = _found(path)
            if f is None:
                if required:
                    problems.append(f"{naming.relative(bundle, path)} is missing: generate it from `fz.py show <bundle> image-prompts` "
                                    "and save it there (or remove the Visual Event in the Master Script).")
                continue
            size = image_size(f.read_bytes())
            if size is None:
                problems.append(f"{f.name} is not a readable PNG or JPEG.")
            elif size[0] < MIN_WIDTH:
                problems.append(f"{f.name} is {size[0]}×{size[1]}; images need to be at least {MIN_WIDTH} pixels wide for video. "
                                f"Generate it again at {SIZE[0]}×{SIZE[1]}.")
            else:
                rows.append((kind, seg, e, f, size))
    specs = diagram_specs(bundle)
    drawn = png_missing = 0
    for seg, e in diagram_events(master):
        spec = specs.get(e["id"])
        png = naming.asset_path(bundle, e, "diagram", "png")
        if spec is None:
            problems.append(f"{e['id']} needs a diagram spec: start from `fz.py draft <bundle> diagrams all <file>`, "
                            "then `fz.py submit <bundle> diagrams <file>`.")
        elif spec["type"] == "image":
            f = _found(png)
            if f is None:
                problems.append(f"{naming.relative(bundle, png)} is missing: generate it from `fz.py show <bundle> image-prompts`.")
            else:
                rows.append(("diagram", seg, e, f, image_size(f.read_bytes()) or (0, 0)))
        else:
            ok = diagrams.draw(spec, png.with_suffix(".svg"), png)
            drawn += 1
            png_missing += 0 if ok else 1
            rows.append(("diagram", seg, e, png if ok else png.with_suffix(".svg"), (diagrams.W, diagrams.H)))
    if problems:
        raise Rejected(problems)
    _gallery(bundle, master, rows)
    bundle.manifest["stages"]["visuals"] = {"status": "built", "images": sum(1 for r in rows if r[0] == "image"),
                                            "diagrams": sum(1 for r in rows if r[0] == "diagram"),
                                            "storyboards": sum(1 for r in rows if r[0] == "storyboard"),
                                            "png_missing": png_missing}
    bundle.log("visuals built")
    editor.build(bundle)
    return bundle.manifest["stages"]["visuals"]


def _gallery(bundle, master: dict, rows: list) -> None:
    md = [f"# Visuals: {master['video'].get('title') or master['video']['id']}", ""]
    cards = []
    for kind, seg, e, f, size in rows:
        rel = f.relative_to(naming.pack_dir(bundle)).as_posix()
        md += [f"- **{e['id']}** · {kind} · `{rel}` ({size[0]}×{size[1]}) · {seg['title']} · starts on \"{e['trigger']}\""]
        cards.append(f'<figure><img src="{html.escape(rel)}" alt="{html.escape(e["description"])}"><figcaption><strong>{e["id"]}</strong> · {kind} · '
                     f'{html.escape(seg["title"])}<br>Starts on: “{html.escape(e["trigger"])}”</figcaption></figure>')
    if not rows:
        md.append("No images or storyboards.")
    page = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Visuals</title><style>"
            "body{font-family:system-ui,sans-serif;margin:2rem;color:#13213c}figure{display:inline-block;width:46%;margin:1%;vertical-align:top}"
            "img{width:100%;border:1px solid #dce7f4;border-radius:8px;background:#fff}figcaption{font-size:14px;margin-top:.4rem}</style></head>"
            f"<body><h1>Visuals</h1>{''.join(cards) or '<p>No images or storyboards.</p>'}</body></html>\n")
    naming.pack_dir(bundle).mkdir(parents=True, exist_ok=True)
    naming.pack_dir(bundle, "visuals.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    naming.pack_dir(bundle, "visuals.html").write_text(page, encoding="utf-8")
