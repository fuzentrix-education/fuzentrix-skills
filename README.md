# Fuzentrix Skills

AI skills that turn an Instructor Script into everything a Fuzentrix course video needs, and that work inside ChatGPT, Codex and Claude.

| Skill | Use it to… |
|---|---|
| `fz-master-script` | Review an Instructor Script, build its Master Script (narration, slide plan, Visual Events), edit it, and get it approved |
| `fz-slides` | Build the Video's editable PowerPoint slides |
| `fz-visuals` | Make the Video's images, code-drawn diagrams and storyboards |
| `fz-teleprompter` | Make the Instructor's teleprompter script |
| `fz-quiz` | Build an LMS quiz for a Topic (Excel + RICH_HTML), or convert an existing quiz workbook |
| `fz-cheatsheet` | Build an interactive LMS cheatsheet for a Topic |
| `fz-coding-problem` | Write LMS HTML for a coding problem |

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

1. **Script.** Attach an Instructor Script (`.pdf`, `.docx`, `.md`, `.txt`) and the Fuzentrix Configuration Pack zip, then say: *"Use Fuzentrix Master Script on this Instructor Script. Video ID dbms-p2-t1-v1."*
2. **Production.** When the Master Script is approved, use Fuzentrix **Slides**, **Visuals** and **Teleprompter**, in the same chat or a new one with the Video Bundle zip.
3. **Topic.** Use Fuzentrix **Quiz** and **Cheatsheet** with the Video Bundle zips of the Topic's Videos.

Every result arrives as a downloadable zip. Upload it again in a new chat to continue.

## Updating

Releases are versioned (`plugin.json` → `version`). Workspaces that imported the marketplace pick up new versions on their daily sync; others reinstall the plugin or re-upload the skills. These files are generated from the Fuzentrix Content Kit; change them there, not here.
