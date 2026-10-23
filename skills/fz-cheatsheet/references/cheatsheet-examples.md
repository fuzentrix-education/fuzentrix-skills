# Cheatsheet: worked examples

## The whole Cheatsheet for the Strings Video

Durga's Video teaches what a String is, the three kinds of quotes, quotes inside a String, and positive and negative indexing. Its key terms are String, Index and Negative indexing. Four sections, each opening with the idea itself and ending with a check.

```json
{
  "title": "Strings in Python",
  "intro": "What a String is, the three ways to quote one, and how to reach any character by its index.",
  "sections": [
    {
      "heading": "What is a String?",
      "source": [{"video": "python-p3-t2-v1", "segments": ["S05", "S06"]}],
      "blocks": [
        {"type": "paragraph", "text": "A **String** is a sequence of characters enclosed within quotes. The name `\"Durga\"` is one value made of five characters: D, u, r, g, a."},
        {"type": "example", "title": "A name on a form", "text": "You type your name, `Durga`, into a college admission form. Programs store names, words and sentences like this as Strings."},
        {"type": "reveal", "question": "How many characters are in the String \"Durga\"?", "answer": "Five: D, u, r, g, a."}
      ]
    },
    {
      "heading": "Single, double or triple quotes",
      "source": [{"video": "python-p3-t2-v1", "segments": ["S06", "S07", "S11"]}],
      "blocks": [
        {"type": "table", "columns": ["Quotes", "Use for", "Example"], "rows": [
          ["Single `' '`", "a one-line String", "`name = 'Durga'`"],
          ["Double `\" \"`", "a one-line String", "`name = \"Durga\"`"],
          ["Triple `''' '''` or `\"\"\" \"\"\"`", "a String over several lines", "`'''Hello Everyone ...'''`"]
        ]},
        {"type": "code", "language": "python", "code": "message = '''Hello Everyone\nWelcome to Fuzentrix\nLearn Python'''\nprint(message)"},
        {"type": "reveal", "question": "Which quotes does a String over three lines need?", "answer": "Triple quotes: ''' ''' or \"\"\" \"\"\"."}
      ]
    },
    {
      "heading": "Quotes inside a String",
      "source": [{"video": "python-p3-t2-v1", "segments": ["S08", "S09", "S10"]}],
      "blocks": [
        {"type": "key_idea", "text": "A single quote inside → double quotes outside. Double quotes inside → single quotes outside."},
        {"type": "code", "language": "python", "code": "message = \"I'm Durga\"\nprint(message)\n\nmessage = 'He said \"Hello\"'\nprint(message)"},
        {"type": "mistakes", "items": ["Writing `'I'm Durga'`: the quote in I'm ends the String early, so Python gives a SyntaxError."]},
        {"type": "reveal", "question": "Which quotes go outside `He said \"Hello\"`?", "answer": "Single quotes, because the sentence already has double quotes inside."}
      ]
    },
    {
      "heading": "Indexing: positive and negative",
      "source": [{"video": "python-p3-t2-v1", "segments": ["S12", "S13", "S14", "S15"]}],
      "blocks": [
        {"type": "paragraph", "text": "Every character has a position number, its **index**. Positive indexing counts from the left, starting at 0. **Negative indexing** counts from the right, starting at -1."},
        {"type": "table", "columns": ["Character", "Index", "Negative index"], "rows": [
          ["D", "0", "-5"], ["u", "1", "-4"], ["r", "2", "-3"], ["g", "3", "-2"], ["a", "4", "-1"]
        ]},
        {"type": "code", "language": "python", "code": "name = \"Durga\"\nprint(name[0])   # D\nprint(name[-1])  # a\nprint(name[-2])  # g"},
        {"type": "mistakes", "items": ["Starting at 1: the first character is at index 0.", "Starting negative indexing at 0: the last character is at -1."]},
        {"type": "image", "id": "durga-index", "alt": "The letters of Durga with their positive and negative index numbers",
         "caption": "Two ways to count the same five characters.",
         "prompt": "Five boxes in a row holding the letters D, u, r, g, a; above each box its index 0, 1, 2, 3, 4; below each box -5, -4, -3, -2, -1"},
        {"type": "reveal", "question": "What is the index of the last character of \"Durga\"?", "answer": "4 counting from the left, or -1 counting from the right."}
      ]
    }
  ],
  "quick_revision": [
    "String = a sequence of characters in quotes",
    "Single or double quotes: a one-line String",
    "Triple quotes: a String over several lines",
    "A quote inside? Use the other kind outside",
    "Index starts at 0 from the left",
    "Negative indexing starts at -1 from the right"
  ]
}
```

## A comparison is a table (DBMS)

From Swara's Video: the receipt example, and the formula she asks students to remember.

```json
{
  "heading": "Data vs Information",
  "source": [{"video": "dbms-p2-t1-v1", "segments": ["S06", "S07"]}],
  "blocks": [
    {"type": "table", "columns": ["Data", "Information"], "rows": [
      ["Raw facts or raw details", "Data processed into something useful"],
      ["`Rahul`, `23A91A0501`, `CSE`, `85`", "Rahul scored 85 in CSE"],
      ["Means little on its own", "Answers a question"]
    ]},
    {"type": "key_idea", "text": "Processed Data = Information."},
    {"type": "mistakes", "items": ["Calling a single value like `85` information: on its own it is data."]},
    {"type": "reveal", "question": "Is \"CSE\" data or information?", "answer": "Data: one raw fact on its own."}
  ]
}
```

## Before and after

| Before | After | Why |
|---|---|---|
| intro "In today's fast-paced world, Strings are everywhere." | "What a String is, the three ways to quote one, and how to reach any character by its index." | say what the page covers |
| a section opening "Let us now look at indexing." | opening with "Every character has a position number, its **index**." | the first block is the idea itself |
| a paragraph comparing single and double quotes | a table: Quotes · Use for · Example | every comparison is a table |
| mistakes "Be careful with quotes." | "Writing `'I'm Durga'`: the quote in I'm ends the String early, so Python gives a SyntaxError." | the wrong belief and the truth |
| an image of "a programmer at a laptop" | the five boxes with both index rows | only where a picture explains faster |
| a section on String slicing | (left out) | the Video doesn't teach it |
