---
name: fz-coding-problem-html
description: "Fuzentrix Coding Problem HTML: converts a given coding problem (statement, solution, test cases, hints, editorial) into the LMS's HTML, word for word. Use when a problem goes into the LMS."
---

# Fuzentrix Coding Problem HTML

Converts a coding problem the user **gives** (pasted, or attached as `.docx`, `.md`, `.txt` or `.pdf`) into LMS-ready HTML: the Problem Statement, Solution, Test Cases, Test Case Explanation, Hints and Editorial it contains, in the form the LMS keeps. It writes nothing new: every word comes from the given problem, and all of it is used. The builder checks both.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`. If it prints a numbered problem list, fix every problem and run the same command again.

## Steps

1. **Get the problem.** If the user pasted it, save it as a `.md` file in the sandbox exactly as given. For code, prefer `.docx`, `.md` or `.txt`; a PDF loses indentation.
2. **Read it:** `fz.py coding-html draft <problem file> <file>`. It lists the problem line by line (L1, L2…), with indentation kept.
3. **Place it into sections** in that file (`fz.py schema coding-html`):
   - Copy each piece's exact words into its field: description, input and output format, constraints, examples, solution code, test cases, hints, editorial. You may add `` `code` `` and `**bold**` marks; change no words.
   - Fill only the sections the problem has. If the user wants only some sections, list them in `sections`.
   - List in `skipped_lines` any line that is only a heading (such as the problem's title line). Labels like "Input Format:" or "Example 1:" need no listing.
   - Give `title` (it names the file) and the solution's `language`.
4. **Build:** `fz.py coding-html build <file> <problem file> <work>/lms`. Add `--run` when the problem includes a Python solution: it runs it on the given examples and test cases and reports anything that fails. Tell the user what it reports; never change the content to make it pass.
   Use the user's LMS rules when they attach their Configuration Pack (`--config <pack zip>`); otherwise the DRAFT rules are used, and the output says so.
5. Reply with the HTML from the built file, ready to paste, plus the file for download. If the problem has images, remind the user to attach them when uploading.

**Done when:** the build succeeds.
