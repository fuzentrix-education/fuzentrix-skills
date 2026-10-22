"""Stage 2: Master Script. First a Segment plan for the whole Video, then the Segments' details
one Master Script Chunk at a time. The AI never writes the whole master.json at once."""
from __future__ import annotations

from . import settings
from .bundle import read_json, write_json
from .problems import Rejected

VIDEO_SECTIONS = ("hook", "intro", "recap", "agenda", "explanation", "summary", "teaser", "outro")


def _num(line_id: str) -> int:
    return int(str(line_id)[1:]) if str(line_id)[1:].isdigit() else -1


def submit_plan(bundle, data: dict) -> list:
    if "1" not in bundle.manifest["gates"]:
        raise Rejected("Record Gate 1 first: the Master Script is planned from the approved Instructor Script.")
    lines = bundle.lines()
    last = len(lines)
    segments = data.get("segments") or []
    problems = []
    if not str(data.get("title", "")).strip():
        problems.append("'title' is empty.")
    if not segments:
        problems.append("'segments' is empty.")
    seen, expected_start = set(), 1
    for i, s in enumerate(segments, 1):
        sid = s.get("id") or f"segment {i}"
        if not s.get("id"):
            problems.append(f"Segment {i} has no 'id'.")
        elif sid in seen:
            problems.append(f"{sid} is used twice; Segment ids must be unique.")
        seen.add(sid)
        if s.get("section") not in VIDEO_SECTIONS:
            problems.append(f"{sid}: section must be one of {', '.join(VIDEO_SECTIONS)}.")
        if not str(s.get("title", "")).strip():
            problems.append(f"{sid}: 'title' is empty.")
        start, end = _num(s.get("start")), _num(s.get("end"))
        if start != expected_start:
            problems.append(f"{sid} must start at L{expected_start} (Segments cover every line once, in order).")
        if end < start or end > last:
            problems.append(f"{sid}: 'end' must be a line from its start to L{last}.")
            break
        expected_start = end + 1
    if segments and expected_start != last + 1 and not any("must start" in p or "'end'" in p for p in problems):
        problems.append(f"The last Segment must end at L{last}; lines L{expected_start}–L{last} are in no Segment.")
    if problems:
        raise Rejected(problems)

    chunks = group_segments(segments, settings.get(bundle, "chunk_lines"))
    write_json(bundle.path("02_master", "plan.json"), data)
    write_json(bundle.path("02_master", "chunks.json"), chunks)
    bundle.manifest["stages"]["master"] = {"status": "in_progress"}
    return chunks


def group_segments(segments: list, target: int) -> list:
    """Master Script Chunks hold whole Segments, up to about `target` lines each."""
    chunks, current, size = [], [], 0
    for s in segments:
        n = _num(s["end"]) - _num(s["start"]) + 1
        if current and size + n > target:
            chunks.append(current)
            current, size = [], 0
        current.append(s["id"])
        size += n
    if current:
        chunks.append(current)
    return [{"id": f"M{i:02d}", "segments": c} for i, c in enumerate(chunks, 1)]


def master_chunks(bundle) -> list:
    path = bundle.path("02_master", "chunks.json")
    return read_json(path) if path.exists() else []


def written_chunks(bundle) -> list:
    folder = bundle.path("02_master", "chunks")
    return sorted(p.stem for p in folder.glob("M*.json")) if folder.exists() else []


def stale_chunks(bundle) -> dict:
    """Written Master Script Chunks that no longer pass their checks against the Reviewed Script (after a Script
    Change or a new Gate 1), with the reasons. They are updated before the Master Script is built again."""
    from .gates import accepted_changes, line_roles

    written = set(written_chunks(bundle))
    if not written or not bundle.path("01_review", "gate1.json").exists():
        return {}
    roles, accepted, plan = line_roles(bundle), accepted_changes(bundle), plan_segments(bundle)
    out = {}
    for c in master_chunks(bundle):
        if c["id"] in written:
            problems = []
            for seg in read_json(bundle.path("02_master", "chunks", f"{c['id']}.json"))["segments"]:
                problems += _check_segment(seg, plan[seg["id"]], segment_lines(bundle, plan[seg["id"]]), roles, accepted)
            if problems:
                out[c["id"]] = problems
    return out


