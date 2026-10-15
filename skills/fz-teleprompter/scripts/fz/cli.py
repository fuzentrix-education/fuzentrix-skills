"""Command-line interface. Each fz-* skill tells the Host App which command to run; end users never type these."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import json

from . import cheatsheet, configpack, editor, gates, lmshtml, master, naming, quiz, review, schemas, settings, slides, status, teleprompter, topic, visuals
from .bundle import Bundle, pack, read_json, unpack, write_json
from .chunks import assign, make_chunks
from .ingest import number_lines, read_script, tags
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
    elif args.what == "image-prompts":
        print(visuals.prompts(bundle))
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
    elif args.what == "editor-pack":
        result = editor.build(bundle)
        bundle.save()
        print(f"Built editor_pack/editor_guide.md and .html, markers.xml (Premiere) and cue_sheet.csv: {result['events']} Visual Event(s), "
              f"about {result['minutes']:.1f} min (estimated).")
    elif args.what == "visuals":
        result = visuals.build(bundle)
        bundle.save()
        note = (f" {result['png_missing']} diagram(s) were drawn as SVG only: this sandbox has no matplotlib for PNG."
                if result["png_missing"] else "")
        print(f"Checked {result['images']} image(s), drew or checked {result['diagrams']} diagram(s), checked {result['storyboards']} "
              f"storyboard(s); wrote editor_pack/visuals.html and refreshed the editor guide. Rebuild the slides to place new images.{note}")
    elif args.what == "slides":
        result = slides.build(bundle)
        bundle.save()
        print(f"Built editor_pack/slides/{result['path'].name} ({result['slides']} editable slides) and slides.md; refreshed the editor guide.")
    elif args.what == "cheatsheet":
        result = cheatsheet.build(bundle)
        bundle.save()
        tid = bundle.manifest["topic"]["id"]
        print(f"Built cheatsheet/{tid}_cheatsheet.html ({result['mode']} HTML), preview.html and insertion_map.md: "
              f"{result['sections']} section(s), {result['images']} image(s).")
    elif args.what == "quiz":
        result = quiz.build(bundle)
        bundle.save()
        tid = bundle.manifest["topic"]["id"]
        print(f"Built quiz/{tid}_quiz.xlsx (PLAIN_TEXT), quiz/{tid}_quiz_html.xlsx (RICH_HTML) and quiz_preview: "
              f"{result['questions']} questions, {result['points']} points.")
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
        print(f"Gate 1 recorded for {record['approver']}: {accepted} of {len(record['decisions'])} Finding(s) accepted.")
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
        todo = "keep the spoken lines as they are; fill in meaning_en, slide and visual_events"
    write_json(args.file, data)
    print(f"Wrote a draft of {args.kind} {args.id} to {args.file}: {todo}, then `fz.py submit <bundle> {args.kind} {args.file}`.")


def cmd_convert_quiz(args) -> None:
    result = quiz.convert_workbook(args.source, args.target)
    print(f"Converted {args.source} → {args.target}: {result['rows']} question row(s) set to RICH_HTML, "
          f"{result['cells']} cell(s) converted to HTML in {result['sheets']} sheet(s).")


def cmd_lms_html(args) -> None:
    result = lmshtml.build(_load_json_file(args.file), args.out)
    checked = (f"{result['test_cases']} of {result['test_cases']} test case(s) and {result['examples']} example(s) passed against the Python solution"
               if result["run"] else "not run: add a Python solution or check_solution to verify the examples and test cases")
    print(f"Built {result['path']}. Checks: {checked}.")


def cmd_schema(args) -> None:
    print(schemas.describe(args.kind))


def cmd_pack_editor(args) -> None:
    import zipfile
    from pathlib import Path as _P

    bundle = Bundle(args.bundle)
    folder = naming.pack_dir(bundle)
    if not folder.exists():
        raise Rejected("There is no Editor Pack yet: build the slides or visuals first.")
    top = f"{naming.video_id(bundle)}_editor_pack"
    out = _P(args.zip)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                z.write(p, f"{top}/{p.relative_to(folder).as_posix()}")
    print(f"Packed the Editor Pack into {out}: give this to the Video Editor.")


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
    print(f"Created Topic Bundle {args.topic_id} from {len(bundle.manifest['videos'])} Video(s): {', '.join(bundle.manifest['videos'])}.")
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
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("show", help="Print part of the bundle")
    p.add_argument("bundle")
    p.add_argument("what", choices=["lines", "chunks", "chunk", "config", "segments", "guidelines", "quiz-request", "sources", "image-prompts", "storyboard-prompts"])
    p.add_argument("id", nargs="?")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("submit", help="Check and save AI-written content JSON")
    p.add_argument("bundle")
    p.add_argument("kind", choices=["review", "review-overview", "plan", "master", "diagrams", "quiz-request", "quiz", "cheatsheet"])
    p.add_argument("file")
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("build", help="Build a deliverable from submitted content")
    p.add_argument("bundle")
    p.add_argument("what", choices=["review", "master", "slides", "visuals", "teleprompter", "editor-pack", "quiz", "cheatsheet"])
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("gate", help="Record a Gate decision")
    p.add_argument("bundle")
    p.add_argument("n", choices=["1", "2", "3"])
    p.add_argument("file", nargs="?")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("draft", help="Write a pre-filled JSON draft for a review or Master Script Chunk")
    p.add_argument("bundle")
    p.add_argument("kind", choices=["review", "master", "diagrams", "quiz", "cheatsheet"])
    p.add_argument("id", help="Chunk id (C01, M01), or the Video id for a quiz")
    p.add_argument("file")
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("convert-quiz", help="Convert an existing LMS quiz workbook to RICH_HTML")
    p.add_argument("source")
    p.add_argument("target")
    p.set_defaults(func=cmd_convert_quiz)

    p = sub.add_parser("lms-html", help="Build LMS HTML for a coding problem from JSON")
    p.add_argument("file")
    p.add_argument("out", help="Folder for the .html file")
    p.set_defaults(func=cmd_lms_html)

    p = sub.add_parser("schema", help="Print the JSON format for a submission or Gate")
    p.add_argument("kind", choices=sorted(schemas.SCHEMAS))
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("pack", help="Zip the Video Bundle for download")
    p.add_argument("bundle")
    p.add_argument("zip")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("pack-editor", help="Zip only the Editor Pack, for the Video Editor")
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
