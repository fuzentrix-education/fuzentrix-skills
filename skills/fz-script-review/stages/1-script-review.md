# Stage 1: Script Review

Goal: every line has the right Line Role, and every problem that would make the Video wrong, confusing or off-guideline is a Finding the Instructor can accept with one word.

Before the first Chunk, read `references/telugu-english.md` (how to read the script, its markers, and how to write in the Instructor's style) and `references/review-examples.md` (Line Roles and Findings on the DBMS and Strings scripts). Read each once per chat.

## For each Chunk the status names (one Chunk per turn)

1. Read it once: `fz.py show <bundle> chunk <Cxx>`. Tags such as `‹bold›`, `‹slide›`, `‹visual›`, `‹animation-start›` mark the Instructor's own formatting and markers.
2. Create the draft: `fz.py draft <bundle> review <Cxx> <file>`. It lists every line with its Line Role blank. `fz.py schema review` gives the format of Findings, `code_checks` and `points_to_check`.
3. Fill in the whole draft in one pass, then write it to the file in one go:
   - a **Line Role** for every line (table below);
   - the **Findings** (tables below);
   - `code_checks`: one per code snippet. Run every Python snippet of the Chunk in **one** sandbox run and compare with the script's `Output:`. A snippet the Instructor shows on purpose as an error (`message = 'I'm Durga'`) passes when it really raises that error.
4. Score it against the rubric at the end of this file. Fix every failed check.
5. Submit once: `fz.py submit <bundle> review <file>`. If the builder lists problems, fix only those and submit again.

### Line Roles

| The line is | Role |
|---|---|
| words the Instructor says to camera, including list items they read out and English definitions | `spoken` |
| a title, section label or slide marker: `Introduction`, `Slide – 6 String Indexing`, `Output:`, `Example:` | `heading` |
| a name before speech: `Swara:` | `speaker_label` |
| `[Visual: …]`, `Animation Start …`, `Animation End` | `stage_direction` |
| an instruction to designers or editors: `(Blod lo vunayii Slide lo place cheyali)` | `note_to_team` |
| code, program output, separators, symbol tables, labels with no verb (`Outer quotes → Double Quotes " "`) | `slide_only` |
| a rough draft or repeat of something said elsewhere | `duplicate` |
| could be spoken or shown only | `spoken`, and name the lines in `points_to_check` |

### Findings: which category

| The problem | Category |
|---|---|
| a false or outdated fact, definition, number or date; an overstatement ("the one and only solution") | `technical` |
| code that doesn't run, or prints something other than the script's `Output:`; a problem statement that contradicts its test case | `code` |
| a concept used before it is explained; a missing bridge; examples that disagree (10,000 students, then "lakshala mandi") | `flow` |
| a Video Section missing or out of order; an agenda or summary that doesn't match what is taught | `guideline` |
| broken words in a spoken or on-screen line: "entiinformation", "ndustry", "fst … recupt" | `hygiene` |

### Findings: which severity

| Effect on the student | Severity |
|---|---|
| learns something false about the topic itself (wrong definition, wrong output, code shown as working that fails) | `critical` |
| a false side fact (history, a famous first), a missing hook, agenda or summary, a promise not kept, an exercise that can't be solved as written | `major` |
| a slip read aloud, inconsistent example numbers, an overstatement, a small imprecision | `minor` |

### What makes a Finding good

- **One Finding per line.** All the slips in one line are one Finding.
- `quote`: the 2–10 exact words that show the problem, copied from the line.
- `problem`: one sentence on what is wrong; for a technical Finding, the correct fact and how you know it (the sandbox output, or the established source).
- `suggestion`: one sentence on the fix.
- `fix_text`: the whole corrected line, whenever the fix changes what is said or shown: in the Instructor's style (`references/telugu-english.md`), within about 30% of the original length unless the Finding is about removing words, changing only what the Finding is about. `""` deletes the line.
- **A missing line** (code whose `Output:` needs a `print`): `after_line` (the line it follows) instead of `line` and `quote`, and the line to add as `fix_text`. It is shown only when it follows a `slide_only` line, otherwise spoken; `role` (`spoken` or `slide_only`) chooses.
- **Facts:** check them against what you know for certain and against the sandbox. When you can't be sure, ask in `points_to_check` instead of making a Finding.
- Flag only what fits a row of the category table. Spelling variants of Telugu words, typos in headings, and style you would merely write differently are not Findings.

## After the last Chunk: the whole-script overview

1. Read the guidelines once: `fz.py show <bundle> guidelines`, and the whole script: `fz.py show <bundle> lines`.
2. Walk the eight Video Sections in order, noting for yourself where each starts or that it is missing (nothing to submit for this).

   | Section | Pass when |
   |---|---|
   | Hook | first, a real-life question or scenario, at most about 45 spoken words (20 s) |
   | Intro | "welcome to Fuzentrix", the Instructor's name, the topic in one line |
   | Recap | 2–3 points from the previous session; not needed in a course's first Video (say so in `points_to_check`) |
   | Agenda | 3–5 points |
   | Explanation | every agenda point is taught: example → concept → definition → technical example |
   | Summary | a checklist matching the agenda point for point |
   | Teaser / fun fact | optional; every fact in it checked |
   | Outro | next session's topic and a goodbye |

3. Each missing or failing Section is a `guideline` Finding: `after_line` where it belongs, and `fix_text` with a line or two in the Instructor's style that the Instructor can accept as it is. When it needs facts only the Instructor has (the next session's topic), write your best guess and ask in `points_to_check`.
4. Check every promise ("Next session lo…", summary items, "we'll see") against what is taught. A summary item never taught is a `major` Finding.
5. Get the format (`fz.py schema review-overview`), submit once: `fz.py submit <bundle> review-overview <file>`, then build the report: `fz.py build <bundle> review`.

## Rubric: score before every submit

Count with a short Python script over your JSON where you can. Every row must pass.

| # | Check | Pass when |
|---|---|---|
| 1 | Line Roles | every line has one; no line the Instructor says is anything but `spoken`; every line in `points_to_check` is marked `spoken` |
| 2 | Markers | every `[Visual: …]` and `Animation Start`/`End` is `stage_direction`; every slide marker is `heading` |
| 3 | Facts | every number, date, "first", "only" and definition in a spoken line was checked; each wrong one is a Finding with the correct fact |
| 4 | Code | every snippet has a `code_check`; every Python snippet is `run`; every mismatch with its `Output:` is a Finding |
| 5 | Slips | every broken word in a spoken line is in a Finding; no Finding is about a Telugu spelling variant or a heading |
| 6 | Findings | each has one exact `quote`, a one-sentence `problem` and `suggestion`; `fix_text` whenever the words change |
| 7 | Style | every `fix_text` is in English letters, keeps the technical terms in English, and is within about 30% of the original length (unless it removes words) |
| 8 | Severity | matches the severity table; `critical` only for false teaching about the topic itself |
| 9 | Overview | all eight Sections walked; agenda and summary compared point for point; every promise checked |
| 10 | Points to check | at most 5 per submission, each a question the Instructor can answer in a few words |

A 700–900-word script usually has 5–12 Findings. With none, or more than 20, go over the tables again before submitting.

**Done when:** `fz.py build <bundle> review` succeeds and the status says "Next: Gate 1".
