"""Command-line interface. Each fz-* skill tells the Host App which command to run; end users never type these."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import json

from . import animations, brandkit, lmspolicy, quizhtml, cheatsheet, configpack, editor, gates, lmshtml, master, naming, quiz, review, schemas, settings, slides, status, teleprompter, topic, visuals
from .bundle import Bundle, pack, read_json, unpack, write_json
from .chunks import assign, make_chunks
from .ingest import number_lines, read_script, tags
from . import kits
from .problems import Rejected, format_problems


def format_line(line: dict) -> str:
    t = tags(line)
    suffix = f"  ‹{', '.join(t)}›" if t else ""
    return f"{line['id']}  {line['text']}{suffix}"


def cmd_new(args) -> None:
    lines = number_lines(read_script(args.script))
    if not lines:
        raise Rejected(f"{args.script} contains no text.")
    pack = configpack.read_release(args.config) if args.config else None  # check before creating anything
    if args.brand and args.brand != "default":
        kits.read_release(brandkit.BRAND, args.brand)
    bundle = Bundle.create(args.bundle, args.video_id, title=args.title, instructor=args.instructor)
    if pack:
        manifest, files = pack
        configpack.snapshot(bundle.root, manifest, files)
        bundle.manifest["config"] = {"version": manifest["config_version"], "draft": False}
    else:
        bundle.manifest["config"] = {"version": None, "draft": True}
    if args.chunk_lines:
        bundle.manifest.setdefault("overrides", {})["chunk_lines"] = args.chunk_lines
    chunks = make_chunks(lines, settings.get(bundle, "chunk_lines"))
    write_json(bundle.path("00_ingest", "lines.json"), assign(lines, chunks))
    write_json(bundle.path("00_ingest", "chunks.json"), chunks)
    bundle.manifest["stages"]["ingest"] = {"status": "done", "source": str(args.script)}
    bundle.log("ingest")
    if args.brand:
        brandkit.attach(bundle, args.brand)
    bundle.save()
    print(f"Created Video Bundle {args.video_id}: {len(lines)} lines in {len(chunks)} Chunk(s).")


def cmd_show(args) -> None:
    bundle = Bundle(args.bundle)
    if args.what == "lines":
        for line in bundle.lines():
            print(format_line(line))
    elif args.what == "config":
        config = bundle.manifest.get("config", {})
        if config.get("draft"):
            print("DRAFT: minimal skill defaults, not the Fuzentrix Configuration Pack")
        else:
            print(f"Configuration Pack {config['version']}")
        for key in sorted(settings.SETTINGS):
            print(f"  {key}: {settings.get(bundle, key)}")
    elif args.what == "guidelines":
        pack_copy = bundle.path("_config_snapshot", "policy", "video-guidelines.md")
        if pack_copy.exists():
            print(pack_copy.read_text(encoding="utf-8"), end="")
        else:
            print("DRAFT: skill default guidelines, not the Fuzentrix Configuration Pack")
            print((Path(__file__).parent / "defaults" / "video-guidelines.md").read_text(encoding="utf-8"), end="")
    elif args.what == "brand":
        print(brandkit.describe(bundle))
    elif args.what == "image-prompts":
        print(visuals.prompts(bundle))
    elif args.what == "cheatsheet-image-prompts":
        print(cheatsheet.prompts(bundle))
    elif args.what == "animation-prompts":
        print(animations.prompts(bundle))
    elif args.what == "storyboard-prompts":
        print(visuals.storyboard_prompts(bundle))
    elif args.what == "sources":
        if not args.id:
            raise Rejected("Name the Video, e.g. `fz.py show <bundle> sources dbms-p2-t1-v1`.")
        print(topic.describe_sources(bundle, args.id))
    elif args.what == "quiz-request":
        print(json.dumps(read_json(bundle.path("quiz", "request.json")), ensure_ascii=False, indent=2))
    elif args.what == "chunks":
        for c in read_json(bundle.path("00_ingest", "chunks.json")):
            print(f"{c['id']}  {c['start']}–{c['end']}  ({c['lines']} line{'s' if c['lines'] != 1 else ''})")
    elif args.what == "segments":
        print(master.describe_chunk(bundle, args.id))
    elif args.what == "chunk":
        if not args.id:
            raise Rejected("Name the Chunk to show, e.g. `fz.py show <bundle> chunk C01`.")
        lines = [l for l in bundle.lines() if l["chunk"] == args.id]
        if not lines:
            raise Rejected(f"There is no Chunk {args.id}. See `fz.py show <bundle> chunks`.")
        for line in lines:
            print(format_line(line))


def _load_json_file(path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise Rejected(f"{path} does not exist.")
    except json.JSONDecodeError as e:
        raise Rejected(f"{path} is not valid JSON: {e}.")
    if not isinstance(data, dict):
        raise Rejected(f"{path} must contain one JSON object.")
    return data


def cmd_submit(args) -> None:
    bundle = Bundle(args.bundle)
    data = _load_json_file(args.file)
    if args.kind == "review":
        chunk = review.submit_chunk(bundle, data)
        msg = f"Accepted Script Review of Chunk {chunk}."
    elif args.kind == "review-overview":
        review.submit_overview(bundle, data)
        msg = "Accepted Script Review overview."
    elif args.kind == "script-changes":
        changes = review.submit_changes(bundle, data)
        msg = f"Accepted {len(changes)} Script Change(s). The Instructor approves them at Gate 1."
    elif args.kind == "master":
        chunk = master.submit_chunk(bundle, data)
        msg = f"Accepted Master Script Chunk {chunk}."
    elif args.kind == "quiz-request":
        request = quiz.submit_request(bundle, data)
        msg = (f"Accepted the Quiz Request: {request['questions_total']} questions "
               f"({', '.join(f'{k} {v}' for k, v in request['by_type'].items() if v)}).")
    elif args.kind == "diagrams":
        n = visuals.submit_diagrams(bundle, data)
        msg = f"Accepted {n} diagram spec(s)."
    elif args.kind == "animations":
        n = animations.submit(bundle, data)
        msg = f"Accepted {n} animation spec(s)."
    elif args.kind == "cheatsheet":
        cheatsheet.submit(bundle, data)
        msg = f"Accepted the Cheatsheet: {len(data['sections'])} section(s)."
    elif args.kind == "quiz":
        vid = quiz.submit_questions(bundle, data)
        msg = f"Accepted the Quiz questions for {vid}."
    elif args.kind == "plan":
        chunks = master.submit_plan(bundle, data)
        msg = f"Accepted the Segment plan: {len(data['segments'])} Segment(s) in {len(chunks)} Master Script Chunk(s)."
    bundle.log(f"submit {args.kind}")
    bundle.save()
    print(msg)
    print(status.next_step(bundle)[1])


def cmd_build(args) -> None:
    bundle = Bundle(args.bundle)
    if args.what == "review":
        result = review.build(bundle)
        bundle.save()
        print(f"Built 01_review/review_report.md and .html: {len(result['findings'])} Finding(s), "
              f"{len(result['points_to_check'])} point(s) to check.")
    elif args.what == "teleprompter":
        result = teleprompter.build(bundle)
        bundle.save()
        print(f"Built teleprompter/ (.txt, .docx, .html) and teleprompter_report.md: {result['words']} spoken words, "
              f"about {result['minutes']:.1f} min.")
    elif args.what == "editor-kit":
        result = editor.build(bundle)
        bundle.save()
        print(f"Built editor_kit/editor_guide.md and .html, markers.xml (Premiere) and cue_sheet.csv: {result['events']} Visual Event(s), "
              f"about {result['minutes']:.1f} min (estimated).")
    elif args.what == "visuals":
        result = visuals.build(bundle, without_images=args.without_images)
        bundle.save()
        note = (f" {result['png_missing']} diagram(s) were drawn as SVG only: this sandbox has no matplotlib for PNG."
                if result["png_missing"] else "")
        if result["missing"]:
            note += (f" {result['missing']} image{'s' if result['missing'] != 1 else ''} still to generate: AI elements are dashed "
                     "placeholders; generate them and build again (`fz.py status <bundle>` lists them).")
        print(f"Checked {result['images']} image(s), drew or checked {result['diagrams']} diagram(s), checked {result['storyboards']} "
              f"storyboard(s); wrote editor_kit/visuals.html and refreshed the editor guide. Rebuild the slides to place new images.{note}")
    elif args.what == "slides":
        result = slides.build(bundle)
        bundle.save()
        print(f"Built editor_kit/slides/{result['path'].name} ({result['slides']} editable slides) and slides.md; refreshed the editor guide.")
    elif args.what == "cheatsheet":
        result = cheatsheet.build(bundle)
        bundle.save()
        tid = bundle.manifest["topic"]["id"]
        look = {"style": "in Brand Kit colours (inline styles the LMS keeps)",
                "span": "in Brand Kit colours on headings, labels and code blocks (the LMS keeps colour on <span> and <pre> only)",
                "class": f"with fz-* classes; give cheatsheet/{tid}_theme.css to the LMS team to install once",
                "structure": "as structure and icons only: these LMS rules keep no colours (no style or fz-* classes)"}[result["mode"]]
        print(f"Built cheatsheet/{tid}_cheatsheet.html, preview.html and insertion_map.md: {result['sections']} section(s), "
              f"{result['images']} image(s), {look}. It passes the LMS cheatsheet_page rules ({result['policy']}).")
        if not result["interactive"]:
            print("These LMS rules don't keep <details>, so each reveal is shown as a question with its answer.")
        if result["missing"]:
            print(f"{result['missing']} image(s) still to generate: `fz.py show <bundle> cheatsheet-image-prompts`.")
    elif args.what == "quiz":
        result = quiz.build(bundle)
        bundle.save()
        tid = bundle.manifest["topic"]["id"]
        print(f"Built quiz/{tid}_quiz.xlsx in the LMS Quiz Template and quiz_preview: {result['questions']} questions, {result['points']} points.")
    elif args.what == "master":
        result = master.build(bundle)
        bundle.save()
        print(f"Built 02_master/master.json, master_script.md and .html: {len(result['segments'])} Segment(s), "
              f"{len(result['points_to_check'])} point(s) to check.")
    print(status.next_step(bundle)[1])


def cmd_gate(args) -> None:
    bundle = Bundle(args.bundle)
    if args.n == "1":
        data = _load_json_file(args.file) if args.file else {}
        record = gates.record_gate1(bundle, data)
        accepted = sum(1 for d in record["decisions"].values() if d == "accept")
        changes = f" and {len(record['script_changes'])} Script Change(s) approved" if record["script_changes"] else ""
        carried = " (decisions kept from the last Gate 1)" if record["decisions_carried_over"] else ""
        print(f"Gate 1 recorded for {record['approver']}: {accepted} of {len(record['decisions'])} Finding(s) accepted{carried}{changes}. "
              "Wrote 01_review/reviewed_script.md and .html.")
    elif args.n == "3":
        record = gates.record_gate3(bundle, _load_json_file(args.file) if args.file else {})
        print(f"Gate 3 recorded for {record['approver']}.")
    elif args.n == "2":
        record = gates.record_gate2(bundle, _load_json_file(args.file) if args.file else {})
        print(f"Gate 2 recorded for {record['approver']}: this is now the Final Master Script.")
    bundle.save()
    print(status.next_step(bundle)[1])


def cmd_draft(args) -> None:
    bundle = Bundle(args.bundle)
    if args.kind == "review":
        data = review.draft_chunk(bundle, args.id)
        todo = "fill in every Line Role and add Findings"
    elif args.kind == "script-changes":
        data = review.draft_changes(bundle)
        todo = "add, edit or remove the Instructor's changes, keeping every change still wanted"
    elif args.kind == "animations":
        data = animations.draft(bundle)
        todo = ("for each animation choose its template, write its diagram (for templates code can draw) and its steps: "
                "which element ids each step shows, and the spoken words that trigger it")
    elif args.kind == "diagrams":
        data = visuals.draft_diagrams(bundle)
        todo = "set each diagram's type (flow, table, tree, compare, or image) and its content"
    elif args.kind == "cheatsheet":
        data = cheatsheet.draft(bundle)
        todo = "write each section's blocks, the intro and the quick revision, covering every key term"
    elif args.kind == "quiz":
        data = quiz.draft_video(bundle, args.id)
        todo = f"write the {len(data['questions'])} question(s) for this Video"
    else:
        data = master.draft_chunk(bundle, args.id)
        todo = ("its spoken lines are refreshed from the Reviewed Script; check its slide and visual_events still fit the new words"
                if args.id in master.written_chunks(bundle) else "keep the spoken lines as they are; fill in meaning_en, slide and visual_events")
    write_json(args.file, data)
    print(f"Wrote a draft of {args.kind} {args.id} to {args.file}: {todo}, then `fz.py submit <bundle> {args.kind} {args.file}`.")


def cmd_attach(args) -> None:
    bundle = Bundle(args.bundle)
    kind = args.kind
    if kind == "auto":
        if args.source == "default":
            raise Rejected("Say which kit 'default' means: `fz.py attach <bundle> brand default`.")
        kind = "brand" if kits.detect(args.source, (brandkit.BRAND, configpack.CONFIG)) is brandkit.BRAND else "config"
    if kind == "brand":
        rec = brandkit.attach(bundle, args.source)
        what = f"Brand Kit {rec['id']} {rec['version']}" + (" (the Default Brand Kit)" if rec["source"] == "default" else "")
    else:
        rec = attach_config(bundle, args.source)
        what = f"Configuration Pack {rec['version']}"
    bundle.save()
    stale = f" Rebuild: {', '.join(rec['stale'])}." if rec.get("stale") else ""
    print(f"Attached {what} to {(bundle.manifest.get('video') or bundle.manifest.get('topic'))['id']}.{stale}")
    print(status.next_step(bundle)[1])


def attach_config(bundle, source) -> dict:
    """Use a Configuration Pack release for this bundle. Deliverables its changed files affect go stale."""
    manifest, files = configpack.read_release(source)
    old_dir = bundle.path(configpack.CONFIG.snapshot)
    old = {f["path"]: f["sha256"] for f in read_json(old_dir / "manifest.json")["files"]} if (old_dir / "manifest.json").exists() else {}
    changed = [f for f in manifest["files"] if old.get(f["path"]) != f["sha256"]]
    configpack.snapshot(bundle.root, manifest, files)
    bundle.manifest["config"] = {"version": manifest["config_version"], "draft": False}
    stale = sorted({s for f in changed for s in f.get("affects", []) if s not in ("ingest", "review", "master")} & set(bundle.manifest["stages"]))
    for s in stale:
        bundle.manifest["stages"].pop(s)
    bundle.log(f"configuration pack {manifest['config_version']}")
    return {"version": manifest["config_version"], "stale": stale}


def cmd_override(args) -> None:
    import yaml

    bundle = Bundle(args.bundle)
    value = yaml.safe_load(args.value) if not args.value.startswith("#") else args.value
    o = brandkit.override(bundle, args.path, value, args.note or "")
    bundle.save()
    print(f"For this bundle only, {args.path} is now {o['value']} (was {o['was']}). Rebuild what uses it.")
    print(status.next_step(bundle)[1])


def _policy(args) -> dict:
    """The LMS HTML Policy: from a bundle, a Configuration Pack, or the skill's draft."""
    if getattr(args, "config", None):
        manifest, files = configpack.read_release(args.config)
        if "policy/lms-html.yaml" not in files:
            raise Rejected(f"Configuration Pack {manifest['config_version']} has no policy/lms-html.yaml.")
        return lmspolicy.completed(kits.load_yaml(files["policy/lms-html.yaml"].decode("utf-8")), f"Configuration Pack {manifest['config_version']}")
    return lmspolicy.load(Bundle(args.bundle) if getattr(args, "bundle", None) else None)


