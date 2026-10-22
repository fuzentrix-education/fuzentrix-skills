"""The JSON the Host App writes for each submission: rules plus one example. `fz.py schema <kind>` prints these."""
from __future__ import annotations

import json

from .master import EVENT_KINDS, EVENT_LAYOUTS, SLIDE_LAYOUTS, VIDEO_SECTIONS
from .quiz import CODE_QUESTIONS, EXPLANATIONS
from .review import CATEGORIES, LINE_ROLES, SEVERITIES

SCHEMAS = {
    "review": (
        f"""Script Review of ONE Chunk. Submit with: fz.py submit <bundle> review <file>
- chunk: the Chunk id (e.g. "C01").
- line_roles: EVERY line of this Chunk → one of {", ".join(LINE_ROLES)}.
  spoken = the Instructor says it to camera. Everything else stays off the teleprompter.
- findings: problems found in this Chunk. Each needs:
  line (a line of this Chunk), quote (exact words copied from that line),
  category ({", ".join(CATEGORIES)}), severity ({", ".join(SEVERITIES)}), problem, suggestion.
  fix_text (optional): the corrected line in the Instructor's own Telugu-English style, if the
  fix changes what is said. Use "" to mean: delete this line.
- code_checks (optional): for each code snippet, lines, status (run | read_only), note.
- points_to_check: anything you could not resolve, for the Instructor to look at.""",
        {
            "chunk": "C05",
            "line_roles": {"L64": "spoken", "L65": "stage_direction", "L66": "spoken"},
            "findings": [{
                "line": "L66",
                "quote": "DBMS ane software ni first time 1966 lo IBM vallu",
                "category": "technical",
                "severity": "major",
                "problem": "IMS (1966) was not the first DBMS; Bachman's IDS (~1963–64) came earlier.",
                "suggestion": "Call IMS one of the earliest and most famous DBMSs.",
                "fix_text": "Meeku telusa? Prapanchamlo modati DBMS lo okati, IBM IMS, 1966 lo NASA kosam create chesaru!",
            }],
            "code_checks": [],
            "points_to_check": ["Is the NASA fact meant as the closing hook?"],
        },
    ),
    "review-overview": (
        f"""Script Review of the WHOLE script (flow, agenda, promises, guideline gaps). Submit with:
fz.py submit <bundle> review-overview <file>
- findings: like Chunk findings, but each gives EITHER line + exact quote (any line),
  OR after_line for something missing (e.g. no agenda after the intro).
  category ({", ".join(CATEGORIES)}), severity ({", ".join(SEVERITIES)}), problem, suggestion.
- points_to_check: anything you could not resolve.""",
        {
            "findings": [{
                "after_line": "L7",
                "category": "guideline",
                "severity": "minor",
                "problem": "No agenda after the intro.",
                "suggestion": "Add a 3–4 point agenda: Data vs Information, Database, DBMS, Types.",
                "fix_text": "Ee session lo manam Data vs Information, Database, DBMS ela work avtundi, mariyu DBMS types nerchukundam.",
            }],
            "points_to_check": [],
        },
    ),
    "script-changes": (
        """The Instructor's own wording changes to their script (Script Changes). Submit with:
fz.py submit <bundle> script-changes <file>
The file holds EVERY Script Change still wanted; it replaces the earlier list. Start from
fz.py draft <bundle> script-changes all <file>. Each change gives either:
- line + text: the line's new words, in the Instructor's own Telugu-English style ("" deletes the line), or
- after_line + text: a new line to add after that line.
- note (optional): why, in a few words.
Script Changes reopen Gate 1, and a built Master Script goes back to Gate 2.""",
        {"changes": [
            {"line": "L66", "text": "IBM IMS, 1966 lo NASA kosam create chesina modati DBMS lo okati!", "note": "Instructor's wording"},
            {"after_line": "L80", "text": "Next class lo manam SQL basics chuddam."},
        ]},
    ),
    "gate1": (
        """Gate 1: the Instructor approves the Reviewed Script. Record with: fz.py gate <bundle> 1 <file>
- approver: the Instructor's name.
- decisions: EVERY Finding id from review_report → "accept" or "reject". When approving again with the
  same Findings (for example after new Script Changes), leave decisions out to keep the earlier ones.
- fix_text (optional): Finding id → the replacement line the Instructor wants instead ("" deletes the line).
- line_roles (optional): corrections to Line Roles, line id → role.
- notes (optional).
Their Script Changes (fz.py submit <bundle> script-changes) are approved with it.""",
        {
            "approver": "Swara",
            "decisions": {"F001": "accept", "F002": "reject", "F003": "accept"},
            "fix_text": {},
            "line_roles": {"L57": "speaker_label"},
            "notes": "",
        },
    ),
    "plan": (
        f"""Master Script plan: the Segments of the WHOLE Video. Submit with: fz.py submit <bundle> plan <file>
- title, agenda (list), learning_objectives (list), key_terms (list of term + definition).
- segments: in order, covering EVERY line exactly once. Each has id ("S01"…), section
  ({", ".join(VIDEO_SECTIONS)}), title, start, end (line ids). A Segment is a stretch that shares one Slide.""",
        {
            "title": "Introduction to DBMS",
            "agenda": ["Data vs Information", "What is a Database", "What a DBMS does", "Types of DBMS"],
            "learning_objectives": ["Tell data from information", "Explain what a DBMS does"],
            "key_terms": [{"term": "DBMS", "definition": "Software to create, store, retrieve, update and delete data in a database."}],
            "segments": [
                {"id": "S01", "section": "hook", "title": "How apps remember you", "start": "L1", "end": "L4"},
                {"id": "S02", "section": "intro", "title": "Welcome", "start": "L5", "end": "L7"},
            ],
        },
    ),
    "master": (
        f"""Master Script of ONE Master Script Chunk. Submit with: fz.py submit <bundle> master <file>
Read the Chunk first with: fz.py show <bundle> segments <chunk id>
- chunk: e.g. "M01". segments: exactly that Chunk's Segments, in order. Each Segment has:
  - meaning_en: what is said, in plain English.
  - spoken: EVERY spoken line of the Segment, in order: {{"line": "L9", "text": <exact line text>}}.
    If an accepted Finding gives replacement text for a line, use that text instead.
    A line added by an accepted Finding or Script Change: {{"text": ..., "from_finding": "F003"}} (or "SC02").
  - slide: title (8 words or fewer), layout ({", ".join(SLIDE_LAYOUTS)}), bullets (English, at most ~5, each at most
    2 lines), source_lines (the lines its content comes from). Optional: code and output (layout code),
    columns [{{title, bullets}}] (layout comparison). For a diagram, write a bullet as "A → B → C".
  - visual_events: kind ({", ".join(EVENT_KINDS)}), description, trigger (exact spoken words where it
    starts), source_lines, layout ({", ".join(EVENT_LAYOUTS)}), optional duration_sec, template, editor_note.
    kind "direction" is a camera, music or sound cue (e.g. "slow zoom in, music builds"); it needs no layout.
  - points_to_check: anything you could not resolve.""",
        {
            "chunk": "M02",
            "segments": [{
                "id": "S04",
                "meaning_en": "A clerk would take a long time to find one fee record among 10,000 paper files.",
                "spoken": [
                    {"line": "L8", "text": "Imagine your college has 10,000 students."},
                    {"line": "L9", "text": "Oka roju meeru fee katti receipt marchipoyaru. Office room ki velli mee fee status check cheyyamani adigaru."},
                ],
                "slide": {"title": "The Paper Files Problem", "layout": "bullets",
                          "bullets": ["10,000 student files", "Slow search", "Errors and lost records"],
                          "source_lines": ["L8", "L9"]},
                "visual_events": [{
                    "kind": "animation",
                    "description": "Stacks of paper files snap-transform into a server icon.",
                    "trigger": "Imagine your college has 10,000 students",
                    "source_lines": ["L8"],
                    "layout": "fullscreen_cutaway",
                    "duration_sec": 3,
                    "template": "transform_morph",
                    "editor_note": "Hard cut from the Instructor; return after the line ends.",
                }],
                "points_to_check": [],
            }],
        },
    ),
    "gate2": (
        """Gate 2: the Content Lead approves the Master Script, making it Final. Record with: fz.py gate <bundle> 2 <file>
- approver: the Content Lead's name.
- notes (optional).""",
        {"approver": "Content Lead name", "notes": ""},
    ),
    "quiz-request": (
        f"""The user's quiz choices, as JSON. Submit with: fz.py submit <bundle> quiz-request <file>
Only include what the user actually asked for; the builder fills in the rest:
- questions_total (default 20, at most 100 per LMS file).
- by_difficulty: easy / medium / hard counts (default 40% / 40% / 20%). Must add up to questions_total.
- by_type: SINGLE_SELECT / MULTI_SELECT / TRUE_FALSE counts (default 60% / 20% / 20%). Must add up to questions_total.
- points: per difficulty (default easy 1, medium 1, hard 2).
- options_per_question: 2, 3 or 4 (default 4).
- explanations: {" or ".join(EXPLANATIONS)} (default correct_only, as in the Fuzentrix template).
- code_questions: {" / ".join(CODE_QUESTIONS)} (default auto: code questions only where the Videos teach code).
- notes: anything else the user asked for, in their words.""",
        {"questions_total": 20, "by_difficulty": {"easy": 8, "medium": 8, "hard": 4},
         "by_type": {"SINGLE_SELECT": 12, "MULTI_SELECT": 4, "TRUE_FALSE": 4},
         "points": {"easy": 1, "medium": 1, "hard": 2}, "explanations": "correct_only", "notes": ""},
    ),
    "quiz": (
        """Quiz questions for ONE Video. Start from: fz.py draft <bundle> quiz <video id> <file>
Submit with: fz.py submit <bundle> quiz <file>
- Keep each planned id, type, difficulty and points as drafted.
- question: one clear question. Mark code with `backticks`, or ``` for a block.
- options: TRUE_FALSE keeps exactly "True" and "False". Others: real, distinct options; no "All/None of the above".
  correct: true or false for every option. SINGLE_SELECT and TRUE_FALSE: exactly one true.
  MULTI_SELECT: at least one true and at least one false.
  explanation: for the correct option(s); for every option when the request says all_options.
  Write the correct option first if you like: the builder reorders options to spread answers across A–D.
- source_segments: the Segment ids (from `fz.py show <bundle> sources <video>`) the question tests.
- answer_check: your re-derivation of the correct answer from the Video, done before marking it.""",
        {"video": "dbms-p2-t1-v1", "questions": [
            {"id": "Q03", "type": "SINGLE_SELECT", "difficulty": "medium", "points": 1, "source_segments": ["S10"],
             "question": "What does a DBMS do when you send it a request?",
             "options": [
                 {"text": "Searches the database and returns the exact result", "correct": True,
                  "explanation": "The DBMS sits between you and the database: it searches and returns the result."},
                 {"text": "Lets you edit the database files directly", "correct": False, "explanation": ""},
                 {"text": "Prints the whole database", "correct": False, "explanation": ""},
                 {"text": "Deletes old records first", "correct": False, "explanation": ""}],
             "answer_check": "S10: 'Meeru DBMS ki request pampistaru, DBMS database lo vetukuthundi, exact result chupistundi.'"}]},
    ),
    "gate3": (
        """Gate 3: the Content Lead approves a Topic deliverable. Record with: fz.py gate <bundle> 3 <file>
- deliverable: "quiz" or "cheatsheet".
- approver: the Content Lead's name.
- notes (optional).""",
        {"deliverable": "quiz", "approver": "Content Lead name", "notes": ""},
    ),
    "cheatsheet": (
        """The Topic's Cheatsheet as typed blocks. Start from: fz.py draft <bundle> cheatsheet all <file>
Submit with: fz.py submit <bundle> cheatsheet <file>
- title, intro (one or two plain sentences), quick_revision (the few lines to remember).
- sections: heading, source (video + segments it summarises), blocks. Block types:
  paragraph {text} · bullets {items} · table {columns, rows} · code {code, language} · key_idea {text}
  example {title, text} · mistakes {items} · image {id, alt, caption, prompt} · reveal {question, answer}
  (click to reveal where the LMS keeps it; otherwise shown as a question and its answer)
- Text may use **bold** and `code` (Fuzentrix markup).
- Images: id is short lowercase words joined by hyphens; prompt says what the image shows; alt text describes it
  in a few words. The HTML holds a placeholder; generate the image afterwards from
  `fz.py show <bundle> cheatsheet-image-prompts`.
- Cover every key term listed in key_terms_to_cover. Include at least one mistakes block.
- Voice: short, concrete sentences with the Instructor's own examples; state facts directly, no filler.""",
        {"title": "Introduction to DBMS", "intro": "Data, information, databases and the DBMS that manages them.",
         "sections": [{"heading": "DBMS: the bridge", "source": [{"video": "dbms-p2-t1-v1", "segments": ["S10"]}],
                       "blocks": [
                           {"type": "paragraph", "text": "You never talk to the database directly: the **DBMS** sits in between."},
                           {"type": "image", "id": "dbms-bridge", "alt": "User sends a request to the DBMS, which searches the database",
                            "caption": "Request → search → result.", "prompt": "A student, a DBMS box and a database cylinder, joined by arrows"},
                           {"type": "mistakes", "items": ["Thinking the app reads the database files itself."]},
                           {"type": "reveal", "question": "What does the DBMS return?", "answer": "The exact result: your marks, not the whole table."}]}],
         "quick_revision": ["DBMS = software to create, store, retrieve, update and delete data"]},
    ),
    "coding-html": (
        """A GIVEN coding problem, placed into LMS sections word for word. Start from:
fz.py coding-html draft <problem file> <file>  (the problem as numbered lines). Build with:
fz.py coding-html build <file> <problem file> <out folder> [--run]
- title: names the file.
- Fill only the sections the problem has, with its exact words (you may add `code` and **bold** marks):
  problem_statement: description, input_format, output_format, constraints (list), examples (input, output, explanation).
  solution: language, code, approach, complexity {time, space}.
  test_cases: list of {input, output}. test_case_explanation: list of {case, explanation}.
  hints: list. editorial: intuition, approach, steps (list), code, language, complexity.
- sections (optional): only these, when the user asked for some sections.
- skipped_lines: line ids that are only a heading or label (e.g. the problem's title line). Lines such as
  "Input Format:" or "Example 1:" are recognised as labels without being listed.
Every field must be in the problem; every line of the problem must be in a section or skipped. Write nothing new.""",
        {"title": "Reverse a String",
         "problem_statement": {"description": "Given a string `s`, print it reversed.", "input_format": "One line containing `s`.",
                               "output_format": "The reversed string.", "constraints": ["1 <= len(s) <= 1000"],
                               "examples": [{"input": "Durga", "output": "agruD", "explanation": "The characters in reverse order."}]},
         "solution": {"language": "python", "code": "s = input().strip()\nprint(s[::-1])"},
         "skipped_lines": ["L1"]},
    ),
    "diagrams": (
        """Diagram specs for the diagram Visual Events. Start from: fz.py draft <bundle> diagrams all <file>
Submit with: fz.py submit <bundle> diagrams <file>. The builder draws them (SVG, plus PNG for Premiere).
Each diagram: event (its id), optional title, and a type:
- flow: steps (2–6 short labels, left to right), optional labels (one per arrow, one or two words).
- table: columns (1–6), rows (1–8, each with one cell per column).
- tree: root, children (1–6).
- compare: left {title, items}, right {title, items} (1–6 items each).
- flowchart: nodes (2–12: id, label, shape process | decision | terminal | io), edges (from, to, optional label
  such as yes/no). Drawn top to bottom; an edge back to an earlier node is drawn round the side as a loop.
- timeline: events (2–7: when, label). cycle: steps (3–6), each leading to the next and the last back to the first.
- layers: layers (2–7, top to bottom), optional highlight (layer number). list: items (1–7), numbered (true/false).
- stat: value (e.g. "70%"), label. title: heading, optional subtitle (a title card; leave out 'title').
- code: code (1–14 lines), language. array: values (2–10), optional pointers [{index, label}].
- image: prompt. Only when none of the above can show it; the image model then makes it (`fz.py show <bundle> image-prompts`).
Labels must be short: a few words that fit a box at a readable size. Use the exact terms the Instructor uses.""",
        {"diagrams": [
            {"event": "S10-E1", "type": "flow", "title": "How a DBMS answers", "steps": ["You", "DBMS", "Database"], "labels": ["request", "search"]},
            {"event": "S13-E1", "type": "tree", "title": "4 types of DBMS", "root": "DBMS",
             "children": ["Hierarchical", "Network", "Relational", "Object-Oriented"]}]},
    ),
    "animations": (
        """Animation specs for the animation Visual Events. Start from: fz.py draft <bundle> animations all <file>
Submit with: fz.py submit <bundle> animations <file>. The build draws each into the Editor Kit: a transparent
full-frame layer per element, a frame per step, a storyboard, a step sheet and spec.json.
Each animation: event (its id), template, and steps (1–8, in order).
- templates code draws, and the diagram type each needs (as in `fz.py schema diagrams`): flow → flow,
  flowchart → flowchart, table_build → table, tree_graph → tree, compare_split → compare, timeline → timeline,
  cycle → cycle, layers → layers, list_build / agenda_build → list, code_typing → code, stat_callout → stat,
  title_card → title, array_pointer → array. Give diagram: that spec. Each step's show lists the element ids it
  adds; every element appears in exactly one step. Ids: title (if the diagram has one); flow node:1…, edge:1-2…,
  label:1-2…; flowchart node:<id>, edge:<from>-<to>, label:<from>-<to>; table frame, header, row:1…; tree
  node:root, node:1…, edge:root-1…; compare panel:left, panel:right, item:left-1…, item:right-1…; timeline axis,
  event:1…; cycle node:1…, edge:1-2…; layers layer:1…; list item:1…; stat value, label; title heading, subtitle;
  code card, line:1…; array cell:1…, pointer:<label>.
- template character_scene / concept_reveal / transform_morph: an illustrated scene. Give elements (1–10, back to
  front), each with id (lowercase-hyphenated) and kind: ai {describe, place, optional character (a Brand Kit
  character id)}; text {text, place}; arrow {from [x, y], to [x, y]}. place is [x, y, width, height] on the
  1920×1080 frame, clear of the presenter area. Steps show element ids. Then generate each ai element from
  `fz.py show <bundle> animation-prompts`.
- template custom: nothing code can draw. Each step gives describe: what appears.
- trigger (optional, per step): the exact spoken words at which the step appears, in the order they are said.
  Steps without one are spread evenly over the animation.""",
        {"animations": [
            {"event": "S10-E1", "template": "flow",
             "diagram": {"type": "flow", "steps": ["You", "DBMS", "Database"], "labels": ["request", "search"]},
             "steps": [{"show": ["node:1"], "trigger": "Meeru"},
                       {"show": ["node:2", "edge:1-2", "label:1-2"], "trigger": "request pampistaru"},
                       {"show": ["node:3", "edge:2-3", "label:2-3"], "trigger": "database lo vetukuthundi"}]},
            {"event": "S12-E1", "template": "custom",
             "steps": [{"describe": "A bank vault door swings open", "trigger": "IMS"}, {"describe": "Rows of records glow one by one"}]}]},
    ),
}


def describe(kind: str) -> str:
    rules, example = SCHEMAS[kind]
    return f"{rules}\n\nExample:\n{json.dumps(example, ensure_ascii=False, indent=2)}"
