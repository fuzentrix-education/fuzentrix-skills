"""Stage 1: Script Review. The Host App writes one review per Chunk plus a whole-script overview;
these checks make sure every Finding points at real words and every line gets a Line Role."""
from __future__ import annotations

from .bundle import read_json, write_json
from .problems import Rejected
from . import views

LINE_ROLES = ("spoken", "heading", "speaker_label", "stage_direction", "note_to_team", "slide_only", "duplicate")
CATEGORIES = ("technical", "flow", "guideline", "hygiene", "code")
SEVERITIES = ("critical", "major", "minor")
CODE_STATUS = ("run", "read_only")


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def chunk_ids(bundle) -> list:
    return [c["id"] for c in read_json(bundle.path("00_ingest", "chunks.json"))]


def reviewed_chunks(bundle) -> list:
    folder = bundle.path("01_review", "chunks")
    return sorted(p.stem for p in folder.glob("C*.json")) if folder.exists() else []


def _check_finding(i: int, f: dict, lines_by_id: dict, allowed_lines, allow_after_line: bool) -> list:
    problems = []
    where = f.get("line") or f.get("after_line") or "?"
    label = f"Finding {i} ({where})"
    if not isinstance(f, dict):
        return [f"Finding {i} must be an object."]
    if f.get("line"):
        line = lines_by_id.get(f["line"])
        if line is None or f["line"] not in allowed_lines:
            problems.append(f"{label}: line {f['line']} is not in this {'script' if allow_after_line else 'Chunk'}.")
        elif not f.get("quote") or _norm(f["quote"]) not in _norm(line["text"]):
            problems.append(f"{label}: the quote is not in line {f['line']}. Copy the exact words from the line.")
    elif allow_after_line and f.get("after_line"):
        if f["after_line"] not in lines_by_id:
            problems.append(f"{label}: after_line {f['after_line']} does not exist.")
    else:
        problems.append(f"{label}: give the line it is about ('line' + exact 'quote')" + (", or 'after_line' for something missing." if allow_after_line else "."))
    if f.get("category") not in CATEGORIES:
        problems.append(f"{label}: category must be one of {', '.join(CATEGORIES)}.")
    if f.get("severity") not in SEVERITIES:
        problems.append(f"{label}: severity must be one of {', '.join(SEVERITIES)}.")
    for key in ("problem", "suggestion"):
        if not str(f.get(key, "")).strip():
            problems.append(f"{label}: '{key}' is empty.")
    if "fix_text" in f and not isinstance(f["fix_text"], str):
        problems.append(f"{label}: fix_text must be text (use \"\" to mean: delete this line).")
    return problems


def submit_chunk(bundle, data: dict) -> str:
    lines = bundle.lines()
    by_id = {l["id"]: l for l in lines}
    chunk = data.get("chunk")
    if chunk not in chunk_ids(bundle):
        raise Rejected(f"'chunk' must name a Chunk of this bundle ({', '.join(chunk_ids(bundle))}).")
    in_chunk = [l["id"] for l in lines if l["chunk"] == chunk]
    problems = []
    roles = data.get("line_roles") or {}
    for lid in in_chunk:
        role = roles.get(lid)
        if role is None:
            problems.append(f"{lid} has no Line Role.")
        elif role not in LINE_ROLES:
            problems.append(f"{lid}: Line Role '{role}' is not one of {', '.join(LINE_ROLES)}.")
    for lid in roles:
        if lid not in in_chunk:
            problems.append(f"{lid} is not in Chunk {chunk}; give Line Roles only for this Chunk's lines.")
    for i, f in enumerate(data.get("findings") or [], 1):
        problems += _check_finding(i, f, by_id, set(in_chunk), allow_after_line=False)
    for i, c in enumerate(data.get("code_checks") or [], 1):
        if c.get("status") not in CODE_STATUS:
            problems.append(f"Code check {i}: status must be 'run' or 'read_only'.")
        for lid in c.get("lines") or []:
            if lid not in in_chunk:
                problems.append(f"Code check {i}: {lid} is not in Chunk {chunk}.")
    if problems:
        raise Rejected(problems)
    write_json(bundle.path("01_review", "chunks", f"{chunk}.json"), data)
    _invalidate(bundle)
    return chunk


def submit_overview(bundle, data: dict) -> None:
    lines = bundle.lines()
    by_id = {l["id"]: l for l in lines}
    problems = []
    for i, f in enumerate(data.get("findings") or [], 1):
        problems += _check_finding(i, f, by_id, set(by_id), allow_after_line=True)
    if problems:
        raise Rejected(problems)
    write_json(bundle.path("01_review", "overview.json"), data)
    _invalidate(bundle)


def _invalidate(bundle) -> None:
    """A changed review means any built report and Gate 1 decisions are out of date."""
    stage = bundle.manifest["stages"].setdefault("review", {})
    if stage.get("status") == "built":
        stage["status"] = "in_progress"
        bundle.manifest["gates"].pop("1", None)
    stage.setdefault("status", "in_progress")


def build(bundle) -> dict:
    missing = [c for c in chunk_ids(bundle) if c not in reviewed_chunks(bundle)]
    problems = [f"Chunk {c} has not been reviewed yet." for c in missing]
    if not bundle.path("01_review", "overview.json").exists():
        problems.append("The whole-script overview has not been submitted yet (`fz.py submit <bundle> review-overview <file>`).")
    if problems:
        raise Rejected(problems)

    order = {l["id"]: i for i, l in enumerate(bundle.lines())}
    roles, chunk_findings, code_checks, points = {}, [], [], []
    for c in chunk_ids(bundle):
        data = read_json(bundle.path("01_review", "chunks", f"{c}.json"))
        roles.update(data["line_roles"])
        chunk_findings += data.get("findings") or []
        code_checks += data.get("code_checks") or []
        points += data.get("points_to_check") or []
    overview = read_json(bundle.path("01_review", "overview.json"))
    points += overview.get("points_to_check") or []
    chunk_findings.sort(key=lambda f: order[f["line"]])
    findings = []
    for i, f in enumerate(chunk_findings + (overview.get("findings") or []), 1):
        findings.append(dict(f, id=f"F{i:03d}"))

    review = {"line_roles": roles, "findings": findings, "code_checks": code_checks, "points_to_check": points}
    write_json(bundle.path("01_review", "review.json"), review)
    md = views.review_markdown(bundle, review)
    views.write_pair(bundle.path("01_review", "review_report"), md, title=f"Script Review: {bundle.manifest['video']['id']}")
    bundle.manifest["stages"]["review"] = {"status": "built", "findings": len(findings)}
    bundle.log("review built")
    return review


def draft_chunk(bundle, chunk: str) -> dict:
    """A review skeleton: every line of the Chunk, with its Line Role left to fill in."""
    if chunk not in chunk_ids(bundle):
        raise Rejected(f"There is no Chunk {chunk} ({', '.join(chunk_ids(bundle))}).")
    roles = {l["id"]: "" for l in bundle.lines() if l["chunk"] == chunk}
    return {"chunk": chunk, "line_roles": roles, "findings": [], "code_checks": [], "points_to_check": []}
