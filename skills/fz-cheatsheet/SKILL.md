---
name: fz-cheatsheet
description: "Fuzentrix Cheatsheet: an interactive LMS page with images for one or more Videos. Use when asked for a cheatsheet or revision page for a Topic."
---

# Fuzentrix Cheatsheet

Builds a revision Cheatsheet for a **Topic** (one or more Videos) from their Final Master Scripts: LMS-ready HTML that keeps to the LMS's tag rules, in the Brand Kit's colours where the LMS allows them, with click-to-reveal checks where it keeps them; its images, made separately; and a map of where each image goes. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write the content as typed blocks in JSON; the builder checks it (sources, key terms, images, voice) and renders the HTML. If it prints a numbered problem list, fix every problem and run the same command again. If it stops with a Python error instead, that is a bug in the builder: tell the user the command and the error's last line, carry on with what doesn't need that command, and don't change the content to get round it.

## Steps

1. **Set up the Topic Bundle** in a working folder in the sandbox (for example `/mnt/data/fz/`).
   - **New Cheatsheet:** the user uploads the Video Bundle zip of each Video; each needs a Final Master Script. Use the Topic ID the user gives (format `course-pN-tN`, e.g. `dbms-p2-t1`; ask if missing): `fz.py topic <work>/<topic-id> --topic-id <id> --title "<title>" --video <zip> --video <zip> …`.
   - **Uploaded Topic Bundle zip** (for example one that already has its Quiz): `fz.py unpack <zip> <work>/<topic-id>`.
2. **Find the next step:** `fz.py status <bundle>`. The Cheatsheet line names it. "Choose a Brand Kit" means: follow `references/brand-kit.md` (the cheatsheet's colours, icons and image style come from it). Otherwise follow `stages/cheatsheet.md`.
3. **End the turn** at Gate 3 or when Done: `fz.py pack <bundle> <work>/<topic-id>.zip`, offer `cheatsheet/preview.html`, the HTML, the images and the bundle zip for download, and say what happens next.

## Always

- The Cheatsheet teaches only what the Videos teach. Every section names the Segments it summarises.
- **Draft once, fill once, submit once.** Fill the whole draft in one pass and write it with a single file write (for example a Python heredoc). Never paste the JSON into the chat.
- **Read each source once** per chat: keep what `fz.py show` printed instead of running it again.
- **On a rejection, fix only the listed problems** and submit again; keep everything that passed.
- **Score before submitting** with the rubric in `stages/cheatsheet.md`; every row must pass.
- **Build once**, after the images are saved: from the moment the Cheatsheet is submitted, the status lists the images still to generate.
- Keep chat replies under about 150 words: what was done, what needs the user's decision, and the files to download.
