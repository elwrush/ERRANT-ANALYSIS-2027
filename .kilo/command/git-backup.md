---
description: Diff, commit with a verbose version message, and push to remote
---
Load the `git-backup` skill from `.kilo/skills/git-backup/SKILL.md` and execute the full workflow:

0. Run `/review` to verify code quality — if violations are found, ask the user whether to continue
1. Check repository state (`git status`, `git log`, `git remote`)
2. Show detailed diff (staged + unstaged)
3. Check for secrets (`.env`, credential patterns)
4. Generate a verbose commit message describing every changed file
5. Present the draft message to the user for approval
6. Stage all safe files, commit with the approved message
7. Push to remote
