# Slide layouts

Every Segment has one slide. It is planned in the Master Script, approved at Gate 2, and then built by Fuzentrix Slides. On screen, readable from the back of a classroom:

- **Title:** 8 words or fewer.
- **Bullets:** at most about 5, each at most 2 lines.
- **Bold text:** text the Instructor marked bold goes on the slide word for word.

| Layout | Use it for | Content |
|---|---|---|
| `title` | Hook and closing slides | title + optional subtitle lines in `bullets` |
| `agenda` | The agenda | up to 6 `bullets`, shown as numbered cards |
| `bullets` | Plain points | `bullets` |
| `definition` | Defining a term | first bullet = the definition (shown in a card); the rest below |
| `code` | Code the Instructor shows | `code` (and `output`, if any) |
| `comparison` | Two sides | `columns: [{title, bullets}, {title, bullets}]` |
| `diagram` | A flow | one bullet written as `A → B → C` becomes connected boxes |
| `quote` | One big statement or fact | first bullet = the statement |
| `image` | A picture beside the points | bullets on the left; the Segment's first image Visual Event on the right |
| `summary` | The summary | `bullets` shown as a ✓ checklist |