def _require_reviewed_script(bundle) -> None:
    if "1" not in bundle.manifest["gates"]:
        raise Rejected("The Reviewed Script is waiting for the Instructor's approval (Gate 1, in Fuzentrix Script Review). "
                       "Update the Master Script after it.")


# --- Master Script Chunks -------------------------------------------------------

SLIDE_LAYOUTS = ("title", "agenda", "bullets", "definition", "code", "comparison", "diagram", "quote", "image", "summary")
EVENT_KINDS = ("animation", "image", "diagram", "code", "broll", "direction")  # direction: camera, music or sound cue
EVENT_LAYOUTS = ("fullscreen_cutaway", "beside_instructor", "overlay", "slide_bg")


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def plan_segments(bundle) -> dict:
    return {s["id"]: s for s in read_json(bundle.path("02_master", "plan.json"))["segments"]}


def segment_lines(bundle, segment: dict) -> list:
    lo, hi = _num(segment["start"]), _num(segment["end"])
    return [l for l in bundle.lines() if lo <= _num(l["id"]) <= hi]


def submit_chunk(bundle, data: dict) -> str:
    from .gates import accepted_changes, line_roles

    _require_reviewed_script(bundle)
    chunks = {c["id"]: c for c in master_chunks(bundle)}
    chunk = chunks.get(data.get("chunk"))
    if chunk is None:
        raise Rejected(f"'chunk' must name a Master Script Chunk of this bundle ({', '.join(chunks) or 'submit the plan first'}).")
    given = [s.get("id") for s in data.get("segments") or []]
    if given != chunk["segments"]:
        raise Rejected(f"Chunk {chunk['id']} must contain exactly Segments {', '.join(chunk['segments'])}, in that order (got {', '.join(map(str, given)) or 'none'}).")

    roles = line_roles(bundle)
    accepted = accepted_changes(bundle)
    plan = plan_segments(bundle)
    problems = []
    for seg in data["segments"]:
        problems += _check_segment(seg, plan[seg["id"]], segment_lines(bundle, plan[seg["id"]]), roles, accepted)
    if problems:
        raise Rejected(problems)

    for seg in data["segments"]:
        for i, e in enumerate(seg.get("visual_events") or [], 1):
            e["id"] = f"{seg['id']}-E{i}"
    write_json(bundle.path("02_master", "chunks", f"{chunk['id']}.json"), data)
    stage = bundle.manifest["stages"].setdefault("master", {})
    if stage.get("status") in ("built", "final"):
        reopen(bundle)
    return chunk["id"]


def reopen(bundle) -> None:
    """Any change after the Master Script was built means Gate 2 must be passed again."""
    bundle.manifest["stages"]["master"]["status"] = "in_progress"
    if bundle.manifest["gates"].pop("2", None) is not None:
        bundle.log("Gate 2 reopened by a Master Script change")
    for stage in ("teleprompter", "slides", "visuals", "editor_kit"):
        bundle.manifest["stages"].pop(stage, None)


