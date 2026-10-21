---
name: fz-teleprompter
description: "Fuzentrix Teleprompter: only the words the Instructor speaks, from a Video's Final Master Script, as .txt, .docx and a scrolling web page. Use when asked for a teleprompter script."
---

# Fuzentrix Teleprompter

Builds the Teleprompter Script: exactly the spoken words of the Final Master Script, formatted for reading on camera. Headings, slide content, stage directions and notes to the team are left out. The builder does this alone; nothing is reworded. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`.

## Steps

1. **Get the Video Bundle.** It needs a Final Master Script (from Fuzentrix Master Script). If the bundle is already in this chat's sandbox, use it; otherwise ask the user to upload the bundle zip and run `fz.py unpack <zip> <work>/<video-id>`.
2. Run `fz.py build <bundle> teleprompter`.
3. Offer the files in `teleprompter/` for download:
   - `<video-id>_teleprompter.txt`, for any teleprompter app;
   - `.docx`, large print;
   - `.html`, a scrolling teleprompter in the browser (Play, Speed, Size, Mirror);
   - `teleprompter_report.md`.
4. Ask the Instructor to skim "Lines kept off the teleprompter" in the report. If a line there should be spoken, that is a Line Role correction: the Instructor makes it at Gate 1 in Fuzentrix Script Review, Fuzentrix Master Script updates the Segment, and then this skill runs again.
5. Pack the bundle (`fz.py pack <bundle> <work>/<video-id>.zip`) and offer the zip.

**Done when:** the build succeeds and the status's `fz-teleprompter` line says Done.
