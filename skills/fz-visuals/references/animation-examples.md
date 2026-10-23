# Animations: worked examples

Specs for animations in the **DBMS** (Swara) and **Strings** (Durga) Videos. Each one is accepted by `fz.py submit <bundle> animations` in the layout its heading names: a `beside_instructor` animation gets only part of the frame, so its labels must be shorter. The spoken words each trigger comes from are quoted with it.

## A flow that builds as it is explained (DBMS · beside_instructor)

> "DBMS anedi **User ki, Database ki madhya** **oka bridge laga** work chestundi. … Meeru DBMS ki **request pampistaru** ➔ DBMS **database lo vetukuthundi** ➔ …"

The two ends appear first, then the bridge, then each arrow as it is named.

```json
{
  "event": "S11-E1",
  "template": "flow",
  "diagram": {"type": "flow", "steps": ["You", "DBMS", "Database"], "labels": ["request", "search"]},
  "steps": [
    {"show": ["node:1", "node:3"], "trigger": "User ki, Database ki madhya"},
    {"show": ["node:2"], "trigger": "oka bridge laga"},
    {"show": ["edge:1-2", "label:1-2"], "trigger": "request pampistaru"},
    {"show": ["edge:2-3", "label:2-3"], "trigger": "database lo vetukuthundi"}
  ]
}
```

## A tree named branch by branch (DBMS · fullscreen_cutaway)

> "So, industry requirements ni batti DBMS ni **4 main types** ga divide chesaru: **Hierarchical DBMS** … **Network DBMS** … **Relational DBMS (RDBMS)** … **Object-Oriented DBMS** …"

"Relational DBMS" is said twice in the Segment, so its trigger takes the next word too. Four branches need the whole frame: beside the Instructor, "Object-Oriented" doesn't fit, and the builder says how many characters do.

```json
{
  "event": "S14-E1",
  "template": "tree_graph",
  "diagram": {"type": "tree", "root": "DBMS", "children": ["Hierarchical", "Network", "Relational", "Object-Oriented"]},
  "steps": [
    {"show": ["node:root"], "trigger": "4 main types"},
    {"show": ["edge:root-1", "node:1"], "trigger": "Hierarchical DBMS"},
    {"show": ["edge:root-2", "node:2"], "trigger": "Network DBMS"},
    {"show": ["edge:root-3", "node:3"], "trigger": "Relational DBMS (RDBMS)"},
    {"show": ["edge:root-4", "node:4"], "trigger": "Object-Oriented DBMS"}
  ]
}
```

## Positions with pointers (Strings · beside_instructor)

> "Ippudu manam **Negative Indexing gurinchi** chuddam. … Negative indexing lo **last character ki -1** index untundi."

```json
{
  "event": "S13-E1",
  "template": "array_pointer",
  "diagram": {"type": "array", "values": ["D", "u", "r", "g", "a"], "pointers": [{"index": 4, "label": "-1"}, {"index": 0, "label": "-5"}]},
  "steps": [
    {"show": ["cell:1", "cell:2", "cell:3", "cell:4", "cell:5"], "trigger": "Negative Indexing gurinchi"},
    {"show": ["pointer:-1"], "trigger": "last character ki -1"},
    {"show": ["pointer:-5"]}
  ]
}
```

The last step has no trigger: nothing in the narration names -5 at that point, so it comes in evenly after -1.

## Two sides compared (Strings · fullscreen_cutaway)

> "**String lopala single quote unte** → outside double quotes use cheyyachu. … **String lopala double quotes unte** → outside single quotes use cheyyachu."

```json
{
  "event": "S10-E1",
  "template": "compare_split",
  "diagram": {
    "type": "compare",
    "left": {"title": "Single quote inside", "items": ["Outside: double quotes", "\"I'm Durga\""]},
    "right": {"title": "Double quotes inside", "items": ["Outside: single quotes", "'He said \"Hello\"'"]}
  },
  "steps": [
    {"show": ["panel:left", "item:left-1", "item:left-2"], "trigger": "String lopala single quote unte"},
    {"show": ["panel:right", "item:right-1", "item:right-2"], "trigger": "String lopala double quotes unte"}
  ]
}
```

## The Instructor's own idea, illustrated (DBMS · fullscreen_cutaway)

> `[Visual: Snap transition. The paper files digitally transform into a sleek server/computer graphic]` "**Exact ga ee problem** ni solve cheyyadanike software world lo **oka DBMS vachindi**."

`ai` elements for the pictures, `text` for the words, `arrow` for the arrow. Everything stays clear of the presenter area (bottom right).

```json
{
  "event": "S05-E1",
  "template": "transform_morph",
  "elements": [
    {"id": "paper-files", "kind": "ai", "describe": "tall untidy stacks of paper files, a few pages slipping out", "place": [160, 220, 560, 600]},
    {"id": "arrow", "kind": "arrow", "from": [780, 520], "to": [1040, 520]},
    {"id": "server", "kind": "ai", "describe": "a sleek modern server rack with glowing blue lights", "place": [1100, 220, 560, 600]},
    {"id": "dbms-label", "kind": "text", "text": "DBMS", "place": [1180, 850, 400, 90]}
  ],
  "steps": [
    {"show": ["paper-files"], "trigger": "Exact ga ee problem"},
    {"show": ["arrow", "server", "dbms-label"], "trigger": "oka DBMS vachindi"}
  ]
}
```

A scene with a person works the same way: the clerk is an `ai` element ("a tired office clerk searching a tall stack of paper files"), and the Brand Kit's own character is used by giving its id, such as `"character": "learner"`.

## Nothing code can draw (DBMS · fullscreen_cutaway)

```json
{
  "event": "S20-E1",
  "template": "custom",
  "steps": [
    {"describe": "A Saturn V rocket on the launch pad, blueprints and stacks of paper beside it", "trigger": "NASA Apollo space program"},
    {"describe": "The paper stacks fly into a mainframe labelled IMS", "trigger": "Information Management System"}
  ]
}
```

## Before and after

| Before | After | Why |
|---|---|---|
| tree labels "Hierarchical DBMS (Tree structure)" | "Hierarchical" | at most 4 words; the root already says DBMS |
| one step showing all four DBMS types | one step per type, on its name | each step shows what its trigger names |
| trigger "Relational DBMS" | "Relational DBMS (RDBMS)" | it must occur once in the Segment |
| a 4-box flow beside the Instructor: "Semester Results", "Students database" | 3 boxes ("Click", "DBMS", "Database"), or (through the Master Script) the layout `fullscreen_cutaway` | beside the Instructor a 4-box flow holds about 5 characters a box, a 3-box flow about 11; the builder says how many |
| an `ai` element "DBMS label on a server" | an `ai` server and a `text` element "DBMS" | the image tool misspells; code doesn't |
| a `text` element at [1700, 900, 300, 100] | [1180, 850, 400, 90] | the presenter stands bottom right |
