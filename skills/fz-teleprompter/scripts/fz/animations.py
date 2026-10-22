"""Animations in the Editor Kit: everything a Video Editor needs to build each animation by hand in Premiere
(no AI), and the spec.json the motion-animation workflow builds from.

The Host App writes an animation spec per animation Visual Event: its template, its content (for templates
code can draw, a diagram spec) and its steps: which elements appear at each step, and the spoken words that
trigger it. The build draws, in the Brand Kit's style:
- elements/: one full-frame 1920×1080 transparent layer per element, z-order in the name, so layers stacked
  in Premiere line up exactly;
- states/: the full frame after each step, to cut or cross-fade between;
- storyboard: every state on one sheet, with its step number and trigger;
- step_sheet.md/.csv: when each step appears, timed from the narration;
- spec.json: the contract for the motion workflow (spec_version 1.0).
Illustrated templates (character_scene, concept_reveal, transform_morph) mix elements the image tool draws on a
transparent background (or a flat key colour the build removes) with code-drawn captions and arrows; each is
placed in its own box on a full-frame layer.
A "custom" animation (nothing code can draw) gets the step sheet and spec.json from described steps.
"""
from __future__ import annotations

import csv
import json
import math

import re

from . import SKILL_VERSION, brandkit, diagrams, naming, png, settings
from .bundle import read_json, write_json
from .problems import Rejected

SPEC_VERSION = "1.0"
FPS = 30
DEFAULT_DURATION = 3
MAX_STEPS = 8
# Animation Template → the diagram type that draws it
TEMPLATES = {"flow": "flow", "flowchart": "flowchart", "table_build": "table", "tree_graph": "tree", "compare_split": "compare",
             "timeline": "timeline", "cycle": "cycle", "layers": "layers", "list_build": "list", "agenda_build": "list",
             "code_typing": "code", "stat_callout": "stat", "title_card": "title", "array_pointer": "array"}
CUSTOM = "custom"
ILLUSTRATED = ("character_scene", "concept_reveal", "transform_morph")
KINDS = ("ai", "text", "arrow")


def animation_events(master: dict) -> list:
    return [(seg, e) for seg in master["segments"] for e in seg.get("visual_events", []) if e.get("kind") == "animation"]


def specs(bundle) -> dict:
    path = bundle.path("visuals", "animations.json")
    return {a["event"]: a for a in read_json(path)["animations"]} if path.exists() else {}


def _rgb(hex_: str) -> tuple:
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def key_color(brand) -> str:
    """The flat background the image tool may use instead of transparency: the Brand Kit's first key colour
    that is far from every brand colour."""
    keys = [k.upper() for k in brand.get("illustration.key_colors") or []]
    colours = [_rgb(brand.color(c)) for c in brand.data.get("colors", {})]
    for k in keys:
        if all(png._dist(c, _rgb(k)) >= 150 for c in colours):
            return k
    return max(keys, key=lambda k: min(png._dist(c, _rgb(k)) for c in colours))


def ai_file(bundle, event_id: str, template: str, element_id: str):
    return folder(bundle, event_id, template) / "ai" / f"{naming.video_id(bundle)}_{event_id}_{element_id}.png"


def missing_ai(bundle, master: dict) -> list:
    """(event, element) pairs whose illustration hasn't been saved yet."""
    out = []
    for _, e in animation_events(master):
        a = specs(bundle).get(e["id"])
        if a and a["template"] in ILLUSTRATED:
            out += [(e, el) for el in a["elements"] if el["kind"] == "ai" and not ai_file(bundle, e["id"], a["template"], el["id"]).exists()]
    return out


