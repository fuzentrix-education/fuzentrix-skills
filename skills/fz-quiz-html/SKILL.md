---
name: fz-quiz-html
description: "Fuzentrix Quiz HTML: turns a quiz workbook's questions, options and explanations into the LMS's RICH_HTML, within its tag rules. Use before uploading a quiz, or for any existing quiz workbook."
---

# Fuzentrix Quiz HTML

Converts a quiz workbook in the LMS Quiz Template to RICH_HTML: every Question, Option and Option Explanation becomes HTML the LMS keeps, and its Content Format becomes RICH_HTML. Each field is checked against its own LMS rules (questions, options and explanations allow different tags); one bad cell stops the whole file, because the LMS rejects a whole import for one bad row. The original workbook stays unchanged.

It works on:
- **workbooks from Fuzentrix Quiz**: their cells already mark code and bold text, so nothing is guessed;
- **any other quiz workbook** in the LMS template: code is recognised by its look, and you can mark it more precisely first (step 3).

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. If it prints a numbered problem list, fix every problem and run the same command again. If it stops with a Python error instead, that is a bug in the builder: tell the user the command and the error's last line, carry on with what doesn't need that command, and don't change the content to get round it.

## Steps

1. **Get the workbook** the user attached (`.xlsx`). Use the LMS rules from their Configuration Pack when they attach it (`--config <pack zip>`) or from a Topic Bundle (`--bundle <bundle>`); otherwise the skill's copy of the LMS rules is used, and the output says which.
2. **Workbook from Fuzentrix Quiz:** go to step 4.
3. **Any other workbook:** mark the code the way a teacher would, so nothing is guessed:
   1. `fz.py quiz-cells <workbook> <file>` lists every question, option and explanation cell.
   2. For each cell that shows code, add to `marks` an entry `{"ref": "<sheet>!<cell>", "marked": "<the same text with marks>"}`. Use `` `code` `` for code inside a sentence (a function, a keyword, a value), ``` blocks (with the language) for whole lines of code, and `**bold**` sparingly. Mark a repeated term once, at its first mention. Change no words: a mark that changes the text is refused.
   3. Leave cells with no code out of `marks`; they are converted as they are.
4. **Convert:** `fz.py convert-quiz <workbook> <work>/<name>_html.xlsx [--marks <file>] [--config <pack> | --bundle <bundle>]`. Add `--plain <work>/<name>_plain.xlsx` if the user also wants a plain-text copy without marks.
5. Offer the RICH_HTML workbook for download, and say how many cells were converted and which LMS rules were used. If any cell is refused (for example a table inside an option), tell the user exactly which cell and why; the fix is made in the quiz, not around the rule.

**Done when:** `convert-quiz` succeeds and the user has the RICH_HTML workbook.
