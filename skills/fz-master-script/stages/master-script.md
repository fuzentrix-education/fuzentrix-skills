# Master Script

Goal: a line-by-line plan of the finished Video: what is said, what is on screen, and every Visual Event, so that slides, visuals and the teleprompter can be built without asking anyone. It is written in two steps: the Segment plan, then the Segments one Master Script Chunk at a time.

Before the plan, read `references/telugu-english.md` (reading the script and writing meaning_en), `references/master-examples.md` (the plan and Segments for the Strings and DBMS scripts) and `references/slide-layouts.md`. Read each once per chat.

## Step 1: the Segment plan

1. Read once: `01_review/reviewed_script.md` (the approved words, with every change marked), `fz.py show <bundle> guidelines`, and `fz.py show <bundle> lines` for the line ids.
2. Split the Video into **Segments**. A Segment is a stretch that shares one slide: one idea, one Video Section.

   | Decide | Rule |
   |---|---|
   | where a Segment starts | at an Instructor slide marker (`Slide – 6 …`), a heading, or where a new idea starts |
   | how long | an explanation Segment: 40–150 spoken words (20–60 s at 140 words a minute), split where the idea changes. Shorter only for a slide students read (code and its output, a list of forms, a problem statement), where the Instructor's slide marker decides. Other Sections: as long as the Instructor makes them |
   | its Video Section | hook, intro, recap, agenda, explanation, summary, teaser, outro, in the guidelines' order |
   | heading and marker lines | belong to the Segment they introduce |
   | lines added at Gate 1 | belong to the Segment of the line they follow; lines added after the last line share its Segment (a summary and an outro added at Gate 1) |
   | its title | 2–6 words, what the student learns there ("Negative indexing", not "Slide 7") |

3. Add the Video's title; the **agenda**: the Instructor's agenda points (3–5, after Gate 1 changes) in English, as they appear on screen; 2–5 **learning objectives**, each starting with a verb a test can check (tell apart, define, explain, write, predict the output); and the **key terms**: every term the Video defines, each defined in 20 words or fewer, as the Instructor defines it.
4. Format: `fz.py schema plan`. Submit once: `fz.py submit <bundle> plan <file>`.

## Step 2: each Master Script Chunk the status names (one per turn)

1. Read it once: `fz.py show <bundle> segments <Mxx>`. It lists each Segment's lines with their Line Roles, and the accepted Findings and Script Changes with their new words.
2. Create the draft: `fz.py draft <bundle> master <Mxx> <file>`. Its `spoken` lines are already exact; keep them as they are.
3. For each Segment, fill in, in one pass:

   **meaning_en**: 1–3 sentences, at most 60 words, in plain English. Every point the narration makes, with the Instructor's names, numbers and examples.

   **slide**, following `references/slide-layouts.md`:
   - title at most 8 words; at most 5 bullets of at most 10 words each; English only;
   - every bullet comes from `source_lines`; nothing the Instructor doesn't say or show. A line added at Gate 1 has no id of its own: cite the line it follows;
   - lines the Instructor made bold go on screen word for word when they are English or code; bold Telugu-English goes on as its English meaning ("Characters sequence ni String antam." → "A String is a sequence of characters");
   - code exactly as in the Reviewed Script, with its output in `output`; at most 12 lines. A code slide shows only code and output, so labels such as `Outer quotes → Double Quotes " "` go in a Visual Event.

   **visual_events**: see the tables below. Each needs `description`: everything on screen, every label written out, in English, at most 40 words.
4. Score it against the rubric. Fix every failed check.
5. Submit once: `fz.py submit <bundle> master <file>`.

### Which Visual Event