def cmd_convert_quiz(args) -> None:
    policy = _policy(args)
    result = quizhtml.convert(args.source, args.target, policy, quizhtml.load_marks(args.marks), args.plain)
    how = []
    if result["marked"]:
        how.append(f"{result['marked']} marked in the AI pass")
    if result["guessed"]:
        how.append(f"{result['guessed']} with code recognised by its look")
    if result["html"]:
        how.append(f"{result['html']} already HTML, checked")
    print(f"Converted {args.source} → {args.target}: {result['rows']} question row(s) set to RICH_HTML, {result['cells']} cell(s) written as "
          f"LMS HTML" + (f" ({'; '.join(how)})" if how else "") + f", each checked against its LMS context ({policy['_source']}).")
    if args.plain:
        print(f"Wrote {args.plain}: the same questions as PLAIN_TEXT, without marks.")


def cmd_quiz_cells(args) -> None:
    n = quizhtml.cells(args.source, args.file)
    print(f"Wrote {n} question, option and explanation cell(s) to {args.file}. Add a 'marks' entry {{ref, marked}} for each cell "
          "that needs `code`, ``` blocks or **bold**; change no words. Then `fz.py convert-quiz <workbook> <out> --marks <file>`.")


def cmd_coding_html(args) -> None:
    if args.action == "draft":
        if len(args.paths) != 2:
            raise Rejected("Use: fz.py coding-html draft <problem file> <draft.json>")
        source, out = args.paths
        data = lmshtml.draft(source)
        write_json(out, data)
        note = f" It has {data['images']} image(s): attach them when uploading." if data["images"] else ""
        print(f"Wrote {out}: the given problem as {len(data['lines'])} numbered lines.{note} Place its words, exactly, into the sections; "
              "list heading-only lines in skipped_lines; then `fz.py coding-html build <file> <problem file> <out folder>`.")
        return
    if len(args.paths) != 3:
        raise Rejected("Use: fz.py coding-html build <converted.json> <problem file> <out folder> [--run]")
    file, source, out = args.paths
    result = lmshtml.build(_load_json_file(file), source, out, _policy(args), run_solution=args.run)
    print(f"Built {result['path']}: {', '.join(result['sections'])}. It passes the LMS coding_problem rules ({result['policy']}).")
    if result.get("images"):
        print(f"The given problem has {result['images']} image(s); attach them when uploading.")
    if args.run:
        if not result["run"]:
            print("Nothing was run: the problem gives no Python solution with examples or test cases.")
        elif result["problems"]:
            print("Running the given solution found problems (reported only; the content is as given):")
            for p_ in result["problems"]:
                print(f"- {p_}")
        else:
            print(f"{result['examples']} example(s) passed against the given solution, and {result['test_cases']} test case(s).")


