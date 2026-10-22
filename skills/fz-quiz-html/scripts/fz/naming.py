"""Where every file of a Video goes, and what it is called. The one place these rules live.

    <bundle>/editor_kit/                      everything the Video Editor needs
        editor_guide.md / .html               timeline: what plays when, which file
        markers.xml                           Premiere sequence markers (one per Visual Event)
        cue_sheet.csv
        slides/       <video>_slides.pptx · slides.md
        images/       <video>_<event>_image.png
        diagrams/     <video>_<event>_diagram.svg / .png
        storyboards/  <video>_<event>_storyboard.png
        animations/   <video>_<event>_<template>.mov        (Stage 3c)
    <bundle>/teleprompter/                    for the Instructor

File names match the Premiere marker names (the event id, e.g. S04-E1), so nothing has to be guessed.
"""
from __future__ import annotations

EDITOR_KIT = "editor_kit"
TELEPROMPTER = "teleprompter"
FOLDERS = {"slides": "slides", "image": "images", "diagram": "diagrams", "storyboard": "storyboards", "animation": "animations"}


def video_id(bundle) -> str:
    return bundle.manifest["video"]["id"]


def kit_dir(bundle, *parts):
    return bundle.path(EDITOR_KIT, *parts)


def slides_file(bundle):
    return kit_dir(bundle, "slides", f"{video_id(bundle)}_slides.pptx")


def asset_name(vid: str, event: dict, kind: str, ext: str) -> str:
    suffix = (event.get("template") or "animation").replace("_", "-") if kind == "animation" else kind
    return f"{vid}_{event['id']}_{suffix}.{ext}"


def asset_path(bundle, event: dict, kind: str, ext: str):
    return kit_dir(bundle, FOLDERS[kind], asset_name(video_id(bundle), event, kind, ext))


def relative(bundle, path) -> str:
    return path.relative_to(bundle.root).as_posix()
