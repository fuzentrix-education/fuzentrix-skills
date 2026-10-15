# Stage 2: Master Script

Goal: a line-by-line plan of the finished Video: what is said, what is on screen, and every Visual Event. It is written in two steps: the Segment plan, then the Segments one Master Script Chunk at a time.

## Step 1: the Segment plan

1. Read `fz.py show <bundle> lines` and `fz.py show <bundle> guidelines`, plus the accepted Findings in `01_review/review_report.md`.
2. Split the Video into **Segments**: each is a stretch that shares one Slide, usually one idea. Give each a Video Section (hook, intro, recap, agenda, explanation, summary, teaser, outro) and a short title. A heading or marker line belongs to the Segment it introduces. Segments cover every line once, in order.
3. Add the title, agenda, learning objectives and key terms. Format: `fz.py schema plan`. Submit: `fz.py submit <bundle> plan <file>`.

## Step 2: each Master Script Chunk the status names

1. Read it: `fz.py show <bundle> segments <Mxx>`. It lists each Segment's lines with their Line Roles, and any accepted Findings with their replacement text.
2. Start from the draft: `fz.py draft <bundle> master <Mxx> <file>`. Its `spoken` lines are already exact (accepted replacements applied, added lines in place, deleted lines left out). Keep them as they are. `fz.py schema master` explains each field. For each Segment, fill in:
   - `meaning_en`: what is said, in plain English.
   - `slide`: what goes on this Segment's slide, in English, taken from what is said. Pick the layout and follow its limits in `references/slide-layouts.md`. The Content Lead approves these slides at Gate 2 through the Slide plan, so get them right here.
   - `visual_events`: an animation, diagram, image or code reveal wherever it makes the idea clearer, and always for the Instructor's own `[Visual: …]` and `Animation Start … End` ideas. A camera, music or sound cue is kind `direction`. A structure the student should see (a flow, table, hierarchy or comparison) is kind `diagram`; describe exactly what it shows. Fuzentrix Visuals draws it later. `trigger` is the exact spoken words where it starts. Suggest an Animation Template when one fits: `title_card`, `agenda_build`, `concept_reveal`, `flow`, `transform_morph`, `table_build`, `code_typing`, `compare_split`, `list_build`, `timeline`, `tree_graph`, `array_pointer`, `character_scene`, `stat_callout`. Aim for a visual change every 20–30 seconds of speech.
3. Self-check, then `fz.py submit <bundle> master <file>`.

## Step 3: build

Run `fz.py build <bundle> master`. It writes `02_master/master.json`, `master_script.md` and `master_script.html`.

## Self-check checklist

- Approved Finding fixes are applied, and rejected ones are not.
- Slide text and Visual Events are faithful to their `source_lines`, with no invented facts or examples.
- `meaning_en` matches the narration, and the slide agrees with what is said.
- Each Visual Event shows what is being said at its trigger.
- Code on slides is correct (run it in the sandbox when you can).
- Agenda, explanation and summary agree.

**Done when:** `fz.py build <bundle> master` succeeds and the status says "Next: Gate 2".