def cmd_check_html(args) -> None:
    if args.policy:
        policy = lmspolicy.from_file(args.policy)
    elif args.config:
        manifest, files = configpack.read_release(args.config)
        if "policy/lms-html.yaml" not in files:
            raise Rejected(f"Configuration Pack {manifest['config_version']} has no policy/lms-html.yaml.")
        policy = lmspolicy.completed(kits.load_yaml(files["policy/lms-html.yaml"].decode("utf-8")), f"Configuration Pack {manifest['config_version']}")
    else:
        policy = lmspolicy.load(Bundle(args.bundle) if args.bundle else None)
    problems = lmspolicy.check(Path(args.file).read_text(encoding="utf-8"), policy, args.context)
    if problems:
        raise Rejected([f"{args.context}: {p}" for p in problems])
    print(f"OK: {args.file} keeps everything under the LMS {args.context} rules ({policy['_source']}).")


def cmd_schema(args) -> None:
    print(schemas.describe(args.kind))


def cmd_pack_editor(args) -> None:
    import zipfile
    from pathlib import Path as _P

    bundle = Bundle(args.bundle)
    folder = naming.kit_dir(bundle)
    if not folder.exists():
        raise Rejected("There is no Editor Kit yet: build the slides or visuals first.")
    top = f"{naming.video_id(bundle)}_editor_kit"
    out = _P(args.zip)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                z.write(p, f"{top}/{p.relative_to(folder).as_posix()}")
    print(f"Packed the Editor Kit into {out}: give this to the Video Editor.")


