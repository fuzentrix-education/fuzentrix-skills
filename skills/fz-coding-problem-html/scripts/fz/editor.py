"""Stage 3d: the Editor Kit, built from the Final Master Script: an editing guide, Premiere sequence
markers (FCP7 XML) and a cue sheet. Before recording, times are estimated from the speaking rate."""
from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape

from . import naming, settings, views
from .bundle import read_json
from .problems import Rejected
from .teleprompter import clean

FPS = 30
DEFAULT_DURATION = 3


def spoken_index(bundle, master: dict) -> dict:
    """Each Segment's spoken words (compared without case or punctuation) and how many words come before it."""
    symbols = settings.get(bundle, "teleprompter_symbols")
    said_before, out = 0, {}
    for seg in master["segments"]:
        words = " ".join(clean(s["text"], symbols) for s in seg.get("spoken", [])).split()
        out[seg["id"]] = {"words": [_word(w) for w in words], "before": said_before}
        said_before += len(words)
    out["_total"] = said_before
    return out


def find(bundle, words: list, phrase: str, start: int = 0):
    """Where a phrase starts among a Segment's words, at or after `start`; None if it isn't there."""
    trig = [_word(w) for w in clean(phrase, settings.get(bundle, "teleprompter_symbols")).split()]
    if not trig:
        return None
    return next((i for i in range(start, len(words) - len(trig) + 1) if words[i:i + len(trig)] == trig), None)


def _timeline(bundle, master: dict) -> list:
    """Each Visual Event with its estimated start (seconds), from words spoken before its trigger."""
    wpm = settings.get(bundle, "words_per_minute")
    index = spoken_index(bundle, master)
    out = []
    for seg in master["segments"]:
        words, before = index[seg["id"]]["words"], index[seg["id"]]["before"]
        for e in seg.get("visual_events", []):
            at = find(bundle, words, e["trigger"]) or 0
            out.append({"segment": seg, "event": e, "start": (before + at) * 60 / wpm})
        seg["_start"] = before * 60 / wpm
    master["_duration"] = index["_total"] * 60 / wpm
    return out


def _word(w: str) -> str:
    """Compare words without case or surrounding punctuation ("DBMS." matches "dbms")."""
    return w.strip(".,;:!?…'\"()[]{}“”‘’").lower()


