# Master Script: worked examples

From two real scripts, after Gate 1: **Strings** (`strings_intro.docx`, Durga, 225 lines, about 600 spoken words) and **DBMS** (`dbms_intro.pdf`, Swara, 71 lines, about 700 spoken words). Line ids are as `fz.py new` numbers them. In the Segments below, `spoken` is left out: it is always the draft's, unchanged. The Strings plan assumes the Instructor accepted a hook (added after L1) and a summary and outro (added after L225).

## The Strings Segment plan

The Instructor's slide markers start most Segments. A marker is not followed where its stretch holds two ideas (the simple rule gets its own slide) or one idea is split by a marker (single and double quotes stay together). S06, S14 and S16–S18 are short in spoken words because students read their slides (the kinds of quotes, code and its output, the practice problems).

| Segment | Section | Title | Lines |
|---|---|---|---|
| S01 | hook | Where your name is stored | L1 |
| S02 | intro | Welcome to Fuzentrix | L2–L3 |
| S03 | recap | Last session | L4–L7 |
| S04 | agenda | Today's agenda | L8–L12 |
| S05 | explanation | What is a String? | L13–L31 |
| S06 | explanation | Three kinds of quotes | L32–L38 |
| S07 | explanation | Single and double quotes | L39–L64 |
| S08 | explanation | A quote inside: I'm Durga | L65–L84 |
| S09 | explanation | Double quotes inside | L85–L106 |
| S10 | explanation | The simple rule | L107–L113 |
| S11 | explanation | Triple quotes | L114–L131 |
| S12 | explanation | String indexing | L132–L145 |
| S13 | explanation | Negative indexing | L146–L172 |
| S14 | explanation | Indexing in code | L173–L182 |
| S15 | explanation | Negative indexing in code | L183–L196 |
| S16 | explanation | Practice: the first character | L197–L202 |
| S17 | explanation | Practice: every character | L203–L215 |
| S18 | explanation | Practice: first and last | L216–L224 |
| S19 | summary | What we learned | L225 |

```json
{
  "agenda": ["Strings and Creation", "String Indexing and Accessing Characters", "Real World Example"],
  "learning_objectives": [
    "Define a String as a sequence of characters",
    "Choose single, double or triple quotes for a given String",
    "Predict the character at a positive or negative index"
  ],
  "key_terms": [
    {"term": "String", "definition": "A sequence of characters enclosed within quotes."},
    {"term": "Index", "definition": "The position number of a character in a String, starting at 0."},
    {"term": "Negative indexing", "definition": "Counting from the right: the last character is -1."}
  ]
}
```

## A Segment with the Instructor's animation (Strings S05)

L14 `Animation Start (Name Example)` … L31 `Animation End` ask for an animation of L15–L30. About 78 spoken words: at least ⌈78 / 70⌉ − 1 = 1 Visual Event.

```json
{
  "id": "S05",
  "meaning_en": "Imagine filling in a college admission form with your name, Durga. \"Durga\" is a single value, but it is made of several characters: D, u, r, g, a. In programming, letters, words and sentences are stored as Strings: a String is a sequence of characters.",
  "slide": {
    "title": "What is a String?",
    "layout": "definition",
    "bullets": ["A String is a sequence of characters", "Example: the name Durga", "Durga = D · u · r · g · a"],
    "source_lines": ["L18", "L21", "L22", "L23", "L24", "L25", "L26", "L30"]
  },
  "visual_events": [
    {
      "kind": "image",
      "description": "A college admission form with the Name field filled in as 'Durga'; other fields blank.",
      "trigger": "College Admission Form fill chesthunam",
      "source_lines": ["L15", "L16"],
      "layout": "beside_instructor"
    },
    {
      "kind": "animation",
      "template": "array_pointer",
      "description": "Five boxes appear one by one as she spells the name: D, u, r, g, a. Then the title '\"Durga\" is a String' appears above them.",
      "trigger": "multiple characters unnayi",
      "source_lines": ["L21", "L22", "L23", "L24", "L25", "L26", "L30"],
      "layout": "fullscreen_cutaway",
      "duration_sec": 16,
      "editor_note": "The Instructor's Name Example animation (L14–L31)."
    }
  ]
}
```

