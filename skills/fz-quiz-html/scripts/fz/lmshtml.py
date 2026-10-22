"""fz-coding-problem-html: a GIVEN coding problem converted into the LMS's HTML. Nothing is written for it.

The Host App reads the problem line by line (draft), then places its text, word for word, into sections
(Problem Statement, Solution, Test Cases, Test Case Explanation, Hints, Editorial). The build checks that every
field's words are in the given problem and that every line of the problem is in some section (labels such as
"Input Format:" and lines listed in skipped_lines excepted), writes HTML in the LMS HTML Policy's
coding_problem form, and checks it. --run runs a given Python solution against the given examples and test
cases and reports what fails; it changes nothing."""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from . import lmspolicy, markup
from .problems import Rejected

SECTIONS = {
    "problem_statement": "Problem Statement",
    "solution": "Solution",
    "test_cases": "Test Cases",
    "test_case_explanation": "Test Case Explanation",
    "hints": "Hints",
    "editorial": "Editorial",
}
CONTEXT = "coding_problem"
LABEL = re.compile(r"^\s*(problem( statement)?|description|input( format)?|output( format)?|constraints?|examples?( \d+)?|"
                   r"sample (input|output)( \d+)?|explanation|solution|approach|intuition|complexity|time complexity|space complexity|"
                   r"test cases?( \d+)?|hints?( \d+)?|editorial|steps?|notes?|code)\s*[:\-–]?\s*", re.I)


def _norm(text) -> str:
    return " ".join(markup.unmark(str(text)).split())


def _empty(value) -> bool:
    return value in (None, "", [], {})


# --- draft -----------------------------------------------------------------------------

def draft(source) -> dict:
    from .ingest import read_source

    got = read_source(source)
    return {"source": Path(source).name, "title": "", "lines": [{"id": f"L{i}", "text": t} for i, t in enumerate(got["lines"], 1)],
            "images": got["images"], "skipped_lines": [],
            "problem_statement": {"description": "", "input_format": "", "output_format": "", "constraints": [], "examples": []},
            "solution": {}, "test_cases": [], "test_case_explanation": [], "hints": [], "editorial": {}}


# --- checks -----------------------------------------------------------------------------

def _fields(data: dict):
    """(where, text) for every field written into the page."""
    ps = data.get("problem_statement") or {}
    for k in ("description", "input_format", "output_format"):
        yield f"problem_statement.{k}", ps.get(k)
    for i, c in enumerate(ps.get("constraints") or [], 1):
        yield f"problem_statement.constraints[{i}]", c
    for i, ex in enumerate(ps.get("examples") or [], 1):
        for k in ("input", "output", "explanation"):
            yield f"example {i} {k}", ex.get(k)
    sol = data.get("solution") or {}
    for k in ("approach", "code"):
        yield f"solution.{k}", sol.get(k)
    for k, v in (sol.get("complexity") or {}).items():
        yield f"solution.complexity.{k}", v
    for i, tc in enumerate(data.get("test_cases") or [], 1):
        for k in ("input", "output"):
            yield f"test case {i} {k}", tc.get(k)
    for i, ex in enumerate(data.get("test_case_explanation") or [], 1):
        yield f"test case explanation {i}", ex.get("explanation")
    for i, h in enumerate(data.get("hints") or [], 1):
        yield f"hint {i}", h
    ed = data.get("editorial") or {}
    for k in ("intuition", "approach", "code"):
        yield f"editorial.{k}", ed.get(k)
    for i, s in enumerate(ed.get("steps") or [], 1):
        yield f"editorial step {i}", s
    for k, v in (ed.get("complexity") or {}).items():
        yield f"editorial.complexity.{k}", v


def shown(data: dict) -> list:
    asked = data.get("sections")
    return [k for k in SECTIONS if not _empty(data.get(k)) and (not asked or k in asked)]


def check(data: dict, lines: list) -> list:
    problems = []
    if not str(data.get("title", "")).strip():
        problems.append("'title' is empty (it names the file).")
    for k in data.get("sections") or []:
        if k not in SECTIONS:
            problems.append(f"sections: '{k}' is not a section ({', '.join(SECTIONS)}).")
    if not shown(data):
        problems.append("No section has content.")
    for i, case in enumerate((data.get("problem_statement") or {}).get("examples") or [], 1):
        if not isinstance(case.get("input"), str) or not isinstance(case.get("output"), str):
            problems.append(f"example {i}: 'input' and 'output' must be text.")
    for i, case in enumerate(data.get("test_cases") or [], 1):
        if not isinstance(case.get("input"), str) or not isinstance(case.get("output"), str):
            problems.append(f"test case {i}: 'input' and 'output' must be text.")
    sol = data.get("solution") or {}
    if sol and str(sol.get("code", "")).strip() and not sol.get("language"):
        problems.append("solution: give the code's 'language'.")
    whole = " ".join(_norm(l["text"]) for l in lines)
    texts = [(where, t) for where, t in _fields(data) if isinstance(t, str) and t.strip()]
    for where, t in texts:
        if _norm(t) not in whole:
            problems.append(f"{where} is not in the given problem word for word; copy its exact words (adding only `code` and **bold** marks).")
    written = " ".join(_norm(t) for _, t in texts)
    skipped = set(data.get("skipped_lines") or [])
    for line in lines:
        rest = _norm(LABEL.sub("", line["text"], count=1)) if LABEL.match(line["text"]) else _norm(line["text"])
        if line["id"] in skipped or not rest:
            continue
        if rest not in written:
            problems.append(f"{line['id']} ({line['text'].strip()}) is in no section; put its words in one, or list it in "
                            "skipped_lines if it is only a heading or label.")
    return problems


