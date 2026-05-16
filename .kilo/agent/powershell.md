# PowerShell 5.1 Environment

This project runs in **Windows PowerShell 5.1** (not bash, not pwsh 7). All commands in this project must use PowerShell-compatible syntax. Common agent patterns that break and their fixes:

## Git commit with multi-line messages

**BAD** (won't work): heredocs, `-F -`, `-m "..."` with embedded quotes, any here-string syntax
**GOOD**: Pass subject and body via separate `-m` arguments:

```powershell
git commit -m "feat: subject line" -m "Body paragraph one." -m "Body paragraph two."
```

Each `-m` appends as a separate paragraph. No quoting issues, no temp files.

## Conditional chaining

**BAD**: `cmd1 && cmd2`
**GOOD**: `cmd1; if ($?) { cmd2 }`

## Exit code checks

**BAD**: `cmd1 || cmd2` or `if [ $? -eq 0 ]; then ...`
**GOOD**: `cmd1; if (-not $?) { Write-Output "failed" }`

## Text search

**BAD**: `rg "pattern" file` or `grep -r "pattern" dir/`
**GOOD**: `Select-String -Path "dir/*.py" -Pattern "pattern"` or `Get-ChildItem dir/ -Recurse -Filter *.py | Select-String -Pattern "pattern"`

## File existence check

**BAD**: `test -f path` or `[ -f path ]`
**GOOD**: `Test-Path path`

## Process substitution / heredocs

**BAD**: `$(cat file)` or `<<EOF ... EOF`
**GOOD**: Write to a temp file first using `Set-Content`, then read it with `Get-Content`

## Redirection

- stderr: `2>&1` — works (same as most shells)
- suppress output: `> $null` (not `> /dev/null`)

## Quoting

- Single quotes `'text $var'` = literal (variable NOT expanded) — use for most strings
- Double quotes `"text $var"` = variable expansion — escape `$` or use single quotes to prevent expansion
- Variables: `$env:VAR_NAME` for env vars, `$varName` for script vars

## Common tool equivalents

| Bash | PowerShell |
|------|-----------|
| `cat file` | `Get-Content file` or `gc file` |
| `rm file` | `Remove-Item file` |
| `mkdir -p a/b` | `mkdir a/b -Force` or `New-Item a/b -ItemType Directory -Force` |
| `ls` | `Get-ChildItem` or `dir` or `ls` |
| `which cmd` | `Get-Command cmd` |
| `echo text` | `Write-Output text` |
| `sort` | `Sort-Object` |
| `head -n 5` | `Get-Content file -TotalCount 5` |
| `wc -l` | `(Get-Content file).Length` or `Measure-Object -Line` |
