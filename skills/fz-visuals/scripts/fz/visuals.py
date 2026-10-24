"""fz-visuals: images, diagrams and storyboards for the Video's Visual Events, saved into the Editor Kit.

Images: every image Visual Event gets a ready prompt in the Fuzentrix house style; the Host App's own image
tool makes it and saves it under the given name. Storyboards (optional) work the same way for animations.
This checks every required file is there and large enough, and writes a gallery for review."""
from __future__ import annotations

import html

from . import brandkit, diagrams, naming, views
from .brandkit import house_style, image_size_wanted  # noqa: F401  (the image prompts use them)
from .png import size as image_size
from .bundle import read_json, write_json
from .problems import Rejected

MIN_WIDTH = 1024


def image_events(master: dict) -> list:
    return [(seg, e) for seg in master["segments"] for e in seg.get("visual_events", []) if e.get("kind") == "image"]


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
    problems = diagrams.validate_all(specs, events, brandkit.load(bundle))
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
    brand = brandkit.load(bundle)
    style, size = house_style(brand), image_size_wanted(brand)
    events = image_events(master)
    specs = diagram_specs(bundle)
    fallbacks = [(seg, e) for seg, e in diagram_events(master) if specs.get(e["id"], {}).get("type") == "image"]
    if not events and not fallbacks:
        return "This Master Script has no image Visual Events."
    out = [f"{len(events) + len(fallbacks)} image(s). Generate each with the image tool at {size[0]}×{size[1]} (landscape), "
           "save it under the path shown, then run `fz.py build <bundle> visuals`.", "", f"House style (for every image): {style}", ""]
    for seg, e in events:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'image', 'png'))} ({size[0]}×{size[1]})",
                f"  Segment {seg['id']} · {seg['title']} · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} Scene: {e['description']} It illustrates: {seg.get('meaning_en', '')}", ""]
    for seg, e in fallbacks:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'diagram', 'png'))} ({size[0]}×{size[1]}, diagram)",
                f"  Segment {seg['id']} · {seg['title']} · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} A clear explanatory diagram: {specs[e['id']]['prompt']} Labels must be spelled exactly.", ""]
    return "\n".join(out)


def storyboard_prompts(bundle) -> str:
    master = require_final(bundle, "Storyboards")
    brand = brandkit.load(bundle)
    style, size = house_style(brand), image_size_wanted(brand)
    panels, grid = brand.get("storyboard.panels") or 4, brand.get("storyboard.grid") or "2×2"
    events = storyboard_events(master)
    if not events:
        return "This Master Script has no animation Visual Events to storyboard."
    out = [f"{len(events)} animation(s). Storyboards are optional: each is ONE image with {panels} numbered panels ({grid}) showing how the "
           f"animation unfolds. Generate at {size[0]}×{size[1]}, save under the path shown, then run `fz.py build <bundle> visuals`.", ""]
    for seg, e in events:
        out += [f"{e['id']} → {naming.relative(bundle, naming.asset_path(bundle, e, 'storyboard', 'png'))}",
                f"  Animation Template: {e.get('template') or 'custom'} · {e.get('duration_sec') or 3} s · starts on \"{e['trigger']}\"",
                f"  Prompt: {style} A {panels}-panel storyboard, panels numbered 1–{panels}, showing step by step: {e['description']}", ""]
    return "\n".join(out)


def build(bundle, without_images: bool = False) -> dict:
    """Everything the Editor Kit needs. without_images: build what code can draw now, with placeholders where AI
    elements go, and leave the stage unfinished until the images are made (for apps that can't generate images)."""
    from . import editor

    master = require_final(bundle, "Visuals")
    brand = brandkit.load(bundle)
    problems, rows, missing = [], [], []
    for kind, events, required in (("image", image_events(master), True), ("storyboard", storyboard_events(master), False)):
        for seg, e in events:
            path = naming.asset_path(bundle, e, kind, "png")
            f = _found(path)
            if f is None:
                if required:
                    (missing if without_images else problems).append(
                        f"{naming.relative(bundle, path)} is missing: generate it from `fz.py show <bundle> image-prompts` "
                        "and save it there (or remove the Visual Event in the Master Script).")
                continue
            size = image_size(f.read_bytes())
            if size is None:
                problems.append(f"{f.name} is not a readable PNG or JPEG.")
            elif size[0] < MIN_WIDTH:
                problems.append(f"{f.name} is {size[0]}×{size[1]}; images need to be at least {MIN_WIDTH} pixels wide for video. "
                                "Generate it again at the size `fz.py show <bundle> image-prompts` gives.")
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
                (missing if without_images else problems).append(
                    f"{naming.relative(bundle, png)} is missing: generate it from `fz.py show <bundle> image-prompts`.")
            else:
                rows.append(("diagram", seg, e, f, image_size(f.read_bytes()) or (0, 0)))
        else:
            ok = diagrams.draw(spec, png.with_suffix(".svg"), png, diagrams.theme_of(brand, e.get("layout")))
            drawn += 1
            png_missing += 0 if ok else 1
            rows.append(("diagram", seg, e, png if ok else png.with_suffix(".svg"), (diagrams.W, diagrams.H)))
    from . import animations
    for e in animations.to_specify(bundle, master):
        problems.append(f"{e['id']} needs an animation spec: start from `fz.py draft <bundle> animations all <file>`, "
                        "then `fz.py submit <bundle> animations <file>`.")
    problems += animations.check_ai(bundle, master, brand, allow_missing=without_images)
    if problems:
        raise Rejected(problems)
    missing += [e["id"] for e, _ in animations.missing_ai(bundle, master)] if without_images else []
    for seg, e, preview in animations.build_all(bundle, master, brand, placeholders=without_images):
        rows.append(("animation", seg, e, preview, image_size(preview.read_bytes()) if preview.suffix == ".png" else (diagrams.W, diagrams.H)))
    _gallery(bundle, master, rows)
    bundle.manifest["stages"]["visuals"] = {"status": "partial" if missing else "built", "missing": len(missing),
                                            "images": sum(1 for r in rows if r[0] == "image"),
                                            "diagrams": sum(1 for r in rows if r[0] == "diagram"),
                                            "storyboards": sum(1 for r in rows if r[0] == "storyboard"),
                                            "animations": sum(1 for r in rows if r[0] == "animation"),
                                            "png_missing": png_missing, "brand": brandkit.signature(bundle)}
    bundle.log("visuals built")
    editor.build(bundle)
    return bundle.manifest["stages"]["visuals"]


def _gallery(bundle, master: dict, rows: list) -> None:
    md = [f"# Visuals: {master['video'].get('title') or master['video']['id']}", ""]
    cards = []
    for kind, seg, e, f, size in rows:
        rel = f.relative_to(naming.kit_dir(bundle)).as_posix()
        md += [f"- **{e['id']}** · {kind} · `{rel}` ({size[0]}×{size[1]}) · {seg['title']} · starts on \"{e['trigger']}\""]
        cards.append(f'<figure><img src="{html.escape(rel)}" alt="{html.escape(e["description"])}"><figcaption><strong>{e["id"]}</strong> · {kind} · '
                     f'{html.escape(seg["title"])}<br>Starts on: “{html.escape(e["trigger"])}”</figcaption></figure>')
    if not rows:
        md.append("No images or storyboards.")
    page = views.gallery_page("Visuals", "".join(cards) or "<p>No images or storyboards.</p>")
    naming.kit_dir(bundle).mkdir(parents=True, exist_ok=True)
    naming.kit_dir(bundle, "visuals.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    naming.kit_dir(bundle, "visuals.html").write_text(page, encoding="utf-8")
