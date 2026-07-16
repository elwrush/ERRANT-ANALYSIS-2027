# Skill: git-backup

## Purpose

Stage all safe changes, generate a descriptive commit message, commit, push to remote, then verify the backup succeeded.

## Rules

- **No force push** (`--force`, `--force-with-lease`) unless dry-run confirms it is safe and the user explicitly approves.
- **Empty commits** are never allowed. If nothing changed, inform the user.
- **Secrets**: Always exclude `.env`, `.env.*`, `*.key`, `*.pem`, `credentials*` from staging. Use `git restore --staged` on any that slip through `git add -A`.
- **Size check**: If `git add -A` stages >500 files or total diff >100MB, warn the user before committing.
- **Commit message** must follow Conventional Commits: `<type>(<scope>): <description>` then blank line then bullet list of per-file changes.

## Agent workflow

### Step 1 — Health check

```bash
git status --short
git log --oneline -5
git remote -v
```

Exit if working tree is clean (nothing to back up). Warn if no remote is configured.

### Step 2 — Diff review

```bash
git diff --stat
git diff --stat --staged
```

Categorise: new files, modified files, deleted files. Flag any binary files (>1MB).

### Step 3 — Secrets scan

Scan `git diff` output for patterns: `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN`, credential strings, IP addresses, private SSH keys. Also check `git status --short` for `.env` files.

Stage with `git add -A`, then immediately unstage dangerous paths:
```bash
git add -A
git restore --staged .env .env.* *.key *.pem credentials* 2>/dev/null; true
```

### Step 4 — Draft commit message

Analyse the diff. Format:

```
<type>(<scope>): <short subject line>

- <file>: <what changed and why>
- <file>: <what changed and why>
...
```

Types: `feat` (new feature), `fix` (bug fix), `refactor` (restructure), `chore` (tooling, config, backup), `docs` (documentation), `test` (tests).

Present the message to the user with `question` tool with options: `Approve`, `Edit`, `Cancel`.

### Step 5 — Commit & push

```bash
git commit -F /tmp/commit_msg.txt
git push 2>&1 || git push -u origin $(git rev-parse --abbrev-ref HEAD) 2>&1
```

If push fails (non-fast-forward, permission denied), report the error and stop. Never force push without explicit approval.

### Step 6 — Verify

```bash
git rev-parse HEAD
git status --short
```

Report: commit hash (short), branch, number of files changed, remote status (ahead/behind).

## Dry-run mode

Run the full workflow but skip `git commit` and `git push`. Present what would happen:
- files that would be staged
- estimated commit size (lines added/deleted)
- remote target branch
