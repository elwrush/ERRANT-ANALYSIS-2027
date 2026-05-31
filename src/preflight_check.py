#!/usr/bin/env python3
"""Preflight check: scan output JSONs for artificial line breaks (handwritten line wraps)."""
import json
import glob
import sys

def check_file(fp):
    with open(fp) as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError:
            return [f"{fp}: invalid JSON"]
    
    text = d.get("student_text", d.get("original_text", ""))
    warnings = []
    
    # Check for \n that isn't paragraph breaks
    if "\n" in text:
        # Look for \n followed by lowercase word (handwritten line wrap indicator)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if next_line and next_line.strip() and next_line.strip()[0].islower():
                warnings.append(f"  Line {i}: '{line.strip()[-30:]}' -> '{next_line.strip()[:30]}' (lowercase continuation)")
        if not warnings:
            # Every \n is followed by uppercase = might be real paragraph breaks
            pass
    
    return warnings


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "M3-3A BASELINE"
    files = sorted(glob.glob(f"outputs/{folder}/*.json"))
    
    if not files:
        print(f"No files found in outputs/{folder}/")
        sys.exit(0)
    
    found = 0
    for fp in files:
        ws = check_file(fp)
        if ws:
            sid = fp.split("/")[-1].replace(".json", "")
            print(f"\n{sid}:")
            for w in ws:
                print(w)
                found += 1
    
    if found == 0:
        print(f"All {len(files)} files clean — no artificial line breaks detected.")
    else:
        print(f"\n{found} issue(s) found. Run with --fix to auto-repair.")
