"""Diagrams drawn by code: exact text, the same result every time, in the Brand Kit's colours and fonts.

A diagram spec (flow, flowchart, table, tree, compare, timeline, cycle, layers, list, stat, title, code or
array) is laid out once as simple drawing primitives, then written
as SVG (standard library) and, where matplotlib is available, as a transparent 1920×1080 PNG for Premiere.
A spec of type "image" hands the diagram to the image model instead.
"""
from __future__ import annotations

from xml.sax.saxutils import escape


W, H = 1920, 1080
TYPES = ("flow", "flowchart", "table", "tree", "compare", "timeline", "cycle", "layers", "list", "stat", "title", "code", "array", "image")
SHAPES = ("process", "decision", "terminal", "io")


class Theme:
    """The Brand Kit's diagram style: colours, font, sizes and the drawing area."""

    def __init__(self, brand, layout: str = None):
        self.brand, self.layout = brand, layout
        d = brand.get("diagrams")
        self.d = d
        a = (d.get("regions") or {}).get(layout) or d["safe_area"]
        self.left, self.right, self.top, self.bottom = a["left"], a["right"], a["top"], a["bottom"]
        self.narrowed = a["right"] - a["left"] < d["safe_area"]["right"] - d["safe_area"]["left"]
        self.min_size, self.flow_gap, self.sizes = d["min_text"], d["flow_gap"], d["sizes"]
        self.role = d.get("font", "heading")
        f = brand.font(self.role)
        self.font_file = f.get("file")
        self.family = f"{f['family']}, {brand.get('fonts.fallback')}" if brand.get("fonts.fallback") else f["family"]

    def c(self, role: str) -> str:
        return self.brand.color(self.d["colors"][role])

    def family_for(self, role: str) -> str:
        f = self.brand.font(role)
        fallback = self.brand.get("fonts.fallback")
        return f"{f['family']}, {fallback}" if fallback and role != "code" else (f"{f['family']}, monospace" if role == "code" else f["family"])

    def fits(self, text: str, size: float, width: float, bold: bool = True) -> bool:
        if self.font_file:
            return self.brand.measure(self.role).width(text, size) <= width
        return len(str(text)) * size * self.d["char_width"]["bold" if bold else "regular"] <= width

    def size_for(self, text: str, width: float, start: float, bold: bool = True):
        size = start
        while size >= self.min_size and not self.fits(text, size, width, bold):
            size -= 2
        return size if size >= self.min_size else None

    def room(self, width: float, bold: bool = True) -> int:
        """About how many characters fit in `width` at the smallest readable size."""
        if self.font_file:
            return self.brand.measure(self.role).capacity(self.min_size, width)
        return max(1, int(width / (self.min_size * self.d["char_width"]["bold" if bold else "regular"])))

    def too_long(self, label: str, what: str, text: str, width: float, start: float, bold: bool = True) -> list:
        """[] if the text fits at a readable size; otherwise a problem saying how much fits, and where more would."""
        if self.size_for(text, width, start, bold):
            return []
        more = (f" in the {self.layout} layout (fullscreen_cutaway gives the animation the whole frame)"
                if self.narrowed else "")
        return [f"{label}: {what + ' ' if what else ''}'{text}' is too long: about {self.room(width, bold)} characters fit there{more}. "
                "Shorten it, or use fewer boxes."]


def theme_of(brand, layout: str = None) -> Theme:
    """The diagram style, sized to the region of the frame a Visual Event's layout gives it."""
    if isinstance(brand, Theme):
        return brand if layout is None or layout == brand.layout else Theme(brand.brand, layout)
    return Theme(brand, layout)


# --- checks ----------------------------------------------------------------------------