def prompts(bundle) -> str:
    from .visuals import house_style, require_final

    master = require_final(bundle, "Animation elements")
    brand = brandkit.load(bundle)
    style, key = house_style(brand), key_color(brand)
    people = {c["id"]: c for c in brand.data.get("characters") or []}
    rows = []
    for seg, e in animation_events(master):
        a = specs(bundle).get(e["id"])
        if not a or a["template"] not in ILLUSTRATED:
            continue
        for el in a["elements"]:
            if el["kind"] != "ai":
                continue
            w, h = el["place"][2], el["place"][3]
            size = (1536, 1024) if w / h > 1.3 else (1024, 1536) if w / h < 0.77 else (1024, 1024)
            who = people.get(el.get("character"))
            refs = ", ".join(who.get("references") or []) if who else ""
            rows += [f"{e['id']} · {a['template']} · {el['id']} → {naming.relative(bundle, ai_file(bundle, e['id'], a['template'], el['id']))} "
                     f"({size[0]}×{size[1]})",
                     f"  Prompt: {style}" + (f" The character is {who['description']}." if who else "")
                     + f" Draw ONLY this, alone: {el['describe']}. Transparent background (a PNG cut-out): no scene, floor, shadow or "
                     f"frame. If the image tool can't make a transparent background, use a flat, solid {key} background instead; "
                     "it is removed automatically.",
                     f"  Reference images to attach: {refs}" if refs else "", ""]
    if not rows:
        return "No illustrated animation elements: every animation is drawn by code."
    return "\n".join([f"{sum(1 for r in rows if ' → ' in r)} animation element(s). Generate each with the image tool, save it under the "
                      "path shown, then run `fz.py build <bundle> visuals`.", ""] + [r for r in rows if r is not None])


def to_specify(bundle, master: dict) -> list:
    have = specs(bundle)
    return [e for _, e in animation_events(master) if e["id"] not in have]


def folder(bundle, event_id: str, template: str):
    return naming.kit_dir(bundle, "animations", f"{naming.video_id(bundle)}_{event_id}_{template.replace('_', '-')}")


def _spoken(seg: dict) -> str:
    return " ".join(s["text"] for s in seg.get("spoken", []))


# --- draft and submit --------------------------------------------------------------------

def draft(bundle) -> dict:
    from .visuals import require_final

    master = require_final(bundle, "Animations")
    have = specs(bundle)
    out = []
    for seg, e in animation_events(master):
        if e["id"] in have:
            out.append(have[e["id"]])
            continue
        template = e.get("template") if e.get("template") in TEMPLATES or e.get("template") in ILLUSTRATED else ""
        entry = {"event": e["id"], "template": template, "description": e["description"], "trigger": e["trigger"],
                 "duration_sec": e.get("duration_sec") or DEFAULT_DURATION, "spoken": _spoken(seg)}
        if template in ILLUSTRATED:
            entry["elements"] = []
        else:
            entry["diagram"] = {"type": TEMPLATES.get(template, "")}
        out.append(dict(entry, steps=[]))
    return {"animations": out}


def submit(bundle, data: dict) -> int:
    from . import editor
    from .visuals import require_final

    master = require_final(bundle, "Animations")
    brand = brandkit.load(bundle)
    events = {e["id"]: (seg, e) for seg, e in animation_events(master)}
    index = editor.spoken_index(bundle, master)
    keep = ("event", "template", "diagram", "elements", "steps")
    given = [{k: v for k, v in a.items() if k in keep} for a in data.get("animations") or []]
    problems, seen = [], set()
    for i, a in enumerate(given, 1):
        ev = a.get("event")
        label = f"Animation {i} ({ev})"
        if ev not in events:
            problems.append(f"{label}: {ev} is not an animation Visual Event in the Final Master Script ({', '.join(events) or 'none'}).")
            continue
        if ev in seen:
            problems.append(f"{label}: {ev} is given twice.")
        seen.add(ev)
        problems += _check(bundle, a, label, events[ev][0], index[events[ev][0]["id"]]["words"], brand)
    if problems:
        raise Rejected(problems)
    for a in given:
        if a["template"] in ILLUSTRATED or a["template"] == CUSTOM:
            a.pop("diagram", None)
        if a["template"] not in ILLUSTRATED:
            a.pop("elements", None)
    merged = dict(specs(bundle), **{a["event"]: a for a in given})
    write_json(bundle.path("visuals", "animations.json"), {"animations": list(merged.values())})
    bundle.manifest["stages"].pop("visuals", None)
    return len(given)


