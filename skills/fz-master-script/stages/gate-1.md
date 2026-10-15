# Gate 1: the Instructor decides on the Script Review

1. Offer `01_review/review_report.html` (and `.md`) for download.
2. In chat, give a short summary: the Points to check, then the Findings grouped by severity (id, line, one-line problem). Include the list of lines that will not be spoken, so the Instructor can correct a Line Role.
3. Ask the Instructor to accept or reject each Finding. "Accept all", or "accept all except F004", is fine. They may also change a replacement line, or correct a Line Role.
4. When they answer, write the decisions (`fz.py schema gate1`), with the Instructor's name as `approver`, and record them: `fz.py gate <bundle> 1 <file>`.
5. Pack the bundle and recommend continuing the Master Script in a new chat with the bundle zip.

**Done when:** `fz.py gate <bundle> 1 <file>` succeeds and the status says "Next: Master Script plan".
