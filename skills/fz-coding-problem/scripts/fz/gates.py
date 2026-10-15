"""Gates: points where a named person approves before work continues."""
from __future__ import annotations

from .bundle import now, read_json, write_json
from .problems import Rejected
from .review import LINE_ROLES

DECISIONS = ("accept", "reject")


def record_gate1(bundle, data: dict) -> dict:
    if bundle.manifest["stages"].get("review", {}).get("status") != "built":
        raise Rejected("Build the review report first (`fz.py build <bundle> review`); Gate 1 decides on its Findings.")
    review = read_json(bundle.path("01_review", "review.json"))
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
              "notes": data.get("notes", "")}
    write_json(bundle.path("01_review", "gate1.json"), record)
    bundle.manifest["gates"]["1"] = {"approver": record["approver"], "at": record["at"]}
    bundle.log(f"gate 1 by {record['approver']}")
    return record


def line_roles(bundle) -> dict:
    """Line Roles after the Instructor's Gate 1 corrections."""
    roles = dict(read_json(bundle.path("01_review", "review.json"))["line_roles"])
    gate1 = bundle.path("01_review", "gate1.json")
    if gate1.exists():
        roles.update(read_json(gate1)["line_roles"])
    return roles


def accepted_findings(bundle) -> dict:
    """Accepted Findings by id, with any replacement text the Instructor changed at Gate 1."""
    gate1 = read_json(bundle.path("01_review", "gate1.json"))
    out = {}
    for f in read_json(bundle.path("01_review", "review.json"))["findings"]:
        if gate1["decisions"].get(f["id"]) == "accept":
            f = dict(f)
            if f["id"] in gate1["fix_text"]:
                f["fix_text"] = gate1["fix_text"][f["id"]]
            out[f["id"]] = f
    return out


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
    record = {"approver": data["approver"], "at": now(), "notes": data.get("notes", "")}
    bundle.manifest["gates"].setdefault("3", {})[deliverable] = record
    bundle.log(f"gate 3 ({deliverable}) by {record['approver']}")
    return record