def _check(bundle, a: dict, label: str, seg: dict, words: list, brand) -> list:
    from . import editor

    template = a.get("template")
    if template not in TEMPLATES and template not in ILLUSTRATED and template != CUSTOM:
        return [f"{label}: template must be one of {', '.join(list(TEMPLATES) + list(ILLUSTRATED) + [CUSTOM])} (custom: nothing code can draw)."]
    steps = a.get("steps") or []
    problems = []
    if not 1 <= len(steps) <= MAX_STEPS:
        problems.append(f"{label}: give 1–{MAX_STEPS} steps (has {len(steps)}).")
    if template in ILLUSTRATED:
        found = _check_elements(a.get("elements") or [], label, brand)
        if found:
            return problems + found
        problems += _check_shown(label, [el["id"] for el in a["elements"]], steps)
    elif template == CUSTOM:
        problems += [f"{label}: step {n} needs 'describe': what appears." for n, st in enumerate(steps, 1) if not str(st.get("describe", "")).strip()]
    else:
        spec = a.get("diagram") or {}
        if spec.get("type") != TEMPLATES[template]:
            return problems + [f"{label}: the {template} template draws a '{TEMPLATES[template]}' diagram; set diagram.type to it."]
        found = diagrams.check(spec, label, brand)
        if found:
            return problems + found
        problems += _check_shown(label, diagrams.element_ids(spec, brand), steps)
    previous, prev_n = -1, None
    for n, st in enumerate(steps, 1):
        if not st.get("trigger"):
            continue
        at = editor.find(bundle, words, st["trigger"], previous + 1)
        if at is None:
            if editor.find(bundle, words, st["trigger"]) is None:
                problems.append(f"{label}: step {n}'s trigger '{st['trigger']}' is not in {seg['id']}'s spoken words; copy the exact words.")
            else:
                problems.append(f"{label}: step {n}'s trigger '{st['trigger']}' must come after step {prev_n}'s in what is said.")
            continue
        previous, prev_n = at, n
    return problems


def _check_shown(label: str, ids: list, steps: list) -> list:
    problems, shown = [], []
    for n, st in enumerate(steps, 1):
        show = st.get("show") or []
        if not show:
            problems.append(f"{label}: step {n} shows nothing; list the element ids it adds ('show').")
        for eid in show:
            if eid not in ids:
                problems.append(f"{label}: {eid} is not an element of this diagram ({', '.join(ids)}).")
            elif eid in shown:
                problems.append(f"{label}: {eid} is shown in more than one step; each element appears once.")
            shown.append(eid)
    missing = [eid for eid in ids if eid not in shown]
    if missing and not any("is not an element" in p for p in problems):
        problems.append(f"{label}: never shown: {', '.join(missing)}. Every element appears in some step.")
    return problems


def _presenter_px(brand) -> tuple:
    x, y, w, h = _presenter(brand)
    return x, y, x + w, y + h


