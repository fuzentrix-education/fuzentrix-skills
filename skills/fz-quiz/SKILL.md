---
name: fz-quiz
description: "Fuzentrix Quiz for one or more Videos in the LMS Quiz Template. Use when asked for quiz questions on a Topic, or to convert an existing quiz workbook to RICH_HTML."
---

# Fuzentrix Quiz

Builds an LMS Quiz from the Final Master Scripts of one or more Videos (a **Topic**), or converts an existing quiz workbook to RICH_HTML. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write content as JSON; the builder checks it against every LMS import rule and either saves it or prints a numbered problem list. Fix every listed problem and run the same command again. Ids (Q03, S10) come from the builder's output; copy them exactly.

## Convert an existing quiz workbook

Run `fz.py convert-quiz <workbook.xlsx> <work>/<name>_html.xlsx`, then offer the new file for download. The original stays unchanged. Done.

## Build a new Quiz

1. **Set up the Topic Bundle** in a working folder in the sandbox (for example `/mnt/data/fz/`).
   - **New Quiz:** the user uploads the Video Bundle zip of each Video in the Topic; each needs a Final Master Script. Use the Topic ID the user gives (format `course-pN-tN`, e.g. `dbms-p2-t1`; ask if missing). Run
     `fz.py topic <work>/<topic-id> --topic-id <id> --title "<title>" --video <zip> --video <zip> …`.
   - **Uploaded Topic Bundle zip:** `fz.py unpack <zip> <work>/<topic-id>`.
2. **Find the next step:** `fz.py status <bundle>`, and follow `stages/quiz.md` for it.
3. **End the turn** at Gate 3, when Done, or when the chat is getting long: `fz.py pack <bundle> <work>/<topic-id>.zip`, offer the readable preview, the workbooks and the bundle zip for download, and say what happens next.

## Always

- Questions test only what the Videos teach. Every question names the Segments it comes from.
- **Self-check before every submit:** re-read your JSON against the checklist in `stages/quiz.md` and fix what you find.
- Keep chat replies short: what was done, what needs the user's decision, and the files to download.
