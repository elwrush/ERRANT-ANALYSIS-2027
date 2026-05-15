#!/usr/bin/env python3
import json
from pathlib import Path

OUTPUTS_DIR = Path("outputs")


def count_words(text: str) -> int:
    return len(text.split())


def main():
    if not OUTPUTS_DIR.exists():
        print(f"No {OUTPUTS_DIR}/ directory found.")
        return

    total = 0
    for d in sorted(OUTPUTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix != ".json":
                continue
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            text = data.get("student_text", "")
            wc = count_words(text)
            data["word_count"] = wc
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            print(f"  {f.parent.name}/{f.name} -> word_count: {wc}")
            total += 1

    print(f"\nDone. Updated {total} file(s).")


if __name__ == "__main__":
    main()
