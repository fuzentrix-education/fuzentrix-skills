"""The Video Bundle: a folder (zipped for hand-off) that carries all state for one Video."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import SKILL_VERSION
from .problems import Rejected


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Bundle:
    def __init__(self, root):
        self.root = Path(root)
        if not (self.root / "manifest.json").exists():
            raise Rejected(f"{self.root} is not a Video Bundle (no manifest.json). Start with `fz.py new` or `fz.py unpack`.")
        self.manifest = read_json(self.root / "manifest.json")
        self._migrate()

    def _migrate(self) -> None:
        """Bring a bundle from an older skill version up to date: the Editor Pack is now the Editor Kit."""
        old, new = self.root / "editor_pack", self.root / "editor_kit"
        stages = self.manifest.get("stages", {})
        if old.is_dir() and not new.exists():
            old.rename(new)
        if "editor_pack" in stages:
            stages["editor_kit"] = stages.pop("editor_pack")
            self.save()

    # --- creation -------------------------------------------------------
    @classmethod
    def create(cls, root, video_id: str, title: str = "", instructor: str = "") -> "Bundle":
        root = Path(root)
        if (root / "manifest.json").exists():
            raise Rejected(f"{root} already contains a Video Bundle. Use a new folder, or continue with `fz.py status`.")
        root.mkdir(parents=True, exist_ok=True)
        write_json(root / "manifest.json", {
            "video": {"id": video_id, "title": title, "instructor": instructor},
            "skill_version": SKILL_VERSION,
            "created": now(),
            "stages": {},
            "gates": {},
            "history": [],
        })
        return cls(root)

    # --- paths ----------------------------------------------------------
    def path(self, *parts) -> Path:
        return self.root.joinpath(*parts)

    # --- state ----------------------------------------------------------
    def save(self) -> None:
        write_json(self.root / "manifest.json", self.manifest)

    def log(self, event: str) -> None:
        self.manifest.setdefault("history", []).append({"at": now(), "event": event})

    def lines(self) -> list:
        return read_json(self.path("00_ingest", "lines.json"))


def pack(root, zip_path) -> Path:
    """Zip a Video Bundle for download. The zip holds one folder named after the Video."""
    import zipfile

    bundle = Bundle(root)
    top = (bundle.manifest.get("video") or bundle.manifest.get("topic"))["id"]
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.root.rglob("*")):
            if p.is_file() and p.resolve() != zip_path.resolve():
                z.write(p, f"{top}/{p.relative_to(bundle.root).as_posix()}")
    return zip_path


def unpack(zip_path, target) -> "Bundle":
    import zipfile

    target = Path(target)
    if (target / "manifest.json").exists():
        raise Rejected(f"{target} already holds a Video Bundle; unpack into a new folder.")
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = [n for n in z.namelist() if not n.endswith("/") and not n.startswith("__MACOSX/")]
            prefix = ""
            if "manifest.json" not in names:
                tops = {n.split("/")[0] for n in names}
                if len(tops) == 1 and f"{next(iter(tops))}/manifest.json" in names:
                    prefix = next(iter(tops)) + "/"
                else:
                    raise Rejected(f"{Path(zip_path).name} is not a Video Bundle (no manifest.json inside).")
            for n in names:
                rel = n[len(prefix):]
                if rel.startswith("/") or ".." in Path(rel).parts:
                    raise Rejected(f"Unsafe path '{n}' inside the zip.")
                dest = target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(n))
    except zipfile.BadZipFile:
        raise Rejected(f"{Path(zip_path).name} is not a readable zip file.")
    return Bundle(target)
