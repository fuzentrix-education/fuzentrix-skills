---
name: fz-visuals
description: "Fuzentrix Visuals: images, code-drawn diagrams and storyboards for a Video's Visual Events, saved into its Editor Pack. Use when asked for a Video's images, diagrams or storyboards."
---

# Fuzentrix Visuals

Makes the visuals named in a Video's Final Master Script and saves them into its Editor Pack, named after their Premiere markers:
- **Images:** generated with this app's image tool, in the Fuzentrix house style.
- **Diagrams:** drawn by code, so the text is exact and they look the same every time.
- **Storyboards:** optional, for animations.

Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. If the builder prints a numbered problem list, fix every problem and run the same command again.

## Steps

1. **Get the Video Bundle.** It needs a Final Master Script (from Fuzentrix Master Script). If the bundle is already in this chat's sandbox, use it; otherwise ask the user to upload the bundle zip and run `fz.py unpack <zip> <work>/<video-id>`.
2. Check `fz.py status <bundle>`, `fz-visuals` line, for what is still needed.
3. **Diagrams** (kind `diagram`):
   1. Start from `fz.py draft <bundle> diagrams all <file>`. Each entry carries its Visual Event's description.
   2. For each, choose the type that shows it exactly: `flow`, `table`, `tree` or `compare` (`fz.py schema diagrams`). Use the Instructor's own terms and short labels.
   3. Only if none of these can show it, use type `image` with a prompt; it is then generated like the images below.
   4. Submit: `fz.py submit <bundle> diagrams <file>`.
4. **Images** (kind `image`, and any `image`-type diagram):
   1. Run `fz.py show <bundle> image-prompts`. Each entry gives the file to save, the size, and a ready prompt with the house style.
   2. Generate each with this app's image tool and save it under exactly that path.
   3. Check the labels are spelled correctly; regenerate if not.
5. **Storyboards** (optional; for animations): when the user wants them, `fz.py show <bundle> storyboard-prompts`, then generate and save each the same way.
6. **Build:** `fz.py build <bundle> visuals`. It:
   - checks every required image is present and large enough;
   - draws the diagrams (SVG, plus PNG where this sandbox can draw it);
   - writes `editor_pack/visuals.html`, a gallery;
   - refreshes the Editor Pack guide and markers.
7. If any slide uses the `image` layout, tell the user to rebuild the slides with Fuzentrix Slides so they pick up the images.
8. Pack the bundle (`fz.py pack <bundle> <work>/<video-id>.zip`). For the Video Editor, also run `fz.py pack-editor <bundle> <work>/<video-id>_editor_pack.zip`. Offer both.

If this app cannot generate images, say so. Diagrams still work, and an image Visual Event can be removed through Fuzentrix Master Script.

**Done when:** the build succeeds and the status's `fz-visuals` line says Done.
