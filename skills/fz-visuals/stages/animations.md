# Animations

Goal: for every animation Visual Event, a spec the builder turns into the Editor Kit files a Video Editor needs to build it by hand in Premiere:
- one transparent full-frame layer per element;
- a frame for each step;
- a storyboard;
- a step sheet timed from the narration;
- `spec.json`, for the motion-animation workflow.

## Write the specs

1. Start from `fz.py draft <bundle> animations all <file>`. Each entry gives the event, its suggested template, description, trigger, duration and the Segment's spoken words. Format: `fz.py schema animations`.
2. For each, choose the **template** that shows it:
   - Code draws these; write the `diagram` exactly like a diagram spec (`fz.py schema diagrams`), with the Instructor's own terms and short labels:
     - `flow` (a few boxes in a row) and `flowchart` (decisions and loops);
     - `table_build`, `tree_graph`, `compare_split`;
     - `timeline`, `cycle`, `layers`;
     - `list_build` and `agenda_build` (a list);
     - `code_typing` (code, line by line);
     - `stat_callout` (one big number), `title_card`;
     - `array_pointer` (array cells with pointers).
   - `character_scene`, `concept_reveal`, `transform_morph`: an illustrated scene. Instead of a diagram, list its `elements`, each with an `id` and a `place` ([x, y, width, height] on the 1920×1080 frame, clear of the presenter area):
     - kind `ai`: something the image tool draws alone, with `describe`, and `character` when it is one of the Brand Kit's characters;
     - kind `text`: a short caption, with `text`;
     - kind `arrow`: `from` and `to` points.
     After submitting, generate each `ai` element from `fz.py show <bundle> animation-prompts` (transparent background, or the flat key colour the prompt names) and save it under the path shown.
   - `custom`: nothing code can draw. Give each step a `describe` instead; the Video Editor builds it from the step sheet (an AI storyboard helps, see the skill's step 6).
3. Write the **steps**, 1–8 of them, in the order they appear. For every template except `custom`, each step lists in `show` the element ids it adds; every element appears in exactly one step. `fz.py schema animations` lists the ids of every diagram type (for example a flow's `node:1`, `edge:1-2`, `label:1-2`; a list's `item:1`; code's `card`, `line:1`). A wrong id is rejected with the diagram's full list.
4. Give a step a `trigger`, the exact spoken words at which it appears, when the narration names that moment. Triggers must come in the order they are said. Steps without one are spread evenly over the animation.
5. Self-check, then `fz.py submit <bundle> animations <file>`.

## Self-check checklist

- Each step shows what is being said at its trigger, and nothing appears before it is mentioned.
- Labels are short, spelled exactly, and use the Instructor's terms.
- Every element is in exactly one step.

**Done when:** `fz.py submit <bundle> animations <file>` accepts every animation, and the status no longer lists animations to specify.
