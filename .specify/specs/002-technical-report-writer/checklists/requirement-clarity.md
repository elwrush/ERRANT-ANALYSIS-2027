# Requirement Clarity Checklist — Technical Report Writer

Checks whether requirements are specific, unambiguous, and have well-defined boundaries.

- [ ] CHK013 Is "interactive session" defined precisely enough — what exactly does the agent ask, in what format, and what are valid/invalid responses? [§FR-002, FR-003]
- [ ] CHK014 Is "grayscale-safe" defined with an unambiguous technical spec (hatching patterns, fill alphas, colour constraints)? [§FR-007, §C-003 Grayscale Rules]
- [ ] CHK015 Is the Markdown draft format specified in sufficient detail to produce deterministic output (heading level, table syntax, image embedding, citation format)? [§plan.md Component 4]
- [ ] CHK016 Is "AI slop" defined with specific prohibitions (em dashes, clichés, hedging, forced informality)? [§FR-008, §FR-009]
- [ ] CHK017 Is "Australian teacher voice" defined with specific examples of permitted and prohibited language? [§FR-009]
- [ ] CHK018 Is "educated Australian" voice defined — what distinguishes it from general English academic tone? [§FR-009]
- [ ] CHK019 Is "baseline section" defined — what exact heading text does each section use? [§FR-004]
- [ ] CHK020 Is "custom section insertion point" defined — is it before/after a baseline section, at a 0-based index, or by section title? [§FR-003, §data-model.md CustomSection]
- [ ] CHK021 Is "page or paragraph number" defined for references — is `(p. 42)` sufficient, or must it include `(Author, 2020, p. 42)` APA full format? [§FR-011]
- [ ] CHK022 Is the PDF output path defined — where is the final PDF saved, and what is its naming convention? [§plan.md Component 5]
- [ ] CHK023 Is the "draft not signed off" note defined — exact text and location in the file? [§Edge Cases, §plan.md Component 5]
- [ ] CHK024 Is "benchmark student proficiency against international standards" defined with specific metrics (CEFR level distribution, Cambridge English Scale scores)? [§FR-004 Section 4]
