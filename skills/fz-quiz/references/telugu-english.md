# Reading a Telugu-English script

Instructor Scripts are Telugu written in English letters, mixed with English technical terms. Read them for meaning; quote them exactly.

## The words that carry the meaning

| Telugu-English | Means | Example from a script |
|---|---|---|
| ante, ante enti | means; what is | "Data ante raw facts" = data means raw facts |
| enti, emi | what | "Database ante enti" = what is a database |
| enduku, endukante | why; because | "Endukante I'm lo unna single quote…" = because the single quote in I'm… |
| ela | how | "ela work avtundi" = how it works |
| kani | but | |
| kabatti, anduke | so; that's why | "Anduke SyntaxError vastundi" = that's why a SyntaxError comes |
| ippudu, mundu, taruvatha | now; before / first; after | |
| manam / mana | we / our ("chuddam" = let's see) | |
| meeru, miru / mee | you / your | |
| chuddam, telusukundam, nerchukundam | let's see, let's find out, let's learn | |
| cheyyali / cheyyachu | must do / can do | "outer String ki double quotes use cheyyachu" = can use double quotes outside |
| vastundi / vachindi | comes / came | |
| avutundi / ayyindi | happens, becomes / happened | |
| undi, unnayi, untundi | is (there), are (there), will be | "multiple characters unnayi" = there are several characters |
| kaadu / ledu | is not / there is no | |
| lo, ki, tho, nundi, meeda | in, to, with, from, on | "database lo" = in the database; "0 nundi" = from 0 |
| ee / aa, ivi / avi | this / that, these / those | |
| oka, okka / anni | a, one / all | |
| … ga | turns a word into an adverb | "simple ga" = simply; "fast ga" = quickly |

English words take Telugu endings: "DBMS ki request pampistaru" = (you) send a request to the DBMS; "String lopala" = inside the String.

## Spelling varies; the meaning doesn't

One word is spelled many ways: chestham / chestam, cheyyali / cheyali, meeru / miru, unnayi / vunnayi. That is how the Instructor writes, not a mistake. Reserve a hygiene Finding for a word that would be **read or shown wrong**:

| In a spoken or on-screen line | Finding? |
|---|---|
| words run together: "entiinformation" | yes: "enti information" |
| letters lost: "ndustry", keyboard slips in English: "fst", "recupt", "pwoer" | yes |
| a Telugu word spelled another way: "chuyddam" for "chuddam" | yes only if it would be misread aloud; otherwise no |
| a typo in a heading or note nobody reads aloud: "Explination", "Blod" | no |

A word you can't read at all ("kavakankunna"): guess from the sentence around it, write the guess into the fix, and put the guess in `points_to_check` for the Instructor to confirm.

## Markers in the script

| Line | Line Role | What it asks for |
|---|---|---|
| `Slide – 4`, `Slide - 13 Summary`, `Introduction`, `Conclusion & The Mind-Blowing Fact` | heading | starts a Segment and its slide |
| `Animation Start (Name Example)` … `Animation End` | stage_direction (both) | the lines between are spoken, and the Instructor wants them animated: one animation Visual Event |
| `[Visual: Snap transition. The paper files … transform into a server]` | stage_direction | the Instructor's own visual idea: it must become a Visual Event |
| `(Blod lo vunayii Slide lo place cheyali)` = "put the bold lines on the slide" | note_to_team | bold lines go on the slide word for word |
| `Swara:` | speaker_label | |
| `Example:`, `Output:`, `Test Case`, `Explination`, `Definition` | heading | a label for what follows |
| code, program output, `-----` separators, `D   u   r   g   a` / `0   1   2   3   4` | slide_only | shown, not read |
| `Outer quotes → Double Quotes " "` (a label with no verb) | slide_only | |
| `String lopala single quote unte → outside double quotes use cheyyachu.` (a sentence) | spoken | |
| `> Processed Data = Information` | spoken | the Instructor says it; a formula worth a callout |

When a line could be either (a list of example values such as `Rahul`, `23A91A0501`, `CSE`, `85`), mark it **spoken** and name the lines in `points_to_check`: a spoken line stays on the teleprompter, so this is the safe default.

## Writing in the Instructor's style (fix_text, Script Changes)

- English letters only, never Telugu script. Keep English technical terms in English (database, String, index, SyntaxError).
- Use the Instructor's own spelling of common words: if they write "chestham", write "chestham".
- Keep the sentence's shape and length (within about 30%); change only what the Finding is about.

| Original | Fixed | What changed |
|---|---|---|
| so fst miru kavakankunna recupt lo em details unnayo chuyddam | So first, mee fee receipt lo em details unnayo chuddam. | the slips; "kavakankunna" guessed as "fee", flagged for the Instructor |
| DBMS aa lakshala mandi students database lo search chesi | DBMS aa 10,000 mandi students database lo search chesi | the number now matches the example (10,000) |

## Writing meaning_en

Translate the meaning in plain English, not word by word, and keep the Instructor's names, numbers and examples:

- "Ee Data ni process chesi, arrange chesi, manaki useful ga marchithe… danini Information antam!" → "When data is processed and arranged so it becomes useful, it is called information."
- "Python lo String indexing 0 nundi start avuthundi." → "In Python, String indexing starts at 0."