def _check_elements(elements: list, label: str, brand) -> list:
    t = diagrams.theme_of(brand)
    if not 1 <= len(elements) <= 10:
        return [f"{label}: an illustrated animation needs 1–10 elements (has {len(elements)})."]
    problems, ids = [], []
    px0, py0, px1, py1 = _presenter_px(brand)
    people = {c["id"] for c in brand.data.get("characters") or []}
    for el in elements:
        eid = str(el.get("id", ""))
        where = f"{label}: element '{eid}'"
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", eid):
            problems.append(f"{where}: 'id' must be short lowercase words joined by hyphens (e.g. learner, server-rack).")
        elif eid in ids:
            problems.append(f"{where}: the id is used twice.")
        ids.append(eid)
        kind = el.get("kind")
        if kind not in KINDS:
            problems.append(f"{where}: kind must be one of {', '.join(KINDS)}.")
            continue
        if kind == "arrow":
            pts = [el.get("from"), el.get("to")]
            if not all(isinstance(p, list) and len(p) == 2 for p in pts):
                problems.append(f"{where}: an arrow needs 'from' and 'to' points [x, y].")
                continue
            boxes = [(p[0], p[1], 1, 1) for p in pts]
        else:
            box = el.get("place")
            if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
                problems.append(f"{where}: 'place' must be [x, y, width, height] in pixels on the 1920×1080 frame.")
                continue
            boxes = [box]
            if box[2] < 64 or box[3] < 64:
                problems.append(f"{where}: its place is too small to see; make it at least 64×64.")
        for x, y, w, h in boxes:
            if x < 0 or y < 0 or x + w > diagrams.W or y + h > diagrams.H:
                problems.append(f"{where}: it goes off the 1920×1080 frame.")
            elif x < px1 and px0 < x + w and y < py1 and py0 < y + h:
                problems.append(f"{where}: it covers the presenter area ({px0}–{px1} × {py0}–{py1}); move it.")
        if kind == "ai":
            if not str(el.get("describe", "")).strip():
                problems.append(f"{where}: an illustrated element needs 'describe': what the image tool draws.")
            if el.get("character") and el["character"] not in people:
                problems.append(f"{where}: the Brand Kit has no character '{el['character']}' ({', '.join(sorted(people)) or 'none'}).")
        if kind == "text":
            text = str(el.get("text", "")).strip()
            if not text:
                problems.append(f"{where}: a text element needs 'text'.")
            elif t.size_for(text, el["place"][2] - 40, t.sizes["caption"], False) is None:
                problems.append(f"{where}: '{text}' is too long for its place; shorten it or widen the place.")
    return problems


def check_ai(bundle, master: dict, brand) -> list:
    """Problems with the saved illustrations: missing, unreadable, or not cut out."""
    problems, key = [], _rgb(key_color(brand))
    for e, el in missing_ai(bundle, master):
        a = specs(bundle)[e["id"]]
        problems.append(f"{naming.relative(bundle, ai_file(bundle, e['id'], a['template'], el['id']))} is missing: generate it from "
                        "`fz.py show <bundle> animation-prompts` and save it there.")
    for _, e in animation_events(master):
        a = specs(bundle).get(e["id"])
        if not a or a["template"] not in ILLUSTRATED:
            continue
        for el in a["elements"]:
            path = ai_file(bundle, e["id"], a["template"], el["id"])
            if el["kind"] != "ai" or not path.exists():
                continue
            try:
                img = png.read(path.read_bytes())
            except Exception:
                problems.append(f"{path.name} is not a readable PNG; save the image as PNG.")
                continue
            if not png.is_transparent(img) and not png.on_key(img, key):
                problems.append(f"{path.name} needs a transparent background (or a flat {key_color(brand)} one); generate it again.")
    return problems


def _ai_prims(bundle, e: dict, a: dict, el: dict, brand) -> tuple:
    """The illustration cut out and fitted into its place: (image primitive, full-frame layer PNG bytes)."""
    img = png.read(ai_file(bundle, e["id"], a["template"], el["id"]).read_bytes())
    if not png.is_transparent(img):
        img = png.key_out(img, _rgb(key_color(brand)))
    x, y, w, h = png.fit(img, tuple(int(v) for v in el["place"]))
    small = png.resize(img, w, h)
    return ("image", x, y, w, h, png.write(small)), png.write(png.on_frame(small, x, y, diagrams.W, diagrams.H))


def _illustrated_elements(bundle, e: dict, a: dict, t) -> list:
    """Like diagrams.elements, for an illustrated animation; AI elements also carry their full-frame layer."""
    out = []
    for z, el in enumerate(a["elements"], 1):
        item = {"id": el["id"], "role": el["kind"], "z": z, "label": el.get("text") or el.get("describe") or el["id"]}
        if el["kind"] == "ai":
            prim, layer = _ai_prims(bundle, e, a, el, t.brand)
            item.update(prims=[prim], layer=layer, source="ai")
        elif el["kind"] == "arrow":
            (fx, fy), (tx, ty) = el["from"], el["to"]
            item.update(prims=[("arrow", fx, fy, tx, ty, t.c("arrow"))], source="code")
        else:
            x, y, w, h = el["place"]
            size = t.size_for(el["text"], w - 40, t.sizes["caption"], False)
            item.update(prims=[("rect", x, y, w, h, t.c("child"), None, 20),
                               ("text", x + w / 2, y + h / 2 + size * 0.35, el["text"], size, t.c("text"), True, "middle")], source="code")
        out.append(item)
    return out


