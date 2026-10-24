"""Where a Video Bundle is, and what to do next. This is how work resumes in a new chat."""
from __future__ import annotations

from .problems import Lazy, MissingPart, part

brandkit, master, review = Lazy("brandkit"), Lazy("master"), Lazy("review")


def _shown(step, bundle) -> str:
    """A skill's status line; a step whose module this skill doesn't ship is shown by its own skill."""
    try:
        return step(bundle)
    except MissingPart:
        return "Shown by that skill (this one doesn't include it)."


def next_step(bundle) -> tuple:
    """Return (the first unfinished skill, one status line per skill)."""
    if bundle.manifest.get("kind") == "topic":
        return topic_next_step(bundle)
    lines = [("fz-script-review", _shown(_review_step, bundle)), ("fz-master-script", _shown(_master_step, bundle))]
    final = bundle.manifest["stages"].get("master", {}).get("status") == "final"
    for skill, step, branded in (("fz-slides", _slides_step, True), ("fz-visuals", _visuals_step, True),
                                 ("fz-teleprompter", _teleprompter_step, False)):
        if not final:
            lines.append((skill, "Waiting for the Final Master Script (fz-master-script, Gate 2)."))
        elif branded and not bundle.manifest.get("brand"):
            lines.append((skill, _shown(lambda b: brandkit.ASK, bundle)))
        else:
            lines.append((skill, _shown(step, bundle)))
    text = "\n".join(f"{skill} · {step}" for skill, step in lines)
    if all(step.startswith("Done") for _, step in lines):
        text += "\nAll done: pack the Video Bundle (`fz.py pack <bundle> <zip>`) and the Editor Kit (`fz.py pack-editor <bundle> <zip>`) for download."
    first = next((skill for skill, step in lines if not step.startswith("Done")), "Done")
    return (first, text)


def _review_step(bundle) -> str:
    stages, gates = bundle.manifest["stages"], bundle.manifest["gates"]
    if "1" in gates and stages.get("review", {}).get("status") == "built":
        return f"Done: Reviewed Script (Gate 1 by {gates['1']['approver']})."
    if stages.get("review", {}).get("status") != "built":
        chunks = review.chunk_ids(bundle)
        done = review.reviewed_chunks(bundle)
        for i, c in enumerate(chunks, 1):
            if c not in done:
                return (f"Next: Script Review of Chunk {c} ({i} of {len(chunks)}). Read it with `fz.py show <bundle> chunk {c}`, "
                        f"start from `fz.py draft <bundle> review {c} <file>`, then `fz.py submit <bundle> review <file>`.")
        if not bundle.path("01_review", "overview.json").exists():
            return ("Next: Script Review overview of the whole script (`fz.py schema review-overview`), "
                    "then `fz.py submit <bundle> review-overview <file>`.")
        return "Next: build the review report with `fz.py build <bundle> review`."
    if "1" not in gates:
        return ("Next: Gate 1. Show the Instructor review_report and record their decision on every Finding "
                "(`fz.py schema gate1`, then `fz.py gate <bundle> 1 <file>`).")
    return f"Done: Reviewed Script (Gate 1 by {gates['1']['approver']})."


def _master_step(bundle) -> str:
    stages, gates = bundle.manifest["stages"], bundle.manifest["gates"]
    if "2" in gates and stages.get("master", {}).get("status") == "final":
        return f"Done: Final Master Script (Gate 2 by {gates['2']['approver']})."
    if "1" not in gates:
        return "Waiting for the Reviewed Script (fz-script-review, Gate 1)."
    chunks = master.master_chunks(bundle)
    if not chunks:
        return ("Next: Master Script plan: the Segments of the whole Video (`fz.py schema plan`), "
                "then `fz.py submit <bundle> plan <file>`.")
    done, stale = master.written_chunks(bundle), master.stale_chunks(bundle)
    for i, c in enumerate(chunks, 1):
        if c["id"] not in done:
            return (f"Next: Master Script of Chunk {c['id']} ({i} of {len(chunks)}): Segments {c['segments'][0]}–{c['segments'][-1]}. "
                    f"Read them with `fz.py show <bundle> segments {c['id']}`, start from `fz.py draft <bundle> master {c['id']} <file>`, "
                    f"then `fz.py submit <bundle> master <file>`.")
        if c["id"] in stale:
            return (f"Next: update Master Script Chunk {c['id']}: the Reviewed Script changed ({stale[c['id']][0]}). "
                    f"Start from `fz.py draft <bundle> master {c['id']} <file>`, which keeps its slide and Visual Events with the new "
                    f"spoken lines; check they still fit the new words, then `fz.py submit <bundle> master <file>`.")
    status = stages.get("master", {}).get("status")
    if status not in ("built", "final"):
        return "Next: build the Master Script with `fz.py build <bundle> master`."
    if "2" not in gates:
        return ("Next: Gate 2. Show the Content Lead master_script (with its Slide plan and Points to check); apply any edits, "
                "then record approval (`fz.py gate <bundle> 2 <file>` with the approver's name).")
    return f"Done: Final Master Script (Gate 2 by {gates['2']['approver']})."


def _slides_step(bundle) -> str:
    stale = brandkit.stale_note(bundle, "slides", "fz.py build <bundle> slides")
    if stale:
        return stale
    if bundle.manifest["stages"].get("slides", {}).get("status") == "built":
        return f"Done: editor_kit/slides/{bundle.manifest['video']['id']}_slides.pptx."
    return "Next: `fz.py build <bundle> slides`."


