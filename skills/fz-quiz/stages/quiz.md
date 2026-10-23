# Quiz

Before writing questions, read `references/quiz-examples.md` (questions on the DBMS and Strings Videos, good and bad) and `references/telugu-english.md` (for reading the Videos' words). Read each once per chat.

## Quiz Request

Turn what the user asked for into JSON: only the choices they actually stated (count, difficulty mix, question types, points, explanations for every option, code questions). Get the format with `fz.py schema quiz-request`, then `fz.py submit <bundle> quiz-request <file>`. The builder fills in Fuzentrix defaults for the rest and plans every question slot (type, difficulty, points, Video). Tell the user the final mix: `fz.py show <bundle> quiz-request`.

## Questions, one Video per turn (as the status names them)

1. Read what the Video teaches, once: `fz.py show <bundle> sources <video id>`. List its key terms and its explanation Segments: these are what the questions cover.
2. Create the draft once: `fz.py draft <bundle> quiz <video id> <file>`. It holds that Video's planned slots. `fz.py schema quiz` explains each field.
3. Plan coverage before writing, in this order, as far as the slots go:
   1. every key term is tested (one question may test two or three terms taught in the same Segment);
   2. every explanation Segment has a question, with no Segment getting a third question while another explanation Segment has none;
   3. the remaining slots go to the Segments that teach the most.
4. Write every question in one pass (the tables and bars below). Put all the code questions' snippets through **one** sandbox run, and write the real output into `answer_check`.
5. Score it against the rubric. Fix every failed check.
6. Submit once: `fz.py submit <bundle> quiz <file>`.

### Which question for which difficulty

| Difficulty | The student must | Example |
|---|---|---|
| easy | recall a definition or fact as the Video states it | At which index does a Python String start? |
| medium | apply it to the Video's own example, or predict the output of code like the Video's | What does `print(name[-2])` print for `name = "Durga"`? |
| hard | handle a new example, tell two ideas apart, or find the error | Which line raises a SyntaxError? |

| Type | Use it for | Bar |
|---|---|---|
| SINGLE_SELECT | one defensible answer | exactly one correct option; no option "almost right" |
| MULTI_SELECT | several parts of one idea (what a DBMS does) | 2–3 correct of 4 |
| TRUE_FALSE | one clear statement | at most 20 words; true or false by the Video's own words, with no "always" or "never" traps; about half the quiz's TRUE_FALSE are true |

### What makes a question good

- **Question:** one idea; at most 30 words, not counting code. Ask it positively; when a negative can't be avoided, make it bold (`**not**`), at most one per ten questions.
- **Options:** as many as planned, real and distinct, similar in form, each between half and one and a half times the correct option's length in words (for MULTI_SELECT, the correct options' average length). Every wrong option is a mistake a student makes about this Video (counting from 1, mixing up -1 and 0, the clerk searching instead of the DBMS), never a joke or an unrelated term.
- **Code:** in Fuzentrix markup: `` `code` `` inside a sentence, a ```` ```python ```` block for whole lines. Options hold no tables or links (the LMS removes them there).
- **Explanation:** 1–2 sentences, at most 35 words, saying *why*, with the Video's example. For all_options, a wrong option's explanation names the mistake.
- **answer_check:** the Segment, the Video's words (or the sandbox output) and the reasoning, written before marking the answer.
- **Test what is taught.** Nothing from outside the Videos; not the date or name in a fun fact unless a learning objective asks for it.

## Build and Gate 3

1. `fz.py build <bundle> quiz` writes:
   - `quiz/<topic>_quiz.xlsx` in the LMS Quiz Template, with code and bold text still marked;
   - `quiz/quiz_preview.html` for review.
2. Offer `quiz_preview.html` and ask the Content Lead to approve it or request changes. A change means rewriting that Video's questions and resubmitting them, then rebuilding.
3. When approved, record it: `fz.py schema gate3`, then `fz.py gate <bundle> 3 <file>` with `"deliverable": "quiz"`.

## Rubric: score before every submit

Count with a short Python script over your JSON. Every row must pass.

| # | Check | Pass when |
|---|---|---|
| 1 | Coverage | every key term is tested; no Segment has a third question while an explanation Segment has none (as far as the slots go) |
| 2 | Difficulty | each question matches its difficulty's row |
| 3 | Answers | exactly one correct for SINGLE_SELECT and TRUE_FALSE; 2–3 of 4 for MULTI_SELECT; each re-derived in `answer_check` |
| 4 | Code | every code question was run in the sandbox; `answer_check` has the real output |
| 5 | Question | one idea, at most 30 words outside code, at most one bold negative per ten |
| 6 | Options | lengths within half to one and a half times the correct one's (MULTI_SELECT: their average); each wrong option a real mistake |
| 7 | Explanation | 1–2 sentences, at most 35 words, says why with the Video's example |
| 8 | Sources | `source_segments` name where it is taught; nothing from outside the Videos |
| 9 | Variety | no two questions test the same fact the same way |
| 10 | Markup | code marked; no tables or links in options |

**Done when:** Gate 3 is recorded for the quiz and the status says Done. Then tell the user the next step the status gives: convert it with Fuzentrix Quiz HTML before uploading, or, when nothing is marked, upload it as it is.
