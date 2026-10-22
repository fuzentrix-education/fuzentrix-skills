"""Kits: versioned, immutable bundles of data that skills read but never run. Two kinds share this code:
the Configuration Pack (how we work) and the Brand Kit (how things look).

A kit owner publishes a release from a staging folder: the files, a manifest.json with every file's
sha256, a zip of both, and current.json pointing at the newest release. A skill loads a release from the
zip (attached, or added from Google Drive), its release folder, or the shared folder with current.json,
checks every hash, and snapshots it into the bundle so later chats don't need it again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import SKILL_VERSION
from .problems import Rejected, format_problems


@dataclass(frozen=True)
class KitType:
    name: str                      # "Configuration Pack", "Brand Kit"
    key: str                       # the bundle manifest key: "config", "brand"
    version_key: str               # manifest.json key holding the release version
    schema_key: str
    schema_version: int
    zip_prefix: str                # release zip: <zip_prefix>-<version>.zip
    snapshot: str                  # the folder inside a bundle
    folder_hint: str               # what the shared folder is called, for messages
    suffixes: frozenset
    required: tuple = ()
    affects: dict = field(default_factory=dict)
    check: Callable = None         # extra checks: files dict → problems


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_tuple(v: str):
    return tuple(int(p) for p in v.split("."))


def load_yaml(text: str):
    import yaml

    return yaml.safe_load(text) or {}


def check_files(kind: KitType, files: dict) -> list:
    """files maps release-relative path → bytes. Returns a list of problems."""
    problems = []
    for rel in sorted(files):
        if Path(rel).suffix.lower() not in kind.suffixes:
            problems.append(f"{rel}: file type not allowed in a {kind.name} (data and approved assets only).")
    for rel in kind.required:
        if rel not in files:
            problems.append(f"{rel}: required file is missing.")
    for rel, data in files.items():
        if rel.endswith(".json"):
            try:
                json.loads(data.decode("utf-8"))
            except Exception as e:
                problems.append(f"{rel}: not valid JSON ({e}).")
        elif rel.endswith((".yaml", ".yml")):
            try:
                load_yaml(data.decode("utf-8"))
            except Exception as e:
                problems.append(f"{rel}: not valid YAML ({e}).")
    if kind.check and not problems:
        problems += kind.check(files)
    return problems


def staged_files(staging: Path) -> dict:
    staging = Path(staging)
    return {p.relative_to(staging).as_posix(): p.read_bytes() for p in sorted(staging.rglob("*"))
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(staging).parts)}


# --- publishing (kit owners) ------------------------------------------------------

def publish(kind: KitType, staging: Path, root: Path, version: str, minimum_skill_version: str = SKILL_VERSION) -> Path:
    root = Path(root)
    files = staged_files(staging)
    problems = check_files(kind, files)
    release = root / "releases" / version
    if release.exists():
        problems.append(f"Release {version} already exists. Releases are immutable; publish a new version.")
    if problems:
        raise Rejected(problems)

    manifest = {
        kind.version_key: version,
        kind.schema_key: kind.schema_version,
        "minimum_skill_version": minimum_skill_version,
        "files": [{"path": rel, "sha256": sha256(data), "affects": kind.affects.get(rel, [])} for rel, data in sorted(files.items())],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    release.mkdir(parents=True)
    for rel, data in files.items():
        (release / rel).parent.mkdir(parents=True, exist_ok=True)
        (release / rel).write_bytes(data)
    (release / "manifest.json").write_bytes(manifest_bytes)
    with zipfile.ZipFile(release / f"{kind.zip_prefix}-{version}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", manifest_bytes)
        for rel, data in files.items():
            z.writestr(rel, data)

    current = {
        kind.version_key: version,
        kind.schema_key: kind.schema_version,
        "minimum_skill_version": minimum_skill_version,
        "release_folder_id": "",
        "manifest_sha256": sha256(manifest_bytes),
    }
    (root / "current.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")  # last: the pointer
    return release


def publish_main(kind: KitType, argv=None) -> int:
    parser = argparse.ArgumentParser(prog="publish.py", description=f"Publish a Fuzentrix {kind.name} release")
    parser.add_argument("staging")
    parser.add_argument("root", help=f"The shared '{kind.folder_hint}' folder (e.g. synced from Google Drive)")
    parser.add_argument("--version", required=True)
    parser.add_argument("--minimum-skill-version", default=SKILL_VERSION)
    args = parser.parse_args(argv)
    try:
        release = publish(kind, Path(args.staging), Path(args.root), args.version, args.minimum_skill_version)
    except Rejected as e:
        print(format_problems(e.problems))
        return 2
    print(f"Published {kind.name} {args.version} to {release}; current.json now points to it.")
    return 0


# --- loading (inside the skill) -----------------------------------------------------

def read_release(kind: KitType, source) -> tuple:
    """Accepts a release .zip, a release folder, or the shared root folder with current.json.
    Returns (manifest, files) after checking compatibility and every hash."""
    source = Path(source)
    if source.is_file() and source.suffix.lower() == ".zip":
        files = read_zip(source)
    elif (source / "current.json").exists():
        current = json.loads((source / "current.json").read_text(encoding="utf-8"))
        return read_release(kind, source / "releases" / current[kind.version_key])
    elif (source / "manifest.json").exists():
        files = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob("*")
                 if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".zip")}
    else:
        raise Rejected(f"{source} is not a {kind.name}. Select the release .zip, its release folder, or the '{kind.folder_hint}' folder.")

    if "manifest.json" not in files:
        raise Rejected(f"The {kind.name} has no manifest.json.")
    manifest = json.loads(files.pop("manifest.json").decode("utf-8"))
    if kind.version_key not in manifest:
        raise Rejected(f"{source.name} is not a {kind.name}.")
    problems = []
    if manifest.get(kind.schema_key) != kind.schema_version:
        problems.append(f"{kind.name} schema {manifest.get(kind.schema_key)} is not supported by this skill (needs {kind.schema_version}).")
    needed = manifest.get("minimum_skill_version", "0.0.0")
    if version_tuple(needed) > version_tuple(SKILL_VERSION):
        problems.append(f"{kind.name} {manifest.get(kind.version_key)} needs skill version {needed} or newer; this skill is {SKILL_VERSION}. "
                        "Install the latest Fuzentrix skills.")
    listed = {f["path"]: f["sha256"] for f in manifest.get("files", [])}
    for rel, digest in sorted(listed.items()):
        if rel not in files:
            problems.append(f"{rel}: listed in manifest.json but missing.")
        elif sha256(files[rel]) != digest:
            problems.append(f"{rel}: content does not match the published release (changed after publishing).")
    for rel in sorted(set(files) - set(listed)):
        problems.append(f"{rel}: not part of the published release.")
    problems += check_files(kind, files)
    if problems:
        raise Rejected(problems)
    return manifest, files


def read_zip(path: Path) -> dict:
    try:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if not n.endswith("/")]
            for n in names:
                if n.startswith("/") or ".." in Path(n).parts:
                    raise Rejected(f"{path.name}: unsafe path '{n}' inside the zip.")
            files = {n: z.read(n) for n in names}
    except zipfile.BadZipFile:
        raise Rejected(f"{path.name} is not a readable zip file.")
    files = {n: d for n, d in files.items() if not n.startswith("__MACOSX/") and not Path(n).name.startswith(".")}
    # tolerate a single top-level folder around the release
    tops = {n.split("/")[0] for n in files}
    if "manifest.json" not in files and len(tops) == 1:
        top = next(iter(tops)) + "/"
        files = {n[len(top):]: d for n, d in files.items()}
    return files


def detect(source, kinds) -> KitType:
    """Which kind of kit a source is, from its manifest.json (or current.json)."""
    source = Path(source)
    if source.is_file() and source.suffix.lower() == ".zip":
        manifest = json.loads(read_zip(source).get("manifest.json", b"{}").decode("utf-8"))
    elif (source / "current.json").exists():
        manifest = json.loads((source / "current.json").read_text(encoding="utf-8"))
    elif (source / "manifest.json").exists():
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    else:
        manifest = {}
    for kind in kinds:
        if kind.version_key in manifest:
            return kind
    raise Rejected(f"{source.name} is neither a Configuration Pack nor a Brand Kit (its manifest.json names neither).")


def snapshot(kind: KitType, bundle_root: Path, manifest: dict, files: dict) -> None:
    target = Path(bundle_root) / kind.snapshot
    if target.exists():
        shutil.rmtree(target)
    for rel, data in files.items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(data)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def snapshot_dir(kind: KitType, bundle_root: Path) -> Path:
    return Path(bundle_root) / kind.snapshot
