# ADR 0001: Migrate legacy Kilo skills to local opencode skills

- **Status:** Accepted
- **Date:** 2026-09-11

## Context

Agent workflows for this repo (image ingest/OCR, ERRANT analysis, per-student PDFs,
filename normalisation, main report, git backup, review) were defined for the legacy
**Kilo Code** environment:

- `.kilo/kilo.json` (`$schema: https://app.kilo.ai/config.json`)
- Skills at `.kilo/skills/<name>/SKILL.md`
- Slash-command shims at `.kilo/command/<name>.md` (and `.kilo/commands/write-technical-report.md`)

Problems this caused:

- Those skills carried **no YAML frontmatter**. opencode requires `name` + `description`
  and silently filters out any skill without a description, so **none of the skills were
  discoverable** in opencode — even though `AGENTS.md` advertised `/errant-analysis` etc.
- There was no `.opencode/` directory, so opencode had no project skills or commands.
- The project now runs under opencode; keeping a second, parallel agent-config tree in
  `.kilo/` would drift from the live one.

## Decision

- Move all project skills to `.opencode/skills/<name>/SKILL.md` and all slash commands to
  `.opencode/command/<name>.md` (opencode default locations; no `opencode.json` needed).
- Add valid opencode frontmatter: `name` matching the folder, and a `description` that
  front-loads the trigger keywords the model/user is likely to say.
- **Delete the legacy `.kilo/` tree** (skills, commands, config, plans, `node_modules`).
- **Do not duplicate `git-backup` as a project skill.** The global
  `~/.agents/skills/git-backup/SKILL.md` already exists and is a superset of the old
  project copy (it adds binary-file exclusions). Add only a project `/git-backup` command
  that loads the global skill.
- **Do not port `.kilo/command/review.md`.** Its Phase 1b ran a Typst compilation check,
  but the PDF pipeline moved to Jinja2 + Playwright, so the command was stale.
- Leave historical `.kilo` references in `.specify/`, `archive/`, and `audit-*.md`
  untouched as point-in-time records.

## Consequences

- The four skills (`errant-analysis`, `ingest-images`, `local-report`, `rename-json-files`)
  and six commands are discoverable via the `skill` tool and `/...` triggers. **An opencode
  restart is required** to load new config-time files.
- `.kilo/` tracked files are recoverable from git history; the untracked `node_modules/`
  is gone and regenerable.
- `AGENTS.md` routes workflows through `.opencode/` paths and references `adr/`.
- If Kilo is ever reintroduced, `.kilo/` must be recreated from scratch — it is no longer
  maintained.
- Single source of truth going forward: edit workflows in `.opencode/skills/...`, never in
  a `.kilo/` tree.