Why: the bold `Characters sequence ni String antam.` (L30) is on the slide in English. The trigger `multiple characters unnayi` occurs once; `Durga` occurs five times. The animation covers about 38 words, so 16 s.

## A code Segment with bold labels (Strings S08)

`Slide – 4 (Blod lo vunayii Slide lo place cheyali)`: the bold lines L66–L71 go on screen word for word. A code slide shows only code and output, so the two labels go in an overlay.

```json
{
  "id": "S08",
  "meaning_en": "In \"I'm Durga\" the word I'm already has a single quote, so the String is written with double quotes outside. Written with single quotes, Python takes the quote in I'm as the end of the String and gives a SyntaxError.",
  "slide": {
    "title": "A Quote Inside: I'm Durga",
    "layout": "code",
    "code": "message = \"I'm Durga\"\nprint(message)",
    "output": "I'm Durga",
    "source_lines": ["L66", "L67", "L69"]
  },
  "visual_events": [
    {
      "kind": "animation",
      "template": "list_build",
      "description": "Two labels appear beside the code, word for word: 'Outer quotes → Double Quotes \" \"' and 'Inside quote → Single Quote ''.",
      "trigger": "already single quote",
      "source_lines": ["L70", "L71"],
      "layout": "overlay",
      "duration_sec": 5
    },
    {
      "kind": "code",
      "description": "The wrong version message = 'I'm Durga', the quote after I highlighted in red, and below it: SyntaxError: unterminated string literal.",
      "trigger": "Same sentence ni ila rayadaniki",
      "source_lines": ["L78", "L81"],
      "layout": "beside_instructor",
      "editor_note": "Back to the slide's correct version at 'So:'."
    }
  ]
}
```

## A list said one by one (DBMS S14)

L50 is the Gate 1 fix ("So, industry requirements ni batti…"). About 34 spoken words.

```json
{
  "id": "S14",
  "meaning_en": "Based on industry needs, DBMSs are divided into four main types: hierarchical (a tree), network (many connections), relational (tables) and object-oriented (objects). Relational DBMS rules the IT industry today.",
  "slide": {
    "title": "4 Types of DBMS",
    "layout": "bullets",
    "bullets": ["Hierarchical: tree structure", "Network: multiple connections", "Relational (RDBMS): tables", "Object-Oriented: objects", "Relational rules the IT industry today"],
    "source_lines": ["L50", "L51", "L52", "L53", "L54", "L55"]
  },
  "visual_events": [
    {
      "kind": "animation",
      "template": "tree_graph",
      "description": "'DBMS' at the top; four branches appear as each is named: Hierarchical, Network, Relational, Object-Oriented.",
      "trigger": "4 main types",
      "source_lines": ["L50", "L51", "L52", "L53", "L54"],
      "layout": "fullscreen_cutaway",
      "duration_sec": 14
    }
  ]
}
```

## Before and after

| Before | After | Rule |
|---|---|---|
| slide title "Slide – 6 String Indexing" | "String Indexing" | a title says what is learned |
| bullet "String lo unna prathi character ki oka position number untundi" | "Every character has a position: its index" | slides are in English |
| bullet "Strings are immutable" | (removed) | only what the Instructor says or shows |
| trigger "Durga" | "multiple characters unnayi" | a trigger occurs once in its Segment |
| description "An animation about strings" | "Five boxes appear one by one: D, u, r, g, a" | every label written out |
| DBMS L12 `[Visual: Snap transition…]` with no Visual Event | a `transform_morph` animation: paper files turn into a server, trigger "Exact ga ee problem ni solve" | every Instructor visual idea becomes a Visual Event |
| one 140-word Segment with only its slide | the slide plus a Visual Event about halfway | ⌈140 / 70⌉ − 1 = 1 |