def _check_segment(seg: dict, planned: dict, lines: list, roles: dict, accepted: dict) -> list:
    sid = seg["id"]
    problems = []
    in_segment = {l["id"]: l for l in lines}
    fixes = {}
    for f in accepted.values():
        if f.get("line") and "fix_text" in f:
            fixes.setdefault(f["line"], []).append(f["fix_text"])

    if not str(seg.get("meaning_en", "")).strip():
        problems.append(f"{sid}: 'meaning_en' (the English meaning of what is said) is empty.")

    # spoken words: every spoken line once, in order, word for word (or an accepted replacement)
    spoken = seg.get("spoken") or []
    expected = [l["id"] for l in lines if roles.get(l["id"]) == "spoken"]
    given = [s.get("line") for s in spoken if s.get("line")]
    for lid in expected:
        if lid not in given and "" not in fixes.get(lid, []):
            problems.append(f"{sid}: {lid} is spoken but missing from 'spoken'.")
    for s in spoken:
        lid = s.get("line")
        if lid:
            if lid not in in_segment:
                problems.append(f"{sid}: {lid} is not in this Segment ({planned['start']}–{planned['end']}).")
            elif roles.get(lid) != "spoken":
                problems.append(f"{sid}: {lid} is a {roles.get(lid, 'unknown').replace('_', ' ')} line, not spoken; leave it out (or change its Line Role at Gate 1).")
            else:
                allowed = [in_segment[lid]["text"]] + [t for t in fixes.get(lid, []) if t]
                if fixes.get(lid):
                    allowed = [t for t in fixes[lid] if t]  # an accepted replacement must be applied
                if _norm(s.get("text", "")) not in [_norm(a) for a in allowed]:
                    problems.append(f"{sid}: {lid} must match the Reviewed Script word for word"
                                    + (" (an accepted Finding or Script Change replaces it; use the new words)." if fixes.get(lid) else "."))
        else:
            fid = s.get("from_finding")
            if not fid or fid not in accepted:
                problems.append(f"{sid}: an added line must name the accepted Finding or Script Change it comes from ('from_finding').")
            if not str(s.get("text", "")).strip():
                problems.append(f"{sid}: an added line has no text.")
    if [g for g in given if g in expected] != [e for e in expected if e in given]:
        problems.append(f"{sid}: spoken lines must stay in the script's order.")

    # slide
    slide = seg.get("slide")
    if not isinstance(slide, dict) or not str(slide.get("title", "")).strip():
        problems.append(f"{sid}: needs a 'slide' with a 'title'.")
    else:
        if slide.get("layout") not in SLIDE_LAYOUTS:
            problems.append(f"{sid}: slide layout must be one of {', '.join(SLIDE_LAYOUTS)}.")
        for lid in slide.get("source_lines") or []:
            if lid not in in_segment:
                problems.append(f"{sid}: slide source line {lid} is not in this Segment.")
        if not slide.get("source_lines"):
            problems.append(f"{sid}: slide 'source_lines' must list the lines its content comes from.")

    # visual events
    said = _norm(" ".join(s.get("text", "") for s in spoken)).lower()
    for i, e in enumerate(seg.get("visual_events") or [], 1):
        label = f"{sid} Visual Event {i}"
        if e.get("kind") not in EVENT_KINDS:
            problems.append(f"{label}: kind must be one of {', '.join(EVENT_KINDS)}.")
        if e.get("kind") != "direction" and e.get("layout") not in EVENT_LAYOUTS:
            problems.append(f"{label}: layout must be one of {', '.join(EVENT_LAYOUTS)}.")
        if not str(e.get("description", "")).strip():
            problems.append(f"{label}: 'description' is empty.")
        trigger = _norm(e.get("trigger", "")).lower()
        if not trigger or trigger not in said:
            problems.append(f"{label}: the trigger is not in {sid}'s spoken words; copy the exact words at which it starts.")
        if not e.get("source_lines"):
            problems.append(f"{label}: 'source_lines' must list the lines it shows.")
        for lid in e.get("source_lines") or []:
            if lid not in in_segment:
                problems.append(f"{label}: source line {lid} is not in this Segment.")
    for key in ("points_to_check",):
        if key in seg and not isinstance(seg[key], list):
            problems.append(f"{sid}: '{key}' must be a list.")
    return problems


def describe_chunk(bundle, chunk_id) -> str:
    """Everything the Host App needs to write one Master Script Chunk."""
    from .gates import accepted_changes, line_roles

    chunks = {c["id"]: c for c in master_chunks(bundle)}
    if chunk_id not in chunks:
        raise Rejected(f"There is no Master Script Chunk {chunk_id} ({', '.join(chunks) or 'submit the plan first'}).")
    roles, plan, accepted = line_roles(bundle), plan_segments(bundle), accepted_changes(bundle)
    out = []
    for sid in chunks[chunk_id]["segments"]:
        seg = plan[sid]
        lines = segment_lines(bundle, seg)
        out.append(f"{sid} · {seg['section']} · {seg['title']}  ({seg['start']}–{seg['end']})")
        ids = {l["id"] for l in lines}
        for l in lines:
            out.append(f"  {l['id']}  [{roles.get(l['id'], '?')}]  {l['text']}")
        for f in accepted.values():
            where = f.get("line") or f.get("after_line")
            if where in ids:
                text = f"  {f['id']} (accepted, {where}): {f['problem']} → {f['suggestion']}"
                if "fix_text" in f:
                    text += f" | replacement: {f['fix_text']!r}" if f["fix_text"] else " | replacement: delete this line"
                out.append(text)
        out.append("")
    return "\n".join(out)