# --- build -----------------------------------------------------------------------------

def build_all(bundle, master: dict, brand) -> list:
    """Draw every specified animation into the Editor Kit. Returns (seg, event, preview file) rows for the gallery."""
    from . import editor

    have = specs(bundle)
    timeline = {t["event"]["id"]: t["start"] for t in editor._timeline(bundle, master)}
    index = editor.spoken_index(bundle, master)
    rows = []
    for seg, e in animation_events(master):
        a = have.get(e["id"])
        if a is None:
            continue
        rows.append((seg, e, _build_one(bundle, master, seg, e, a, brand, timeline[e["id"]], index[seg["id"]])))
    return rows


def _times(bundle, e: dict, a: dict, start: float, seg_index: dict, brand) -> list:
    from . import editor

    wpm = settings.get(bundle, "words_per_minute")
    duration = e.get("duration_sec") or DEFAULT_DURATION
    steps, out, previous = a["steps"], [], -1
    for n, st in enumerate(steps):
        at = editor.find(bundle, seg_index["words"], st["trigger"], previous + 1) if st.get("trigger") else None
        if at is not None:
            previous = at
            t = (seg_index["before"] + at) * 60 / wpm
        elif n == 0:
            t = start
        else:
            t = out[-1] + duration / len(steps)
        out.append(round(t, 2))
    return out


