---
name: fz-master-script
description: "Fuzentrix Master Script: from a Video's Reviewed Script, the Master Script (narration, slide plan, Visual Events), its edits and approval. Use after Script Review, for edits, or approving it."
---

# Fuzentrix Master Script

Builds a Video's **Master Script** from its Reviewed Script (approved at Gate 1 in Fuzentrix Script Review): what is said, what is on each slide, and every Visual Event. Then:
1. **edits** in plain language;
2. **Gate 2**: the Content Lead approves, and the Master Script becomes Final.

Slides (`fz-slides`), visuals (`fz-visuals`) and the teleprompter (`fz-teleprompter`) are all built from the Final Master Script.

All work lives in a **Video Bundle**: a folder, zipped for download and uploaded again to continue. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. You write content as JSON; the builder checks it and either saves it or prints a numbered problem list. Fix every listed problem and run the same command again. Ids (L12, M01, S04, F003, SC01) come from the builder's output; copy them exactly.

## Steps

1. **Get the Video Bundle.** It needs a Reviewed Script (from Fuzentrix Script Review). If the bundle is already in this chat's sandbox, use it; otherwise ask the user to upload the bundle zip and run `fz.py unpack <zip> <work>/<video-id>`. A raw Instructor Script is reviewed first, with Fuzentrix Script Review.
2. **Find the next step:** `fz.py status <bundle>`, and read the `fz-master-script` line. "Waiting for the Reviewed Script" means the Instructor approves it first, in Fuzentrix Script Review.
3. **Read only the stage file for that step**, and follow it until its "Done when" is met:
   - the Master Script plan, a Master Script Chunk, or updating one → `stages/master-script.md`
   - Gate 2, or any edit the user asks for → `stages/gate-2-and-edits.md`
4. **End the turn** at Gate 2, when the Master Script is Final, or when the chat is getting long: run `fz.py pack <bundle> <work>/<video-id>.zip`, offer the readable files and the bundle zip for download, and say what happens next. Once Final, the next skills are Fuzentrix Slides, Visuals and Teleprompter.

## Always

- The spoken words are the Reviewed Script's, exactly. A change to what the Instructor says is a Script Change, made in Fuzentrix Script Review and approved by the Instructor; this skill then updates the Segments it touches.
- Long scripts are handled one Chunk per turn, in the order the status gives.
- **Self-check before every submit:** re-read your JSON against the stage's checklist and fix what you find. Anything you cannot resolve goes in `points_to_check`, so the person at the Gate sees it.
- Keep chat replies short: what was done, what needs the user's decision, and the files to download.
