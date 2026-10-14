---
name: fz-script
description: "Fuzentrix Script: Script Review of an Instructor Script, then the Master Script (narration, slide plan, Visual Events) and its approval. Use for a new script, edits, or approving it."
---

# Fuzentrix Script

The first skill for every Video. It takes an Instructor Script (usually Telugu-English; `.docx`, `.pdf`, `.md` or `.txt`) through:
1. **Script Review**, then **Gate 1**: the Instructor decides on each Finding;
2. the **Master Script**: what is said, what is on each slide, every Visual Event;
3. **edits** in plain language;
4. **Gate 2**: the Content Lead approves, and the Master Script becomes Final.

Slides (`fz-slides`), visuals (`fz-visuals`) and the teleprompter (`fz-teleprompter`) are all built from the Final Master Script.

All work lives in a **Video Bundle**: a folder, zipped for download and uploaded again to continue. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write content as JSON; the builder checks it and either saves it or prints a numbered problem list. Fix every listed problem and run the same command again. Ids (L12, C02, M01, S04, F003) come from the builder's output; copy them exactly.

## Steps

1. **Set up the Video Bundle** in a working folder in the sandbox (for example `/mnt/data/fz/`).
   - **New script:** use the Video ID the user gives (format `course-pN-tN-vN`, e.g. `dbms-p2-t1-v1`; ask if missing) and the Configuration Pack the user attached or selected from Google Drive (the release `.zip`, or the `Fuzentrix Configuration` folder):
     `fz.py new <script> <work>/<video-id> --video-id <id> --title "<title>" --instructor "<name>" --config <pack>`.
     With no Configuration Pack, leave out `--config`; the bundle is then a DRAFT, and you tell the user so.
   - **Uploaded Video Bundle zip:** `fz.py unpack <zip> <work>/<video-id>`.
2. **Find the next step:** `fz.py status <bundle>`, and read the `fz-script` line.
3. **Read only the stage file for that step**, and follow it until its "Done when" is met:
   - Script Review → `stages/1-script-review.md`
   - Gate 1 → `stages/gate-1.md`
   - Master Script → `stages/2-master-script.md`
   - Gate 2, or any edit the user asks for → `stages/gate-2-and-edits.md`
4. **End the turn** at a Gate, when the Master Script is Final, or when the chat is getting long: run `fz.py pack <bundle> <work>/<video-id>.zip`, offer the readable files and the bundle zip for download, and say what happens next. After each Gate, recommend continuing in a new chat by uploading the bundle zip. Once Final, the next skills are Fuzentrix Slides, Visuals and Teleprompter.

## Always

- The Instructor's words are reproduced exactly. Only Findings the Instructor accepted at Gate 1 change them.
- Long scripts are handled one Chunk per turn, in the order the status gives.
- **Self-check before every submit:** re-read your JSON against the stage's checklist and fix what you find. Anything you cannot resolve goes in `points_to_check`, so the person at the Gate sees it.
- Keep chat replies short: what was done, what needs the user's decision, and the files to download.