def check(spec: dict, label: str, brand) -> list:
    t = theme_of(brand)
    LEFT, RIGHT, FLOW_GAP = t.left, t.right, t.flow_gap
    kind = spec.get("type")
    if kind not in TYPES:
        return [f"{label}: type must be one of {', '.join(TYPES)}."]
    problems = []
    if kind == "flow":
        steps = spec.get("steps") or []
        if not 2 <= len(steps) <= 6:
            problems.append(f"{label}: a flow needs 2–6 steps (has {len(steps)}).")
        else:
            box_w = (RIGHT - LEFT - FLOW_GAP * (len(steps) - 1)) / len(steps)
            problems += [p for s in steps for p in t.too_long(label, "step", s, box_w - 30, t.sizes["box"])]
        labels = spec.get("labels") or []
        if labels and len(labels) != len(steps) - 1:
            problems.append(f"{label}: 'labels' needs one label per arrow ({len(steps) - 1}), or leave it out.")
        problems += [f"{label}: arrow label '{l}' is too long: about {t.room(FLOW_GAP - 16, False)} characters fit; one or two short words."
                     for l in labels if not t.fits(l, t.sizes["label"], FLOW_GAP - 16, False)]
    elif kind == "table":
        cols, rows = spec.get("columns") or [], spec.get("rows") or []
        if not 1 <= len(cols) <= 6 or not 1 <= len(rows) <= 8:
            problems.append(f"{label}: a table needs 1–6 columns and 1–8 rows.")
        elif any(len(r) != len(cols) for r in rows):
            problems.append(f"{label}: every row needs {len(cols)} cells.")
        else:
            cell_w = (RIGHT - LEFT) / len(cols) - 24
            problems += [p for row in [cols] + rows for c in row for p in t.too_long(label, "cell", c, cell_w, t.sizes["table_header"])]
    elif kind == "tree":
        children = spec.get("children") or []
        if not spec.get("root") or not 1 <= len(children) <= 6:
            problems.append(f"{label}: a tree needs a root and 1–6 children.")
        else:
            box_w = (RIGHT - LEFT - 30 * (len(children) - 1)) / len(children)
            problems += [p for c in children for p in t.too_long(label, "", c, box_w - 24, t.sizes["tree_child"])]
    elif kind == "compare":
        half = (RIGHT - LEFT - 40) / 2
        for side in ("left", "right"):
            part = spec.get(side) or {}
            if not part.get("title") or not 1 <= len(part.get("items") or []) <= 6:
                problems.append(f"{label}: '{side}' needs a title and 1–6 items.")
            else:
                problems += [p for i in part["items"] for p in t.too_long(label, "item", i, half - 90, t.sizes["compare_item"], False)]
    elif kind == "image":
        if not str(spec.get("prompt", "")).strip():
            problems.append(f"{label}: an image diagram needs a 'prompt' for the image model.")
    elif kind in MORE:
        problems += MORE[kind][0](spec, label, t)
    if spec.get("title"):
        problems += t.too_long(label, "title", spec["title"], RIGHT - LEFT, t.sizes["title"])
    return problems


# --- layout --------------------------------------------------------------------------------

def layout(spec: dict, brand) -> list:
    """Primitives: ("rect", x, y, w, h, fill, stroke, radius), ("text", x, y, text, size, colour, bold, anchor),
    ("arrow", x1, y1, x2, y2, colour), ("line", x1, y1, x2, y2, colour)."""
    return [prim for _, _, _, prim in _parts(spec, theme_of(brand))]


def elements(spec: dict, brand) -> list:
    """The diagram as named elements, in drawing order (z), for animations:
    [{"id": "node:1", "role": "node", "label": "You", "z": 1, "prims": [...]}, ...]."""
    out, index = [], {}
    for eid, role, label, prim in _parts(spec, theme_of(brand)):
        if eid not in index:
            index[eid] = len(out)
            out.append({"id": eid, "role": role, "label": label, "z": len(out) + 1, "prims": []})
        out[index[eid]]["prims"].append(prim)
    return out


def element_ids(spec: dict, brand) -> list:
    return [e["id"] for e in elements(spec, brand)]


