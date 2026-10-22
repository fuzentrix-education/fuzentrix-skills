---
name: fz-visuals
description: "Fuzentrix Visuals: a Video's Editor Kit: images, code-drawn diagrams and each animation's layers, frames and step sheet. Use for a Video's visuals, animations or editor kit."
---

# Fuzentrix Visuals

Builds a Video's **Editor Kit**: everything the Video Editor needs to edit it in Premiere without AI. Every file is named after its Premiere marker, in the Brand Kit's style:
- **Images:** generated with this app's image tool.
- **Diagrams:** drawn by code, so the text is exact and they look the same every time.
- **Animations:** for each one, a transparent full-frame layer per element, a frame for each step, a storyboard, a step sheet timed from the narration, and `spec.json` for the motion-animation workflow.
- **Storyboards:** optional AI sketches, for animations code can't draw.

Terms are defined in `references/glossary.md`.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. If the builder prints a numbered problem list, fix every problem and run the same command again.

## Steps

1. **Get the Video Bundle.** It needs a Final Master Script (from Fuzentrix Master Script). If the bundle is already in this chat's sandbox, use it; otherwise ask the user to upload the bundle zip and run `fz.py unpack <zip> <work>/<video-id>`.
2. Check `fz.py status <bundle>`, `fz-visuals` line, for what is still needed. "Choose a Brand Kit" means: follow `references/brand-kit.md`. Images, diagrams and animations take their style, characters, colours and fonts from it.
3. **Diagrams** (kind `diagram`):
   1. Start from `fz.py draft <bundle> diagrams all <file>`. Each entry carries its Visual Event's description.
   2. For each, choose the type that shows it exactly (`fz.py schema diagrams`). Use the Instructor's own terms and short labels.
   3. Only if no type can show it, use type `image` with a prompt; it is then generated like the images below.
   4. Submit: `fz.py submit <bundle> diagrams <file>`.
4. **Animations** (kind `animation`): follow `stages/animations.md`.
5. **Images** (kind `image`, and any `image`-type diagram):
   1. Run `fz.py show <bundle> image-prompts`. Each entry gives the file to save, the size, and a ready prompt in the Brand Kit's style.
   2. Generate each with this app's image tool and save it under exactly that path.
   3. Check the labels are spelled correctly; regenerate if not.
6. **Storyboards** (optional; for `custom` animations): when the user wants them, `fz.py show <bundle> storyboard-prompts`, then generate and save each the same way.
7. **Build:** `fz.py build <bundle> visuals`. It:
   - checks every required image is present and large enough;
   - draws the diagrams and every animation's layers, frames, storyboard and step sheet (SVG, plus PNG where this sandbox can draw it);
   - writes `editor_kit/visuals.html`, a gallery;
   - refreshes the editor guide, the Premiere markers (one per animation step too) and `brand/` (logos, fonts, colours).
8. If any slide uses the `image` layout, tell the user to rebuild the slides with Fuzentrix Slides so they pick up the images.
9. Pack the bundle (`fz.py pack <bundle> <work>/<video-id>.zip`). For the Video Editor, also run `fz.py pack-editor <bundle> <work>/<video-id>_editor_kit.zip`. Offer both.

If this app cannot generate images, say so. Diagrams and code-drawn animations still work, and an image Visual Event can be removed through Fuzentrix Master Script.

**Done when:** the build succeeds and the status's `fz-visuals` line says Done.
