# Quiz

## Quiz Request

Turn what the user asked for into JSON: only the choices they actually stated (count, difficulty mix, question types, points, explanations for every option, code questions). Get the format with `fz.py schema quiz-request`, then `fz.py submit <bundle> quiz-request <file>`. The builder fills in Fuzentrix defaults for the rest and plans every question slot (type, difficulty, points, Video). Tell the user the final mix: `fz.py show <bundle> quiz-request`.

## Questions, one Video at a time (as the status names them)

1. Read what the Video teaches: `fz.py show <bundle> sources <video id>`.
2. Start from the draft: `fz.py draft <bundle> quiz <video id> <file>`. It holds that Video's planned slots. `fz.py schema quiz` explains each field.
3. Write each question:
   - **easy:** recall a definition or fact from the Video. **medium:** apply or explain it. **hard:** compare, spot the error, or reason about a new example.
   - One idea per question, in clear English; the Video's own examples (Rahul, the fee receipt, the college portal) make good questions.
   - Wrong options are believable mistakes a student might make, similar in length and style to the correct one.
   - Code (when the Video teaches code): mark it with backticks, and run it in the sandbox to confirm the answer.
   - Explanations say *why* the answer is correct, in one or two sentences.
4. Self-check, then `fz.py submit <bundle> quiz <file>`.

## Build and Gate 3

1. `fz.py build <bundle> quiz` writes:
   - `quiz/<topic>_quiz.xlsx` (PLAIN_TEXT) and `quiz/<topic>_quiz_html.xlsx` (RICH_HTML), both in the LMS Quiz Template;
   - `quiz/quiz_preview.html` for review.
2. Offer `quiz_preview.html` and ask the Content Lead to approve it or request changes. A change means rewriting that Video's questions and resubmitting them, then rebuilding.
3. When approved, record it: `fz.py schema gate3`, then `fz.py gate <bundle> 3 <file>` with `"deliverable": "quiz"`.

## Self-check checklist

- Each correct answer was re-derived from the Video (`answer_check`) before it was marked.
- Exactly one defensible answer for single select; no option is "almost right".
- Every question traces to its `source_segments`, with no facts the Video doesn't teach.
- No two questions test the same fact the same way.

**Done when:** Gate 3 is recorded for the quiz and the status says Done. Upload `<topic>_quiz_html.xlsx` to the LMS.
