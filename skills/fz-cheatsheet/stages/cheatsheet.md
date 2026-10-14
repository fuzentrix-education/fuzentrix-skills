# Cheatsheet

## Write it

1. Read what each Video teaches: `fz.py show <bundle> sources <video id>` for every Video in the Topic.
2. Start from the draft: `fz.py draft <bundle> cheatsheet all <file>`. It has a section per Video with its source Segments, and the key terms the Cheatsheet must cover. `fz.py schema cheatsheet` explains every block type.
3. Write each section the way a good teacher's revision notes read:
   - Lead with the idea itself: a definition, the Instructor's own example (Rahul, the fee receipt, the college portal), or a table that compares.
   - Short, concrete sentences in English. One idea per block.
   - Use a `table` for any comparison (data vs information, types of DBMS), `code` for anything students type, `key_idea` for the one line to remember, and `mistakes` for real misconceptions.
   - Add a `reveal` self-check question to most sections; students click to see the answer.
   - Add an `image` where a picture explains faster than words, such as a flow, a structure or a comparison. Generate it with the app's image tool in the Fuzentrix style: clean 2D, white background, royal-blue and navy accents, short English labels, no clutter. Save it into `cheatsheet/images/` with a short file name, then reference it.
4. Self-check, then `fz.py submit <bundle> cheatsheet <file>`.

## Build and Gate 3

1. `fz.py build <bundle> cheatsheet` writes:
   - `cheatsheet/<topic>_cheatsheet.html`, the HTML to paste into the LMS;
   - `preview.html`;
   - `insertion_map.md`, saying which image goes where.
2. Offer `preview.html` and the images, and ask the Content Lead to approve or request changes. A change means editing the JSON in `cheatsheet/cheatsheet.json`, resubmitting it and rebuilding.
3. When approved: `fz.py gate <bundle> 3 <file>` with `"deliverable": "cheatsheet"` (`fz.py schema gate3`).

## Self-check checklist

- Every fact is in the Videos (`source`); nothing extra is added.
- Every key term is covered and correctly defined.
- Each image is saved, has alt text, and its labels are spelled correctly.
- It reads like a teacher's notes: no generic openers, no padding, no repeated points.

**Done when:** Gate 3 is recorded for the cheatsheet and the status says "Cheatsheet · Done".
