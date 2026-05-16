# Typst Troubleshooting Reference

## Page geometry & headers

### Problem: Header renders as raw code text
Content inside `place(top + left, dy: ...)[ ... ]` is in **markup mode**. Function calls like `grid(...)`, `line(...)` without `#` prefix are treated as literal text.

**Fix**: Always use `#grid(...)`, `#line(...)` inside `place()[...]` content blocks.

```typst
// ❌ Wrong — renders as literal text
place(top + left, dy: 0cm)[
  grid(columns: (1fr, 2fr, 1fr), ...)
]

// ✅ Correct — function calls are prefixed
place(top + left, dy: 0cm)[
  #grid(columns: (1fr, 2fr, 1fr), ...)
]
```

### Problem: Header `place()` doesn't fix margin gap
Using `place()` with `header-ascent: 0pt` still leaves body starting at `top:` margin on all pages, creating blank space on non-header pages.

**Fix**: Don't use Typst's `header:` mechanism for decorative mastheads that only appear on page 1. Put the masthead as **regular body content** at the start of each section. Body starts at the same `top:` margin on every page — no phantom gaps.

```typst
// ❌ Wrong — using header mechanism with place()
#set page(header: context { if condition { place(...)[#grid(...)] } })

// ✅ Correct — masthead as body content
#grid(columns: (1fr, 2fr, 1fr), image("/logo.png"), text[Title])
#line(length: 100%, stroke: 1.0pt)
#v(1em)
```

---

## Context blocks & pad-to-four

### Problem: `[]` renders as literal text "[]"
In **code mode** (inside `context { ... }`), `[]` is an **empty array literal**, not an empty content block. The array serializes as `[]` in the output.

```typst
// ❌ Wrong — [] in code mode is an array
context { [] }

// ❌ Wrong — #[] in markup is also array
[#[] <label>]

// ✅ Correct — use box for invisible anchor
#box(width: 0pt) <label>

// ✅ Correct — function argument brackets are safe
page([])
```

### Problem: `pagebreak()` consolidates to fewer blank pages
Multiple consecutive `pagebreak()` calls inside a `context` block **merge into one break**. This causes 3-page booklets instead of 4.

**Root cause**: All content produced inside a `context { }` block is evaluated at the same logical position. Multiple `pagebreak()` elements at the same position merge.

**Fix**: Use `page([])` instead of `pagebreak()`. The `page()` function creates an actual page element that cannot be consolidated.

| Approach | Result |
|----------|--------|
| `pagebreak()` in for loop | ❌ Consolidates |
| `h(0pt)` + `pagebreak()` | ❌ Still consolidates |
| `" "` + `pagebreak()` | ❌ Leaves visible space character |
| `page([])` | ✅ Creates separate pages |

```typst
// ❌ Wrong — consolidates to 1 page
context {
  for _ in range(2) { pagebreak() }
}

// ✅ Correct — creates 2 separate blank pages
context {
  for _ in range(2) { page([]) }
}
```

### Working pad-to-four implementation

```typst
#box(width: 0pt) <pad-anchor-0>
#context {
  let num = counter(page).at(label("pad-anchor-0")).first()
  for _ in range(calc.rem-euclid(4 - num, 4)) {
    page([])
  }
}
```

### Key Typst mode rules

| Context | `[]` means | Example |
|---------|-----------|---------|
| Markup mode (top level, `[...]`) | Content block | `[hello]` → renders "hello" |
| Code mode (`#expr`, `context {}`) | Array literal | `page([])` — safe as function arg |
| Code mode standalone expression | Array literal | `[]` as statement → renders "[]" |
| `#` in markup | Enters code mode | `#[]` = array, not content |

---

## Grid & images

### Problem: Images not horizontally aligned
**Fix**: Use `align: (left + horizon, center + horizon, right + horizon)` in grid columns with `horizon` (vertical center) not `bottom`.

