"""The Topic Bundle: the Final Master Scripts of one or more Videos, for building a Quiz and a Cheatsheet."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import SKILL_VERSION
from .bundle import Bundle, now, read_json, unpack, write_json
from .problems import Rejected


def create(root, topic_id: str, title: str, videos: list) -> Bundle:
    root = Path(root)
    if (root / "manifest.json").exists():
        raise Rejected(f"{root} already contains a bundle. Use a new folder.")
    if not videos:
        raise Rejected("Name at least one Video Bundle with --video.")
    masters, problems, config_from = [], [], None
    with tempfile.TemporaryDirectory() as tmp:
        for i, source in enumerate(videos):
            source = Path(source)
            video = unpack(source, Path(tmp) / f"v{i}") if source.suffix.lower() == ".zip" else Bundle(source)
            vid = video.manifest["video"]["id"]
            if video.manifest.get("stages", {}).get("master", {}).get("status") != "final":
                problems.append(f"{vid} has no Final Master Script yet; pass its Gate 2 first.")
                continue
            masters.append((vid, read_json(video.path("02_master", "master.json")), video.manifest.get("config", {})))
            if config_from is None and video.path("_config_snapshot").exists():
                config_from = Path(tmp) / "config"
                shutil.copytree(video.path("_config_snapshot"), config_from)
        ids = [m[0] for m in masters]
        for vid in set(ids):
            if ids.count(vid) > 1:
                problems.append(f"{vid} is listed more than once.")
        if problems:
            raise Rejected(problems)

        root.mkdir(parents=True, exist_ok=True)
        for vid, master, _ in masters:
            write_json(root / "videos" / vid / "master.json", master)
        if config_from:
            shutil.copytree(config_from, root / "_config_snapshot")
    config = masters[0][2] if masters else {"draft": True, "version": None}
    write_json(root / "manifest.json", {
        "kind": "topic",
        "topic": {"id": topic_id, "title": title},
        "videos": ids,
        "skill_version": SKILL_VERSION,
        "config": config,
        "created": now(),
        "stages": {},
        "gates": {},
        "history": [{"at": now(), "event": f"topic created from {', '.join(ids)}"}],
    })
    return Bundle(root)


def is_topic(bundle) -> bool:
    return bundle.manifest.get("kind") == "topic"


def masters(bundle) -> dict:
    return {vid: read_json(bundle.path("videos", vid, "master.json")) for vid in bundle.manifest["videos"]}


def describe_sources(bundle, video_id: str) -> str:
    """What one Video teaches, for writing Quiz questions and Cheatsheets: objectives, terms, and each Segment."""
    from . import settings
    from .teleprompter import clean

    all_masters = masters(bundle)
    if video_id not in all_masters:
        raise Rejected(f"{video_id} is not in this Topic ({', '.join(all_masters)}).")
    m = all_masters[video_id]
    symbols = settings.get(bundle, "teleprompter_symbols")
    out = [f"# {video_id}: {m['video'].get('title', '')}", ""]
    if m.get("learning_objectives"):
        out += ["Learning objectives:"] + [f"- {o}" for o in m["learning_objectives"]] + [""]
    if m.get("key_terms"):
        out += ["Key terms:"] + [f"- {t['term']}: {t['definition']}" for t in m["key_terms"]] + [""]
    for seg in m["segments"]:
        said = " ".join(clean(s["text"], symbols) for s in seg.get("spoken", []))
        out += [f"{seg['id']} · {seg['section']} · {seg['title']}",
                f"Meaning: {seg.get('meaning_en', '')}",
                f"Said: {said}"]
        slide = seg.get("slide") or {}
        if slide.get("title"):
            out.append(f"Slide: {slide['title']}" + (f" | {' | '.join(slide.get('bullets') or [])}" if slide.get("bullets") else ""))
        out.append("")
    return "\n".join(out)
