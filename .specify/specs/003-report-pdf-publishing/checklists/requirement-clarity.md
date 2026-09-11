# Requirement Clarity Checklist — Report PDF Publishing

Checks whether requirements are specific, unambiguous, and have well-defined boundaries.

- [ ] CHK117 Is "no Ghostscript" defined as no `gs` invocation anywhere in `src/`? [§FR-001]
- [ ] CHK118 Is "stripped of transparency" defined technically (composite over white → RGB, no alpha channel)? [§FR-002]
- [ ] CHK119 Is "alpha-free chart" defined (no opacity/fill-opacity/stroke-opacity; opaque white background)? [§FR-003]
- [ ] CHK120 Is the pre-blend colour rule for the target band specified? [§FR-003]
- [ ] CHK121 Is "not collated" defined (no padding, no concatenation, no interleaving)? [§FR-004]
- [ ] CHK122 Is "single files only" unambiguous about removed vs retained artifacts? [§FR-004, §FR-005]
- [ ] CHK123 Is the filename pattern exact? [§FR-006]
- [ ] CHK124 Is the scope of "both pipelines" enumerated? [§FR-001, §FR-002]
- [ ] CHK125 Is the Acrobat "no flattening" verification method defined (PDF object scan)? [§Success Criteria]
- [ ] CHK126 Is "converged" defined (all FR/NFR met or explicitly waived)? [§Success Criteria]
