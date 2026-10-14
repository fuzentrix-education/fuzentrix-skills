# Stage 1: Script Review

Goal: find everything that would make the Video wrong, confusing or off-guideline, and give every line a Line Role.

## For each Chunk the status names

1. Read it: `fz.py show <bundle> chunk <Cxx>`. Tags such as `‹bold›`, `‹slide›`, `‹visual›`, `‹animation-start›` mark the Instructor's own formatting and markers.
2. Start from the draft: `fz.py draft <bundle> review <Cxx> <file>`. It lists every line with its Line Role left blank. `fz.py schema review` explains each field.
3. Give **every line a Line Role**:
   - `spoken`: the Instructor says it to camera (most lines).
   - `heading`: titles such as "Introduction" or "Conclusion & The Mind-Blowing Fact"; `Slide – 2 …` lines.
   - `speaker_label`: "Swara:".
   - `stage_direction`: `[Visual: …]`, `Animation Start …`, `Animation End`.
   - `note_to_team`: instructions to designers or editors, e.g. "(Blod lo vunayii Slide lo place cheyali)".
   - `slide_only`: content shown but not read aloud: code listings, `Output:` blocks, separator lines, arrow notes such as "Outer quotes → Double Quotes".
   - `duplicate`: a repeated or rough draft of something said elsewhere.
4. Write **Findings**, each quoting the exact words of its line:
   - `technical`: wrong facts, outdated information, wrong code or outputs, misleading simplifications. Run Python snippets in the sandbox when you can and compare the real output; mark each snippet in `code_checks` as `run` or `read_only`.
   - `flow`: a concept used before it is explained, a missing bridge, a jump in difficulty, an analogy that breaks.
   - `hygiene`: broken or misspelled words that will be read aloud or shown (e.g. "entiinformation"), leftover drafts.
   - When the fix changes what is said, give `fix_text`: the corrected line in the Instructor's own Telugu-English style. `""` means delete the line.
5. Self-check, then `fz.py submit <bundle> review <file>`.

## After the last Chunk: the whole-script overview

1. Read the guidelines: `fz.py show <bundle> guidelines`, and the whole script: `fz.py show <bundle> lines`.
2. Check the Video against the guidelines: hook, intro, recap, agenda, explanation, summary, outro. Check every promise ("we'll cover X", summary items) is actually covered, and that the agenda and summary match.
3. Something missing (e.g. no agenda) is a Finding with `after_line`: the line it should follow. Get the format: `fz.py schema review-overview`, then `fz.py submit <bundle> review-overview <file>`.
4. Build the report: `fz.py build <bundle> review`.

## Self-check checklist

- Every Finding is correct, quotes the right line, and has a sensible severity (`critical` = would teach something false).
- No agenda or summary promise is missed.
- Every code snippet is marked `run` or `read_only`.
- Nothing the Instructor says to camera is marked as anything other than `spoken`.

**Done when:** `fz.py build <bundle> review` succeeds and the status says "Next: Gate 1".