def build(bundle) -> dict:
    from . import views
    from .gates import accepted_changes, line_roles

    _require_reviewed_script(bundle)
    missing = [c["id"] for c in master_chunks(bundle) if c["id"] not in written_chunks(bundle)]
    if not master_chunks(bundle):
        raise Rejected("Submit the Segment plan first.")
    if missing:
        raise Rejected([f"Master Script Chunk {c} has not been written yet." for c in missing])
    stale = stale_chunks(bundle)
    if stale:
        raise Rejected([f"Master Script Chunk {c} must be updated: {p}" for c, problems in stale.items() for p in problems])

    plan = read_json(bundle.path("02_master", "plan.json"))
    planned = {s["id"]: s for s in plan["segments"]}
    segments, points = [], []
    for c in master_chunks(bundle):
        for seg in read_json(bundle.path("02_master", "chunks", f"{c['id']}.json"))["segments"]:
            p = planned[seg["id"]]
            merged = {"id": seg["id"], "section": p["section"], "title": p["title"], "start": p["start"], "end": p["end"]}
            merged.update({k: v for k, v in seg.items() if k != "id"})
            segments.append(merged)
            points += [f"{seg['id']}: {pt}" for pt in seg.get("points_to_check") or []]
    for i, seg in enumerate(segments, 1):
        seg["slide"] = dict(seg["slide"], id=f"SL{i:02d}")

    master = {
        "video": dict(bundle.manifest["video"], title=plan["title"]),
        "config": bundle.manifest.get("config", {}),
        "agenda": plan.get("agenda", []),
        "learning_objectives": plan.get("learning_objectives", []),
        "key_terms": plan.get("key_terms", []),
        "segments": segments,
        "line_roles": line_roles(bundle),
        "findings_applied": sorted(accepted_changes(bundle)),
        "points_to_check": points,
    }
    write_json(bundle.path("02_master", "master.json"), master)
    views.write_pair(bundle.path("02_master", "master_script"), views.master_markdown(bundle, master),
                     title=f"Master Script: {plan['title']}")
    bundle.manifest["stages"]["master"] = {"status": "built"}
    bundle.manifest["gates"].pop("2", None)
    bundle.log("master built")
    return master


def draft_chunk(bundle, chunk_id: str) -> dict:
    """A Master Script Chunk skeleton with every Segment's spoken lines already filled in exactly: the script's words
    with every accepted Finding and Script Change applied (replacements, additions in place, deletions left out).
    The Host App fills in meaning_en, slide and visual_events. For a Chunk already written, those are kept and only
    the spoken lines are refreshed from the Reviewed Script."""
    from .gates import accepted_changes, line_roles

    chunks = {c["id"]: c for c in master_chunks(bundle)}
    if chunk_id not in chunks:
        raise Rejected(f"There is no Master Script Chunk {chunk_id} ({', '.join(chunks) or 'submit the plan first'}).")
    roles, plan, accepted = line_roles(bundle), plan_segments(bundle), accepted_changes(bundle)
    replace = {f["line"]: f["fix_text"] for f in accepted.values() if f.get("line") and "fix_text" in f}
    additions = [f for f in accepted.values() if f.get("after_line") and f.get("fix_text")]
    saved_path = bundle.path("02_master", "chunks", f"{chunk_id}.json")
    saved = {seg["id"]: seg for seg in read_json(saved_path)["segments"]} if saved_path.exists() else {}
    segments = []
    for sid in chunks[chunk_id]["segments"]:
        seg = plan[sid]
        lo, hi = _num(seg["start"]), _num(seg["end"])
        entries = []
        for l in segment_lines(bundle, seg):
            if roles.get(l["id"]) == "spoken" and replace.get(l["id"], None) != "":
                entries.append((_num(l["id"]), {"line": l["id"], "text": replace.get(l["id"], l["text"])}))
        for f in additions:
            if lo <= _num(f["after_line"]) <= hi:
                entries.append((_num(f["after_line"]) + 0.5, {"text": f["fix_text"], "from_finding": f["id"]}))
        spoken = [e for _, e in sorted(entries, key=lambda x: x[0])]
        segments.append(dict(saved[sid], spoken=spoken) if sid in saved else {
            "id": sid,
            "meaning_en": "",
            "spoken": spoken,
            "slide": {"title": "", "layout": "", "bullets": [], "source_lines": []},
            "visual_events": [],
            "points_to_check": [],
        })
    return {"chunk": chunk_id, "segments": segments}
