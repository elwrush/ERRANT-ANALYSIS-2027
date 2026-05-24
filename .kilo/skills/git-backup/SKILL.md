# Skill: git-backup

## Purpose

Stage all safe changes, generate a descriptive commit message, commit, and push to remote.

## Agent workflow

Run these steps in order:

1. **Check state** — `git status`, `git log -5`, `git remote -v`. Clean tree → stop.
2. **Show diff** — `git diff`, `git diff --staged`. Categorise changes (new/modified/deleted).
3. **Secrets check** — Scan for `.env` and credential patterns. Exclude `.env` files from staging.
4. **Draft message** — Analyse diff, draft a message with type (`feat`/`fix`/`refactor`/`chore`), subject line, and per-file description. Present to user with `question` for approve/edit/cancel.
5. **Commit** — `git add -A`, `git restore --staged .env .env.*`, `git commit -m "message"`.
6. **Push** — `git push` (or `git push -u origin <branch>` if no upstream).
7. **Confirm** — Report commit hash, branch, file count, remote status.