def _build_one(bundle, master: dict, seg: dict, e: dict, a: dict, brand, event_start: float, seg_index: dict):
    vid = naming.video_id(bundle)
    base = folder(bundle, e["id"], a["template"])
    base.mkdir(parents=True, exist_ok=True)
    t = diagrams.theme_of(brand)
    starts = _times(bundle, e, a, event_start, seg_index, brand)
    hold = (brand.get("motion.durations") or {}).get("min_hold", 1.0)
    end = max(starts[0] + (e.get("duration_sec") or DEFAULT_DURATION), starts[-1] + hold)
    durations = [round((starts[i + 1] if i + 1 < len(starts) else end) - s, 2) for i, s in enumerate(starts)]

    elements, element_rows, state_files, preview = [], [], [], None
    if a["template"] != CUSTOM:
        elements = _illustrated_elements(bundle, e, a, t) if a["template"] in ILLUSTRATED else diagrams.elements(a["diagram"], t)
        for el in elements:
            name = f"{vid}_{e['id']}_L{el['z']:02d}_{el['id'].replace(':', '-')}"
            files = _draw(el["prims"], base / "elements" / name, t, layer=el.get("layer"))
            element_rows.append(dict({k: el[k] for k in ("id", "role", "label", "z")}, bbox=_bbox(el["prims"]),
                                     source=el.get("source", "code"), files=files))
        shown = []
        for k, st in enumerate(a["steps"], 1):
            shown += st["show"]
            prims = [p for el in elements if el["id"] in shown for p in el["prims"]]
            state_files.append(_draw(prims, base / "states" / f"{vid}_{e['id']}_state{k}", t))
        preview = _storyboard(base, [[p for el in elements if el["id"] in [i for st in a["steps"][:k] for i in st["show"]] for p in el["prims"]]
                                     for k in range(1, len(a["steps"]) + 1)], a["steps"], t)
    labels = {el["id"]: el["label"] for el in elements}

    steps = []
    for n, (st, s, d) in enumerate(zip(a["steps"], starts, durations), 1):
        steps.append({"n": n, "trigger": st.get("trigger") or "", "start_sec": s, "offset_sec": round(s - starts[0], 2), "duration_sec": d,
                      "enter": list(st.get("show") or []), "exit": [], "describe": st.get("describe") or "",
                      "shows": " · ".join(labels[i] for i in st.get("show") or []) or st.get("describe", ""),
                      "state": state_files[n - 1] if state_files else None})
    _step_sheet(base, e, a, steps, element_rows)
    spec = {
        "spec_version": SPEC_VERSION,
        "generator": {"skill_version": SKILL_VERSION},
        "video": {"id": vid, "title": master["video"].get("title", "")},
        "event": {"id": e["id"], "segment": seg["id"], "template": a["template"], "layout": e.get("layout"), "trigger": e["trigger"],
                  "description": e["description"], "editor_note": e.get("editor_note", "")},
        "brand": {"id": brand.info.get("id"), "version": brand.info.get("version"), "source": brand.info.get("source"),
                  "colors": {k: brand.color(k) for k in brand.data.get("colors", {})},
                  "fonts": {r: {"family": f["family"], "file": f.get("file")} for r, f in brand.data["fonts"].items() if isinstance(f, dict)},
                  "motion": brand.data.get("motion", {})},
        "canvas": {"width": diagrams.W, "height": diagrams.H, "fps": FPS,
                   "safe_area": [t.left, t.top, t.right - t.left, t.bottom - t.top], "presenter_area": _presenter(brand)},
        "timing": {"basis": "estimated_wpm", "words_per_minute": settings.get(bundle, "words_per_minute"),
                   "event_start_sec": starts[0], "duration_sec": round(end - starts[0], 2)},
        "elements": element_rows,
        "steps": [{k: v for k, v in st.items() if k != "shows"} for st in steps],
        "storyboard": preview,
    }
    (base / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    final = (state_files[-1] if state_files else None) or preview
    return base / (final.get("png") or final["svg"]) if final else base / "step_sheet.md"


def _presenter(brand) -> list:
    p = brand.get("slides.presenter_area")
    return [round(p["x"] * diagrams.W), round(p["y"] * diagrams.H), round(p["w"] * diagrams.W), round(p["h"] * diagrams.H)]


def _draw(prims: list, stem, t, size=None, layer: bytes = None) -> dict:
    """SVG always; PNG where the sandbox can draw (an illustration's layer PNG is made without drawing).
    Returns the files, relative to the animation folder."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    w, h = size or (diagrams.W, diagrams.H)
    stem.with_suffix(".svg").write_text(diagrams.to_svg(prims, t, (w, h)), encoding="utf-8")
    files = {"svg": f"{stem.parent.name}/{stem.name}.svg" if stem.parent.name in ("elements", "states") else f"{stem.name}.svg"}
    if layer is not None:
        stem.with_suffix(".png").write_bytes(layer)
        files["png"] = files["svg"][:-4] + ".png"
    elif diagrams.to_png(prims, stem.with_suffix(".png"), t, (w, h)):
        files["png"] = files["svg"][:-4] + ".png"
    return files


def _bbox(prims: list) -> list:
    xs, ys = [], []
    for p in prims:
        if p[0] == "rect":
            xs += [p[1], p[1] + p[3]]
            ys += [p[2], p[2] + p[4]]
        elif p[0] == "text":
            width = len(str(p[3])) * p[4] * 0.55
            x0 = p[1] - (width / 2 if p[7] == "middle" else width if p[7] == "end" else 0)
            xs += [x0, x0 + width]
            ys += [p[2] - p[4] * 0.8, p[2] + p[4] * 0.2]
        elif p[0] in ("arrow", "line"):
            xs += [p[1], p[3]]
            ys += [p[2], p[4]]
        elif p[0] == "poly":
            xs += [x for x, _ in p[1]]
            ys += [y for _, y in p[1]]
        elif p[0] == "image":
            xs += [p[1], p[1] + p[3]]
            ys += [p[2], p[2] + p[4]]
    if not xs:
        return [0, 0, 0, 0]
    return [round(min(xs)), round(min(ys)), round(max(xs) - min(xs)), round(max(ys) - min(ys))]


def _scaled(prims: list, f: float, ox: float, oy: float) -> list:
    out = []
    for p in prims:
        k = p[0]
        if k == "rect":
            _, x, y, w, h, fill, stroke, r = p
            out.append(("rect", x * f + ox, y * f + oy, w * f, h * f, fill, stroke, r * f))
        elif k == "text":
            _, x, y, text, size, col, bold, anchor = p
            out.append(("text", x * f + ox, y * f + oy, text, round(size * f, 1), col, bold, anchor))
        elif k in ("arrow", "line"):
            _, x1, y1, x2, y2, col = p
            out.append((k, x1 * f + ox, y1 * f + oy, x2 * f + ox, y2 * f + oy, col))
        elif k == "poly":
            _, pts, fill, stroke = p
            out.append(("poly", [(x * f + ox, y * f + oy) for x, y in pts], fill, stroke))
        elif k == "image":
            _, x, y, w, h, data = p
            out.append(("image", x * f + ox, y * f + oy, w * f, h * f, data))
    return out


def _storyboard(base, states: list, steps: list, t) -> dict:
    n = len(states)
    cols = 1 if n == 1 else 2 if n <= 4 else 3 if n <= 6 else 4
    rows = math.ceil(n / cols)
    margin, caption = 40, 56
    panel_w = (diagrams.W - margin * (cols + 1)) / cols
    f = panel_w / diagrams.W
    panel_h = diagrams.H * f
    height = int(margin + rows * (panel_h + caption + margin))
    prims = [("rect", 0, 0, diagrams.W, height, t.c("card"), None, 0)]
    for k, state in enumerate(states):
        col, row = k % cols, k // cols
        ox, oy = margin + col * (panel_w + margin), margin + row * (panel_h + caption + margin)
        prims.append(("rect", ox, oy, panel_w, panel_h, t.c("card"), t.c("card_border"), 12))
        prims += _scaled(state, f, ox, oy)
        trig = steps[k].get("trigger")
        prims.append(("text", ox, oy + panel_h + 38, f"{k + 1} · “{trig}”" if trig else f"{k + 1}", 28, t.c("label"), True, "start"))
    return _draw(prims, base / "storyboard", t, (diagrams.W, height))


def _clock(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def _step_sheet(base, e: dict, a: dict, steps: list, element_rows: list) -> None:
    files = {r["id"]: r["files"].get("png") or r["files"]["svg"] for r in element_rows}
    with open(base / "step_sheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["step", "trigger", "start", "start_sec", "offset_sec", "duration_sec", "shows", "state", "layers"])
        for st in steps:
            state = (st["state"] or {}).get("png") or (st["state"] or {}).get("svg") or ""
            w.writerow([st["n"], st["trigger"], _clock(st["start_sec"]), st["start_sec"], st["offset_sec"], st["duration_sec"],
                        st["shows"], state, " ".join(files[i] for i in st["enter"])])
    md = [f"# {e['id']} · {a['template']} · step sheet", "",
          f"{e['description']}", "",
          "Times are **estimated** from the speaking rate; place each step on its trigger words in the recording.", ""]
    if element_rows:
        md += ["Stack the layers in `elements/` on the timeline in order (L01 at the bottom): each is a full 1920×1080 transparent frame, "
               "so they line up exactly. Or cut between the frames in `states/`.", ""]
    md += ["| Step | Starts on | Time | Hold | Shows | Frame |", "|---|---|---|---|---|---|"]
    for st in steps:
        state = (st["state"] or {}).get("png") or (st["state"] or {}).get("svg") or ""
        md.append(f"| {st['n']} | {('“' + st['trigger'] + '”') if st['trigger'] else '(spread evenly)'} | {_clock(st['start_sec'])} | "
                  f"{st['duration_sec']} s | {st['shows']} | {('`' + state + '`') if state else ''} |")
    (base / "step_sheet.md").write_text("\n".join(md) + "\n", encoding="utf-8")
