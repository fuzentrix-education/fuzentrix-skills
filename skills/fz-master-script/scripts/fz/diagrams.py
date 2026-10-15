"""Diagrams drawn by code: exact text, Fuzentrix colours, the same result every time.

A diagram spec (flow, table, tree or compare) is laid out once as simple drawing primitives, then written
as SVG (standard library) and, where matplotlib is available, as a transparent 1920×1080 PNG for Premiere.
A spec of type "image" hands the diagram to the image model instead.
"""
from __future__ import annotations

from xml.sax.saxutils import escape


W, H = 1920, 1080
TYPES = ("flow", "table", "tree", "compare", "image")
NAVY, BLUE, LIGHT, BORDER, WHITE, SLATE = "#062858", "#0A59C8", "#E5EFFD", "#DCE7F4", "#FFFFFF", "#52657D"
FONT = "Aptos, 'Segoe UI', Arial, sans-serif"
# Drawing area: inside the margins and clear of the presenter area (bottom-right 10% × 20%).
LEFT, RIGHT, TOP, BOTTOM = 120, 1640, 120, 840
MIN_SIZE = 28  # smallest readable text on a 1080p frame
FLOW_GAP = 170


def _fits(text: str, size: float, width: float, bold: bool = True) -> bool:
    return len(str(text)) * size * (0.58 if bold else 0.53) <= width


def _size_for(text: str, width: float, start: float, bold: bool = True):
    size = start
    while size >= MIN_SIZE and not _fits(text, size, width, bold):
        size -= 2
    return size if size >= MIN_SIZE else None


# --- checks ----------------------------------------------------------------------------

def check(spec: dict, label: str) -> list:
    kind = spec.get("type")
    if kind not in TYPES:
        return [f"{label}: type must be one of {', '.join(TYPES)}."]
    problems = []
    too_long = lambda text, width, start: _size_for(text, width, start) is None
    if kind == "flow":
        steps = spec.get("steps") or []
        if not 2 <= len(steps) <= 6:
            problems.append(f"{label}: a flow needs 2–6 steps (has {len(steps)}).")
        else:
            box_w = (RIGHT - LEFT - FLOW_GAP * (len(steps) - 1)) / len(steps)
            problems += [f"{label}: step '{s}' is too long for a diagram box; keep it to a few words." for s in steps if too_long(s, box_w - 30, 44)]
        labels = spec.get("labels") or []
        if labels and len(labels) != len(steps) - 1:
            problems.append(f"{label}: 'labels' needs one label per arrow ({len(steps) - 1}), or leave it out.")
        problems += [f"{label}: arrow label '{l}' is too long; one or two short words." for l in labels if not _fits(l, 28, FLOW_GAP - 16, False)]
    elif kind == "table":
        cols, rows = spec.get("columns") or [], spec.get("rows") or []
        if not 1 <= len(cols) <= 6 or not 1 <= len(rows) <= 8:
            problems.append(f"{label}: a table needs 1–6 columns and 1–8 rows.")
        elif any(len(r) != len(cols) for r in rows):
            problems.append(f"{label}: every row needs {len(cols)} cells.")
        else:
            cell_w = (RIGHT - LEFT) / len(cols) - 24
            problems += [f"{label}: cell '{c}' is too long for a diagram box." for row in [cols] + rows for c in row if too_long(c, cell_w, 34)]
    elif kind == "tree":
        children = spec.get("children") or []
        if not spec.get("root") or not 1 <= len(children) <= 6:
            problems.append(f"{label}: a tree needs a root and 1–6 children.")
        else:
            box_w = (RIGHT - LEFT - 30 * (len(children) - 1)) / len(children)
            problems += [f"{label}: '{c}' is too long for a diagram box." for c in children if too_long(c, box_w - 24, 34)]
    elif kind == "compare":
        half = (RIGHT - LEFT - 40) / 2
        for side in ("left", "right"):
            part = spec.get(side) or {}
            if not part.get("title") or not 1 <= len(part.get("items") or []) <= 6:
                problems.append(f"{label}: '{side}' needs a title and 1–6 items.")
            else:
                problems += [f"{label}: '{i}' is too long for a diagram box." for i in part["items"] if _size_for(i, half - 90, 32, False) is None]
    elif kind == "image":
        if not str(spec.get("prompt", "")).strip():
            problems.append(f"{label}: an image diagram needs a 'prompt' for the image model.")
    if spec.get("title") and too_long(spec["title"], RIGHT - LEFT, 52):
        problems.append(f"{label}: the title is too long.")
    return problems


