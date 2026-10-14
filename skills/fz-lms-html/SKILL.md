---
name: fz-lms-html
description: "Fuzentrix LMS HTML for coding problems: Problem Statement, Solution, Test Cases, Hints, Editorial. Use when asked for /lms content."
---

# Fuzentrix LMS HTML

Writes paste-ready LMS HTML for a coding problem: exactly the sections the user asks for, from Problem Statement, Solution, Test Cases, Test Case Explanation, Hints and Editorial.

Every file is built by `scripts/fz.py` in this skill's folder: `python <skill folder>/scripts/fz.py <command>`.

## Steps

1. **Note exactly which sections the user asked for.** "Give me the Problem Statement" means only `problem_statement`.
2. **Write the content as JSON** (`fz.py schema lms-html`):
   - Keep every requirement, example, constraint, formula and code detail the user supplied exactly as given.
   - Add a `check_solution` in Python whenever there are examples or test cases. It is never shown, and it proves the expected outputs are right.
   - Make test cases cover the edge cases the constraints allow, such as the smallest input, the largest input, and repeated values.
3. **Build:** `fz.py lms-html <file> <work>/lms`. The builder:
   - rejects any section that wasn't requested and any requested section that is missing;
   - runs the Python solution on every example and test case.
   Fix every problem it lists and build again.
4. **Reply with the HTML** from the built file, ready to paste, plus the file for download. Add no commentary unless the user asks for an explanation.

**Done when:** the build succeeds and the checks line says the examples and test cases passed (or that there is no Python solution to run them against).
