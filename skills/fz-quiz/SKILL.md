---
name: fz-quiz
description: "Fuzentrix Quiz: quiz questions for one or more Videos, as an Excel workbook in the LMS Quiz Template. Use when asked for a quiz on a Topic."
---

# Fuzentrix Quiz

Builds an LMS Quiz from the Final Master Scripts of one or more Videos (a **Topic**), as an Excel workbook in the LMS Quiz Template. Code and bold text stay marked in the cells (`` `code` ``, ``` blocks, `**bold**`); Fuzentrix Quiz HTML (`fz-quiz-html`) turns them into the LMS's RICH_HTML before upload. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write content as JSON; the builder checks it against every LMS import rule and either saves it or prints a numbered problem list. Fix every listed problem and run the same command again. Ids (Q03, S10) come from the builder's output; copy them exactly. If it stops with a Python error instead, that is a bug in the builder: tell the user the command and the error's last line, carry on with what doesn't need that command, and don't change the content to get round it.

To convert an existing quiz workbook to RICH_HTML, use Fuzentrix Quiz HTML instead.

## Steps

1. **Set up the Topic Bundle** in a working folder in the sandbox (for example `/mnt/data/fz/`).
   - **New Quiz:** the user uploads the Video Bundle zip of each Video in the Topic; each needs a Final Master Script. Use the Topic ID the user gives (format `course-pN-tN`, e.g. `dbms-p2-t1`; ask if missing). Run
     `fz.py topic <work>/<topic-id> --topic-id <id> --title "<title>" --video <zip> --video <zip> …`.
   - **Uploaded Topic Bundle zip:** `fz.py unpack <zip> <work>/<topic-id>`.
2. **Find the next step:** `fz.py status <bundle>`, and follow `stages/quiz.md` for it.
3. **End the turn** at Gate 3, when Done, or when the chat is getting long: `fz.py pack <bundle> <work>/<topic-id>.zip`, offer the readable preview, the workbooks and the bundle zip for download, and say what happens next.

## Always

- Questions test only what the Videos teach. Every question names the Segments it comes from.
- **One Video's questions per turn**, in the order the status gives. After submitting them, end the turn with one line of progress; the next turn starts from `fz.py status`.
- **Draft once, fill once, submit once.** Fill the whole draft in one pass and write it with a single file write (for example a Python heredoc). Never paste the JSON into the chat.
- **Read each source once** per chat: keep what `fz.py show` printed instead of running it again.
- **On a rejection, fix only the listed problems** and submit again; keep everything that passed.
- **Score before every submit** with the rubric in `stages/quiz.md`; every row must pass.
- Keep chat replies under about 150 words: what was done, what needs the user's decision, and the files to download.