# --- layout --------------------------------------------------------------------------------

def layout(spec: dict) -> list:
    """Primitives: ("rect", x, y, w, h, fill, stroke, radius), ("text", x, y, text, size, colour, bold, anchor),
    ("arrow", x1, y1, x2, y2, colour), ("line", x1, y1, x2, y2, colour)."""
    p = []
    top = TOP
    if spec.get("title"):
        p.append(("text", LEFT, TOP + 40, spec["title"], 52, NAVY, True, "start"))
        top = TOP + 110
    kind = spec["type"]
    if kind == "flow":
        steps, labels = spec["steps"], spec.get("labels") or []
        gap = FLOW_GAP
        box_w = (RIGHT - LEFT - gap * (len(steps) - 1)) / len(steps)
        box_h, y = 150, (top + BOTTOM) / 2 - 75
        for i, step in enumerate(steps):
            x = LEFT + i * (box_w + gap)
            p.append(("rect", x, y, box_w, box_h, BLUE, None, 24))
            p.append(("text", x + box_w / 2, y + box_h / 2 + 14, step, _size_for(step, box_w - 30, 44), WHITE, True, "middle"))
            if i:
                p.append(("arrow", x - gap + 10, y + box_h / 2, x - 10, y + box_h / 2, NAVY))
                if i - 1 < len(labels):
                    p.append(("text", x - gap / 2, y + box_h / 2 - 22, labels[i - 1], 28, SLATE, False, "middle"))
    elif kind == "table":
        cols, rows = spec["columns"], spec["rows"]
        col_w = (RIGHT - LEFT) / len(cols)
        row_h = min(80, (BOTTOM - top - 90) / len(rows))
        p.append(("rect", LEFT, top, RIGHT - LEFT, 90 + row_h * len(rows), WHITE, BORDER, 16))
        p.append(("rect", LEFT, top, RIGHT - LEFT, 90, LIGHT, None, 16))
        for j, c in enumerate(cols):
            p.append(("text", LEFT + j * col_w + 24, top + 58, c, _size_for(c, col_w - 24, 34), NAVY, True, "start"))
        for i, row in enumerate(rows):
            y = top + 90 + i * row_h
            if i:
                p.append(("line", LEFT, y, RIGHT, y, BORDER))
            for j, c in enumerate(row):
                p.append(("text", LEFT + j * col_w + 24, y + row_h / 2 + 11, c, min(30, _size_for(c, col_w - 24, 34) or MIN_SIZE), NAVY, False, "start"))
    elif kind == "tree":
        children = spec["children"]
        root_w, root_h = 520, 120
        rx, ry = (LEFT + RIGHT) / 2 - root_w / 2, top
        p.append(("rect", rx, ry, root_w, root_h, BLUE, None, 24))
        p.append(("text", rx + root_w / 2, ry + root_h / 2 + 14, spec["root"], _size_for(spec["root"], root_w - 30, 44), WHITE, True, "middle"))
        gap = 30
        box_w = (RIGHT - LEFT - gap * (len(children) - 1)) / len(children)
        cy = ry + root_h + 160
        for i, c in enumerate(children):
            x = LEFT + i * (box_w + gap)
            p.append(("line", rx + root_w / 2, ry + root_h, x + box_w / 2, cy, NAVY))
            p.append(("rect", x, cy, box_w, 110, LIGHT, BLUE, 20))
            p.append(("text", x + box_w / 2, cy + 66, c, _size_for(c, box_w - 24, 34), NAVY, True, "middle"))
    elif kind == "compare":
        half = (RIGHT - LEFT - 40) / 2
        for k, side in enumerate(("left", "right")):
            part = spec[side]
            x = LEFT + k * (half + 40)
            p.append(("rect", x, top, half, 100 + 62 * max(len(spec["left"]["items"]), len(spec["right"]["items"])) + 50, WHITE, BORDER, 20))
            p.append(("rect", x, top, half, 100, LIGHT, None, 20))
            p.append(("text", x + 30, top + 64, part["title"], _size_for(part["title"], half - 60, 40), BLUE, True, "start"))
            for i, item in enumerate(part["items"]):
                y = top + 160 + i * 62
                p.append(("rect", x + 30, y - 20, 14, 14, BLUE, None, 2))
                p.append(("text", x + 60, y, item, min(32, _size_for(item, half - 90, 32, False) or MIN_SIZE), NAVY, False, "start"))
    return p


