# Gate 1 and Script Changes: the Instructor approves the Reviewed Script

## Presenting the review

1. Offer `01_review/review_report.html` (and `.md`) for download.
2. In chat, give a short summary: the Points to check, then the Findings grouped by severity (id, line, one-line problem). Include the list of lines that will not be spoken, so the Instructor can correct a Line Role.
3. Ask the Instructor to accept or reject each Finding ("accept all", or "accept all except F004", is fine), and whether they want to change any of their own wording.

## Script Changes: the Instructor changes their words

Use this whenever the Instructor wants different words: now, or later, even after the Master Script is written.

1. Start from the current list: `fz.py draft <bundle> script-changes all <file>`. Add the new changes and keep every earlier change that is still wanted, because the submission replaces the whole list. Format: `fz.py schema script-changes`.
   - To change a line, give `line` and its new `text`. `""` deletes the line.
   - To add a line, give `after_line` and `text`.
2. Use the Instructor's words exactly as they give them. When they describe a change instead ("make the hook shorter"), write it in their own Telugu-English style and show it to them before submitting.
3. Submit: `fz.py submit <bundle> script-changes <file>`. Gate 1 reopens, so the Instructor approves again. If a Master Script exists, it goes back to Gate 2, and Fuzentrix Master Script updates the Segments whose words changed.

A different replacement for an accepted Finding can also be given at Gate 1, as `fix_text`.

## Recording Gate 1

1. When the Instructor approves, write the decisions (`fz.py schema gate1`) with their name as `approver`, and record them: `fz.py gate <bundle> 1 <file>`. To approve again after Script Changes, with the same Findings, `approver` is enough: the earlier decisions are kept.
2. Offer `01_review/reviewed_script.html`: the script exactly as approved, with every change marked.
3. Pack the bundle. Recommend continuing with Fuzentrix Master Script in a new chat with the bundle zip. If a Master Script already exists, name the Master Script Chunks it must update (the status's `fz-master-script` line).

## Self-check checklist

- Every decision on a Finding comes from the Instructor, not an assumption.
- Every Script Change is in the Instructor's own words, or wording they confirmed, on the right line.
- No earlier Script Change was dropped from the list by mistake.

**Done when:** `fz.py gate <bundle> 1 <file>` succeeds and the status's `fz-script-review` line says Done.
