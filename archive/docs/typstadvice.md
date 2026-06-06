# Typst Template Advice — Writing Error-Free, Economical Templates

This guide is for agents and humans producing Typst templates in this project. It covers **what Typst source looks like that compiles first time**, **how to avoid common errors**, and **how to write templates that are fast, maintainable, and minimal**.

---

## Table of Contents

1. [Fundamental Principles](#1-fundamental-principles)
2. [The Three Modes — Markup, Code, Math](#2-the-three-modes--markup-code-math)
3. [Set Rules vs. Show Rules — When to Use What](#3-set-rules-vs-show-rules--when-to-use-what)
4. [Template Structure Patterns](#4-template-structure-patterns)
5. [Image and Resource Handling](#5-image-and-resource-handling)
6. [Typst-Specific Pitfalls (to Memorise)](#6-typst-specific-pitfalls-to-memorise)
7. [Economy — Writing Fast, Minimal Templates](#7-economy--writing-fast-minimal-templates)
8. [Typst Content Generation (no Jinja2)](#8-typst-content-generation-no-jinja2)
9. [Red-Green Test Workflow](#9-red-green-test-workflow)
10. [Quick Reference — One-Shot Template Skeleton](#10-quick-reference--one-shot-template-skeleton)

---

## 1. Fundamental Principles

### 1.1 Every function call must be verified

**Never write a single line of Typst code that you have not confirmed against an authoritative source.** Typst evolves fast — agent training data is always stale. Consult these sources in order:

1. **Remote Typst GitHub repo** (`github.com/typst/typst`) via `gh search code` or `gh api` — the only authoritative, up-to-date source:
   ```powershell
   gh search code "pub fn image" --repo typst/typst --limit 5
   gh api repos/typst/typst/contents/crates/typst-library/src/visualize/image/mod.rs
   ```
2. **Bundled docs** at `.kilo/skills/typst-author/docs/` — a snapshot that may be stale. Cross-reference against the remote repo when possible.
3. **Local packed repo** at `knowledge-base/typst-packed.json` — a stalest snapshot. Use only when offline.

If none of the above contain the function you need, **do not use it** — find an alternative syntax you can confirm.

### 1.2 Typst compiles cold — zero tolerance for syntax errors

Unlike interpreted languages with REPLs, Typst halts on the first error with a line number. You must pre-verify everything: function names, parameter names, argument types, set-rule syntax, show-rule syntax, content-block vs. code-block delimiters.

### 1.3 Understand the root flag

Typst resolves relative paths from the **source `.typ` file's directory**. Absolute paths (starting with `/`) resolve from the **project root**, which defaults to the parent of the main file. Use `--root .` when compiling from the project root:

```powershell
typst compile --root . "typst/code/subfolder/index.typ" "typst/PDF/subfolder/index.pdf"
```

This means `#import "/templates/header.typ"` works if `--root .` is set.

---

## 2. The Three Modes — Markup, Code, Math

This is the single biggest source of errors in generated Typst code.

### 2.1 Markup mode (default)

Use `#` to enter code mode. Within a content block `[...]`, the same rule applies.

```typst
This is markup. #rect(width: 1cm) is a code call.
```

### 2.2 Code mode (curly braces)

Inside `{ ... }`, you do NOT use `#` before function calls. The `#` prefix is only needed when escaping back into markup.

```typst
#{
  let x = 10
  rect(width: x * 1pt)   // no # here
}
```

### 2.3 Content blocks (square brackets)

Square brackets `[...]` produce content. Inside them, you are back in markup mode, so `#` is required again:

```typst
#let my-content = [This is #emph[emphasis] inside content]
```

### Rule of thumb

| Context | `#` required? | Example |
|---------|---------------|---------|
| Document body | Yes | `#rect(width: 1cm)` |
| Inside `[...]` content block | Yes | `[Hello #text(red)[world]]` |
| Inside `{...}` code block | No | `{ rect(width: 1cm) }` |
| Inside function argument list | No | `let f(x) = { x + 1 }` |
| Inside show rule body | Depends | `show: it => { block(it) }` (code) vs `show: it => [ #block(it) ]` (content) |

---

## 3. Set Rules vs. Show Rules — When to Use What

### 3.1 Set rules — configure defaults

```typst
#set text(font: "Roboto", size: 10pt)
#set page(paper: "a4", margin: (x: 0.75in, top: 1.25in, bottom: 0.75in))
#set par(leading: 0.55em)        // leading is ADDITIONAL space, not a multiplier
#set heading(numbering: "1.")
```

- Scoped to the current block or file
- Only **optional** parameters can be set
- Use for page setup, font, spacing, column layout

### 3.2 Show-set rules — style a specific element type

```typst
#show heading: set text(navy)       // all headings are navy
#show heading.where(level: 1): set align(center)   // only level-1 headings
```

### 3.3 Show-transform rules — completely redefine an element

```typst
#show heading: it => block[
  \~
  #emph(it.body)
  \~
]
```

The `it` parameter receives the element. It has **fields matching the function's parameters** (e.g., `it.body`, `it.level`, `it.numbering`).

### 3.4 Show-everything rules — template wrapper

```typst
#show: doc => conf(title: "My Doc", doc)
```

This is the **template pattern**. The entire document body is passed as `doc`, and the function receives it as a content argument.

### 3.5 When to use each

| Goal | Use |
|------|-----|
| Change default font | `#set text(font: ...)` |
| Change page margins | `#set page(margin: ...)` |
| Add header/footer | `#set page(header: ...)` |
| Make all h2s italic | `#show heading.where(level: 2): set text(style: "italic")` |
| Add decor around every heading | `#show heading: it => block[#emph(it.body)]` |
| Wrap entire doc in a template | `#show: template.with(args...)` |
| Replace text strings | `#show "foo": "bar"` |

---

## 4. Template Structure Patterns

### 4.1 Module template (for re-export)

This is the pattern used in `templates/mathayom-header.typ`:

```typst
// reusable-header.typ
#let my-header(
  title: "Default Title",
  logo-path: "logo.png",
  show-rule: true,
) = {
  let content = grid(
    columns: (1fr, 2fr, 1fr),
    align: (left + horizon, center + horizon, right + horizon),
    image(logo-path, height: 1.2cm),
    text(size: 16pt, weight: "bold")[#title],
    [],
  )
  if show-rule {
    block(stroke: (bottom: 0.5pt + black), inset: (bottom: 6pt), content)
  } else {
    block(inset: (bottom: 6pt), content)
  }
}
```

Import and use:
```typst
#import "/templates/reusable-header.typ": my-header

#set page(header: context {
  if counter(page).get().first() == 1 { my-header() }
})

= Document body
```

### 4.2 Everything-show template (wraps entire doc)

```typst
#let conf(title: "Untitled", authors: (), abstract: [], doc) = {
  set page(paper: "us-letter", margin: 1in)
  set text(font: "Libertinus Serif", size: 11pt)
  set par(justify: true)

  align(center, text(1.4em, weight: "bold")[#title])

  if authors.len() > 0 {
    let n = calc.min(authors.len(), 3)
    grid(columns: (1fr,) * n,
      ..authors.map(a => [ #a.name \ #a.affiliation ]),
    )
  }

  doc   // ← inserts the document body here
}

// main.typ
#import "/templates/conference-template.typ": conf

#show: conf.with(title: "My Paper", authors: ((name: "Alice", affiliation: "UCL"),))

= Introduction
...
```

### 4.3 Inline template (for single-file scripts)

Used in `json_to_pdf.py` — the `.typ` file is generated in Python via `build_typ_content()` and written as a single self-contained file:

```typst
#set text(font: "Roboto", size: 10pt)
#set par(leading: 0.55em)
#set page(margin: (x: 0.75in, top: 1.25in, bottom: 0.75in))

#show: it => {
  set page(
    header: context {
      if counter(page).get().first() == 1 {
        block(stroke: (bottom: 0.5pt + black))[
          #image("logo.png", height: 1.35cm)
        ]
      }
    },
  )
  it
}

= Heading
Content here.
```

---

## 5. Image and Resource Handling

### 5.1 Images must exist at compile time

Typst resolves image paths relative to the **source `.typ` file's directory** (or absolute from `--root`). If the image is not found, compilation fails.

**Best practice** — copy images to the same directory as the `.typ` file, or use absolute paths from `--root`:

```typst
// Relative to .typ file (good)
#image("logo.png", height: 1.35cm)

// Absolute from project root (good, needs --root .)
#image("/templates/logo.png", height: 1.35cm)

// Wrong — resolves relative to .typ file but file isn't there
#image("C:\absolute\path\logo.png")
```

### 5.2 Font handling

Specify `--font-path` on the CLI if using non-standard fonts:

```powershell
typst compile --font-path "%APPDATA%\TinyTeX\texmf-dist\fonts\opentype\google\roboto" source.typ output.pdf
```

Font warnings (e.g. "unknown font family") do not prevent compilation — Typst falls back to system fonts.

### 5.3 Logo placement in headers

```typst
#set page(
  header: context {
    if counter(page).get().first() == 1 {
      grid(
        columns: (1fr, 2fr, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        image("logo-left.png", height: 1.2cm),
        text(size: 14pt, weight: "bold")[Title],
        image("logo-right.png", height: 1.8cm),
      )
    }
  }
)
```

**Important**: The `context` keyword is essential here — the page counter value is not known until layout time.

---

## 6. Typst-Specific Pitfalls (to Memorise)

### 6.1 Arrays use parentheses, not brackets

```typst
// CORRECT
let items = (1, 2, 3)
let columns = (auto, 1fr, 2fr)

// WRONG
let items = [1, 2, 3]    // → this is a content block, not an array!
```

### 6.2 No tuples — only arrays

Typst has arrays, not tuples. A single-element array needs a trailing comma:

```typst
let single = (1,)        // array of one int
let not-tuple = (1)      // this is just 1 (the int)
```

### 6.3 Access array elements with `.at()`, not `[]`

```typst
// CORRECT
let first = my-array.at(0)

// WRONG
let first = my-array[0]
```

### 6.4 `#` hash usage — the most common bug

| Context | Rule | Correct | Incorrect |
|---------|------|---------|-----------|
| Markup | `#` before code | `#rect(width: 1cm)` | `rect(width: 1cm)` |
| Content block `[...]` | `#` before code | `[Hello #emph[world]]` | `[Hello emph[world]]` |
| Code block `{...}` | NO `#` | `{ rect(width: 1cm) }` | `{ #rect(width: 1cm) }` |
| Show rule body (code) | NO `#` | `show: it => { rect(it) }` | `show: it => { #rect(it) }` |
| Show rule body (content) | `#` inside `[]` | `show: it => [ #rect(it) ]` | Undefined |
| Function argument | NO `#` | `text("red")[content]` | `text(#"red")[content]` |

### 6.5 Dictionaries: `()` with `key: value`

```typst
let margins = (top: 1in, bottom: 0.75in, x: 0.75in)
let stroke = (bottom: 0.5pt + black)
```

### 6.6 Leading is ADDITIONAL space

```typst
#set par(leading: 0.55em)
```

The `leading` parameter adds **extra** space between lines on top of the font's natural leading. A value of `0.55em` means 0.55em *extra* space, not total line height = 0.55em. This is contrary to how leading works in CSS.

### 6.7 `context` keyword for introspection

Any code that depends on page number, counter values, or location requires `context`:

```typst
// WRONG — will fail to compile
#counter(page).get()

// CORRECT
#context counter(page).get()

// Also correct in a show rule body (context is implicit)
#show: it => {
  set page(header: context {
    if counter(page).get().first() == 1 { ... }
  })
  it
}
```

### 6.8 `set page()` inserts a page break

Changing page setup via `set page()` forces a new page to start. Place all page setup at the **very top** of your file, before any content.

### 6.9 Escape sequences

```typst
$ → \$      // dollar sign (prevents math mode)
# → \#      // hash sign (prevents code mode)
~ → \~      // tilde (prevents non-breaking space)
```

### 6.10 `auto` is a special value

`auto` means "use the default." It is commonly used for `width`, `height`, `fill`, `stroke`, and table column widths. Not to be confused with `none` (absence of value).

### 6.11 Table cells: `table.cell()` and `table.header()`

```typst
#table(
  columns: (auto, 1fr, 2fr, auto),
  stroke: 1pt,
  table.header([*Time*], [*Goal*], [*Procedure*], [*Int*]),
  table.cell(colspan: 4, fill: luma(230))[*STAGE 1: WARM-UP*],
  [5 min], [Aim text], [Procedure text], [T-S],
)
```

---

## 7. Economy — Writing Fast, Minimal Templates

### 7.1 Compilation speed rules

| Slow pattern | Fast alternative |
|-------------|------------------|
| Many small `show` rules | Consolidate into fewer `show` rules |
| Heavy use of `query()` for every page | Pre-compute in Python (f-strings) |
| Complex `grid` with many nested blocks | Simplify to `table` where possible |
| Multiple `context` blocks per page | Compute once, store in variable |

### 7.2 Minimise compiler iterations

Typst may need multiple passes for cross-references, counters, and `locate()`. If you see "layout did not converge within 5 attempts," you are using context-heavy features in a way that creates a feedback loop.

**Solution**: Pre-compute anything that doesn't need Typst's layout engine. For lesson plans, dates, stage numbers, and page counts are known at generation time — pass them directly from Python via f-strings.

### 7.3 Use Python f-strings for what they're good at

The `json_to_pdf.py` pipeline uses Python f-strings to build `.typ` content. This is the right pattern:

```
JSON data → Python (f-strings) → .typ file on disk → typst compile → PDF
```

**Do in Python (f-strings):**
- String formatting (dates, stage aims, procedure text)
- Conditional sections (transcript, answer key)
- Loop expansion (stages → table rows)
- Markdown → Typst conversion
- Content transformations (humanize aims, clean procedures)

**Do in Typst:**
- Page layout (margins, headers, columns)
- Typography (font, size, leading, alignment)
- Table styling (stroke, fill, column widths)
- Counter management (page numbers)

### 7.4 Reduce redundancy

Instead of repeating `#set` rules, use a single `show` block:

```typst
// Prefer grouping in an everything-show:
#show: doc => {
  set text(font: "Roboto", size: 10pt)
  set par(leading: 0.55em)
  set page(margin: (x: 0.75in, top: 1.25in, bottom: 0.75in))
  doc
}
```

This makes it easy to extract into a reusable module later.

---

## 8. Typst Content Generation (no Jinja2)

**Jinja2 is no longer used.** The pipeline now builds `.typ` content directly in Python via `build_typ_content()` using f-strings. The old template `templates/lesson-plan-template.typ` is kept for reference only.

### 8.1 Content generation via Python f-strings

The `.typ` file is built directly in Python using `build_typ_content()` in `scripts/json_to_pdf.py`. Data is embedded inline using f-strings, avoiding any runtime evaluation or template engine. This is simpler, faster, and eliminates the Jinja2 dependency entirely.

### 8.2 Markdown to Typst conversion (md_to_typst)

The `md_to_typst()` function handles these conversions for legacy answer key files:

| Markdown | Typst |
|----------|-------|
| `# Heading` | `= Heading` |
| `### Heading` | `=== Heading` |
| `**bold**` | `*bold*` |
| `*italic*` | `_italic_` |
| `- bullet` | `- bullet` |
| `---` | `#line(length: 100%)` |

---

## 9. Red-Green Test Workflow

Use the `test_typst_output.py` script to validate every generated template:

```powershell
python scripts/test_typst_output.py `
    --typ-file "typst/code/{subfolder}/index.typ" `
    --pdf-output "typst/PDF/{subfolder}/index.pdf" `
    --expect-text "Critical string" `
    --forbid-text "TODO" `
    --expect-page-count 2
```

### 9.1 What to test

- **Every critical string** that must appear (header title, headings, key content)
- **No placeholder text** (`--forbid-text "TODO"`, `--forbid-text "lorem"`)
- **Expected page count** — page breaks must be correct
- **Answer key and transcript** — if they exist, their content must be valid Typst markup (converted from .md by `migrate_answer_keys.py`)

### 9.2 Iteration loop

```powershell
$tries = 0
do {
    $tries++
    Write-Host "Attempt $tries..."
    python scripts/test_typst_output.py <args>
    $passed = $LASTEXITCODE -eq 0
    if (-not $passed) { <fix .typ code and recompile> }
} while (-not $passed -and $tries -lt 10)
```

### 9.3 Common test failures and fixes

| Failure | Likely cause | Fix |
|---------|-------------|-----|
| `--expect-text "Hello"` fails | Text is inside a `#show` transform | Check show rule returns content unchanged |
| `--forbid-text "TODO"` fails | Placeholder left in template | Replace with static content or empty |
| `--expect-page-count` fails | Wrong number of `#pagebreak()` | Count required page breaks from data |
| Text appears garbled | Markdown conversion missed a `$` or `\` | Add escaping in `md_to_typst()` |

---

## 10. Quick Reference — One-Shot Template Skeleton

This is a minimal, proven template that compiles every time:

```typst
// ==========================================
// PAGE SETUP — place FIRST, before any content
// ==========================================
#set page(
  paper: "a4",
  margin: (x: 0.75in, top: 1.25in, bottom: 0.75in),
  numbering: "1",
)

// TYPOGRAPHY — set globally
#set text(font: "Roboto", size: 11pt)
#set par(leading: 0.55em)

// ==========================================
// HEADER (page 1 only)
// ==========================================
#show: doc => {
  set page(
    header: context {
      if counter(page).get().first() == 1 {
        grid(
          columns: (1fr, 1fr, 1fr),
          align: (left + horizon, center + horizon, right + horizon),
          image("logo-left.png", height: 1.35cm),
          text(size: 14pt, weight: "bold")[Title],
          image("logo-right.png", height: 1.8cm),
        )
      }
    },
  )
  doc
}

// ==========================================
// DOCUMENT CONTENT
// ==========================================
= Heading 1

Content here.

// Table example
#table(
  columns: (auto, 1fr, 2fr, auto),
  stroke: 1pt,
  table.header([*Time*], [*Goal*], [*Procedure*], [*Int*]),
  [5 min], [Aim], [Procedure text], [T-S],
)
```

**Verification checklist before first compile:**
- [ ] `#` hash usage correct in every context
- [ ] All `set page()` calls at the top
- [ ] Image paths exist (relative to `.typ` file or absolute from `--root`)
- [ ] Arrays use `()`, not `[]`
- [ ] `.at()` used for array access
- [ ] `context` used where counters/locations are read
- [ ] No LaTeX syntax (`\section`, `\begin`, `\end`, `$...$` for math unless intended)
- [ ] Font name matches an installed font (or remove font spec to use default)
- [ ] `--root` flag matches the expected root for absolute paths
