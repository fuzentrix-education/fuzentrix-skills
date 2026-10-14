"""Stage 3e: the Teleprompter Script. Only the words the Instructor speaks, taken unchanged from the
Final Master Script, formatted for reading on camera. No AI involved."""
from __future__ import annotations

import html
import re

from . import naming, settings
from .bundle import read_json
from .docx_writer import write_docx
from .problems import Rejected

_LEADING_MARKERS = re.compile(r"^(?:[*\-•✔✓>➔→]\s*)+")
_PAUSE_END = (".", "?", "!", "…")


def clean(text: str, symbols: dict) -> str:
    text = _LEADING_MARKERS.sub("", text.strip())
    for symbol, replacement in symbols.items():
        text = text.replace(symbol, f" {replacement} " if replacement else " ")
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = " ".join(text.split())
    return re.sub(r"\s+(\.\.\.|…|[,.;:?!])", r"\1", text)


def wrap(text: str, words_per_line: int) -> list:
    """Line breaks for reading aloud:
    - break after a pause (sentence end or '...') once a line has 3+ words;
    - at the word limit, run up to 2 words further if that ends the line on a pause or comma;
    - otherwise break after the line's last comma in its second half;
    - otherwise break at the limit."""
    words, lines, current, i = text.split(), [], [], 0
    soft = _PAUSE_END + (",",)
    while i < len(words):
        current.append(words[i])
        i += 1
        if len(current) >= 3 and current[-1].endswith(_PAUSE_END):
            lines.append(" ".join(current))
            current = []
        elif len(current) >= words_per_line:
            ahead = words[i:i + 2]
            k = next((j for j, w in enumerate(ahead) if w.endswith(soft)), None)
            if k is not None:
                current += ahead[:k + 1]
                i += k + 1
                lines.append(" ".join(current))
                current = []
                continue
            commas = [j for j, w in enumerate(current[:-1]) if w.endswith(",") and j + 1 >= (words_per_line + 1) // 2]
            if commas:
                lines.append(" ".join(current[:commas[-1] + 1]))
                current = current[commas[-1] + 1:]
            else:
                lines.append(" ".join(current))
                current = []
    if current:
        lines.append(" ".join(current))
    return lines


def build(bundle) -> dict:
    if bundle.manifest["stages"].get("master", {}).get("status") != "final":
        raise Rejected("The Teleprompter Script is built only from a Final Master Script. Record Gate 2 first.")
    master = read_json(bundle.path("02_master", "master.json"))
    symbols = settings.get(bundle, "teleprompter_symbols")
    per_line = settings.get(bundle, "line_length_words")

    blocks = []
    for seg in master["segments"]:
        block = []
        for s in seg.get("spoken", []):
            block += wrap(clean(s["text"], symbols), per_line)
        if block:
            blocks.append(block)
    lines = [line for i, block in enumerate(blocks) for line in ([""] if i else []) + block]

    video_id = master["video"]["id"]
    folder = bundle.path(naming.TELEPROMPTER)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{video_id}_teleprompter.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_docx(folder / f"{video_id}_teleprompter.docx", lines)
    (folder / f"{video_id}_teleprompter.html").write_text(_page(master["video"].get("title") or video_id, blocks), encoding="utf-8")

    words = sum(len(l.split()) for l in lines)
    wpm = settings.get(bundle, "words_per_minute")
    report = _report(bundle, master, words, wpm)
    (folder / "teleprompter_report.md").write_text(report, encoding="utf-8")
    bundle.manifest["stages"]["teleprompter"] = {"status": "built", "words": words}
    bundle.log("teleprompter built")
    return {"words": words, "minutes": words / wpm, "lines": len([l for l in lines if l])}


def _report(bundle, master: dict, words: int, wpm: int) -> str:
    text_by_id = {l["id"]: l["text"] for l in bundle.lines()}
    removed = [(lid, role) for lid, role in master["line_roles"].items() if role != "spoken"]
    out = [f"# Teleprompter report: {master['video']['id']}", "",
           f"- Spoken words: {words}", f"- Estimated reading time: {words / wpm:.1f} min at {wpm} words per minute", "",
           "## Lines kept off the teleprompter", "",
           "Check that nothing you meant to say is here.", ""]
    out += [f"- {lid} · {role.replace('_', ' ')}: {text_by_id.get(lid, '')}" for lid, role in removed] or ["- None"]
    return "\n".join(out) + "\n"


def _page(title: str, blocks: list) -> str:
    paragraphs = "\n".join("<p>" + "<br>".join(html.escape(l) for l in block) + "</p>" for block in blocks)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Teleprompter: {html.escape(title)}</title>
<style>
body{{margin:0;background:#000;color:#fff;font-family:system-ui,-apple-system,Segoe UI,sans-serif}}
#controls{{position:fixed;top:0;left:0;right:0;display:flex;gap:1rem;align-items:center;padding:.6rem 1rem;background:#111;font-size:15px;z-index:2}}
#controls button{{font-size:15px;padding:.3rem .8rem}}
#text{{padding:40vh 8vw;font-size:var(--size,56px);line-height:1.45}}
#text p{{margin:0 0 1.2em}}
body.mirror #text{{transform:scaleX(-1)}}
#guide{{position:fixed;top:40vh;left:0;right:0;border-top:2px solid rgba(255,80,80,.6);pointer-events:none}}
</style></head><body>
<div id="controls">
<button id="play">Play</button>
<label>Speed <input id="speed" type="range" min="10" max="200" value="60"></label>
<label>Size <input id="size" type="range" min="28" max="120" value="56"></label>
<label><input id="mirror" type="checkbox"> Mirror (for teleprompter glass)</label>
</div>
<div id="guide"></div>
<div id="text">
{paragraphs}
</div>
<script>
let playing=false,last=null,carry=0;
const speed=document.getElementById('speed');
function step(t){{if(!playing){{last=null;return;}}if(last!==null){{carry+=speed.value*(t-last)/1000;const px=Math.floor(carry);if(px){{window.scrollBy(0,px);carry-=px;}}}}last=t;requestAnimationFrame(step);}}
document.getElementById('play').onclick=e=>{{playing=!playing;e.target.textContent=playing?'Pause':'Play';if(playing)requestAnimationFrame(step);}};
document.getElementById('size').oninput=e=>document.getElementById('text').style.setProperty('--size',e.target.value+'px');
document.getElementById('mirror').onchange=e=>document.body.classList.toggle('mirror',e.target.checked);
document.addEventListener('keydown',e=>{{if(e.code==='Space'){{e.preventDefault();document.getElementById('play').click();}}}});
</script>
</body></html>
"""
