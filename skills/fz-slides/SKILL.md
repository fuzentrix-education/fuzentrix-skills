---
name: fz-slides
description: "Fuzentrix Slides: editable PowerPoint slides on the Fuzentrix master, built from a Video's Final Master Script into its Editor Kit. Use when asked for the slides or PPT of a Video."
---

# Fuzentrix Slides

Builds the Video's slides: one editable slide per Segment, exactly as planned in the approved Master Script's Slide plan. The slides use the Fuzentrix master, colours and background art, and the bottom-right presenter area stays empty. They go into the Video's Editor Kit. Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. If it stops with a Python error instead, that is a bug in the builder: tell the user the command and the error's last line, carry on with what doesn't need that command, and don't change the content to get round it.

## Steps

1. **Get the Video Bundle.** It needs a Final Master Script (from Fuzentrix Master Script). If the bundle is already in this chat's sandbox, use it; otherwise ask the user to upload the bundle zip and run `fz.py unpack <zip> <work>/<video-id>`.
2. Check `fz.py status <bundle>`, `fz-slides` line. "Waiting for the Final Master Script" means the Master Script must be approved first, in Fuzentrix Master Script. "Choose a Brand Kit" means: follow `references/brand-kit.md`. The slides take their template, background, colours, fonts and label from it; a change the user asks for in the chat is made there too.
3. Run `fz.py build <bundle> slides`.
4. If it lists problems ("SL04 bullet 2 is too long…", "too many bullets"), the slide content must change in the Master Script, which reopens its approval. Tell the user exactly which slide and what is wrong, and that the fix is made with Fuzentrix Master Script. Do not edit the slides by hand around the problem.
5. Offer `editor_kit/slides/<video-id>_slides.pptx` and `slides.md` for download. Building the slides also refreshes the Editor Kit guide and markers. If the Video Editor needs slide images, they export them from PowerPoint (File → Export).
6. If Fuzentrix Visuals adds images later, run this skill again so `image` slides pick them up.
7. Pack the bundle (`fz.py pack <bundle> <work>/<video-id>.zip`) and offer the zip.

The layouts and their limits are in `references/slide-layouts.md`.

**Done when:** the build succeeds and the status's `fz-slides` line says Done.
