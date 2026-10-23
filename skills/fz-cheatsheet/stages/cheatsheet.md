# Cheatsheet

Before writing, read `references/cheatsheet-examples.md` (sections for the DBMS and Strings Videos) and `references/telugu-english.md` (for reading the Videos' words). Read each once per chat.

## Write it

1. Read what each Video teaches, once: `fz.py show <bundle> sources <video id>` for every Video in the Topic.
2. Create the draft once: `fz.py draft <bundle> cheatsheet all <file>`. It has a section per Video with its source Segments, and the key terms the Cheatsheet must cover. `fz.py schema cheatsheet` explains every block type.
3. Plan the sections: usually one per main idea, 3–7 for one Video, each citing the Segments it summarises. Order them as the Videos teach.
4. Write every section in one pass, the way a good teacher's revision notes read (tables and bars below). Run every `code` block in **one** sandbox run.
5. Write the `intro` and `quick_revision` last.
6. Score it against the rubric. Fix every failed check.
7. Submit once: `fz.py submit <bundle> cheatsheet <file>`.
8. **Images:** `fz.py show <bundle> cheatsheet-image-prompts` once; generate them one after another in this turn, saving each under exactly its name. Check every label is spelled exactly; regenerate once if not.

### Which block

| The content | Block |
|---|---|
| the idea itself, said plainly | `paragraph` (or `key_idea` when it is the one line to remember) |
| any comparison: data vs information, single vs double quotes, positive vs negative index | `table` |
| anything a student types | `code` (with its `language`) |
| the Instructor's own worked example (Rahul's receipt, the name Durga) | `example` |
| a list of parts or steps (the 4 types of DBMS) | `bullets` |
| what students get wrong | `mistakes` |
| a check the student answers before looking | `reveal` |
| a structure or flow a picture shows faster than words | `image` |

### Bars

- **Section:** 2–6 blocks. The first block is the idea itself: a definition, a table or the Instructor's example, never a lead-in.
- **paragraph:** at most 50 words. **key_idea:** at most 20 words, at most one per section.
- **bullets:** at most 6 items, each at most 15 words.
- **table:** at most 4 columns and 6 rows; cells at most 8 words.
- **code:** at most 12 lines, exactly as the Video shows it or follows from it, and run.
- **mistakes:** 1–3 items, each a real misconception from the Video's topic, written as the wrong belief and the truth, at most 20 words. At least one `mistakes` block in the Cheatsheet.
- **reveal:** in at least 3 of every 5 sections; the question answerable from that section; the answer at most 25 words.
- **image:** at most one per section and 4 in all, only where a picture explains faster; `prompt` 15–40 words naming every label; `alt` 5–15 words saying what it shows; `caption` at most 12 words.
- **intro:** 1–2 sentences, at most 35 words: what the page covers.
- **quick_revision:** 4–8 lines, each at most 12 words, together naming every key term.
- **Voice:** short, concrete sentences in English with the Instructor's examples; facts stated directly. Write in Fuzentrix markup: `` `code` `` and `**bold**` inside text.

## Build and Gate 3

1. `fz.py build <bundle> cheatsheet` checks the HTML against the LMS HTML Policy and writes:
   - `cheatsheet/<topic>_cheatsheet.html`, the HTML to paste into the LMS, in the Brand Kit's colours as far as the LMS keeps them;
   - `<topic>_theme.css`, when the LMS keeps only `fz-*` classes: the LMS team installs it once;
   - `preview.html`, with the images in place;
   - `insertion_map.md`: each image's placeholder and file, to attach when uploading.

   Tell the user what the build says the LMS rules leave out (such as click-to-reveal), and which rules it used.
2. Offer `preview.html` and the images, and ask the Content Lead to approve or request changes. A change means editing the JSON in `cheatsheet/cheatsheet.json`, resubmitting it and rebuilding.
3. When approved: `fz.py gate <bundle> 3 <file>` with `"deliverable": "cheatsheet"` (`fz.py schema gate3`). Every image must be generated first.

## Rubric: score before submitting

Count with a short Python script over your JSON. Every row must pass.

| # | Check | Pass when |
|---|---|---|
| 1 | Sources | every fact is in the Segments its section cites; nothing added |
| 2 | Key terms | every key term covered and defined as the Instructor defines it |
| 3 | Openings | each section's first block is the idea itself |
| 4 | Block choice | every comparison is a table; everything typed is a `code` block, run |
| 5 | Lengths | every block within its bar above |
| 6 | Mistakes | at least one block; each item a real wrong belief and its truth |
| 7 | Reveals | in at least 3 of every 5 sections, answerable from the section |
| 8 | Images | at most one per section and 4 in all; prompt names every label; alt says what it shows |
| 9 | Revision | `quick_revision` 4–8 short lines naming every key term |
| 10 | Voice | no generic openers or padding; no point made twice |

**Done when:** Gate 3 is recorded for the cheatsheet and the status says "Cheatsheet · Done".
