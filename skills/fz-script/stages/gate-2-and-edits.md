# Gate 2, and edits to the Master Script

## Presenting for approval

1. Offer `02_master/master_script.html` (and `.md`) for download. Its **Slide plan** lists exactly what will be on every slide.
2. In chat: the Points to check, then a short outline (Segments with their titles, slides and Visual Events).
3. Ask the Content Lead to approve, or to describe changes in plain language.

## Applying an edit

1. Find the Segment(s) the edit touches in `02_master/master_script.md`, and their Master Script Chunk (`fz.py show <bundle> segments <Mxx>`).
2. Rewrite that whole Chunk's JSON from `02_master/chunks/<Mxx>.json` with the change, self-check it, and `fz.py submit <bundle> master <file>`. Then `fz.py build <bundle> master`.
3. Changing what the Instructor **says** goes through the Instructor:
   - add the change as a Finding with `fix_text` (resubmit that Chunk's review, then `fz.py build <bundle> review`);
   - record Gate 1 again, with the earlier decisions from `01_review/gate1.json` plus the new one;
   - then update the Master Script Chunk.
4. Tell the user what changed. A change to a Final Master Script reopens Gate 2; the status shows it.

## Recording approval

When the Content Lead approves, write the approval (`fz.py schema gate2`) and record it: `fz.py gate <bundle> 2 <file>`.

**Done when:** `fz.py gate <bundle> 2 <file>` succeeds and the status's `fz-script` line says Done. Then tell the user the Master Script is Final, and that Fuzentrix Slides, Visuals and Teleprompter can now build from it, in this chat or a new one.