def _parts(spec: dict, t: Theme) -> list:
    """(element id, role, label, primitive) for every primitive, in drawing order."""
    LEFT, RIGHT, TOP, BOTTOM, z, c = t.left, t.right, t.top, t.bottom, t.sizes, t.c
    p = []
    add = lambda eid, role, label, prim: p.append((eid, role, label, prim))
    top = TOP
    if spec.get("title"):
        add("title", "title", spec["title"], ("text", LEFT, TOP + 40, spec["title"], z["title"], c("title"), True, "start"))
        top = TOP + 110
    kind = spec["type"]
    if kind == "flow":
        steps, labels = spec["steps"], spec.get("labels") or []
        gap = t.flow_gap
        box_w = (RIGHT - LEFT - gap * (len(steps) - 1)) / len(steps)
        box_h, y = 150, (top + BOTTOM) / 2 - 75
        for i, step in enumerate(steps):
            x = LEFT + i * (box_w + gap)
            node = f"node:{i + 1}"
            add(node, "node", step, ("rect", x, y, box_w, box_h, c("box"), None, 24))
            add(node, "node", step, ("text", x + box_w / 2, y + box_h / 2 + 14, step, t.size_for(step, box_w - 30, z["box"]), c("box_text"), True, "middle"))
            if i:
                edge = f"edge:{i}-{i + 1}"
                add(edge, "edge", f"{steps[i - 1]} → {step}", ("arrow", x - gap + 10, y + box_h / 2, x - 10, y + box_h / 2, c("arrow")))
                if i - 1 < len(labels):
                    add(f"label:{i}-{i + 1}", "label", labels[i - 1],
                        ("text", x - gap / 2, y + box_h / 2 - 22, labels[i - 1], z["label"], c("label"), False, "middle"))
    elif kind == "table":
        cols, rows = spec["columns"], spec["rows"]
        col_w = (RIGHT - LEFT) / len(cols)
        row_h = min(80, (BOTTOM - top - 90) / len(rows))
        add("frame", "frame", "table", ("rect", LEFT, top, RIGHT - LEFT, 90 + row_h * len(rows), c("card"), c("card_border"), 16))
        add("header", "header", " · ".join(cols), ("rect", LEFT, top, RIGHT - LEFT, 90, c("header"), None, 16))
        for j, col in enumerate(cols):
            add("header", "header", " · ".join(cols),
                ("text", LEFT + j * col_w + 24, top + 58, col, t.size_for(col, col_w - 24, z["table_header"]), c("text"), True, "start"))
        for i, row in enumerate(rows):
            y = top + 90 + i * row_h
            rid, label = f"row:{i + 1}", " · ".join(row)
            if i:
                add(rid, "row", label, ("line", LEFT, y, RIGHT, y, c("card_border")))
            for j, cell in enumerate(row):
                add(rid, "row", label, ("text", LEFT + j * col_w + 24, y + row_h / 2 + 11, cell,
                                        min(z["table_cell"], t.size_for(cell, col_w - 24, z["table_header"]) or t.min_size), c("text"), False, "start"))
    elif kind == "tree":
        children = spec["children"]
        root_w, root_h = 520, 120
        rx, ry = (LEFT + RIGHT) / 2 - root_w / 2, top
        add("node:root", "node", spec["root"], ("rect", rx, ry, root_w, root_h, c("box"), None, 24))
        add("node:root", "node", spec["root"], ("text", rx + root_w / 2, ry + root_h / 2 + 14, spec["root"],
                                                t.size_for(spec["root"], root_w - 30, z["tree_root"]), c("box_text"), True, "middle"))
        gap = 30
        box_w = (RIGHT - LEFT - gap * (len(children) - 1)) / len(children)
        cy = ry + root_h + 160
        for i, child in enumerate(children):
            x = LEFT + i * (box_w + gap)
            add(f"edge:root-{i + 1}", "edge", f"{spec['root']} → {child}", ("line", rx + root_w / 2, ry + root_h, x + box_w / 2, cy, c("arrow")))
            add(f"node:{i + 1}", "node", child, ("rect", x, cy, box_w, 110, c("child"), c("child_border"), 20))
            add(f"node:{i + 1}", "node", child, ("text", x + box_w / 2, cy + 66, child, t.size_for(child, box_w - 24, z["tree_child"]), c("text"), True, "middle"))
    elif kind == "compare":
        half = (RIGHT - LEFT - 40) / 2
        for k, side in enumerate(("left", "right")):
            part = spec[side]
            x = LEFT + k * (half + 40)
            panel = f"panel:{side}"
            add(panel, "panel", part["title"], ("rect", x, top, half, 100 + 62 * max(len(spec["left"]["items"]), len(spec["right"]["items"])) + 50,
                                                c("card"), c("card_border"), 20))
            add(panel, "panel", part["title"], ("rect", x, top, half, 100, c("header"), None, 20))
            add(panel, "panel", part["title"], ("text", x + 30, top + 64, part["title"], t.size_for(part["title"], half - 60, z["compare_title"]),
                                                c("heading"), True, "start"))
            for i, item in enumerate(part["items"]):
                y = top + 160 + i * 62
                iid = f"item:{side}-{i + 1}"
                add(iid, "item", item, ("rect", x + 30, y - 20, 14, 14, c("bullet"), None, 2))
                add(iid, "item", item, ("text", x + 60, y, item, min(z["compare_item"], t.size_for(item, half - 90, z["compare_item"], False) or t.min_size),
                                        c("text"), False, "start"))
    elif kind in MORE:
        MORE[kind][1](spec, t, add, top)
    return p


# --- more types: each is (check, draw) ----------------------------------------------------

def _fit(t, text, width, start, label, what, bold=True) -> list:
    return t.too_long(label, what, text, width, start, bold)