def _visuals_step(bundle) -> str:
    from .bundle import read_json

    stale = brandkit.stale_note(bundle, "visuals", "fz.py build <bundle> visuals")
    if stale:
        return stale
    if bundle.manifest["stages"].get("visuals", {}).get("status") == "built":
        return "Done: images, diagrams and storyboards are in editor_kit/ (see visuals.html)."
    visuals, animations = part("visuals"), part("animations")
    m = read_json(bundle.path("02_master", "master.json"))
    images, todo = visuals.missing_images(bundle, m), visuals.diagrams_to_draw(bundle, m)
    anims, ai = animations.to_specify(bundle, m), animations.missing_ai(bundle, m)
    if images or todo or anims or ai:
        parts = []
        if images:
            parts.append(f"{len(images)} image{'s' if len(images) != 1 else ''} to generate (`fz.py show <bundle> image-prompts`)")
        if todo:
            parts.append(f"{len(todo)} diagram{'s' if len(todo) != 1 else ''} to draw (`fz.py draft <bundle> diagrams all <file>`)")
        if anims:
            parts.append(f"{len(anims)} animation{'s' if len(anims) != 1 else ''} to specify (`fz.py draft <bundle> animations all <file>`)")
        if ai:
            parts.append(f"{len(ai)} animation element{'s' if len(ai) != 1 else ''} to generate (`fz.py show <bundle> animation-prompts`)")
        return "Next: " + "; ".join(parts) + ", then `fz.py build <bundle> visuals`."
    return "Next: `fz.py build <bundle> visuals` (storyboards are optional: `fz.py show <bundle> storyboard-prompts`)."


def _teleprompter_step(bundle) -> str:
    if bundle.manifest["stages"].get("teleprompter", {}).get("status") == "built":
        return "Done: teleprompter/ (.txt, .docx, .html)."
    return "Next: Teleprompter Script: `fz.py build <bundle> teleprompter`."


def topic_next_step(bundle) -> tuple:
    """A Topic has two independent deliverables; report the next step for each."""
    quiz_step, sheet_step = _shown(_quiz_step, bundle), _shown(_cheatsheet_step, bundle)
    stage = "Quiz" if not quiz_step.startswith("Done") else "Cheatsheet"
    return (stage, f"Quiz · {quiz_step}\nCheatsheet · {sheet_step}")


def _quiz_step(bundle) -> str:
    quiz = part("quiz")

    stages = bundle.manifest["stages"]
    if "quiz_request" not in stages:
        return ("Next: Quiz Request. Turn the user's quiz choices into JSON (`fz.py schema quiz-request`), "
                "then `fz.py submit <bundle> quiz-request <file>`.")
    done = quiz.written_videos(bundle)
    for vid in bundle.manifest["videos"]:
        if vid not in done:
            return (f"Next: Quiz questions for {vid}. Read `fz.py show <bundle> sources {vid}`, start from "
                    f"`fz.py draft <bundle> quiz {vid} <file>`, then `fz.py submit <bundle> quiz <file>`.")
    if stages.get("quiz", {}).get("status") != "built":
        return "Next: build the Quiz with `fz.py build <bundle> quiz`."
    if "quiz" not in bundle.manifest["gates"].get("3", {}):
        return ("Next: Gate 3. Show the Content Lead quiz_preview.html; apply edits, then record approval "
                "(`fz.py gate <bundle> 3 <file>`, deliverable quiz).")
    if stages["quiz"].get("markup", True):
        return ("Done: the Quiz is approved. Before uploading, turn it into the LMS's RICH_HTML with Fuzentrix Quiz HTML "
                "(fz-quiz-html): its cells mark code and bold text.")
    return "Done: the Quiz is approved. <topic>_quiz.xlsx is plain text and can be uploaded to the LMS as it is."


def _cheatsheet_step(bundle) -> str:
    missing_images = part("cheatsheet").missing_images

    if not bundle.manifest.get("brand"):
        return brandkit.ASK
    stale = brandkit.stale_note(bundle, "cheatsheet", "fz.py build <bundle> cheatsheet")
    if stale:
        return stale
    stage = bundle.manifest["stages"].get("cheatsheet", {}).get("status")
    if stage is None:
        return ("Next: Cheatsheet. Read `fz.py show <bundle> sources <video>` for each Video, start from "
                "`fz.py draft <bundle> cheatsheet all <file>`, then `fz.py submit <bundle> cheatsheet <file>`.")
    missing = missing_images(bundle)
    if stage != "built" and not missing:
        return "Next: build the Cheatsheet with `fz.py build <bundle> cheatsheet`."
    if missing:
        return (f"Next: {len(missing)} cheatsheet image{'s' if len(missing) != 1 else ''} to generate "
                "(`fz.py show <bundle> cheatsheet-image-prompts`), then `fz.py build <bundle> cheatsheet`.")
    if "cheatsheet" not in bundle.manifest["gates"].get("3", {}):
        return ("Next: Gate 3. Show the Content Lead cheatsheet/preview.html; apply edits, then record approval "
                "(`fz.py gate <bundle> 3 <file>`, deliverable cheatsheet).")
    return ("Done: the Cheatsheet is approved. Paste <topic>_cheatsheet.html into the LMS and attach each image where "
            "insertion_map.md shows its placeholder.")
