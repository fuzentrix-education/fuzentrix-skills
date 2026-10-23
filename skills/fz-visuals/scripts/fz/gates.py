"""Gates: points where a named person approves before work continues."""
from __future__ import annotations

import hashlib
import json

from . import views
from .bundle import now, read_json, write_json
from .problems import Rejected
from .review import LINE_ROLES, script_changes

DECISIONS = ("accept", "reject")


def _fingerprint(review: dict) -> str:
    return hashlib.sha256(json.dumps(review["findings"], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def record_gate1(bundle, data: dict) -> dict:
    """The Instructor approves the Reviewed Script: a decision on every Finding, plus their Script Changes.
    Approving again with the same Findings (say, after new Script Changes) may leave out the decisions;
    the earlier ones are kept."""
    if bundle.manifest["stages"].get("review", {}).get("status") != "built":
        raise Rejected("Build the review report first (`fz.py build <bundle> review`); Gate 1 decides on its Findings.")
    review = read_json(bundle.path("01_review", "review.json"))
    earlier = bundle.path("01_review", "gate1.json")
    earlier = read_json(earlier) if earlier.exists() else None
    carried = not data.get("decisions") and bool(earlier) and earlier.get("review_fingerprint") == _fingerprint(review)
    if carried:
        data = dict(data, decisions=earlier["decisions"], fix_text={**earlier["fix_text"], **(data.get("fix_text") or {})},
                    line_roles={**earlier["line_roles"], **(data.get("line_roles") or {})})
    lines = {l["id"] for l in bundle.lines()}
    ids = [f["id"] for f in review["findings"]]
    decisions = data.get("decisions") or {}
    problems = []
    if not str(data.get("approver", "")).strip():
        problems.append("'approver' must name the Instructor who made these decisions.")
    for fid in ids:
        if fid not in decisions:
            problems.append(f"{fid} has no decision (use 'accept' or 'reject').")
        elif decisions[fid] not in DECISIONS:
            problems.append(f"{fid}: decision must be 'accept' or 'reject', not '{decisions[fid]}'.")
    for fid in decisions:
        if fid not in ids:
            problems.append(f"{fid} is not a Finding in this review.")
    for fid, text in (data.get("fix_text") or {}).items():
        if fid not in ids:
            problems.append(f"fix_text: {fid} is not a Finding in this review.")
        elif not isinstance(text, str):
            problems.append(f"fix_text: {fid} must be text (\"\" deletes the line).")
    for lid, role in (data.get("line_roles") or {}).items():
        if lid not in lines:
            problems.append(f"line_roles: {lid} does not exist.")
        elif role not in LINE_ROLES:
            problems.append(f"line_roles: {lid} role '{role}' is not one of {', '.join(LINE_ROLES)}.")
    if problems:
        raise Rejected(problems)
    record = {"approver": data["approver"], "at": now(), "decisions": decisions,
              "fix_text": data.get("fix_text") or {}, "line_roles": data.get("line_roles") or {},
              "script_changes": [c["id"] for c in script_changes(bundle)], "decisions_carried_over": carried,
              "review_fingerprint": _fingerprint(review), "notes": data.get("notes", "")}
    write_json(bundle.path("01_review", "gate1.json"), record)
    bundle.manifest["gates"]["1"] = {"approver": record["approver"], "at": record["at"]}
    bundle.log(f"gate 1 by {record['approver']}")
    views.write_pair(bundle.path("01_review", "reviewed_script"), views.reviewed_script_markdown(bundle),
                     title=f"Reviewed Script: {bundle.manifest['video']['id']}")
    from . import master
    if bundle.manifest["stages"].get("master", {}).get("status") in ("built", "final") and master.stale_chunks(bundle):
        master.reopen(bundle)  # the approved words changed under a built Master Script
    return record


def line_roles(bundle) -> dict:
    """Line Roles after the Instructor's Gate 1 corrections."""
    roles = dict(read_json(bundle.path("01_review", "review.json"))["line_roles"])
    gate1 = bundle.path("01_review", "gate1.json")
    if gate1.exists():
        roles.update(read_json(gate1)["line_roles"])
    return roles


def accepted_changes(bundle) -> dict:
    """Every change the Master Script applies to the Instructor Script, by id: the Findings the Instructor accepted
    at Gate 1 (with any replacement they changed) and their own Script Changes (SC01…). A Script Change to a line
    replaces an accepted Finding's replacement for that line."""
    gate1 = read_json(bundle.path("01_review", "gate1.json"))
    changes = script_changes(bundle)
    changed = {c["line"] for c in changes if c.get("line")}
    out = {}
    for f in read_json(bundle.path("01_review", "review.json"))["findings"]:
        if gate1["decisions"].get(f["id"]) == "accept":
            f = dict(f)
            if f["id"] in gate1["fix_text"]:
                f["fix_text"] = gate1["fix_text"][f["id"]]
            if f.get("line") in changed:
                f.pop("fix_text", None)
            out[f["id"]] = f
    for c in changes:
        where = {"line": c["line"]} if c.get("line") else {"after_line": c["after_line"]}
        out[c["id"]] = dict(where, id=c["id"], fix_text=c["text"], source="instructor",
                            problem="Script Change by the Instructor", suggestion=c.get("note") or "use these words",
                            **({"role": c["role"]} if c.get("role") else {}))
    return out


def added_role(change: dict, roles: dict) -> str:
    """The Line Role of a line a Finding or Script Change adds: as given, else shown only (slide_only) when it follows a
    line that is only shown (a print after code), else spoken (a hook after a heading)."""
    return change.get("role") or ("slide_only" if roles.get(change["after_line"]) == "slide_only" else "spoken")


def record_gate2(bundle, data: dict) -> dict:
    if bundle.manifest["stages"].get("master", {}).get("status") != "built":
        raise Rejected("Build the Master Script first (`fz.py build <bundle> master`); Gate 2 approves it.")
    if not str(data.get("approver", "")).strip():
        raise Rejected("'approver' must name the Content Lead approving this Master Script.")
    record = {"approver": data["approver"], "at": now(), "notes": data.get("notes", "")}
    bundle.manifest["gates"]["2"] = record
    bundle.manifest["stages"]["master"]["status"] = "final"
    bundle.log(f"gate 2 by {record['approver']}: Final Master Script")
    return record


def record_gate3(bundle, data: dict) -> dict:
    """Gate 3: the Content Lead approves a Topic deliverable (the Quiz or the Cheatsheet)."""
    deliverable = data.get("deliverable", "quiz")
    if deliverable not in ("quiz", "cheatsheet"):
        raise Rejected("'deliverable' must be 'quiz' or 'cheatsheet'.")
    if bundle.manifest["stages"].get(deliverable, {}).get("status") != "built":
        raise Rejected(f"Build the {deliverable} first (`fz.py build <bundle> {deliverable}`); Gate 3 approves it.")
    if not str(data.get("approver", "")).strip():
        raise Rejected("'approver' must name the Content Lead.")
    if deliverable == "cheatsheet":
        from .cheatsheet import image_file, missing_images
        missing = missing_images(bundle)
        if missing:
            raise Rejected([f"{image_file(bundle, b['id']).name} is not generated yet; the Content Lead approves the cheatsheet with its images "
                            "(`fz.py show <bundle> cheatsheet-image-prompts`)." for b in missing])
    record = {"approver": data["approver"], "at": now(), "notes": data.get("notes", "")}
    bundle.manifest["gates"].setdefault("3", {})[deliverable] = record
    bundle.log(f"gate 3 ({deliverable}) by {record['approver']}")
    return record