### Problem: Text off-center due to visual weight of larger logo
**Fix**: Adjust column widths to compensate. `(1fr, 2fr, 1fr)` is mathematically centered but visually unbalanced if one column's image is much larger. Use `(0.8fr, 2fr, 1.2fr)` or similar to shift visual center.

---

## Line breaks

### Problem: Line break in text content
**Fix**: Use backslash at end of line in Typst markup:
```typst
// Typst line break — backslash at end of line
[I scanned your writing for errors and underlined the corrections. \
Carefully comparing the original and corrected versions...]
```

In Python source, split into two string literals:
```python
lines.append('...common mistakes\\')
lines.append('and improve your writing skills.])')
```

The `\\` in Python produces `\` in Typst, and the newline after the append separates the Typst lines.

---

## `calc.rem-euclid` is the correct function
From the Typst docs: `calc.rem-euclid(dividend, divisor)` calculates the least nonnegative remainder. Use `calc.rem-euclid(4 - num, 4)` for pad-to-four calculations. Not `calc.rem()` (which preserves sign).

---

## Compiler behavior

### Context blocks and convergence
Typst may need multiple layout iterations to resolve `context` blocks. If `pagebreak()` or `page()` inside context block causes oscillation (layout doesn't converge within 5 attempts), separate the calculation and page insertion into two context blocks:

```typst
#let rest-pages = state("rest-pages", 0)
#context {
  let num = here().position().page
  let rem = calc.rem(num, 4)
  if rem != 0 { rest-pages.update(4 - rem) }
}
#context[
  #for i in range(rest-pages.final()) [#pagebreak()]
]
```

---

## Paragraph breaks

### Problem: Paragraphs merge together — no blank line separation

Single `\n` in Typst markup is treated as **whitespace** (collapsed to a space). A **blank line** (`\n\n`) is required for a paragraph break. 

```typst
// \n alone = space, not paragraph break
This is line 1.\nThis is line 2.
// → "This is line 1. This is line 2." (same paragraph)

// \n\n = paragraph break
This is paragraph 1.\n\nThis is paragraph 2.
// → Two separate paragraphs with a blank line between
```

**Data sources**: The ERRANT `corrected_typst` field (produced by `errant_analysis.py:build_corrected_typst()`) stores paragraph separators as single `\n`, not `\n\n`. This is common in NLP pipeline output.

**Fix**: In `build_student_block()` (`generate_report.py`), convert all single `\n` to `\n\n` before placing the text in the Typst source:
```python
marked = markup.replace("\n", "\n\n")
```

Note: The `<u>` → `#underline[]` conversion layer (`convert_markup()`) was **completely eliminated**. `errant_analysis.py:build_corrected_typst()` now emits Typst-native `#underline[text]` directly. The only remaining transformation is the `\n` → `\n\n` doubling.

**Do NOT**: 
- Leave `\n` unmodified (they collapse to spaces → paragraphs merge)
- Use `\` (backslash) for paragraph breaks (that's a LINE break, same paragraph)
- Remove `\n` entirely (space replacement also merges paragraphs)

**Working code** in `src/generate_report.py:build_student_block()`:
```python
markup = student.get("corrected_typst", student.get("corrected_with_markup", ""))
marked = markup.replace("\n", "\n\n")
```

**Working code** in `src/errant_analysis.py:build_corrected_typst()`:
```python
if edit.c_toks:
    result_parts.append(f"#underline[{esc(edit.c_str)}]")
    # Preserve trailing whitespace from last consumed token
    if edit.o_toks:
        last_idx = edit.o_end - 1
        if 0 <= last_idx < len(tokens):
            orig_tok = tokens[last_idx]
            ws = orig_tok.text_with_ws[len(orig_tok.text):]
            result_parts.append(ws)
result = "".join(result_parts)
result = re.sub(r"\](?=[^\s\]\)])", "] ", result)
return result
```