def cmd_pack(args) -> None:
    path = pack(args.bundle, args.zip)
    print(f"Packed the Video Bundle into {path}. Offer this file for download; upload it in a new chat to continue.")


def cmd_unpack(args) -> None:
    bundle = unpack(args.zip, args.bundle)
    what = "Topic Bundle" if topic.is_topic(bundle) else "Video Bundle"
    print(f"Unpacked {what} {(bundle.manifest.get('video') or bundle.manifest.get('topic'))['id']} into {bundle.root}.")
    print(status.next_step(bundle)[1])


def cmd_topic(args) -> None:
    bundle = topic.create(args.bundle, args.topic_id, args.title, args.video)
    if args.brand:
        brandkit.attach(bundle, args.brand)
        bundle.save()
    print(f"Created Topic Bundle {args.topic_id} from {len(bundle.manifest['videos'])} Video(s): {', '.join(bundle.manifest['videos'])}.")
    if bundle.manifest.get("brand_note"):
        print(bundle.manifest["brand_note"])
    print(status.next_step(bundle)[1])


def cmd_status(args) -> None:
    bundle = Bundle(args.bundle)
    if topic.is_topic(bundle):
        t = bundle.manifest["topic"]
        n = len(bundle.manifest["videos"])
        print(f"Topic {t['id']} · {n} Video{'s' if n != 1 else ''} · " + ("DRAFT defaults" if bundle.manifest["config"].get("draft") else f"Configuration Pack {bundle.manifest['config'].get('version')}"))
        stage, step = status.next_step(bundle)
        print(f"Stage: {stage}")
        print(step)
        return
    video = bundle.manifest["video"]
    config = bundle.manifest.get("config", {})
    print(f"Video {video['id']} · " + ("DRAFT defaults" if config.get("draft") else f"Configuration Pack {config.get('version')}"))
    stage, step = status.next_step(bundle)
    print(f"Stage: {stage}")
    print(step)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fz.py", description="Fuzentrix Video Bundle builders")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new", help="Read an Instructor Script into a new Video Bundle")
    p.add_argument("script")
    p.add_argument("bundle")
    p.add_argument("--video-id", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--instructor", default="")
    p.add_argument("--chunk-lines", type=int, default=0, help="Run override: target lines per Chunk")
    p.add_argument("--config", help="Configuration Pack: release .zip, release folder, or the shared folder with current.json")
    p.add_argument("--brand", help="Brand Kit: release .zip, release folder, the shared folder, or 'default'")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("show", help="Print part of the bundle")
    p.add_argument("bundle")
    p.add_argument("what", choices=["lines", "chunks", "chunk", "config", "brand", "segments", "guidelines", "quiz-request", "sources", "image-prompts", "animation-prompts", "storyboard-prompts", "cheatsheet-image-prompts"])
    p.add_argument("id", nargs="?")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("submit", help="Check and save AI-written content JSON")
    p.add_argument("bundle")
    p.add_argument("kind", choices=["review", "review-overview", "script-changes", "plan", "master", "diagrams", "animations", "quiz-request", "quiz", "cheatsheet"])
    p.add_argument("file")
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("build", help="Build a deliverable from submitted content")
    p.add_argument("bundle")
    p.add_argument("what", choices=["review", "master", "slides", "visuals", "teleprompter", "editor-kit", "quiz", "cheatsheet"])
    p.add_argument("--without-images", action="store_true",
                   help="visuals: build what code can draw now, with placeholders for images not generated yet")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("gate", help="Record a Gate decision")
    p.add_argument("bundle")
    p.add_argument("n", choices=["1", "2", "3"])
    p.add_argument("file", nargs="?")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("draft", help="Write a pre-filled JSON draft for a review or Master Script Chunk")
    p.add_argument("bundle")
    p.add_argument("kind", choices=["review", "script-changes", "master", "diagrams", "animations", "quiz", "cheatsheet"])
    p.add_argument("id", help="Chunk id (C01, M01), the Video id for a quiz, or 'all'")
    p.add_argument("file")
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("attach", help="Use a Brand Kit or Configuration Pack for an existing bundle")
    p.add_argument("bundle")
    p.add_argument("kind", choices=["brand", "config", "auto"])
    p.add_argument("source", help="Release .zip, release folder, the shared folder with current.json, or 'default' (brand)")
    p.set_defaults(func=cmd_attach)

    p = sub.add_parser("override", help="Change one Brand Kit value for this bundle, as the user asked in the prompt")
    p.add_argument("bundle")
    p.add_argument("path", help="e.g. colors.primary or slides.label.text")
    p.add_argument("value")
    p.add_argument("--note", help="What the user asked, in a few words")
    p.set_defaults(func=cmd_override)

    p = sub.add_parser("convert-quiz", help="Convert a quiz workbook's questions, options and explanations to LMS RICH_HTML")
    p.add_argument("source")
    p.add_argument("target")
    p.add_argument("--marks", help="The AI marking pass (from quiz-cells): only marks, no changed words")
    p.add_argument("--plain", help="Also write a PLAIN_TEXT copy without marks")
    p.add_argument("--bundle", help="Use this bundle's Configuration Pack LMS HTML Policy")
    p.add_argument("--config", help="Use a Configuration Pack release (.zip or folder) for the LMS HTML Policy")
    p.set_defaults(func=cmd_convert_quiz)

    p = sub.add_parser("quiz-cells", help="List a quiz workbook's text cells for an AI marking pass")
    p.add_argument("source")
    p.add_argument("file")
    p.set_defaults(func=cmd_quiz_cells)

    p = sub.add_parser("coding-html", help="Convert a given coding problem into LMS HTML (draft, then build)")
    p.add_argument("action", choices=["draft", "build"])
    p.add_argument("paths", nargs="+", help="draft: <problem file> <draft.json> · build: <converted.json> <problem file> <out folder>")
    p.add_argument("--run", action="store_true", help="Run a given Python solution against the given examples and test cases (report only)")
    p.add_argument("--bundle", help="Use this bundle's Configuration Pack LMS HTML Policy")
    p.add_argument("--config", help="Use a Configuration Pack release (.zip or folder) for the LMS HTML Policy")
    p.set_defaults(func=cmd_coding_html)

    p = sub.add_parser("check-html", help="Check HTML against the LMS HTML Policy for one context")
    p.add_argument("file")
    p.add_argument("--context", required=True, choices=list(lmspolicy.CONTEXTS))
    p.add_argument("--bundle", help="Use this bundle's Configuration Pack policy")
    p.add_argument("--config", help="Use a Configuration Pack release (.zip or folder)")
    p.add_argument("--policy", help="Use an lms-html.yaml file directly (to try new rules)")
    p.set_defaults(func=cmd_check_html)

    p = sub.add_parser("schema", help="Print the JSON format for a submission or Gate")
    p.add_argument("kind", choices=sorted(schemas.SCHEMAS))
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("pack", help="Zip the Video Bundle for download")
    p.add_argument("bundle")
    p.add_argument("zip")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("pack-editor", help="Zip only the Editor Kit, for the Video Editor")
    p.add_argument("bundle")
    p.add_argument("zip")
    p.set_defaults(func=cmd_pack_editor)

    p = sub.add_parser("unpack", help="Restore an uploaded Video Bundle zip to continue work")
    p.add_argument("zip")
    p.add_argument("bundle")
    p.set_defaults(func=cmd_unpack)

    p = sub.add_parser("topic", help="Create a Topic Bundle from Video Bundles with Final Master Scripts")
    p.add_argument("bundle", help="New folder for the Topic Bundle")
    p.add_argument("--topic-id", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--video", action="append", default=[], help="A Video Bundle folder or .zip (repeat for each Video)")
    p.add_argument("--brand", help="Brand Kit for the Topic (otherwise the one its Videos share)")
    p.set_defaults(func=cmd_topic)

    p = sub.add_parser("status", help="Where this Video Bundle is, and the next step")
    p.add_argument("bundle")
    p.set_defaults(func=cmd_status)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except Rejected as e:
        print(format_problems(e.problems))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
