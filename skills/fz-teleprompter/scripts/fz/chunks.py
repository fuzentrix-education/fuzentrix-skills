"""Split a long Instructor Script into Chunks a Host App can handle in one turn."""
from __future__ import annotations

_SENTENCE_END = tuple(".?!:;\"'”’)]…")
_BULLETS = ("*", "-", "•", "✔", ">", "➔")


def is_heading(line: dict) -> bool:
    """A place where a new topic likely starts: a slide/animation marker, or a short title-like line."""
    if line.get("marker") in ("slide", "animation-start"):
        return True
    text = line["text"]
    if text.startswith(_BULLETS) or text.endswith(_SENTENCE_END):
        return False
    return len(text.split()) <= 6


def make_chunks(lines: list, target: int) -> list:
    """Cut before a heading once the chunk is at least half full; always cut at the target size,
    except that an Animation Start…End block is kept together up to 1.5× the target."""
    chunks, current, in_animation = [], [], False
    for line in lines:
        size = len(current)
        cut = size >= target and not (in_animation and size < 1.5 * target)
        if size and is_heading(line) and size >= target / 2 and not in_animation:
            cut = True
        if cut:
            chunks.append(current)
            current = []
        current.append(line)
        if line.get("marker") == "animation-start":
            in_animation = True
        elif line.get("marker") == "animation-end":
            in_animation = False
    if current:
        chunks.append(current)
    return [
        {"id": f"C{i:02d}", "start": c[0]["id"], "end": c[-1]["id"], "lines": len(c)}
        for i, c in enumerate(chunks, 1)
    ]


def assign(lines: list, chunks: list) -> list:
    """Return lines with their chunk id attached."""
    out, i = [], 0
    for chunk in chunks:
        for _ in range(chunk["lines"]):
            out.append(dict(lines[i], chunk=chunk["id"]))
            i += 1
    return out
