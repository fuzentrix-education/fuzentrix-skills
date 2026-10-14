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
    "gate1": (
        """Gate 1: the Instructor's decisions on the Script Review. Record with: fz.py gate <bundle> 1 <file>
- approver: the Instructor's name.
- decisions: EVERY Finding id from review_report → "accept" or "reject".
- fix_text (optional): Finding id → the replacement line the Instructor wants instead ("" deletes the line).
- line_roles (optional): corrections to Line Roles, line id → role.
- notes (optional).""",
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
    A line added by an accepted Finding: {{"text": ..., "from_finding": "F003"}}.
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
  example {title, text} · mistakes {items} · image {file, alt, caption} · reveal {question, answer} (click to reveal)
- Text may use **bold** and `code`.
- Images: save each generated image into cheatsheet/images/ first; alt text describes it in a few words.
- Cover every key term listed in key_terms_to_cover. Include at least one mistakes block.
- Voice: short, concrete sentences with the Instructor's own examples; state facts directly, no filler.""",
        {"title": "Introduction to DBMS", "intro": "Data, information, databases and the DBMS that manages them.",
         "sections": [{"heading": "DBMS: the bridge", "source": [{"video": "dbms-p2-t1-v1", "segments": ["S10"]}],
                       "blocks": [
                           {"type": "paragraph", "text": "You never talk to the database directly: the **DBMS** sits in between."},
                           {"type": "image", "file": "dbms-bridge.png", "alt": "User sends a request to the DBMS, which searches the database",
                            "caption": "Request → search → result."},
                           {"type": "mistakes", "items": ["Thinking the app reads the database files itself."]},
                           {"type": "reveal", "question": "What does the DBMS return?", "answer": "The exact result: your marks, not the whole table."}]}],
         "quick_revision": ["DBMS = software to create, store, retrieve, update and delete data"]},
    ),
    "lms-html": (
        """A coding problem's LMS content. Build with: fz.py lms-html <file> <out folder>
- title. requested: ONLY the sections the user asked for, from:
  problem_statement, solution, test_cases, test_case_explanation, hints, editorial.
  Fill exactly those sections; leave every other section out.
- problem_statement: description, input_format, output_format, constraints (list), examples (input, output, explanation).
- solution: language, code, approach, complexity {time, space}.
- test_cases: list of {input, output} (exact stdin and stdout).
- test_case_explanation: list of {case, explanation}.
- hints: list, from gentle to specific.
- editorial: intuition, approach, steps (list), optional code, complexity.
- check_solution (optional, never shown): {language: "python", code}. Include it whenever examples or test cases
  exist and the solution was not requested; the builder runs it on every example and test case.
Use `backticks` for code inside text. Keep the user's requirements, examples and constraints exactly.""",
        {"title": "Reverse a String", "requested": ["problem_statement", "test_cases"],
         "problem_statement": {"description": "Given a string `s`, print it reversed.", "input_format": "One line containing `s`.",
                               "output_format": "The reversed string.", "constraints": ["1 <= len(s) <= 1000"],
                               "examples": [{"input": "Durga", "output": "agruD", "explanation": "The characters in reverse order."}]},
         "test_cases": [{"input": "abc", "output": "cba"}],
         "check_solution": {"language": "python", "code": "s = input().strip()\nprint(s[::-1])"}},
    ),
    "diagrams": (
        """Diagram specs for the diagram Visual Events. Start from: fz.py draft <bundle> diagrams all <file>
Submit with: fz.py submit <bundle> diagrams <file>. The builder draws them (SVG, plus PNG for Premiere).
Each diagram: event (its id), optional title, and a type:
- flow: steps (2–6 short labels, left to right), optional labels (one per arrow, one or two words).
- table: columns (1–6), rows (1–8, each with one cell per column).
- tree: root, children (1–6).
- compare: left {title, items}, right {title, items} (1–6 items each).
- image: prompt. Only when none of the above can show it; the image model then makes it (`fz.py show <bundle> image-prompts`).
Labels must be short: a few words that fit a box at a readable size. Use the exact terms the Instructor uses.""",
        {"diagrams": [
            {"event": "S10-E1", "type": "flow", "title": "How a DBMS answers", "steps": ["You", "DBMS", "Database"], "labels": ["request", "search"]},
            {"event": "S13-E1", "type": "tree", "title": "4 types of DBMS", "root": "DBMS",
             "children": ["Hierarchical", "Network", "Relational", "Object-Oriented"]}]},
    ),
}


def describe(kind: str) -> str:
    rules, example = SCHEMAS[kind]
    return f"{rules}\n\nExample:\n{json.dumps(example, ensure_ascii=False, indent=2)}"
