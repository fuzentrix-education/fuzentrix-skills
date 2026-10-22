"""The Fuzentrix Configuration Pack: how we work (video guidelines, teleprompter and feature settings, LMS rules).
Published as immutable releases and loaded into a bundle by `kits`; skills never run anything from it.
"""
from __future__ import annotations

from pathlib import Path

from . import kits

SCHEMA_VERSION = 1
REQUIRED = ["policy/video-guidelines.md"]
AFFECTS = {
    "policy/video-guidelines.md": ["review", "master"],
    "policy/teleprompter.yaml": ["teleprompter"],
    "policy/features.yaml": ["ingest"],
    "policy/cheatsheet.yaml": ["cheatsheet"],
    "policy/lms-html.yaml": ["cheatsheet", "quiz"],
    "templates/lms_quiz_template.xlsx": ["quiz"],
}


def _check(files: dict) -> list:
    problems = []
    for rel, data in sorted(files.items()):
        if rel.endswith((".yaml", ".yml")):
            problems += [f"{rel}: {p}" for p in _check_policy(rel, kits.load_yaml(data.decode("utf-8")))]
    return problems


def _check_policy(rel: str, value) -> list:
    if not isinstance(value, dict):
        return ["must be a mapping of setting: value."]
    if rel == "policy/brand.yaml":
        return ["brand settings (colours, fonts, templates, styles) live in the Brand Kit now, not the Configuration Pack."]
    if rel == "policy/lms-html.yaml":
        from .lmspolicy import check_policy
        return check_policy(value)
    problems = []
    if rel == "policy/features.yaml" and "chunk_lines" in value:
        v = value["chunk_lines"]
        if not isinstance(v, int) or not 2 <= v <= 1000:
            problems.append("chunk_lines must be a whole number between 2 and 1000.")
    if rel == "policy/cheatsheet.yaml":
        for old in ("html_mode", "image_base_url"):
            if old in value:
                problems.append(f"{old} is gone: what the cheatsheet HTML may use (styles, classes, image placeholders) is set in "
                                "policy/lms-html.yaml, the LMS HTML Policy.")
        if "banned_phrases" in value and not (isinstance(value["banned_phrases"], list) and all(isinstance(p, str) for p in value["banned_phrases"])):
            problems.append("banned_phrases must be a list of phrases.")
        if "require_mistakes" in value and not isinstance(value["require_mistakes"], bool):
            problems.append("require_mistakes must be true or false.")
    if rel == "policy/teleprompter.yaml":
        if "cues" in value and value["cues"] != "none":
            problems.append("cues: only 'none' is available in this skill version.")
        for key, lo, hi in (("line_length_words", 3, 20), ("words_per_minute", 60, 250)):
            if key in value and (not isinstance(value[key], int) or not lo <= value[key] <= hi):
                problems.append(f"{key} must be a whole number between {lo} and {hi}.")
        if "symbols" in value and not (isinstance(value["symbols"], dict) and all(isinstance(v, str) for v in value["symbols"].values())):
            problems.append("symbols must map each symbol to its replacement text.")
    return problems


CONFIG = kits.KitType(
    name="Configuration Pack", key="config", version_key="config_version", schema_key="config_schema_version",
    schema_version=SCHEMA_VERSION, zip_prefix="fuzentrix-config", snapshot="_config_snapshot",
    folder_hint="Fuzentrix Configuration",
    suffixes=frozenset({".md", ".yaml", ".yml", ".json", ".txt", ".csv", ".xlsx"}),
    required=tuple(REQUIRED), affects=AFFECTS, check=_check)


def check_files(files: dict) -> list:
    return kits.check_files(CONFIG, files)


def publish(staging: Path, root: Path, version: str, minimum_skill_version: str = kits.SKILL_VERSION) -> Path:
    return kits.publish(CONFIG, staging, root, version, minimum_skill_version)


def publish_main(argv=None) -> int:
    return kits.publish_main(CONFIG, argv)


def read_release(source) -> tuple:
    return kits.read_release(CONFIG, source)


def snapshot(bundle_root: Path, manifest: dict, files: dict) -> None:
    kits.snapshot(CONFIG, bundle_root, manifest, files)


def policy(bundle_root: Path, name: str) -> dict:
    """Read a YAML policy file from the bundle's pinned snapshot, or {} if absent."""
    path = Path(bundle_root) / CONFIG.snapshot / "policy" / name
    if not path.exists():
        return {}
    return kits.load_yaml(path.read_text(encoding="utf-8"))