def _clock(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def _asset(bundle, e: dict) -> str:
    """The Editor Kit file for this Visual Event, relative to the Editor Kit folder."""
    vid = naming.video_id(bundle)
    kind = e.get("kind")
    if kind in ("image", "diagram"):
        return f"{naming.FOLDERS[kind]}/{naming.asset_name(vid, e, kind, 'png')}"
    if kind == "animation":
        from . import animations
        spec = animations.specs(bundle).get(e["id"])
        if spec is None:
            return "animation spec pending (fz-visuals)"
        return f"animations/{animations.folder(bundle, e['id'], spec['template']).name}/"
    if kind == "broll":
        return "stock or AI B-roll, sourced separately"
    return ""


def _brand_folder(bundle, folder) -> None:
    """editor_kit/brand/: the logos, the fonts the kit may share, and the colours, for editing by hand."""
    from . import brandkit

    try:
        brand = brandkit.load(bundle)
    except Rejected:
        return  # no Brand Kit chosen yet
    out = folder / "brand"
    md = [f"# Brand: {brand.label}", "", "## Colours", ""]
    md += [f"- **{name}** `{brand.color(name)}`" for name in brand.data.get("colors", {})]
    md += ["", "## Fonts", ""]
    for role, f in brand.data["fonts"].items():
        if not isinstance(f, dict):
            continue
        if f.get("file") and f.get("redistributable"):
            name = f"{role}{Path(f['file']).suffix}"
            (out / "fonts").mkdir(parents=True, exist_ok=True)
            (out / "fonts" / name).write_bytes(brand.file(f["file"]))
            md.append(f"- **{role}**: {f['family']}. Install `fonts/{name}` before opening the slides or graphics.")
        else:
            md.append(f"- **{role}**: {f['family']}. Install it on this computer (it is not shared in the kit).")
    logos = brand.data.get("logos") or {}
    if logos:
        md += ["", "## Logos", ""]
        for name, rel in logos.items():
            (out / "logos").mkdir(parents=True, exist_ok=True)
            target = out / "logos" / f"{name}{Path(rel).suffix}"
            target.write_bytes(brand.file(rel))
            md.append(f"- **{name}**: `logos/{target.name}`")
    out.mkdir(parents=True, exist_ok=True)
    (out / "brand.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _steps(bundle, e: dict) -> list:
    """The steps of a built animation, from its spec.json (none until fz-visuals has built it)."""
    if e.get("kind") != "animation":
        return []
    from . import animations
    spec = animations.specs(bundle).get(e["id"])
    path = animations.folder(bundle, e["id"], spec["template"]) / "spec.json" if spec else None
    if not path or not path.exists():
        return []
    import json
    return json.loads(path.read_text(encoding="utf-8"))["steps"]


def _storyboard(bundle, e: dict) -> str:
    path = naming.asset_path(bundle, e, "storyboard", "png")
    return f"storyboards/{path.name}" if e.get("kind") == "animation" and path.exists() else ""


def build(bundle) -> dict:
    if bundle.manifest["stages"].get("master", {}).get("status") != "final":
        raise Rejected("The Editor Kit is built from the Final Master Script. Record Gate 2 first.")
    master = read_json(bundle.path("02_master", "master.json"))
    timeline = _timeline(bundle, master)
    vid = master["video"]["id"]
    folder = naming.kit_dir(bundle)
    folder.mkdir(parents=True, exist_ok=True)

    # Premiere: FCP7 XML sequence with one sequence marker per Visual Event
    total = int(master["_duration"] * FPS) + FPS * 10
    marks = []
    for t in timeline:
        e = t["event"]
        start = int(round(t["start"] * FPS))
        dur = int((e.get("duration_sec") or DEFAULT_DURATION) * FPS)
        comment = " · ".join(x for x in (e["kind"], e.get("template") or "", (e.get("layout") or "").replace("_", " "),
                                         e["description"], e.get("editor_note") or "", _asset(bundle, e)) if x)
        marks.append(f"<marker><name>{escape(e['id'])}</name><comment>{escape(comment)}</comment><in>{start}</in><out>{start + dur}</out></marker>")
        for st in _steps(bundle, e)[1:]:
            at = int(round(st["start_sec"] * FPS))
            what = " · ".join(x for x in (f"step {st['n']}", st.get("shows") or st.get("describe") or "") if x)
            marks.append(f"<marker><name>{escape(e['id'])}.{st['n']}</name><comment>{escape(what)}</comment>"
                         f"<in>{at}</in><out>{at + int(st['duration_sec'] * FPS)}</out></marker>")
    rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5"><sequence id="fz-markers">'
           f"<name>{escape(vid)} markers</name><duration>{total}</duration>{rate}"
           f"<timecode>{rate}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>"
           "<media><video><format><samplecharacteristics><width>1920</width><height>1080</height></samplecharacteristics></format><track/></video>"
           "<audio><track/></audio></media>" + "".join(marks) + "</sequence></xmeml>\n")
    (folder / "markers.xml").write_text(xml, encoding="utf-8")

    with open(folder / "cue_sheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "event", "segment", "kind", "layout", "template", "duration_sec", "trigger", "description", "asset", "editor_note"])
        for t in timeline:
            e = t["event"]
            w.writerow([_clock(t["start"]), e["id"], t["segment"]["id"], e["kind"], e.get("layout") or "", e.get("template") or "",
                        e.get("duration_sec") or DEFAULT_DURATION, e["trigger"], e["description"], _asset(bundle, e), e.get("editor_note") or ""])

    say = views.as_spoken(bundle)
    md = [f"# Editor guide: {master['video'].get('title') or vid}", "",
          "Times are **estimated** from the speaking rate until the recording is synced; use the Trigger Phrase to place each event exactly.", "",
          "**Premiere:** File → Import → `markers.xml` adds a sequence with one marker per Visual Event (name = event id). "
          "`cue_sheet.csv` has the same list as a spreadsheet.", "",
          f"**Slides:** `slides/{vid}_slides.pptx` (one slide per Segment, SL01…). **Images:** `images/` · **Diagrams:** `diagrams/` · "
          "**Storyboards:** `storyboards/` · **Animations:** `animations/`. Every file is named `<video>_<event>_<kind>` after its marker.", ""]
    events = {t["event"]["id"]: t for t in timeline}
    for seg in master["segments"]:
        words = " ".join(say(s["text"]) for s in seg.get("spoken", [])).split()
        excerpt = " ".join(words[:18]) + (" …" if len(words) > 18 else "")
        md += [f"## {_clock(seg['_start'])} · {seg['id']} · {seg['section']} · {seg['title']}", "",
               f"> {excerpt or '(no spoken words)'}", "",
               f"**On screen:** {seg['slide']['id']} · {seg['slide']['layout']} · {seg['slide']['title']}", ""]
        for e in seg.get("visual_events", []):
            t = events[e["id"]]
            md += [f"**{_clock(t['start'])} · {e['id']} · {e['kind']}" + (f" · {e['layout'].replace('_', ' ')}" if e.get("layout") else "")
                   + f" · {e.get('duration_sec') or DEFAULT_DURATION} s**", "",
                   f"- Starts on: \"{e['trigger']}\"", f"- Shows: {e['description']}"]
            if e.get("template"):
                md.append(f"- Animation Template: {e['template']}")
            if _asset(bundle, e):
                md.append(f"- File: `{_asset(bundle, e)}`")
            if e["kind"] == "animation" and _steps(bundle, e):
                anim = _asset(bundle, e)
                md.append(f"- Build it by hand: `{anim}step_sheet.md` gives each step's trigger and time; stack the layers in "
                          f"`{anim}elements/` (L01 at the bottom) or cut between the frames in `{anim}states/`. "
                          f"`{anim}spec.json` is for the motion workflow.")
            if _storyboard(bundle, e):
                md.append(f"- Storyboard: `{_storyboard(bundle, e)}`")
            if e.get("editor_note"):
                md.append(f"- Editor note: {e['editor_note']}")
            md.append("")
    views.write_pair(folder / "editor_guide", "\n".join(md) + "\n", title=f"Editor guide: {vid}")
    _brand_folder(bundle, folder)
    bundle.manifest["stages"]["editor_kit"] = {"status": "built", "events": len(timeline)}
    bundle.log("editor kit built")
    return {"events": len(timeline), "minutes": master["_duration"] / 60}
