# Animations

Goal: for every animation Visual Event, a spec the builder turns into the Editor Kit files a Video Editor needs to build it by hand in Premiere: one transparent full-frame layer per element, a frame for each step, a storyboard, a step sheet timed from the narration, and `spec.json` for the motion-animation workflow.

Before writing, read `references/animation-examples.md` (specs for the DBMS and Strings Videos, accepted by the builder) once per chat.

## Write the specs

1. Create the draft once: `fz.py draft <bundle> animations all <file>`. Each entry gives the event, its suggested template, description, trigger, duration, the Segment's spoken words, its `layout`, the `area` of the frame it may draw in and the `presenter_area` to keep clear (both [x, y, width, height]). Format: `fz.py schema animations`.
2. Fill in every animation in one pass:
   - the **template** (table below; keep the Master Script's suggestion unless it can't show the description);
   - for code-drawn templates, the `diagram`, written like a diagram spec (`fz.py schema diagrams`);
   - for illustrated templates, the `elements`;
   - for `custom`, a `describe` per step;
   - the **steps**.
3. Score it against the rubric. Fix every failed check.
4. Submit once: `fz.py submit <bundle> animations <file>`. A wrong element id is rejected with the diagram's full list of ids: copy from it.
5. For illustrated templates, generate each `ai` element from `fz.py show <bundle> animation-prompts`, all in one batch, and save each under the path shown.

### Which template

| The description shows | Template | diagram type |
|---|---|---|
| a few steps in a row (You → DBMS → Database) | `flow` | flow (2–6 steps) |
| steps with a decision or a loop | `flowchart` | flowchart (2–12 nodes) |
| rows of facts appearing (character → index) | `table_build` | table (≤ 6 columns, ≤ 8 rows) |
| a parent and its kinds (DBMS → 4 types) | `tree_graph` | tree (1–6 children) |
| two sides compared (single vs double quotes) | `compare_split` | compare (1–6 items a side) |
| dated events | `timeline` | timeline (2–7) |
| a loop of 3–6 stages | `cycle` | cycle |
| stacked levels | `layers` | layers (2–7) |
| points appearing one by one | `list_build`, `agenda_build` | list (1–7) |
| code appearing line by line | `code_typing` | code (1–14 lines) |
| positions in a sequence, with pointers (index 0 at D, -1 at a) | `array_pointer` | array (2–10 values) |
| one number or formula | `stat_callout` | stat |
| a title | `title_card` | title |
| a scene with a person or objects (a clerk among paper files) | `character_scene` | elements |
| something revealed or explained by a picture | `concept_reveal` | elements |
| one thing turning into another (paper files → server) | `transform_morph` | elements |
| something none of these can show | `custom` | (steps with describe) |

### Illustrated elements

- 1–10 elements, back to front. `ai` for what only a picture can show (a person, an object); `text` for any words (the image tool misspells, code doesn't); `arrow` for any arrow.
- `place` is [x, y, width, height] on the 1920×1080 frame, inside the entry's `area` and clear of its `presenter_area`. Keep elements at least 40 px apart.
- `describe` an `ai` element in 6–20 words: what it is, its pose or state, no background. Use a Brand Kit `character` id when it is the brand's character.

### Steps

- One step per thing the narration names: 1 for a `stat_callout` or `title_card`, 2–6 for most others, at most 8.
- Each element appears in exactly one step; an edge appears with or after both nodes it joins.
- **trigger**: the fewest consecutive spoken words (usually 2–6) that name what appears, occurring once in the Segment; triggers in the order they are said. Leave a trigger out only when nothing is named, and the step is spread evenly.
- **Labels**, spelled exactly, in the Instructor's terms ("Relational", not "RDBMS-based systems"):
  - in a box (flow and flowchart nodes, tree children, cycle steps, timeline events): at most 4 words, and short enough for the box. The narrower the `area` and the more boxes, the less fits. With the Default Brand Kit, a flow beside the Instructor holds about 11 characters a box with 3 boxes and 5 with 4; full screen, about 22 and 13. The builder says how many characters fit; shorten the label, use fewer boxes, or a template with more room (a list);
  - in a list, a compare side or a table cell: at most 8 words;
  - a bold line the Master Script puts on screen word for word goes in a list or compare item, as written.
  If the description can't be shown in its layout at all, tell the user: the layout is changed in Fuzentrix Master Script (it reopens Gate 2).

## Rubric: score before submitting

| # | Check | Pass when |
|---|---|---|
| 1 | Template | it can show the whole description; the Instructor's own animation idea is kept |
| 2 | Labels | box labels at most 4 words, list and compare items at most 8; spelled exactly, in the Instructor's terms; bold lines as written; nothing on screen that isn't said |
| 3 | Order | nothing appears before it is named; each step shows what its trigger names |
| 4 | Triggers | each occurs once in its Segment, in spoken order; every named moment has one |
| 5 | Elements | each in exactly one step; no edge before both its nodes |
| 6 | Steps | 1 for a stat or title card; 2–6 for most others; at most 8 |
| 7 | Placement | illustrated elements inside `area`, clear of `presenter_area`, 40 px apart |
| 8 | AI elements | each `describe` is 6–20 words about one thing, with no background (the prompt asks for a transparent one) |

**Done when:** `fz.py submit <bundle> animations <file>` accepts every animation, and the status no longer lists animations to specify.
