"""The Fuzentrix Configuration Pack: publish immutable releases, and load one into a Video Bundle.

A release is plain data (YAML/JSON/Markdown and approved assets). Skills never run anything from it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from . import SKILL_VERSION
from .problems import Rejected, format_problems

SCHEMA_VERSION = 1
ALLOWED_SUFFIXES = {
    ".md", ".yaml", ".yml", ".json", ".txt", ".csv",
    ".pptx", ".potx", ".png", ".jpg", ".jpeg", ".svg", ".ttf", ".otf", ".woff", ".woff2",
}
REQUIRED = ["policy/video-guidelines.md"]
AFFECTS = {
    "policy/video-guidelines.md": ["review", "master"],
    "policy/teleprompter.yaml": ["teleprompter"],
    "policy/features.yaml": ["ingest"],
    "policy/brand.yaml": ["slides", "assets", "animation-jobs"],
    "policy/cheatsheet.yaml": ["cheatsheet"],
}


# --- shared checks ------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _version_tuple(v: str):
    return tuple(int(p) for p in v.split("."))


def _load_yaml(text: str):
    import yaml

    return yaml.safe_load(text) or {}


def check_files(files: dict) -> list:
    """files maps release-relative path → bytes. Returns a list of problems."""
    problems = []
    for rel in sorted(files):
        if Path(rel).suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"{rel}: file type not allowed in a Configuration Pack (data and approved assets only).")
    for rel in REQUIRED:
        if rel not in files:
            problems.append(f"{rel}: required file is missing.")
    for rel, data in files.items():
        if rel.endswith((".yaml", ".yml")):
            try:
                value = _load_yaml(data.decode("utf-8"))
            except Exception as e:
                problems.append(f"{rel}: not valid YAML ({e}).")
                continue
            problems += [f"{rel}: {p}" for p in _check_policy(rel, value)]
        elif rel.endswith(".json"):
            try:
                json.loads(data.decode("utf-8"))
            except Exception as e:
                problems.append(f"{rel}: not valid JSON ({e}).")
    return problems


def _check_policy(rel: str, value) -> list:
    if not isinstance(value, dict):
        return ["must be a mapping of setting: value."]
    problems = []
    if rel == "policy/features.yaml" and "chunk_lines" in value:
        v = value["chunk_lines"]
        if not isinstance(v, int) or not 2 <= v <= 1000:
            problems.append("chunk_lines must be a whole number between 2 and 1000.")
    if rel == "policy/cheatsheet.yaml":
        if "html_mode" in value and value["html_mode"] not in ("semantic", "styled"):
            problems.append("html_mode must be 'semantic' (no CSS/JS, safest for the LMS) or 'styled'.")
        if "banned_phrases" in value and not (isinstance(value["banned_phrases"], list) and all(isinstance(p, str) for p in value["banned_phrases"])):
            problems.append("banned_phrases must be a list of phrases.")
        if "require_mistakes" in value and not isinstance(value["require_mistakes"], bool):
            problems.append("require_mistakes must be true or false.")
        if "image_base_url" in value and not isinstance(value["image_base_url"], str):
            problems.append("image_base_url must be text.")
    if rel == "policy/teleprompter.yaml":
        if "cues" in value and value["cues"] != "none":
            problems.append("cues: only 'none' is available in this skill version.")
        for key, lo, hi in (("line_length_words", 3, 20), ("words_per_minute", 60, 250)):
            if key in value and (not isinstance(value[key], int) or not lo <= value[key] <= hi):
                problems.append(f"{key} must be a whole number between {lo} and {hi}.")
        if "symbols" in value and not (isinstance(value["symbols"], dict) and all(isinstance(v, str) for v in value["symbols"].values())):
            problems.append("symbols must map each symbol to its replacement text.")
    return problems


# --- publishing (configuration owners) ---------------------------------------

def publish(staging: Path, root: Path, version: str, minimum_skill_version: str = SKILL_VERSION) -> Path:
    staging, root = Path(staging), Path(root)
    files = {p.relative_to(staging).as_posix(): p.read_bytes() for p in sorted(staging.rglob("*")) if p.is_file() and not p.name.startswith(".")}
    problems = check_files(files)
    release = root / "releases" / version
    if release.exists():
        problems.append(f"Release {version} already exists. Releases are immutable; publish a new version.")
    if problems:
        raise Rejected(problems)

    manifest = {
        "config_version": version,
        "config_schema_version": SCHEMA_VERSION,
        "minimum_skill_version": minimum_skill_version,
        "files": [{"path": rel, "sha256": _sha256(data), "affects": AFFECTS.get(rel, [])} for rel, data in sorted(files.items())],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    release.mkdir(parents=True)
    for rel, data in files.items():
        (release / rel).parent.mkdir(parents=True, exist_ok=True)
        (release / rel).write_bytes(data)
    (release / "manifest.json").write_bytes(manifest_bytes)
    with zipfile.ZipFile(release / f"fuzentrix-config-{version}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", manifest_bytes)
        for rel, data in files.items():
            z.writestr(rel, data)

    current = {
        "config_version": version,
        "config_schema_version": SCHEMA_VERSION,
        "minimum_skill_version": minimum_skill_version,
        "release_folder_id": "",
        "manifest_sha256": _sha256(manifest_bytes),
    }
    (root / "current.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")  # last: the pointer
    return release


def publish_main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="publish.py", description="Publish a Fuzentrix Configuration Pack release")
    parser.add_argument("staging")
    parser.add_argument("root", help="The shared 'Fuzentrix Configuration' folder (e.g. synced from Google Drive)")
    parser.add_argument("--version", required=True)
    parser.add_argument("--minimum-skill-version", default=SKILL_VERSION)
    args = parser.parse_args(argv)
    try:
        release = publish(Path(args.staging), Path(args.root), args.version, args.minimum_skill_version)
    except Rejected as e:
        print(format_problems(e.problems))
        return 2
    print(f"Published Configuration Pack {args.version} to {release}; current.json now points to it.")
    return 0


# --- loading (inside the skill) -------------------------------------------------

def read_release(source) -> tuple:
    """Accepts a release .zip, a release folder, or the shared root folder with current.json.
    Returns (manifest, files) after checking compatibility and every hash."""
    source = Path(source)
    if source.is_file() and source.suffix.lower() == ".zip":
        files = _read_zip(source)
    elif (source / "current.json").exists():
        current = json.loads((source / "current.json").read_text(encoding="utf-8"))
        return read_release(source / "releases" / current["config_version"])
    elif (source / "manifest.json").exists():
        files = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob("*")
                 if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".zip")}
    else:
        raise Rejected(f"{source} is not a Configuration Pack. Select the release .zip, its release folder, or the 'Fuzentrix Configuration' folder.")

    if "manifest.json" not in files:
        raise Rejected("The Configuration Pack has no manifest.json.")
    manifest = json.loads(files.pop("manifest.json").decode("utf-8"))
    problems = []
    if manifest.get("config_schema_version") != SCHEMA_VERSION:
        problems.append(f"Configuration Pack schema {manifest.get('config_schema_version')} is not supported by this skill (needs {SCHEMA_VERSION}).")
    needed = manifest.get("minimum_skill_version", "0.0.0")
    if _version_tuple(needed) > _version_tuple(SKILL_VERSION):
        problems.append(f"Configuration Pack {manifest.get('config_version')} needs skill version {needed} or newer; this skill is {SKILL_VERSION}. Install the latest Fuzentrix skills.")
    listed = {f["path"]: f["sha256"] for f in manifest.get("files", [])}
    for rel, digest in sorted(listed.items()):
        if rel not in files:
            problems.append(f"{rel}: listed in manifest.json but missing.")
        elif _sha256(files[rel]) != digest:
            problems.append(f"{rel}: content does not match the published release (changed after publishing).")
    for rel in sorted(set(files) - set(listed)):
        problems.append(f"{rel}: not part of the published release.")
    problems += check_files(files)
    if problems:
        raise Rejected(problems)
    return manifest, files


def _read_zip(path: Path) -> dict:
    try:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            for n in names:
                if n.startswith("/") or ".." in Path(n).parts:
                    raise Rejected(f"{path.name}: unsafe path '{n}' inside the zip.")
            files = {n: z.read(n) for n in names}
    except zipfile.BadZipFile:
        raise Rejected(f"{path.name} is not a readable zip file.")
    # tolerate a single top-level folder around the release
    tops = {n.split("/")[0] for n in files}
    if "manifest.json" not in files and len(tops) == 1:
        top = next(iter(tops)) + "/"
        files = {n[len(top):]: d for n, d in files.items()}
    return {n: d for n, d in files.items() if not Path(n).name.startswith(".") and not n.startswith("__MACOSX/")}


def snapshot(bundle_root: Path, manifest: dict, files: dict) -> None:
    target = Path(bundle_root) / "_config_snapshot"
    if target.exists():
        shutil.rmtree(target)
    for rel, data in files.items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(data)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def policy(bundle_root: Path, name: str) -> dict:
    """Read a YAML policy file from the bundle's pinned snapshot, or {} if absent."""
    path = Path(bundle_root) / "_config_snapshot" / "policy" / name
    if not path.exists():
        return {}
    return _load_yaml(path.read_text(encoding="utf-8"))