| What is said | kind | template, or what to draw |
|---|---|---|
| steps that happen in order (request → DBMS → database) | animation | `flow` |
| steps with a decision or a loop | animation | `flowchart` |
| two things side by side (data vs information; single vs double quotes) | animation | `compare_split` |
| items named one after another (agenda points, recap points) | animation | `agenda_build`, `list_build` |
| a parent and its kinds (the 4 types of DBMS) | animation | `tree_graph` |
| rows of facts (characters and their index numbers) | animation | `table_build` |
| positions in a sequence (D u r g a with index 0–4, or -5 to -1) | animation | `array_pointer` |
| code built up line by line as it is explained | animation | `code_typing` |
| code shown whole, or a wrong version and its error | code | the code and the error, in `description` |
| one number or formula to remember ("Processed Data = Information") | animation | `stat_callout` |
| events in time | animation | `timeline` |
| something that repeats in a loop | animation | `cycle` |
| a stack of levels | animation | `layers` |
| a story moment with a person (a clerk among paper files) | animation | `character_scene` |
| one thing turning into another (paper files → a server) | animation | `transform_morph` |
| a picture beside the points (a fee receipt, an admission form) | image | the picture, its labels |
| a structure shown whole while the Instructor talks about it | diagram | the boxes and arrows, every label |
| the Video's or a part's title | animation | `title_card` |
| camera, music or sound | direction | (no layout) |

An Instructor's `[Visual: …]` or `Animation Start … End` always becomes a Visual Event, with their idea in `description` and `editor_note`. Name the parts one by one in the narration → animation; talked about as a whole → diagram or image.

### Where it sits on screen

| layout | Use when | Usual length |
|---|---|---|
| `fullscreen_cutaway` | the visual needs the whole frame: a full diagram, the Instructor's own transition | 3–10 s |
| `beside_instructor` | the Instructor keeps talking to camera while it explains: images, small diagrams | as long as the words about it |
| `overlay` | a short callout over the Instructor: a number, a label, a list item | 2–5 s |
| `slide_bg` | it builds on the slide itself: agenda points, code | the Segment |

### Timing

- **trigger**: the fewest consecutive spoken words (usually 2–6) that say what appears, and occur once in the Segment.
- **duration_sec**: about the time to say the words it covers, at 2.3 words a second; at least 3.
- **Density**: something changes on screen at least every 70 spoken words (30 s). The new slide is the first change, so a Segment of N spoken words needs at least ⌈N / 70⌉ − 1 Visual Events (any kind but `direction`): none up to 70 words, one up to 140, two up to 210. Add more only where they make the idea clearer: across the Video, at most one Visual Event per 25 spoken words, since each one is work for the Video Editor.
- **One animation at a time**: an animation's trigger comes at least (the previous one's duration × 2.3) words after the previous animation's trigger.

## Updating a Master Script Chunk

When the status says "Next: update Master Script Chunk Mxx", the Reviewed Script changed under it:

1. Create the draft: `fz.py draft <bundle> master <Mxx> <file>`: the Chunk as written, with its `spoken` lines refreshed.
2. Check `meaning_en`, the slide and every Visual Event against the new words: each `trigger` still spoken, the slide still true to what is said.
3. Score it, then `fz.py submit <bundle> master <file>`. Update every Chunk the status names before building.

## Step 3: build

Run `fz.py build <bundle> master`. It writes `02_master/master.json`, `master_script.md` and `master_script.html`.

## Rubric: score before every submit

Count with a short Python script over your JSON. Every row must pass.

| # | Check | Pass when |
|---|---|---|
| 1 | Words | `spoken` is exactly the draft's |
| 2 | Meaning | every `meaning_en` is 1–3 sentences, at most 60 words, and leaves out no point of the narration |
| 3 | Slides | titles at most 8 words; at most 5 bullets, each at most 10 words; English; every bullet traceable to `source_lines` |
| 4 | Bold | every bold English or code line is on screen word for word (slide or Visual Event); bold Telugu-English is there in English |
| 5 | Code | code on slides matches the Reviewed Script and was run in the sandbox; its `output` is the real output |
| 6 | Instructor ideas | every `[Visual: …]` and `Animation Start … End` has a Visual Event |
| 7 | Density | each Segment has at least ⌈spoken words / 70⌉ − 1 Visual Events; the Video at most one per 25 spoken words |
| 8 | Triggers | each is 2–6 words (one when that word is unique), occurs once in its Segment, and is where the thing is named |
| 9 | Overlap | no two animations run at once |
| 10 | Facts | nothing on screen that the Instructor doesn't say or show; agenda, key terms and summary agree |

**Done when:** `fz.py build <bundle> master` succeeds and the status says "Next: Gate 2".
