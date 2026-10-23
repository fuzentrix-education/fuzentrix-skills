# Quiz: worked examples

Questions on the **Strings** Video (Durga: quotes, indexing, negative indexing) and the **DBMS** Video (Swara: data, information, the DBMS as a bridge). Each passes `fz.py submit <bundle> quiz`, and every code question was run.

## easy · recall what the Video states

```json
{
  "id": "Q01", "type": "SINGLE_SELECT", "difficulty": "easy", "points": 1,
  "source_segments": ["S12"],
  "question": "At which index does a Python String start?",
  "options": [
    {"text": "0", "correct": true, "explanation": "Python String indexing starts at 0: in \"Durga\", D is at index 0."},
    {"text": "1", "correct": false, "explanation": ""},
    {"text": "-1", "correct": false, "explanation": ""},
    {"text": "5", "correct": false, "explanation": ""}
  ],
  "answer_check": "S12: 'Python lo String indexing 0 nundi start avuthundi.' D → Index 0."
}
```

The wrong options are the real mistakes: counting from 1, confusing the first index with the last (-1), and using the length (5).

## medium · predict the output of code like the Video's

```json
{
  "id": "Q02", "type": "SINGLE_SELECT", "difficulty": "medium", "points": 1,
  "source_segments": ["S13", "S15"],
  "question": "What does this code print?\n\n```python\nname = \"Durga\"\nprint(name[-2])\n```",
  "options": [
    {"text": "g", "correct": true, "explanation": "-1 is the last character, a, so -2 is the one before it: g."},
    {"text": "r", "correct": false, "explanation": ""},
    {"text": "u", "correct": false, "explanation": ""},
    {"text": "a", "correct": false, "explanation": ""}
  ],
  "answer_check": "S13: last character is -1 (a → -1, g → -2). Ran it: prints g."
}
```

## medium · apply it to the Video's own example

```json
{
  "id": "Q03", "type": "SINGLE_SELECT", "difficulty": "medium", "points": 1,
  "source_segments": ["S11"],
  "question": "You click \"Semester Results\" on the college portal. Where does your request go first?",
  "options": [
    {"text": "To the DBMS software", "correct": true, "explanation": "You never talk to the database directly: the DBMS takes the request, searches and returns only your marks."},
    {"text": "Straight into the database files", "correct": false, "explanation": ""},
    {"text": "To a clerk in the office", "correct": false, "explanation": ""},
    {"text": "To every student's record", "correct": false, "explanation": ""}
  ],
  "answer_check": "S11: 'Meeru direct ga database tho matladaleru.' Then 'Meeru DBMS ki request pampistaru ➔ DBMS database lo vetukuthundi'."
}
```

## hard · find the error in a new example

```json
{
  "id": "Q04", "type": "SINGLE_SELECT", "difficulty": "hard", "points": 2,
  "source_segments": ["S08", "S09", "S10"],
  "question": "Which line raises a SyntaxError?",
  "options": [
    {"text": "`message = 'I'm Durga'`", "correct": true, "explanation": "The quote in I'm ends the single-quoted String early. With a single quote inside, use double quotes outside."},
    {"text": "`message = \"I'm Durga\"`", "correct": false, "explanation": ""},
    {"text": "`message = 'He said \"Hello\"'`", "correct": false, "explanation": ""},
    {"text": "`message = \"Durga\"`", "correct": false, "explanation": ""}
  ],
  "answer_check": "S08: the single quote in I'm ends the String; ran all four: only the first raises SyntaxError."
}
```

## MULTI_SELECT and TRUE_FALSE

```json
{
  "id": "Q05", "type": "MULTI_SELECT", "difficulty": "easy", "points": 1,
  "source_segments": ["S10"],
  "question": "Which jobs does a DBMS do, as the Video lists them?",
  "options": [
    {"text": "Creates and stores data", "correct": true, "explanation": "A DBMS creates, stores, retrieves, updates and deletes data in a database."},
    {"text": "Retrieves the exact record", "correct": true, "explanation": "It finds your one record among 10,000."},
    {"text": "Updates and deletes records", "correct": true, "explanation": "Changing attendance or fee status is an update."},
    {"text": "Replaces the database itself", "correct": false, "explanation": ""}
  ],
  "answer_check": "S10: 'Database ni Create cheyadaniki, Store cheyadaniki, Retrieve cheyadaniki, Update, mariyu Delete cheyadaniki use ayye powerful software ni DBMS antaru.'"
}
```

```json
{
  "id": "Q06", "type": "TRUE_FALSE", "difficulty": "easy", "points": 1,
  "source_segments": ["S07"],
  "question": "\"Rahul scored 85 in CSE\" is information.",
  "options": [
    {"text": "True", "correct": true, "explanation": "The raw facts Rahul, CSE and 85 are processed into a useful statement: processed data = information."},
    {"text": "False", "correct": false, "explanation": ""}
  ],
  "answer_check": "S07: 'Rahul ki CSE lo 85 vachayi. Idi Information.'"
}
```

## Before and after

| Before | After | Why |
|---|---|---|
| "Which of the following statements about Python String indexing, as discussed in the session, is correct?" | "At which index does a Python String start?" | one idea, few words |
| options "0" and "It depends on how long the String is" | "0", "1", "-1", "5" | the longest option shouldn't give the answer away |
| a wrong option "Banana" | "5" (the length of "Durga") | every wrong option is a real mistake |
| "In which year did IBM create IMS?" | (left out) | a fun-fact date, not a learning objective |
| "Which is not a type of DBMS?" | "Which type of DBMS stores data in tables?" | ask positively |
| explanation "Because it is correct." | "-1 is the last character, a, so -2 is the one before it: g." | say why, with the Video's example |
| "What does `print(name[5])` print?" | (left out, or asked as "Which index gives the last character?") | the Video never shows what goes wrong past the end |
