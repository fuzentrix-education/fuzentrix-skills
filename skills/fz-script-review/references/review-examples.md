# Script Review: worked examples

From two real scripts: **DBMS** (`dbms_intro.pdf`, Instructor Swara, 71 lines) and **Strings** (`strings_intro.docx`, Instructor Durga, 225 lines). Line ids are as `fz.py new` numbers them.

## Line Roles

| Line | Role | Why |
|---|---|---|
| DBMS L1 `DBMS Demo Video Script` | heading | the file's title |
| DBMS L12 `[Visual: Snap transition. The paper files digitally transform into a sleek server/computer graphic]` | stage_direction | the Instructor's visual idea; the Master Script turns it into a Visual Event |
| DBMS L20–L23 `* Rahul`, `* 23A91A0501`, `* CSE`, `* 85` | spoken, + point to check | example values; she may read them out or only show them |
| DBMS L29 `> Processed Data = Information` | spoken | she says the formula |
| DBMS L49 `6. so` | heading | a leftover outline number |
| DBMS L57 `Swara:` | speaker_label | |
| DBMS L71 `dbms ane software ni 1966 lo ibm vallu …` | duplicate | a rough, unpunctuated repeat of the NASA fact in L66–L67 |
| Strings L5–L7 `Continue Statement and its Syntax`, … | spoken | the recap points she reads out |
| Strings L14 `Animation Start (Name Example)`, L31 `Animation End` | stage_direction | the lines between are spoken and animated |
| Strings L22–L26 `D...`, `u...` | spoken | she spells the name aloud |
| Strings L34 `A String is a sequence of characters enclosed within quotes.` | spoken | an English definition, read aloud |
| Strings L42 `name = 'Durga'`, L43 `Output:`, L44 `Durga` | slide_only, heading, slide_only | code, its label, its output |
| Strings L65 `Slide – 4 (Blod lo vunayii Slide lo place cheyali)` | heading | a slide marker that also carries a note ("put the bold lines on the slide"); the marker wins, and the Master Script follows the note |
| Strings L70 `Outer quotes → Double Quotes " "` | slide_only | a label with no verb |
| Strings L108 `String lopala single quote unte → outside double quotes use cheyyachu.` | spoken | a sentence |
| Strings L118 `''' '''` | slide_only | shows the syntax |
| Strings L138–L139 `D u r g a` / `0 1 2 3 4` | slide_only | a table of symbols |
| Strings L141 `D → Index 0` | spoken, + point to check | she likely reads "D, index zero"; ask |

## Findings worth making

A Chunk Finding (`line` + `quote`) and an overview Finding (`after_line`):

```json
{
  "line": "L66",
  "quote": "first time 1966 lo IBM vallu",
  "category": "technical",
  "severity": "major",
  "problem": "IMS (IBM, 1966) was not the first DBMS: Charles Bachman's IDS at General Electric came earlier (about 1963–64).",
  "suggestion": "Call IMS one of the earliest and most famous DBMSs.",
  "fix_text": "Meeku telusa? Famous early DBMS lo okati aina IMS ni 1966 lo IBM vallu enduku create chesaro telusa? NASA kosam!"
}
```

```json
{
  "after_line": "L1",
  "category": "guideline",
  "severity": "major",
  "problem": "The Video opens with the intro; the guidelines need a hook of at most 20 seconds first.",
  "suggestion": "Open with a real-life question about where names and messages are stored.",
  "fix_text": "Instagram lo mee username, WhatsApp lo mee message, college form lo mee peru... ivanni Python lo ela store avutayo eppudaina alochinchara?"
}
```

More, in one line each (category · severity · quote → what the Finding says):

| Script | Finding |
|---|---|
| DBMS L14 | hygiene · minor · "entiinformation" → split the words, smooth the rough sentence: "So DBMS ante simple idea vachindi. Daaniki mundu, manam Data ante enti, Information ante enti, Database ante enti chuddam." |
| DBMS L15 | hygiene · minor · "fst miru kavakankunna recupt" → "So first, mee fee receipt lo em details unnayo chuddam."; "kavakankunna" guessed, so it goes in `points_to_check` too |
| DBMS L46 | flow · minor · "aa lakshala mandi students" → the example college has 10,000 students (L8, L30, L37); say "aa 10,000 mandi students" |
| DBMS L47 | technical · minor · "The one and only solution is DBMS." → overstatement: small data can live in plain files; "best solution DBMS" |
| DBMS L50 | hygiene · minor · "ndustry requirements" → "So, industry requirements ni batti…" |
| DBMS L62 | guideline · major · "Types & Evolution" → the summary promises Evolution, which is never taught; drop it from the summary |
| DBMS L67 | technical · major · "Eeroju manam phones lo vade tech, appudu moon landing ki vaadaru" → misleading; a true closer: IMS is still used by many banks today |
| DBMS after L7 | guideline · major · no agenda → add one line naming the four points the summary checks off |
| Strings L112 | technical · minor · "normal Strings kosam almost same" → for a String with no quotes inside, they are exactly the same: "exactly same" |
| Strings L205 | code · minor · "create a String containing the word "Python"" → the test case gives `Python` as Input, but the program creates the String itself and reads nothing; say "read a word" or drop the Input |
| Strings L221 | code · minor · "Enter Name: Durga" → the Input is `Durga`; "Enter Name:" is the prompt the program prints |
| Strings after L225 | guideline · major · `Slide – 13 Summary` has no words → a summary that checks off the three agenda points: "So friends, ee session lo manam Strings and Creation, String Indexing and Accessing Characters, inka Real World Examples nerchukunnam." |
| Strings after L225 | guideline · minor · no outro → "Next session lo manam String Slicing nerchukundam. I hope meeku ee class nachindi. Thank you!", and ask in `points_to_check` whether Slicing is next |

A line the code needs, added after the line it follows. It follows a `slide_only` line, so it is shown, not spoken:

```json
{
  "after_line": "L42",
  "category": "code",
  "severity": "minor",
  "problem": "name = 'Durga' prints nothing, so the slide's Output (L43–L44) can't come from this code.",
  "suggestion": "Add print(name) after the assignment.",
  "fix_text": "print(name)"
}
```

A code check for a snippet shown on purpose as wrong:

```json
{"lines": ["L78"], "status": "run", "note": "Raises SyntaxError: unterminated string literal, as L81 says. Not a Finding."}
```

## Not Findings

| In the script | Why not |
|---|---|
| "chestham" here, "chestam" there; "cheskundhama" | Telugu spelling varies; it reads aloud correctly |
| "Explination" (Strings L51, L72, L92) | a heading nobody reads aloud |
| `message = 'I'm Durga'` (Strings L78), `message = "He said "Hello""` (L101) | wrong on purpose: she is showing the SyntaxError |
| Two slide markers numbered 5 (Strings L85, L114) | slide numbering for the team; the slides are planned from the Segments, not these numbers |
| "Instagram", "Swiggy" | real apps students know: a good hook |

## Points to check

Short questions the Instructor answers in a few words:

- DBMS L20–L23: will you read the example values (Rahul, 23A91A0501, CSE, 85) aloud, or only show them?
- DBMS L15: "kavakankunna" was read as "fee"; is "mee fee receipt" what you meant?
- Strings L141–L145, L158–L162 and L164–L168: do you read out the "D → Index 0" lines, or only show them?
- Strings: is String Slicing the next session's topic (for the outro)?
- DBMS: is this the first DBMS Video? If not, it needs a recap.