def _flowchart_geometry(spec, t, top):
    """Layers top to bottom: loops found by depth-first search are drawn as back edges; every other edge
    points down. Nodes are layered by longest path and ordered by the average position of their neighbours."""
    ids = [n["id"] for n in spec["nodes"]]
    edges = [(e["from"], e["to"]) for e in spec.get("edges") or []]
    succ = {i: [v for u, v in edges if u == i] for i in ids}
    state, back = {}, set()

    def dfs(u):
        state[u] = 1
        for v in succ[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                dfs(v)
        state[u] = 2
    for i in ids:
        if i not in state:
            dfs(i)
    fwd = [e for e in edges if e not in back]
    layer = {i: 0 for i in ids}
    for _ in ids:
        for u, v in fwd:
            layer[v] = max(layer[v], layer[u] + 1)
    rows = [[i for i in ids if layer[i] == k] for k in range(max(layer.values()) + 1)]
    gap = 60
    room = (t.right - 90 if back else t.right) - t.left

    def width(n):
        return min(420, (room - gap * (n - 1)) / n)

    def centres(row):
        w = width(len(row))
        start = t.left + room / 2 - (len(row) * w + (len(row) - 1) * gap) / 2
        return {i: start + k * (w + gap) + w / 2 for k, i in enumerate(row)}
    x = {}
    for row in rows:
        x.update(centres(row))
    for _ in range(3):  # barycentre sweeps, down then up
        for k in list(range(1, len(rows))) + list(range(len(rows) - 2, -1, -1)):
            near = {i: [u for u, v in fwd if v == i] + [v for u, v in fwd if u == i] for i in rows[k]}
            rows[k].sort(key=lambda i: sum(x[j] for j in near[i]) / len(near[i]) if near[i] else x[i])
            x.update(centres(rows[k]))
    layer_h = (t.bottom - top) / len(rows)
    box_h = min(120, layer_h * 0.62)  # the rest of each level is room for the arrows
    boxes = {}
    for k, row in enumerate(rows):
        w = width(len(row))
        for i in row:
            cy = top + layer_h * (k + 0.5)
            boxes[i] = (x[i] - w / 2, cy - box_h / 2, w, box_h)
    return rows, boxes, back, box_h


def _check_flowchart(spec, label, t):
    nodes, problems = spec.get("nodes") or [], []
    if not 2 <= len(nodes) <= 12:
        return [f"{label}: a flowchart needs 2–12 nodes (has {len(nodes)})."]
    ids = [n.get("id") for n in nodes]
    if len(set(ids)) != len(ids) or not all(ids):
        problems.append(f"{label}: every node needs its own 'id'.")
    for n in nodes:
        if n.get("shape", "process") not in SHAPES:
            problems.append(f"{label}: node '{n.get('id')}' shape must be one of {', '.join(SHAPES)}.")
        if not str(n.get("label", "")).strip():
            problems.append(f"{label}: node '{n.get('id')}' has no label.")
    for k, e in enumerate(spec.get("edges") or [], 1):
        for end in ("from", "to"):
            if e.get(end) not in ids:
                problems.append(f"{label}: edge {k} {'goes to' if end == 'to' else 'comes from'} '{e.get(end)}', which is not a node.")
    if problems:
        return problems
    rows, boxes, _, box_h = _flowchart_geometry(spec, t, t.top + (110 if spec.get("title") else 0))
    if len(rows) > 6 or box_h < 60:
        return [f"{label}: the flowchart is {len(rows)} steps deep; keep it to 6 levels or split it into two diagrams."]
    if max(len(r) for r in rows) > 4:
        return [f"{label}: one level has {max(len(r) for r in rows)} nodes side by side; keep it to 4."]
    for n in nodes:
        w = boxes[n["id"]][2] * (0.62 if n.get("shape") == "decision" else 1) - 30
        problems += _fit(t, n["label"], w, t.sizes["node"], label, "node")
    problems += [p for e in spec.get("edges") or [] if e.get("label") for p in _fit(t, e["label"], 140, t.sizes["label"], label, "edge label", False)]
    return problems


def _draw_flowchart(spec, t, add, top):
    c, z = t.c, t.sizes
    rows, boxes, back, box_h = _flowchart_geometry(spec, t, top)
    for n in spec["nodes"]:
        x, y, w, h = boxes[n["id"]]
        cx, cy, shape, eid = x + w / 2, y + h / 2, n.get("shape", "process"), f"node:{n['id']}"
        if shape == "decision":
            add(eid, "node", n["label"], ("poly", [(cx, y), (x + w, cy), (cx, y + h), (x, cy)], c("decision"), None))
            colour, width = c("box_text"), w * 0.62 - 30
        elif shape == "io":
            add(eid, "node", n["label"], ("poly", [(x + 24, y), (x + w, y), (x + w - 24, y + h), (x, y + h)], c("child"), c("child_border")))
            colour, width = c("text"), w - 60
        else:
            add(eid, "node", n["label"], ("rect", x, y, w, h, c("terminal" if shape == "terminal" else "box"), None, h / 2 if shape == "terminal" else 16))
            colour, width = c("box_text"), w - 30
        add(eid, "node", n["label"], ("text", cx, cy + 11, n["label"], t.size_for(n["label"], width, z["node"]) or t.min_size, colour, True, "middle"))
    side = max(b[0] + b[2] for b in boxes.values()) + 50
    for k, e in enumerate(spec.get("edges") or []):
        u, v = e["from"], e["to"]
        (ux, uy, uw, uh), (vx, vy, vw, vh) = boxes[u], boxes[v]
        eid, label = f"edge:{u}-{v}", f"{u} → {v}"
        if (u, v) in back:  # round the right-hand side, back up to the target
            lane = side + 18 * k % 54
            add(eid, "edge", label, ("line", ux + uw, uy + uh / 2, lane, uy + uh / 2, c("arrow")))
            add(eid, "edge", label, ("line", lane, uy + uh / 2, lane, vy + vh / 2, c("arrow")))
            add(eid, "edge", label, ("arrow", lane, vy + vh / 2, vx + vw + 6, vy + vh / 2, c("arrow")))
            lx, ly = lane + 12, (uy + vy + vh) / 2
            anchor = "start"
        else:
            x1, y1, x2, y2 = ux + uw / 2, uy + uh, vx + vw / 2, vy - 6
            add(eid, "edge", label, ("arrow", x1, y1, x2, y2, c("arrow")))
            lx, ly, anchor = (x1 + x2) / 2 + 14, (y1 + y2) / 2 + 10, "start"
        if e.get("label"):
            add(f"label:{u}-{v}", "label", e["label"], ("text", lx, ly, e["label"], z["label"], c("label"), False, anchor))


def _check_timeline(spec, label, t):
    events = spec.get("events") or []
    if not 2 <= len(events) <= 7 or not all(isinstance(e, dict) and e.get("when") and e.get("label") for e in events):
        return [f"{label}: a timeline needs 2–7 events, each with 'when' and 'label'."]
    w = (t.right - t.left) / len(events) - 20
    return [p for e in events for p in _fit(t, e["label"], w, t.sizes["timeline_label"], label, "event", False) + _fit(t, e["when"], w, t.sizes["timeline_when"], label, "date")]


def _draw_timeline(spec, t, add, top):
    c, z, events = t.c, t.sizes, spec["events"]
    axis = (top + t.bottom) / 2
    add("axis", "axis", "timeline", ("line", t.left, axis, t.right, axis, c("axis")))
    step = (t.right - t.left) / len(events)
    for i, e in enumerate(events):
        x, eid, w = t.left + step * (i + 0.5), f"event:{i + 1}", step - 20
        above = i % 2 == 0
        add(eid, "event", f"{e['when']} {e['label']}", ("rect", x - 14, axis - 14, 28, 28, c("box"), None, 14))
        add(eid, "event", f"{e['when']} {e['label']}", ("text", x, axis - 100 if above else axis + 70, e["when"],
                                                        t.size_for(e["when"], w, z["timeline_when"]), c("heading"), True, "middle"))
        add(eid, "event", f"{e['when']} {e['label']}", ("text", x, axis - 56 if above else axis + 112, e["label"],
                                                        t.size_for(e["label"], w, z["timeline_label"], False), c("text"), False, "middle"))


def _cycle_geometry(n: int, t, top) -> tuple:
    """Centre, radius and box width: boxes shrink as steps crowd, so every arrow keeps room."""
    import math as m
    r = min((t.bottom - top) / 2 - 70, 380)
    chord = 2 * r * m.sin(m.pi / n)
    return ((t.left + t.right) / 2, (top + t.bottom) / 2), r, min(260, chord - 120)


def _check_cycle(spec, label, t):
    steps = spec.get("steps") or []
    if not 3 <= len(steps) <= 6:
        return [f"{label}: a cycle needs 3–6 steps (has {len(steps)})."]
    _, _, w = _cycle_geometry(len(steps), t, t.top + (110 if spec.get("title") else 0))
    return [p for s_ in steps for p in _fit(t, s_, w - 30, t.sizes["cycle"], label, "step")]


def _draw_cycle(spec, t, add, top):
    import math as m
    c, z, steps = t.c, t.sizes, spec["steps"]
    (cx, cy), r, w = _cycle_geometry(len(steps), t, top)
    pts = [(cx + r * m.cos(m.radians(-90 + 360 * i / len(steps))), cy + r * m.sin(m.radians(-90 + 360 * i / len(steps)))) for i in range(len(steps))]
    for i, (x, y) in enumerate(pts):
        add(f"node:{i + 1}", "node", steps[i], ("rect", x - w / 2, y - 50, w, 100, c("box"), None, 24))
        add(f"node:{i + 1}", "node", steps[i], ("text", x, y + 11, steps[i], t.size_for(steps[i], w - 30, z["cycle"]), c("box_text"), True, "middle"))
    for i, (x1, y1) in enumerate(pts):
        j = (i + 1) % len(pts)
        x2, y2 = pts[j]
        d = m.hypot(x2 - x1, y2 - y1) or 1
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        # leave each box exactly at its edge (boxes are w × 100), with a small gap, curving outward
        clip = min(w / 2 / abs(ux) if ux else 1e9, 50 / abs(uy) if uy else 1e9) + 14
        sx, sy, ex, ey = x1 + ux * clip, y1 + uy * clip, x2 - ux * clip, y2 - uy * clip
        bend = 0.25
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        cx_, cy_ = mx - bend * (ey - sy), my + bend * (ex - sx)
        if m.hypot(cx_ - cx, cy_ - cy) < m.hypot(mx - cx, my - cy):
            bend = -bend
        add(f"edge:{i + 1}-{j + 1}", "edge", f"{steps[i]} → {steps[j]}", ("curve", sx, sy, ex, ey, c("arrow"), bend))


def _check_layers(spec, label, t):
    layers = spec.get("layers") or []
    if not 2 <= len(layers) <= 7:
        return [f"{label}: a layers diagram needs 2–7 layers (has {len(layers)})."]
    return [p for l in layers for p in _fit(t, l, t.right - t.left - 60, t.sizes["layer"], label, "layer")]


def _draw_layers(spec, t, add, top):
    c, z, layers = t.c, t.sizes, spec["layers"]
    band = min(110, (t.bottom - top - 14 * (len(layers) - 1)) / len(layers))
    for i, name in enumerate(layers):
        y = top + i * (band + 14)
        hot = spec.get("highlight") == i + 1
        add(f"layer:{i + 1}", "layer", name, ("rect", t.left, y, t.right - t.left, band, c("highlight" if hot else "child"), None if hot else c("child_border"), 18))
        add(f"layer:{i + 1}", "layer", name, ("text", (t.left + t.right) / 2, y + band / 2 + 12, name,
                                               t.size_for(name, t.right - t.left - 60, z["layer"]), c("box_text" if hot else "text"), True, "middle"))


def _check_list(spec, label, t):
    items = spec.get("items") or []
    if not 1 <= len(items) <= 7:
        return [f"{label}: a list needs 1–7 items (has {len(items)})."]
    return [p for i in items for p in _fit(t, i, t.right - t.left - 110, t.sizes["list_item"], label, "item", False)]


def _draw_list(spec, t, add, top):
    c, z, items = t.c, t.sizes, spec["items"]
    row = min(110, (t.bottom - top) / len(items))
    for i, item in enumerate(items):
        y, eid = top + i * row, f"item:{i + 1}"
        if spec.get("numbered"):
            add(eid, "item", item, ("rect", t.left, y + row / 2 - 30, 60, 60, c("box"), None, 14))
            add(eid, "item", item, ("text", t.left + 30, y + row / 2 + 11, str(i + 1), 30, c("box_text"), True, "middle"))
        else:
            add(eid, "item", item, ("rect", t.left + 20, y + row / 2 - 9, 18, 18, c("bullet"), None, 3))
        add(eid, "item", item, ("text", t.left + 90, y + row / 2 + 12, item, t.size_for(item, t.right - t.left - 110, z["list_item"], False),
                                c("text"), False, "start"))


def _check_stat(spec, label, t):
    if not str(spec.get("value", "")).strip() or not str(spec.get("label", "")).strip():
        return [f"{label}: a stat needs a 'value' (e.g. 70%) and a 'label'."]
    w = t.right - t.left
    return _fit(t, spec["value"], w, t.sizes["stat_value"], label, "value") + _fit(t, spec["label"], w, t.sizes["stat_label"], label, "label", False)


def _draw_stat(spec, t, add, top):
    c, z, w = t.c, t.sizes, t.right - t.left
    mid = (top + t.bottom) / 2
    add("value", "value", spec["value"], ("text", (t.left + t.right) / 2, mid + 20, spec["value"], t.size_for(spec["value"], w, z["stat_value"]),
                                           c("heading"), True, "middle"))
    add("label", "label", spec["label"], ("text", (t.left + t.right) / 2, mid + 110, spec["label"], t.size_for(spec["label"], w, z["stat_label"], False),
                                           c("text"), False, "middle"))


def _check_title(spec, label, t):
    if not str(spec.get("heading", "")).strip():
        return [f"{label}: a title card needs a 'heading' (and optionally a 'subtitle')."]
    w = t.right - t.left
    out = _fit(t, spec["heading"], w, t.sizes["heading"], label, "heading")
    return out + (_fit(t, spec["subtitle"], w, t.sizes["subtitle"], label, "subtitle", False) if spec.get("subtitle") else [])


def _draw_title(spec, t, add, top):
    c, z, w = t.c, t.sizes, t.right - t.left
    mid = (top + t.bottom) / 2
    add("heading", "heading", spec["heading"], ("text", t.left, mid, spec["heading"], t.size_for(spec["heading"], w, z["heading"]), c("title"), True, "start"))
    add("heading", "heading", spec["heading"], ("rect", t.left, mid + 30, 140, 12, c("box"), None, 6))
    if spec.get("subtitle"):
        add("subtitle", "subtitle", spec["subtitle"], ("text", t.left, mid + 100, spec["subtitle"],
                                                        t.size_for(spec["subtitle"], w, z["subtitle"], False), c("label"), False, "start"))


def _check_code(spec, label, t):
    lines = str(spec.get("code") or "").split("\n")
    if not str(spec.get("code", "")).strip() or len(lines) > 14:
        return [f"{label}: code needs 1–14 lines (has {len(lines) if spec.get('code') else 0})."]
    m = t.brand.measure("code")
    w = t.right - t.left - 80
    return [f"{label}: code line {i} is too wide; break it or shorten names." for i, l in enumerate(lines, 1) if m.width(l, t.sizes["code"]) > w]


def _draw_code(spec, t, add, top):
    c, z = t.c, t.sizes
    lines = str(spec["code"]).split("\n")
    line_h = z["code"] * 1.45
    add("card", "card", "code", ("rect", t.left, top, t.right - t.left, line_h * len(lines) + 60, c("code_bg"), None, 18))
    for i, line in enumerate(lines):
        add(f"line:{i + 1}", "line", line, ("text", t.left + 40, top + 30 + line_h * (i + 0.8), line or " ", z["code"], c("code_text"), False, "start", "code"))


def _check_array(spec, label, t):
    values = spec.get("values") or []
    if not 2 <= len(values) <= 10:
        return [f"{label}: an array needs 2–10 values (has {len(values)})."]
    problems = [f"{label}: pointer '{p_.get('label')}' points at index {p_.get('index')}, outside the array."
                for p_ in spec.get("pointers") or [] if not isinstance(p_.get("index"), int) or not 0 <= p_["index"] < len(values)]
    cell = min(140, (t.right - t.left) / len(values))
    return problems + [p for v in values for p in _fit(t, str(v), cell - 20, t.sizes["array"], label, "value")]


def _draw_array(spec, t, add, top):
    c, z, values = t.c, t.sizes, spec["values"]
    cell = min(140, (t.right - t.left) / len(values))
    x0, y = (t.left + t.right) / 2 - cell * len(values) / 2, (top + t.bottom) / 2 - cell / 2 - 40
    for i, v in enumerate(values):
        x, eid = x0 + i * cell, f"cell:{i + 1}"
        add(eid, "cell", str(v), ("rect", x, y, cell, cell, c("card"), c("child_border"), 8))
        add(eid, "cell", str(v), ("text", x + cell / 2, y + cell / 2 + 14, str(v), t.size_for(str(v), cell - 20, z["array"]), c("text"), True, "middle"))
        add(eid, "cell", str(v), ("text", x + cell / 2, y + cell + 34, str(i), z["index"], c("label"), False, "middle"))
    for p_ in spec.get("pointers") or []:
        x = x0 + p_["index"] * cell + cell / 2
        eid = f"pointer:{p_['label']}"
        add(eid, "pointer", p_["label"], ("arrow", x, y + cell + 150, x, y + cell + 50, c("highlight")))
        add(eid, "pointer", p_["label"], ("text", x, y + cell + 190, p_["label"], z["array"], c("highlight"), True, "middle"))


MORE = {"flowchart": (_check_flowchart, _draw_flowchart), "timeline": (_check_timeline, _draw_timeline),
        "cycle": (_check_cycle, _draw_cycle), "layers": (_check_layers, _draw_layers), "list": (_check_list, _draw_list),
        "stat": (_check_stat, _draw_stat), "title": (_check_title, _draw_title), "code": (_check_code, _draw_code),
        "array": (_check_array, _draw_array)}


def curve_control(x1, y1, x2, y2, bend) -> tuple:
    """The control point of a curved arrow, the same one matplotlib's arc3 uses on our y-down frame."""
    return (x1 + x2) / 2 - bend * (y2 - y1), (y1 + y2) / 2 + bend * (x2 - x1)


# --- writers -------------------------------------------------------------------------------

def to_svg(prims: list, brand, size=None) -> str:
    t = theme_of(brand)
    FONT = t.family
    w_, h_ = size or (W, H)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_}" height="{h_}" viewBox="0 0 {w_} {h_}">',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{t.c("arrow")}"/></marker></defs>']
    for prim in prims:
        kind = prim[0]
        if kind == "rect":
            _, x, y, w, h, fill, stroke, r = prim
            line = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{r}" fill="{fill}"{line}/>')
        elif kind == "dashed":  # where something still to be made will go
            _, x, y, w, h, stroke, r = prim
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{r}" fill="none" stroke="{stroke}" '
                       'stroke-width="4" stroke-dasharray="18 12"/>')
        elif kind == "text":
            _, x, y, text, size, colour, bold, anchor = prim[:8]
            weight = "700" if bold else "400"
            family = t.family_for(prim[8]) if len(prim) > 8 else FONT
            out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
                       f'fill="{colour}" text-anchor="{anchor}">{escape(str(text))}</text>')
        elif kind == "arrow":
            _, x1, y1, x2, y2, colour = prim
            out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{colour}" stroke-width="6" marker-end="url(#arrow)"/>')
        elif kind == "line":
            _, x1, y1, x2, y2, colour = prim
            out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{colour}" stroke-width="3"/>')
        elif kind == "curve":
            _, x1, y1, x2, y2, colour, bend = prim
            cx, cy = curve_control(x1, y1, x2, y2, bend)
            out.append(f'<path d="M{x1:.0f},{y1:.0f} Q{cx:.0f},{cy:.0f} {x2:.0f},{y2:.0f}" fill="none" stroke="{colour}" '
                       f'stroke-width="6" marker-end="url(#arrow)"/>')
        elif kind == "image":
            import base64
            _, x, y, w, h, data = prim
            out.append(f'<image x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
                       f'href="data:image/png;base64,{base64.b64encode(data).decode("ascii")}"/>')
        elif kind == "poly":
            _, points, fill, stroke = prim
            pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in points)
            line = f' stroke="{stroke}" stroke-width="3"' if stroke else ""
            out.append(f'<polygon points="{pts}" fill="{fill}"{line}/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def to_png(prims: list, path, brand, size=None) -> bool:
    """Draw with matplotlib if the sandbox has it. Returns False when it doesn't (the SVG still exists).
    The text uses the Brand Kit's font file when the kit has one, else matplotlib's own font."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties
        from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    except Exception:
        return False
    t = theme_of(brand)
    font = {}
    if t.font_file:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix="." + t.font_file.rsplit(".", 1)[-1], delete=False)
        tmp.write(t.brand.file(t.font_file))
        tmp.close()
        font = {"fontproperties": FontProperties(fname=tmp.name)}
    w_, h_ = size or (W, H)
    fig = plt.figure(figsize=(w_ / 100, h_ / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_)
    ax.set_ylim(h_, 0)
    ax.axis("off")
    px_to_pt = 0.72  # at 100 dpi
    for order, prim in enumerate(prims, 1):  # zorder keeps the painter's order (images included)
        kind = prim[0]
        if kind == "rect":
            _, x, y, w, h, fill, stroke, r = prim
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor=fill,
                                        edgecolor=stroke or fill, linewidth=2 if stroke else 0, zorder=order))
        elif kind == "dashed":
            _, x, y, w, h, stroke, r = prim
            ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", facecolor="none",
                                        edgecolor=stroke, linewidth=3, linestyle=(0, (6, 4)), zorder=order))
        elif kind == "text":
            _, x, y, text, size, colour, bold, anchor = prim[:8]
            extra = {"family": "monospace"} if len(prim) > 8 and prim[8] == "code" else font
            ax.text(x, y, str(text), fontsize=size * px_to_pt, color=colour, fontweight="bold" if bold else "normal",
                    ha={"middle": "center", "start": "left", "end": "right"}[anchor], va="baseline", zorder=order, **extra)
        elif kind == "arrow":
            _, x1, y1, x2, y2, colour = prim
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=30, color=colour, linewidth=4, zorder=order))
        elif kind == "line":
            _, x1, y1, x2, y2, colour = prim
            ax.plot([x1, x2], [y1, y2], color=colour, linewidth=2, zorder=order)
        elif kind == "curve":
            _, x1, y1, x2, y2, colour, bend = prim
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), connectionstyle=f"arc3,rad={bend}", arrowstyle="-|>",
                                         mutation_scale=30, color=colour, linewidth=4, zorder=order))
        elif kind == "image":
            import io
            import matplotlib.image as mpimg
            _, x, y, w, h, data = prim
            ax.imshow(mpimg.imread(io.BytesIO(data), format="png"), extent=(x, x + w, y + h, y), interpolation="bilinear", zorder=order)
        elif kind == "poly":
            from matplotlib.patches import Polygon
            _, points, fill, stroke = prim
            ax.add_patch(Polygon(points, closed=True, facecolor=fill, edgecolor=stroke or fill, linewidth=2 if stroke else 0, zorder=order))
    ax.set_xlim(0, w_)
    ax.set_ylim(h_, 0)
    fig.savefig(path, transparent=True, dpi=100)
    plt.close(fig)
    return True


def draw(spec: dict, svg_path, png_path, brand) -> bool:
    t = theme_of(brand)
    prims = layout(spec, t)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(to_svg(prims, t), encoding="utf-8")
    return to_png(prims, png_path, t)


def validate_all(specs: list, events: dict, brand) -> list:
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
        problems += check(spec, label, theme_of(brand, events[ev].get("layout")))
    return problems

