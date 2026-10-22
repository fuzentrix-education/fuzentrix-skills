# Choosing the Brand Kit

Everything about how slides, images, diagrams and cheatsheets look comes from a **Brand Kit**: the slide template and background, colours, fonts, logos, illustration style and characters.

## When the status says "Next: choose a Brand Kit"

1. Ask the user for their Brand Kit: the release `.zip`, attached to the chat or added from Google Drive. A link pasted into the chat can't be opened here; the file itself is needed.
2. If they give one: `fz.py attach <bundle> brand <zip>`.
3. If they have none, or want the usual Fuzentrix look: `fz.py attach <bundle> brand default`, and tell them the Default Brand Kit is used.

The bundle keeps its Brand Kit, so later chats don't need it again. Attaching a different one later marks everything built with the old one for rebuilding.

## When the user asks for a change in the chat

For example "make the accent green" or "label the slides ACME ACADEMY":

1. `fz.py show <bundle> brand` lists the values; pick the one that matches.
2. `fz.py override <bundle> <value> <new value> --note "<what they asked>"`, for example `fz.py override <bundle> colors.primary "#1B998B" --note "green accent"`. It applies to this Video only, and is recorded with the note.
3. Rebuild what uses it.

A lasting change for every Video belongs in a new Brand Kit release, made by whoever owns the brand.
