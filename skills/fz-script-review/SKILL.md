---
name: fz-script-review
description: "Fuzentrix Script Review: checks an Instructor Script, takes the Instructor's decisions and wording changes, and gets it approved. Use for a new script or any change to what the Instructor says."
---

# Fuzentrix Script Review

The first skill for every Video. It takes an Instructor Script (usually Telugu-English; `.docx`, `.pdf`, `.md` or `.txt`) to a **Reviewed Script** the Instructor has approved:
1. **Script Review**: Findings on everything that would make the Video wrong, confusing or off-guideline, and a Line Role for every line;
2. the Instructor's decision on each Finding, and their **Script Changes**: their own changes to the wording;
3. **Gate 1**: the Instructor approves the Reviewed Script.

Fuzentrix Master Script (`fz-master-script`) builds the Master Script from the Reviewed Script. Any later change to what the Instructor says comes back here, even after the Master Script is written.

All work lives in a **Video Bundle**: a folder, zipped for download and uploaded again to continue. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write content as JSON; the builder checks it and either saves it or prints a numbered problem list. Fix every listed problem and run the same command again. Ids (L12, C02, F003, SC01) come from the builder's output; copy them exactly.

## Steps

1. **Set up the Video Bundle** in a working folder in the sandbox (for example `/mnt/data/fz/`).
   - **New script:** use the Video ID the user gives (format `course-pN-tN-vN`, e.g. `dbms-p2-t1-v1`; ask if missing) and the Configuration Pack the user attached or selected from Google Drive (the release `.zip`, or the `Fuzentrix Configuration` folder):
     `fz.py new <script> <work>/<video-id> --video-id <id> --title "<title>" --instructor "<name>" --config <pack>`.
     With no Configuration Pack, leave out `--config`; the bundle is then a DRAFT, and you tell the user so.
   - **Uploaded Video Bundle zip:** `fz.py unpack <zip> <work>/<video-id>`.
   - **A rewritten script** (a new file, not a few changes) starts a new Video Bundle with `fz.py new`, and the review starts again. If the Video already has a Master Script, tell the user it will be rebuilt too, and offer Script Changes instead for smaller edits.
2. **Find the next step:** `fz.py status <bundle>`, and read the `fz-script-review` line.
3. **Read only the stage file for that step**, and follow it until its "Done when" is met:
   - Script Review → `stages/1-script-review.md`
   - Gate 1, Script Changes, or any change to the Instructor's words → `stages/gate-1-and-changes.md`
4. **End the turn** at Gate 1, when the Reviewed Script is approved, or when the chat is getting long: run `fz.py pack <bundle> <work>/<video-id>.zip`, offer the readable files and the bundle zip for download, and say what happens next. Once approved, the next skill is Fuzentrix Master Script, in a new chat with the bundle zip.

## Always

- The Instructor's words are reproduced exactly. Only Findings the Instructor accepts and their own Script Changes change them.
- Long scripts are handled one Chunk per turn, in the order the status gives.
- **Self-check before every submit:** re-read your JSON against the stage's checklist and fix what you find. Anything you cannot resolve goes in `points_to_check`, so the Instructor sees it.
- Keep chat replies short: what was done, what needs the Instructor's decision, and the files to download.
