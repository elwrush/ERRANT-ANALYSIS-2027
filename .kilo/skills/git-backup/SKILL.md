# Skill: git-backup

## Purpose

Diff all working-tree changes, generate a verbose version commit message describing exactly what changed, stage, commit, and push to the remote repository.

## Workflow

The agent executes these steps in order.

### 1. Check repository state

```bash
git status
git log --oneline -5
git remote -v
```

- If working tree is clean: report "Nothing to commit" and stop.
- If no remote configured: commit only, warn about missing remote.

### 2. Show detailed diff

```bash
git diff              # unstaged changes
git diff --staged     # staged changes
```

Summarize the change categories:
- **New files** (untracked)
- **Modified files**
- **Deleted files**
- **Renamed files**

Call out any sensitive patterns (`.env`, `API_KEY`, `SECRET`, `TOKEN`, `PASSWORD`).

### 3. Check for secrets

Search for `.env` files and files containing credential patterns. If found:
- Warn the user with the list of flagged files
- Exclude `.env` files from staging: `git restore --staged .env .env.*`
- Do not commit secrets

### 4. Generate a verbose commit message

Analyze the diff output and draft a message:

```
<type>: <concise subject line>

<detailed description of what changed and why>

Changed files:
- path/to/file.py: <what changed in this file>
- path/to/other.py: <what changed in this file>
```

Conventions:
- **Types**: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`
- **Subject**: 50-72 chars, imperative mood
- **Body**: full-sentence descriptions, one per changed concern
- **Why**, not just what — explain the motivation
- Match the style of recent commit messages (from `git log`)

Present the message to the user with a question tool:
- **Approve** → proceed with the draft
- **Edit** → ask the user to provide their own message
- **Cancel** → abort

### 5. Stage and commit

```bash
git add -A
git restore --staged .env .env.*    # if present
git commit -m "<approved message>"
```

Verify: `git log -1 --oneline`

### 6. Push to remote

```bash
git push
```

On failure:
- **Behind remote**: warn user, suggest `git pull --rebase`
- **No upstream**: `git push -u origin <current-branch>`
- **Auth failure**: report error, stop

### 7. Confirm

Report back:
```
Commit: <hash> on <branch>
Files:  <N> changed, <ins> insertions(+), <del> deletions(-)
Remote: <url>
Status: pushed / committed only
```

## Edge cases

| Scenario | Behavior |
|----------|----------|
| Clean working tree | Exit with "Nothing to commit." |
| No remote configured | Commit only, warn |
| Push behind remote | Warn, suggest pull/rebase, no force |
| Merge conflict | Abort, tell user to resolve manually first |
| `.env` files present | Exclude from staging, warn user |
| Partial staging (some already staged) | Include in diff summary |

## Scripting note

This is an agent workflow — there is no Python script. The agent runs the git commands directly.
