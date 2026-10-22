# Fuzentrix Skills

AI skills that turn an Instructor Script into everything a Fuzentrix course video needs, and that work inside ChatGPT, Codex and Claude.

| Skill | Use it to… |
|---|---|
| `fz-script-review` | Review an Instructor Script, take the Instructor's decisions and wording changes, and get it approved (the Reviewed Script) |
| `fz-master-script` | Build the Master Script (narration, slide plan, Visual Events) from the Reviewed Script, edit it, and get it approved |
| `fz-slides` | Build the Video's editable PowerPoint slides on the Brand Kit's template |
| `fz-visuals` | Build the Editor Kit: images, code-drawn diagrams and flowcharts, and every animation's layers, frames and step sheet |
| `fz-teleprompter` | Make the Instructor's teleprompter script |
| `fz-quiz` | Build a Topic's quiz as an Excel workbook in the LMS template |
| `fz-quiz-html` | Turn any quiz workbook into the LMS's RICH_HTML, within its tag rules |
| `fz-cheatsheet` | Build a Topic's cheatsheet in brand colours, within the LMS's tag rules |
| `fz-coding-problem-html` | Convert a given coding problem into LMS HTML, word for word |

Every skill is self-contained: its instructions plus the tested Python builders it runs (`scripts/fz.py`). No API keys or servers are needed.

## Install

### ChatGPT (Business, Enterprise, Edu, Healthcare)

**As a plugin for the whole workspace (recommended).** A workspace admin goes to **Admin → Plugins → Add → Import marketplace from a GitHub repo** and enters this repository. Private repositories work, and the marketplace re-syncs daily. Then they set who can install the **fuzentrix-skills** plugin. Each user then installs it from **Plugins** in ChatGPT, and the skills work in chats on web, desktop and mobile.

**As individual skills (no admin needed, if uploads are allowed).** Download a skill's zip from this repository's Releases, or zip a folder from `skills/`. Then in ChatGPT: **Skills → Create → Upload from your computer**. Repeat for each skill.

### Codex (CLI, or Codex in the ChatGPT desktop app)

```bash
codex plugin marketplace add fuzentrix-education/fuzentrix-skills
```

Then open `/plugins` (CLI) or the **Plugins** tab (desktop app), install **fuzentrix-skills**, and start a new session.

### Claude Code

```
/plugin marketplace add fuzentrix-education/fuzentrix-skills
/plugin install fuzentrix-skills@fuzentrix
```

### Other agents (Gemini CLI, Cursor, …)

```bash
npx skills@latest add fuzentrix-education/fuzentrix-skills
```

Or copy the folders in `skills/` into the agent's skills folder.

Menu names change between app versions. If a step looks different, note what you saw.

## Use

Two kinds of release zip go with the skills (attach them, or add them from Google Drive): the **Configuration Pack** (how we work, including the LMS's tag rules) and the **Brand Kit** (how things look: template, colours, fonts, logos, characters). Without a Brand Kit, the skills ask for one and otherwise use the Fuzentrix look.

1. **Script Review.** Attach an Instructor Script (`.pdf`, `.docx`, `.md`, `.txt`) and the Fuzentrix Configuration Pack zip, then say: *"Use Fuzentrix Script Review on this Instructor Script. Video ID dbms-p2-t1-v1."* The Instructor decides on each Finding, makes any wording changes, and approves.
2. **Master Script.** In a new chat with the bundle zip: *"Use Fuzentrix Master Script for this Video Bundle."* The Content Lead approves it.
3. **Production.** When the Master Script is approved, use Fuzentrix **Slides**, **Visuals** and **Teleprompter**, in the same chat or a new one with the Video Bundle zip (and the Brand Kit zip). Visuals hands the Video Editor the Editor Kit.
4. **Topic.** Use Fuzentrix **Quiz** and **Cheatsheet** with the Video Bundle zips of the Topic's Videos; then **Quiz HTML** to turn the quiz into RICH_HTML for upload.
5. **Coding problems.** Give **Coding Problem HTML** a problem (pasted or attached); it converts it, word for word.

Every result arrives as a downloadable zip. Upload it again in a new chat to continue.

## Updating

Releases are versioned (`plugin.json` → `version`). Workspaces that imported the marketplace pick up new versions on their daily sync; others reinstall the plugin or re-upload the skills. These files are generated from the Fuzentrix Content Kit; change them there, not here.
