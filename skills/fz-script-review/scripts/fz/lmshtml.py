"""fz-coding-problem: LMS HTML for coding problems (Problem Statement, Solution, Test Cases, Test Case Explanation,
Hints, Editorial). Only the requested sections are built; a Python solution is run against every example
and test case before anything is written."""
from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .problems import Rejected

SECTIONS = {
    "problem_statement": "Problem Statement",
    "solution": "Solution",
    "test_cases": "Test Cases",
    "test_case_explanation": "Test Case Explanation",
    "hints": "Hints",
    "editorial": "Editorial",
}


def _inline(text) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(str(text), quote=False))


def _pre(text) -> str:
    return f"<pre><code>{html.escape(str(text).strip(chr(10)), quote=False)}</code></pre>"


def _empty(value) -> bool:
    return value in (None, "", [], {})


def check(data: dict) -> list:
    problems = []
    requested = data.get("requested") or []
    if not requested:
        problems.append(f"'requested' must list the sections the user asked for ({', '.join(SECTIONS)}).")
    for key in requested:
        if key not in SECTIONS:
            problems.append(f"'{key}' is not a section; use {', '.join(SECTIONS)}.")
        elif _empty(data.get(key)):
            problems.append(f"{key} was requested but is empty.")
    for key in SECTIONS:
        if key not in requested and not _empty(data.get(key)):
            problems.append(f"{key} was not requested; leave it out (the user asked only for {', '.join(requested)}).")
    if not str(data.get("title", "")).strip():
        problems.append("'title' is empty.")
    ps = data.get("problem_statement") or {}
    if ps and not str(ps.get("description", "")).strip():
        problems.append("problem_statement: 'description' is empty.")
    for i, ex in enumerate(ps.get("examples") or [], 1):
        if not isinstance(ex.get("input"), str) or not isinstance(ex.get("output"), str):
            problems.append(f"example {i}: 'input' and 'output' must be text.")
    for i, tc in enumerate(data.get("test_cases") or [], 1):
        if not isinstance(tc.get("input"), str) or not isinstance(tc.get("output"), str):
            problems.append(f"test case {i}: 'input' and 'output' must be text.")
    for name in ("solution", "check_solution"):
        sol = data.get(name)
        if sol and (not sol.get("language") or not str(sol.get("code", "")).strip()):
            problems.append(f"{name}: needs 'language' and 'code'.")
    return problems


def _normalise(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def verify(data: dict) -> dict:
    """Run a Python solution (the shown one, or the hidden check_solution) on every example and test case."""
    solution = data.get("solution") or data.get("check_solution")
    cases = [(f"example {i}", ex) for i, ex in enumerate((data.get("problem_statement") or {}).get("examples") or [], 1)]
    cases += [(f"test case {i}", tc) for i, tc in enumerate(data.get("test_cases") or [], 1)]
    result = {"run": False, "examples": 0, "test_cases": 0, "problems": []}
    if not cases or not solution or str(solution.get("language", "")).lower() not in ("python", "python3", "py"):
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


def render(data: dict) -> str:
    out = []
    for key in SECTIONS:
        if key not in data.get("requested", []):
            continue
        body = [f"<h2>{SECTIONS[key]}</h2>"]
        value = data[key]
        if key == "problem_statement":
            body.append(f"<p>{_inline(value['description'])}</p>")
            for field, title in (("input_format", "Input Format"), ("output_format", "Output Format")):
                if value.get(field):
                    body += [f"<h3>{title}</h3>", f"<p>{_inline(value[field])}</p>"]
            if value.get("constraints"):
                body += ["<h3>Constraints</h3>", "<ul>" + "".join(f"<li><code>{html.escape(c, quote=False)}</code></li>" for c in value["constraints"]) + "</ul>"]
            for i, ex in enumerate(value.get("examples") or [], 1):
                body += [f"<h3>Example {i}</h3>", "<p><strong>Input</strong></p>", _pre(ex["input"]), "<p><strong>Output</strong></p>", _pre(ex["output"])]
                if ex.get("explanation"):
                    body.append(f"<p><strong>Explanation:</strong> {_inline(ex['explanation'])}</p>")
        elif key == "solution":
            if value.get("approach"):
                body.append(f"<p>{_inline(value['approach'])}</p>")
            body.append(_pre(value["code"]))
            for k, label in (("time", "Time complexity"), ("space", "Space complexity")):
                if (value.get("complexity") or {}).get(k):
                    body.append(f"<p><strong>{label}:</strong> <code>{html.escape(value['complexity'][k], quote=False)}</code></p>")
        elif key == "test_cases":
            for i, tc in enumerate(value, 1):
                body += [f"<h3>Test Case {i}</h3>", "<p><strong>Input</strong></p>", _pre(tc["input"]), "<p><strong>Output</strong></p>", _pre(tc["output"])]
        elif key == "test_case_explanation":
            for i, ex in enumerate(value, 1):
                body += [f"<h3>Test Case {ex.get('case', i)}</h3>", f"<p>{_inline(ex.get('explanation', ''))}</p>"]
        elif key == "hints":
            body.append("<ol>" + "".join(f"<li>{_inline(h)}</li>" for h in value) + "</ol>")
        elif key == "editorial":
            for field, title in (("intuition", "Intuition"), ("approach", "Approach")):
                if value.get(field):
                    body += [f"<h3>{title}</h3>", f"<p>{_inline(value[field])}</p>"]
            if value.get("steps"):
                body.append("<ol>" + "".join(f"<li>{_inline(s)}</li>" for s in value["steps"]) + "</ol>")
            if value.get("code"):
                body.append(_pre(value["code"]))
            c = value.get("complexity") or {}
            if c:
                body += ["<h3>Complexity</h3>", "<ul>" + "".join(f"<li><strong>{k.title()}:</strong> <code>{html.escape(v, quote=False)}</code></li>" for k, v in c.items()) + "</ul>"]
        out.append("<section>\n" + "\n".join(body) + "\n</section>")
    return "\n".join(out) + "\n"


def build(source: dict, out_dir) -> dict:
    problems = check(source)
    if problems:
        raise Rejected(problems)
    result = verify(source)
    if result["problems"]:
        raise Rejected(result["problems"])
    slug = re.sub(r"[^a-z0-9]+", "-", source["title"].lower()).strip("-") or "problem"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{slug}.html"
    path.write_text(render(source), encoding="utf-8")
    return dict(result, path=path)
