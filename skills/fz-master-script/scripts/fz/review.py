"""Stage 1: Script Review. The Host App writes one review per Chunk plus a whole-script overview;
these checks make sure every Finding points at real words and every line gets a Line Role."""
from __future__ import annotations

from .bundle import read_json, write_json
from .problems import Rejected
from . import views

from .vocab import CATEGORIES, CODE_STATUS, LINE_ROLES, SEVERITIES  # noqa: F401  (others import them from here)


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
    elif f.get("after_line"):  # something missing: fix_text is the line to add after it
        if f["after_line"] not in lines_by_id:
            problems.append(f"{label}: after_line {f['after_line']} does not exist.")
        elif f["after_line"] not in allowed_lines:
            problems.append(f"{label}: after_line {f['after_line']} is not in this Chunk; a line is added in the Chunk of the line it follows.")
        elif not allow_after_line and not str(f.get("fix_text") or "").strip():
            problems.append(f"{label}: give the line to add as 'fix_text'.")
    else:
        problems.append(f"{label}: give the line it is about ('line' + exact 'quote'), or 'after_line' and the line to add as 'fix_text'.")
    if f.get("category") not in CATEGORIES:
        problems.append(f"{label}: category must be one of {', '.join(CATEGORIES)}.")
    if f.get("severity") not in SEVERITIES:
        problems.append(f"{label}: severity must be one of {', '.join(SEVERITIES)}.")
    for key in ("problem", "suggestion"):
        if not str(f.get(key, "")).strip():
            problems.append(f"{label}: '{key}' is empty.")
    if f.get("role") not in (None, "spoken", "slide_only"):
        problems.append(f"{label}: role must be spoken or slide_only (the Line Role of the added line).")
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
    chunk_findings.sort(key=lambda f: order[f["line"]] if f.get("line") else order[f["after_line"]] + 0.5)
    findings = []
    for i, f in enumerate(chunk_findings + (overview.get("findings") or []), 1):
        findings.append(dict(f, id=f"F{i:03d}"))

    review = {"line_roles": roles, "findings": findings, "code_checks": code_checks, "points_to_check": points}
    write_json(bundle.path("01_review", "review.json"), review)
    md = review_markdown(bundle, review)
    views.write_pair(bundle.path("01_review", "review_report"), md, title=f"Script Review: {bundle.manifest['video']['id']}")
    bundle.manifest["stages"]["review"] = {"status": "built", "findings": len(findings)}
    bundle.log("review built")
    return review


def script_changes(bundle) -> list:
    """The Instructor's own wording changes (SC01…), made while they review the script."""
    path = bundle.path("01_review", "script_changes.json")
    return read_json(path)["changes"] if path.exists() else []


def submit_changes(bundle, data: dict) -> list:
    """Replace the Script Changes. They need the Instructor's approval at Gate 1, so any earlier Gate 1 reopens,
    and a built Master Script goes back to Gate 2."""
    from . import master

    if bundle.manifest["stages"].get("review", {}).get("status") != "built":
        raise Rejected("Build the review report first (`fz.py build <bundle> review`): the Instructor makes Script Changes while reviewing it.")
    changes = data.get("changes")
    if not isinstance(changes, list):
        raise Rejected("'changes' must be a list of every Script Change (an empty list removes them all).")
    lines = {l["id"] for l in bundle.lines()}
    problems, seen = [], set()
    for i, c in enumerate(changes, 1):
        label = f"Change {i}"
        if not isinstance(c, dict):
            problems.append(f"{label} must be an object.")
            continue
        if c.get("line") and c.get("after_line"):
            problems.append(f"{label}: give 'line' (to change or delete it) or 'after_line' (to add a line after it), not both.")
            continue
        key = ("line", c["line"]) if c.get("line") else ("after_line", c.get("after_line"))
        if not key[1]:
            problems.append(f"{label}: give 'line' to change or delete a line, or 'after_line' to add a line after it.")
        elif key[1] not in lines:
            problems.append(f"{label}: {key[1]} does not exist.")
        elif key in seen:
            problems.append(f"{label}: {key[1]} already has a change; give one change per line.")
        seen.add(key)
        text = c.get("text")
        if not isinstance(text, str):
            problems.append(f"{label}: 'text' must be the new words (\"\" deletes the line).")
        elif key[0] == "after_line" and not text.strip():
            problems.append(f"{label}: an added line needs 'text'.")
    if problems:
        raise Rejected(problems)
    saved = [dict(c, id=f"SC{i:02d}") for i, c in enumerate(changes, 1)]
    write_json(bundle.path("01_review", "script_changes.json"), {"changes": saved})
    if bundle.manifest["gates"].pop("1", None) is not None:
        bundle.log("Gate 1 reopened by Script Changes")
    if bundle.manifest["stages"].get("master", {}).get("status") in ("built", "final"):
        master.reopen(bundle)
    return saved


def draft_changes(bundle) -> dict:
    """The current Script Changes, to edit and submit again in full."""
    return {"changes": [{k: v for k, v in c.items() if k != "id"} for c in script_changes(bundle)]}


def draft_chunk(bundle, chunk: str) -> dict:
    """A review skeleton: every line of the Chunk, with its Line Role left to fill in."""
    if chunk not in chunk_ids(bundle):
        raise Rejected(f"There is no Chunk {chunk} ({', '.join(chunk_ids(bundle))}).")
    roles = {l["id"]: "" for l in bundle.lines() if l["chunk"] == chunk}
    return {"chunk": chunk, "line_roles": roles, "findings": [], "code_checks": [], "points_to_check": []}


# --- the readable page (moved from views) ---

def review_markdown(bundle, review: dict) -> str:
    lines_by_id = {l["id"]: l for l in bundle.lines()}
    out = [f"# Script Review: {bundle.manifest['video']['id']}", "", views.config_note(bundle), "",
           "## Points to check", "", views.bullet_list(review["points_to_check"]), "", "## Findings", ""]
    if not review["findings"]:
        out.append("No Findings.")
    for f in review["findings"]:
        where = f["line"] if f.get("line") else f"after {f['after_line']}"
        out += [f"### {f['id']} · {f['severity']} · {f['category']} · {where}", ""]
        if f.get("quote"):
            out += [f"> {f['quote']}", ""]
        out += [f"**Problem:** {f['problem']}", "", f"**Suggestion:** {f['suggestion']}", ""]
        if "fix_text" in f:
            out += [f"**Replacement line:** {f['fix_text'] or '(delete this line)'}", ""]
    if review.get("code_checks"):
        out += ["## Code checks", ""]
        for c in review["code_checks"]:
            out.append(f"- {', '.join(c.get('lines', []))}: **{c['status'].replace('_', ' ')}**" + (f": {c['note']}" if c.get("note") else ""))
        out.append("")
    not_spoken = [(lid, role) for lid, role in review["line_roles"].items() if role != "spoken"]
    out += ["## Lines that will not be spoken", "",
            "These lines stay off the teleprompter. Tell us if any of them should be spoken.", ""]
    out += [f"- {lid} · {role.replace('_', ' ')}: {lines_by_id[lid]['text']}" for lid, role in not_spoken] or ["- None"]
    return "\n".join(out) + "\n"