# --- writers -------------------------------------------------------------------------------

def to_svg(prims: list) -> str:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{NAVY}"/></marker></defs>']
    for prim in prims:
        kind = prim[0]
        if kind == "rect":
            _, x, y, w, h, fill, stroke, r = prim
            line = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{r}" fill="{fill}"{line}/>')
        elif kind == "text":
            _, x, y, text, size, colour, bold, anchor = prim
            weight = "700" if bold else "400"
            out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
                       f'fill="{colour}" text-anchor="{anchor}">{escape(str(text))}</text>')
        elif kind == "arrow":
            _, x1, y1, x2, y2, colour = prim
            out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{colour}" stroke-width="6" marker-end="url(#arrow)"/>')
        elif kind == "line":
            _, x1, y1, x2, y2, colour = prim
            out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{colour}" stroke-width="3"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def to_png(prims: list, path) -> bool:
    """Draw with matplotlib if the sandbox has it. Returns False when it doesn't (the SVG still exists)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    except Exception:
        return False
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    px_to_pt = 0.72  # at 100 dpi
    for prim in prims:
        kind = prim[0]
        if kind == "rect":
            _, x, y, w, h, fill, stroke, r = prim
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=fill,
                                        edgecolor=stroke or fill, linewidth=2 if stroke else 0))
        elif kind == "text":
            _, x, y, text, size, colour, bold, anchor = prim
            ax.text(x, y, str(text), fontsize=size * px_to_pt, color=colour, fontweight="bold" if bold else "normal",
                    ha={"middle": "center", "start": "left", "end": "right"}[anchor], va="baseline")
        elif kind == "arrow":
            _, x1, y1, x2, y2, colour = prim
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=30, color=colour, linewidth=4))
        elif kind == "line":
            _, x1, y1, x2, y2, colour = prim
            ax.plot([x1, x2], [y1, y2], color=colour, linewidth=2)
    fig.savefig(path, transparent=True, dpi=100)
    plt.close(fig)
    return True


def draw(spec: dict, svg_path, png_path) -> bool:
    prims = layout(spec)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(to_svg(prims), encoding="utf-8")
    return to_png(prims, png_path)


def validate_all(specs: list, events: dict) -> list:
    problems, seen = [], set()
    for i, spec in enumerate(specs, 1):
        ev = spec.get("event")
        label = f"Diagram {i} ({ev})"
        if ev not in events:
            problems.append(f"{label}: {ev} is not a diagram Visual Event in the Final Master Script ({', '.join(events) or 'none'}).")
            continue
        if ev in seen:
            problems.append(f"{label}: {ev} is given twice.")
        seen.add(ev)
        problems += check(spec, label)
    return problems

