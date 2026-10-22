# Cheatsheet

## Write it

1. Read what each Video teaches: `fz.py show <bundle> sources <video id>` for every Video in the Topic.
2. Start from the draft: `fz.py draft <bundle> cheatsheet all <file>`. It has a section per Video with its source Segments, and the key terms the Cheatsheet must cover. `fz.py schema cheatsheet` explains every block type.
3. Write each section the way a good teacher's revision notes read:
   - Lead with the idea itself: a definition, the Instructor's own example (Rahul, the fee receipt, the college portal), or a table that compares.
   - Short, concrete sentences in English. One idea per block.
   - Use a `table` for any comparison (data vs information, types of DBMS), `code` for anything students type, `key_idea` for the one line to remember, and `mistakes` for real misconceptions.
   - Add a `reveal` self-check question to most sections; students click to see the answer.
   - Add an `image` where a picture explains faster than words, such as a flow, a structure or a comparison: give it an `id` (e.g. `data-vs-information`), `alt` text, an optional `caption`, and a `prompt` saying what it shows. The HTML holds a placeholder for it; the image itself is made next.
   - Write in Fuzentrix markup: `` `code` `` and `**bold**` inside text; a `code` block with its `language`.
4. Self-check, then `fz.py submit <bundle> cheatsheet <file>`.
5. **Images:** `fz.py show <bundle> cheatsheet-image-prompts` gives each image's file name and a prompt in the Brand Kit's style. Generate each with the app's image tool and save it under exactly that name. Check the labels are spelled correctly.

## Build and Gate 3

1. `fz.py build <bundle> cheatsheet` checks the HTML against the LMS HTML Policy and writes:
   - `cheatsheet/<topic>_cheatsheet.html`, the HTML to paste into the LMS, in the Brand Kit's colours as far as the LMS keeps them;
   - `<topic>_theme.css`, when the LMS keeps only `fz-*` classes: the LMS team installs it once;
   - `preview.html`, with the images in place;
   - `insertion_map.md`: each image's placeholder and file, to attach when uploading.

   Tell the user what the build says the LMS rules leave out (colours, click-to-reveal). If the rules are the DRAFT ones, say so; the LMS team's rules go in the Configuration Pack.
2. Offer `preview.html` and the images, and ask the Content Lead to approve or request changes. A change means editing the JSON in `cheatsheet/cheatsheet.json`, resubmitting it and rebuilding.
3. When approved: `fz.py gate <bundle> 3 <file>` with `"deliverable": "cheatsheet"` (`fz.py schema gate3`). Every image must be generated first.

## Self-check checklist

- Every fact is in the Videos (`source`); nothing extra is added.
- Every key term is covered and correctly defined.
- Each image has a clear prompt and real alt text; once generated, its labels are spelled correctly.
- It reads like a teacher's notes: no generic openers, no padding, no repeated points.

**Done when:** Gate 3 is recorded for the cheatsheet and the status says "Cheatsheet · Done".
