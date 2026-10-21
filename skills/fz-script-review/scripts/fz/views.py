"""Readable views. Every JSON file a person might need gets a Markdown twin and an HTML page
generated from it, so the readable version always matches the data."""
from __future__ import annotations

import html
import re
from pathlib import Path


def config_note(bundle) -> str:
    config = bundle.manifest.get("config", {})
    if config.get("draft"):
        return "_DRAFT: built with minimal skill defaults, not the Fuzentrix Configuration Pack._"
    return f"_Configuration Pack {config.get('version')}_"


def bullet_list(items) -> str:
    items = [str(i) for i in items if str(i).strip()]
    return "\n".join(f"- {i}" for i in items) if items else "- None"


def review_markdown(bundle, review: dict) -> str:
    lines_by_id = {l["id"]: l for l in bundle.lines()}
    out = [f"# Script Review: {bundle.manifest['video']['id']}", "", config_note(bundle), "",
           "## Points to check", "", bullet_list(review["points_to_check"]), "", "## Findings", ""]
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


def reviewed_script_markdown(bundle) -> str:
    """The Instructor Script with every accepted Finding and Script Change applied: what the Instructor approved
    at Gate 1, and the words the Master Script must use."""
    from .gates import accepted_changes, line_roles

    gate = bundle.manifest["gates"]["1"]
    roles, changes = line_roles(bundle), accepted_changes(bundle)
    replaced = {c["line"]: c for c in changes.values() if c.get("line") and "fix_text" in c}
    added = {}
    for c in changes.values():
        if c.get("after_line") and c.get("fix_text"):
            added.setdefault(c["after_line"], []).append(c)
    out = [f"# Reviewed Script: {bundle.manifest['video']['id']}", "",
           f"Approved by {gate['approver']} at Gate 1 ({gate['at'][:10]}). The **spoken** lines are said on camera exactly as "
           "written here, and the Master Script uses these words. Changes are marked with the Finding (F…) or "
           "Script Change (SC…) that made them.", "", config_note(bundle), ""]
    for line in bundle.lines():
        lid, role, c = line["id"], roles.get(line["id"], "unknown"), replaced.get(line["id"])
        if c is None:
            words, tag = line["text"], ""
        else:
            words = f"~~{line['text']}~~ " + (c["fix_text"] or "(deleted)")
            tag = f" _({c['id']})_"
        out.append(f"- **{lid}** {words}{tag}" if role == "spoken" else f"- {lid} · _{role.replace('_', ' ')}_ · {words}{tag}")
        out += [f"- **+ after {lid}** {a['fix_text']} _({a['id']})_" for a in added.get(lid, [])]
    return "\n".join(out) + "\n"


def as_spoken(bundle):
    """How a script line is said: the same clean-up the Teleprompter Script uses (no bullets, ✔ or '>')."""
    from . import settings
    from .teleprompter import clean

    symbols = settings.get(bundle, "teleprompter_symbols")
    return lambda text: clean(text, symbols)


def spoken_words(master: dict, say) -> int:
    return sum(len(say(s["text"]).split()) for seg in master["segments"] for s in seg.get("spoken", []))


def master_markdown(bundle, master: dict) -> str:
    say = as_spoken(bundle)
    words = spoken_words(master, say)
    minutes = words / 140
    out = [f"# Master Script: {master['video']['title']}", "", config_note(bundle), "",
           f"**Video:** {master['video']['id']}" + (f" · {master['video']['instructor']}" if master['video'].get('instructor') else "")
           + f" · {words} spoken words (about {minutes:.0f} min)", "",
           "## Points to check", "", bullet_list(master["points_to_check"]), "",
           "## Agenda", "", bullet_list(master["agenda"]), "",
           "## Slide plan", "", "What appears on each slide, in order. Slides are built from this once the Master Script is approved.", "",
           "| Slide | Segment | Layout | Title | On screen |", "| --- | --- | --- | --- | --- |"]
    cell = lambda t: str(t).replace("|", "/").replace("\n", " ")
    for seg in master["segments"]:
        sl = seg["slide"]
        shown = " · ".join(cell(say(b)) for b in sl.get("bullets") or [])
        if sl.get("code"):
            shown = (shown + " · " if shown else "") + "code: " + cell(sl["code"])
        out.append(f"| {sl['id']} | {seg['id']} | {sl['layout']} | {cell(sl['title'])} | {shown} |")
    out.append("")
    if master.get("learning_objectives"):
        out += ["## Learning objectives", "", bullet_list(master["learning_objectives"]), ""]
    for seg in master["segments"]:
        out += [f"## {seg['id']} · {seg['section']} · {seg['title']}  ({seg['start']}–{seg['end']})", "",
                f"**Meaning (English):** {seg['meaning_en']}", "", "**Narration (Instructor's words):**", ""]
        out += [f"> {say(s['text'])}" + (f"  _(added: {s['from_finding']})_" if s.get("from_finding") else "") for s in seg.get("spoken", [])] or ["> (no spoken words)"]
        slide = seg["slide"]
        out += ["", f"**On screen: {slide['id']} · {slide['layout']} · {slide['title']}**", ""]
        if slide.get("bullets"):
            out += [f"- {b}" for b in slide["bullets"]]
        if slide.get("code"):
            out += ["", "`" + slide["code"].replace("\n", "` / `") + "`"]
        for e in seg.get("visual_events", []):
            out += ["", f"**Visual Event {e['id']} · {e['kind']}" + (f" · {e['layout'].replace('_', ' ')}" if e.get("layout") else "")
                    + (f" · {e['duration_sec']} s" if e.get("duration_sec") else "") + "**", "",
                    f"- Starts on: \"{e['trigger']}\"", f"- Shows: {e['description']}"]
            if e.get("template"):
                out.append(f"- Animation Template: {e['template']}")
            if e.get("editor_note"):
                out.append(f"- Editor note: {e['editor_note']}")
        out.append("")
    return "\n".join(out) + "\n"


# --- Markdown → HTML for the subset these views use ------------------------------

def write_pair(stem: Path, markdown: str, title: str) -> None:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".md").write_text(markdown, encoding="utf-8")
    stem.with_suffix(".html").write_text(to_html(markdown, title), encoding="utf-8")


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", text)
    return text


def to_html(markdown: str, title: str) -> str:
    body, in_list, table = [], False, []
    lines = markdown.splitlines() + [""]
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                table.append(cells)
            continue
        if table:
            head, rows = table[0], table[1:]
            body.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                        + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table>")
            table = []
        if line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_inline(line[2:])}</li>")
            continue
        if in_list:
            body.append("</ul>")
            in_list = False
        m = re.match(r"^(#{1,4}) (.*)", line)
        if m:
            n = len(m.group(1))
            body.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif line.startswith("> "):
            body.append(f"<blockquote>{_inline(line[2:])}</blockquote>")
        elif line:
            body.append(f"<p>{_inline(line)}</p>")
    if in_list:
        body.append("</ul>")
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title><style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#1d2433}"
        "h1,h2,h3{color:#0b3d91}blockquote{margin:.5rem 0;padding:.5rem 1rem;border-left:4px solid #2f6fde;background:#eef4ff}"
        "code{background:#f2f4f7;padding:0 .25rem;border-radius:3px}li{margin:.2rem 0}"
        "table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dce7f4;padding:.35rem .5rem;text-align:left;vertical-align:top}th{background:#eef4ff}"
        "</style></head><body>\n" + "\n".join(body) + "\n</body></html>\n"
    )
