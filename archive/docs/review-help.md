# Setting Up a Systematic Code Review Command

A guide for agents in any project to create a `/review` command that enforces project conventions, runs automated checks, and catches AI-specific issues before code is committed.

This document captures the design decisions from Lesson Plan Writer 3's review system so you can replicate the pattern in other projects.

---

## The Problem

AI-generated code is fluent, confident, and often subtly wrong. Common failure modes:

- **Plausible but incorrect logic** — it looks right but doesn't work
- **Hallucinated dependencies** — imports libraries that don't exist or aren't installed
- **Hidden assumptions** — the AI assumes context it doesn't have
- **Convention drift** — each generation uses slightly different patterns
- **Missing domain context** — the AI doesn't know your project's idiosyncratic rules

A human programmer can catch these in review. When the user is not a programmer, the review must be systematic and automated.

---

## Architecture Decision: Command, Not Skill

A Kilo project can use either a **command** (`.kilo/command/<name>.md`) or a **skill** (`.kilo/skills/<name>/SKILL.md`). For review, use a command:

| Criterion | Command | Skill |
|---|---|---|
| Loads on demand | Yes (no restart) | No (requires restart) |
| Complexity | Simple instruction list | Full multi-step workflow |
| Best for | One-shot actions | Complex pipelines |
| Fits review? | Yes — "check everything" | No — overengineered |

Skills in Lesson Plan Writer 3 handle 900-line pipelines (template copy, HTML construction, file I/O). Review is conceptually simpler: run checks, inspect changes, report violations. A command is the right tool.

---

## What a Review Command Does

A `/review` command performs four phases:

### Phase 1: Automated Checks

Run every automated quality gate the project has:

```powershell
# Lint
python -m ruff check --fix .
python -m ruff format .

# Tests
python -m pytest tests/ -v
```

**Stop here if either fails.** Do not proceed to quality review if the code doesn't even parse or tests don't pass.

Adapt the commands to the project's language and tools:
- JavaScript/TypeScript: `npx eslint`, `npx prettier`, `npm test`
- Go: `go vet`, `golangci-lint`, `go test ./...`
- Rust: `cargo clippy`, `cargo fmt --check`, `cargo test`
- Any: check `AGENTS.md` for the project's lint/test commands

### Phase 2: Uncommitted Changes Audit

Show what changed and exit cleanly if nothing has:

```powershell
git diff --stat
git diff
```

If `git status` shows "nothing to commit, working tree clean", report and exit. No point reviewing an empty diff.

### Phase 3: Quality Review Checklist

For each changed file, check against **every applicable rule** from the project's conventions. This is the critical phase — it encodes the domain knowledge that the AI lacks.

**Where to find the rules:**
- `AGENTS.md` — the primary source of project conventions
- Skill files (`.kilo/skills/*/SKILL.md`) — specific pipeline rules
- Design reference docs (e.g., `docs/slide-design-reference.md`)

**Organise rules by file type:**

```markdown
#### HTML Slides (`output/*/slides/index.html`)
1. Icon placement must match spec
2. Fragment classes must not use `highlight-*`
3. Auto-animate requires sibling `<section data-auto-animate>` elements
4. ...

#### JSON (`output/*/*.json`)
1. Keys use underscore not hyphen: `lesson_plan` not `lesson-plan`
2. Required fields present: `teacher`, `lesson_plan.stages`
3. ...

#### Python (`scripts/*.py`)
1. API keys externalised, not hardcoded
2. Error handling for all subprocess calls
3. ...
```

**Cover these categories in every project:**
1. **File format rules** — JSON schema, indentation, naming conventions
2. **Framework-specific rules** — component structure, import patterns
3. **Security** — hardcoded secrets, dependency validity
4. **AI-specific** — hallucinated imports, over-engineered solutions, plausible-but-wrong logic
5. **Content/language** — when the project generates human-facing content (documentation, educational materials, UI text)

### Phase 4: Report

Output a structured summary:

```powershell
=== REVIEW REPORT ===

--- Phase 1: Automated Checks ---
Lint: PASSED (0 errors, 0 warnings)
Tests: PASSED (56/56)

--- Phase 2: Changed Files ---
output/demo/slides/index.html
scripts/json_to_pdf.py

--- Phase 3: Quality Violations ---
NONE — all rules pass

=== CONCLUSION ===
✅ Review passed — ready for /git-backup
```

If violations exist, list each one with the file path and rule reference so the AI can fix it.

---

## Integrating with Backup/Commit

The review should be the **first step** in any commit workflow. In Lesson Plan Writer 3, the `/git-backup` command now runs `/review` before staging anything:

```
Before:  /lint → stage → commit → push
After:   /review (lint + tests + quality) → stage → commit → push
```

If review finds violations, ask the user whether to continue. Some violations are warnings, not blockers. The user decides.

---

## Key Principles

### 1. One Checklist, Many Projects

Each project gets its own `.kilo/command/review.md` because conventions are project-specific. Do not create a global review skill — it would be too generic to catch domain-level issues.

### 2. Rules Must Be Explicit

A rule like "check for good code quality" is useless. A rule like "no `highlight-green` class on fragments (forces `opacity: 1`)" is actionable. Write rules so an agent can mechanically verify them.

### 3. Stop on Automated Failure

If lint or tests fail, do not proceed to quality review. The code must be mechanically valid before you audit its quality. This prevents the review from wasting time reporting style issues in code that doesn't compile.

### 4. Keep the Checklist Aligned with AGENTS.md

When project conventions change, update `AGENTS.md` AND the review checklist. The two must stay in sync. A good practice: have the review command reference AGENTS.md as the source of truth.

### 5. The Report Is for the Agent, Not the User

The user is not a programmer. The review report tells the agent what to fix. Write violations as actionable instructions: "Replace `class="fragment highlight-green"` with `class="fragment answer-correct"` on line 142." The agent then fixes them.

---

## Template

Use this as a starting skeleton when creating `/review` for a new project:

```markdown
---
description: Run lint, tests, and quality review of uncommitted changes against project conventions.
---

# Command: Review

## Workflow

### Phase 1: Automated Checks
[project-specific lint command]
[project-specific test command]

Stop if either fails.

### Phase 2: Uncommitted Changes Audit
git diff --stat
git diff

### Phase 3: Quality Review
[file-type-specific rules from AGENTS.md]

### Phase 4: Report
Summarise results. List violations with file paths and fix instructions.
```

---

## Summary

A `/review` command gives a non-programmer user systematic quality control over AI-generated code. It does not replace human judgment — it replaces the absence of judgment by encoding project knowledge into a checklist that the AI runs against itself. The command is simple to create, requires no external tools beyond what the project already uses, and integrates naturally into commit workflows.