# --- running a given solution -------------------------------------------------------------

def _normalise(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def verify(data: dict) -> dict:
    """Run the given Python solution on every given example and test case. Reports; changes nothing."""
    solution = data.get("solution") or {}
    cases = [(f"example {i}", ex) for i, ex in enumerate((data.get("problem_statement") or {}).get("examples") or [], 1)]
    cases += [(f"test case {i}", tc) for i, tc in enumerate(data.get("test_cases") or [], 1)]
    result = {"run": False, "examples": 0, "test_cases": 0, "problems": []}
    if not cases or str(solution.get("language", "")).lower() not in ("python", "python3", "py") or not solution.get("code"):
        return result
    result["run"] = True
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "solution.py"
        path.write_text(solution["code"], encoding="utf-8")
        for label, case in cases:
            try:
                r = subprocess.run([sys.executable, str(path)], input=case["input"] + "\n", capture_output=True, text=True, timeout=10)
            except subprocess.TimeoutExpired:
                result["problems"].append(f"{label}: the solution took longer than 10 seconds.")
                continue
            got = _normalise(r.stdout)
            if r.returncode != 0:
                result["problems"].append(f"{label}: the solution failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'exit ' + str(r.returncode)}")
            elif got != _normalise(case["output"]):
                result["problems"].append(f"{label}: expected {_normalise(case['output'])!r} but the solution prints {got!r}.")
            else:
                result["examples" if label.startswith("example") else "test_cases"] += 1
    return result


# --- rendering ------------------------------------------------------------------------------

def render(data: dict, policy: dict) -> str:
    def text(t):
        return markup.render(t, policy)

    def code(t, lang=""):
        return lmspolicy.code_block(policy, html.escape(str(t).strip("\n"), quote=False), lang)

    def complexity(c):
        return "<ul>" + "".join(f"<li><strong>{html.escape(k.title())}:</strong> {markup.inline(v)}</li>" for k, v in c.items()) + "</ul>"
    out = []
    for key in shown(data):
        body, value = [f"<h2>{SECTIONS[key]}</h2>"], data[key]
        if key == "problem_statement":
            if value.get("description"):
                body.append(text(value["description"]))
            for field, title in (("input_format", "Input Format"), ("output_format", "Output Format")):
                if value.get(field):
                    body += [f"<h3>{title}</h3>", text(value[field])]
            if value.get("constraints"):
                body += ["<h3>Constraints</h3>", "<ul>" + "".join(
                    f"<li>{markup.inline(c) if '`' in c else '<code>' + html.escape(c, quote=False) + '</code>'}</li>" for c in value["constraints"]) + "</ul>"]
            for i, ex in enumerate(value.get("examples") or [], 1):
                body += [f"<h3>Example {i}</h3>", "<p><strong>Input</strong></p>", code(ex["input"]), "<p><strong>Output</strong></p>", code(ex["output"])]
                if ex.get("explanation"):
                    body.append(f"<p><strong>Explanation:</strong> {markup.inline(ex['explanation'])}</p>")
        elif key == "solution":
            if value.get("approach"):
                body.append(text(value["approach"]))
            if value.get("code"):
                body.append(code(value["code"], value.get("language", "")))
            if value.get("complexity"):
                body.append(complexity(value["complexity"]))
        elif key == "test_cases":
            for i, tc in enumerate(value, 1):
                body += [f"<h3>Test Case {i}</h3>", "<p><strong>Input</strong></p>", code(tc["input"]), "<p><strong>Output</strong></p>", code(tc["output"])]
        elif key == "test_case_explanation":
            for i, ex in enumerate(value, 1):
                body += [f"<h3>Test Case {html.escape(str(ex.get('case', i)))}</h3>", text(ex.get("explanation", ""))]
        elif key == "hints":
            body.append("<ol>" + "".join(f"<li>{markup.inline(h)}</li>" for h in value) + "</ol>")
        elif key == "editorial":
            for field, title in (("intuition", "Intuition"), ("approach", "Approach")):
                if value.get(field):
                    body += [f"<h3>{title}</h3>", text(value[field])]
            if value.get("steps"):
                body.append("<ol>" + "".join(f"<li>{markup.inline(s)}</li>" for s in value["steps"]) + "</ol>")
            if value.get("code"):
                body.append(code(value["code"], value.get("language", "")))
            if value.get("complexity"):
                body += ["<h3>Complexity</h3>", complexity(value["complexity"])]
        inner = "\n".join(body)
        out.append(f"<section>\n{inner}\n</section>" if lmspolicy.allows(policy, CONTEXT, "section") else inner)
    return "\n".join(out) + "\n"


def build(data: dict, source, out_dir, policy: dict, run_solution: bool = False) -> dict:
    from .ingest import read_source

    got = read_source(source)
    lines = [{"id": f"L{i}", "text": t} for i, t in enumerate(got["lines"], 1)]
    problems = check(data, lines)
    if problems:
        raise Rejected(problems)
    page = render(data, policy)
    found = lmspolicy.check(page, policy, CONTEXT)
    if found:
        raise Rejected([f"The HTML would not survive the LMS: {p}" for p in found])
    result = verify(data) if run_solution else {"run": False, "problems": []}
    slug = re.sub(r"[^a-z0-9]+", "-", data["title"].lower()).strip("-") or "problem"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{slug}.html"
    path.write_text(page, encoding="utf-8")
    return dict(result, path=path, sections=[SECTIONS[k] for k in shown(data)], images=got["images"], policy=policy["_source"])
