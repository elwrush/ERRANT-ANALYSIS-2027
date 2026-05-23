# Plan: Implement Literature-Backed Few-Shot Prompt for GEC

## Goal
Implement a 4-shot GEC prompt following the Goto et al. 2026 / Davis et al. 2024 TOOL template format, and test it on student 30378 (Ti) using the DeepSeek 5-pass pipeline.

## Source: Goto et al. 2026 Appendix A (Figure 4)

```
You are a grammatical error correction tool. Your task is to correct the grammaticality
and spelling in the input sentence. Make the smallest possible change in order to make
the sentence grammatically correct. Change as few words as possible. Do not rephrase
parts of the sentence that are already grammatical. Do not change the meaning of the
sentence by adding or removing information. If the sentence is already grammatically
correct, you should output the original sentence without changing anything. Return only
the corrected text and nothing more.

[FEWSHOT]    ← replaced with 4 example pairs in Input/Output sentence format

Input sentence: [SOURCE]
Output sentence:
```

The `[FEWSHOT]` consists of 4 fixed examples (same for every input), each formatted as:
```
Input sentence: [erroneous sentence]
Output sentence: [corrected sentence]
```

## Step 1: Replace CORRECTION_PROMPT in `src/errant_analysis_deepseek.py`

Replace the current prompt (lines 44-46) with the following:

```python
# Few-shot prompt following Goto et al. 2026 / Davis et al. 2024 TOOL template (Appendix A, Figure 4).
# 4 fixed examples covering common error types: preposition, article, verb tense, word choice.
CORRECTION_PROMPT = """You are a grammatical error correction tool. Your task is to correct the grammaticality and spelling in the input sentence. Make the smallest possible change in order to make the sentence grammatically correct. Change as few words as possible. Do not rephrase parts of the sentence that are already grammatical. Do not change the meaning of the sentence by adding or removing information. If the sentence is already grammatically correct, you should output the original sentence without changing anything. Return only the corrected text and nothing more.

Input sentence: She is good in playing piano.
Output sentence: She is good at playing piano.

Input sentence: He is good student.
Output sentence: He is a good student.

Input sentence: Yesterday I go to the park.
Output sentence: Yesterday I went to the park.

Input sentence: I very like music.
Output sentence: I really like music.

Input sentence: {text}
Output sentence:"""
```

### Example design rationale

| Example | Error type | Input | Output | Why this example |
|---------|-----------|-------|--------|-----------------|
| 1 | Preposition | `good in playing` | `good at playing` | Thai L1 preposition errors are frequent. "in" → "at" is a single-token change |
| 2 | Article | `is good student` | `is a good student` | Article omission is the #1 non-native error. "good student" → "a good student" |
| 3 | Verb tense | `Yesterday I go` | `Yesterday I went` | Tense marking is a key difficulty. "go" → "went" with temporal adverb |
| 4 | Word choice | `very like music` | `really like music` | Thai L1 "very" + verb pattern. "very like" → "really like" |

All examples show **single-token minimal changes** — this is critical: the model observes that "minimal" means changing exactly the word that's wrong, not rewriting the sentence.

## Step 2: Run the analysis

```bash
$env:DEEPSEEK_BATCH_KEY = [Environment]::GetEnvironmentVariable("DEEPSEEK_BATCH_KEY", "User")
$env:PYTHONPATH = "$env:PYTHONPATH;$PWD\src"
python src/errant_analysis_deepseek.py --batch "M2-5A BASELINE" 2>&1
```

This will process all 19 files (or you can target a single student with a separate test script for Ti only).

## Step 3: Evaluate

After running, check the local-working output for Ti (30378):

```bash
python -c "import json; d=json.load(open('local-working/M2-5A BASELINE-30378.json')); print('CORRECTED:'); print(d['corrected_text']); print(); t=sum(e['count'] for e in d['errant_analysis']['errors']); print(f'{t} corrections, {d[\"error_rate\"]}%, {d[\"metadata\"][\"uncertain_edit_count\"]} uncertain')"
```

Compare vs the previous 5-pass DeepSeek output (which was 39 corrections at 53%).

## Key differences from the failed earlier attempt

| Earlier (failed) approach | This (literature-backed) approach |
|---|---|
| Examples showed entire sentences rewritten | Examples show **single-token changes** only |
| "I like play game" → "I like playing games" (2 edits) | "He is good student" → "He is a good student" (1 edit) |
| Used `{role: "user"}` with examples | Uses **system message** per Goto et al. Appendix A |
| Had annotations like "Only 'play' changed to 'playing'" | No annotations — the examples speak for themselves |
| Temperature 1.0 caused too much diversity | Keep temperature 1.0 but let the examples constrain the model |

## Potential adaptation

If the 4 examples are too simple (not representative of multi-edit sentences), swap example 2 or 3 for a sentence with 2-3 minimal edits:

```python
Input sentence: My friend always help me when I need him.
Output sentence: My friend always helps me when I need him.
```

This shows SVA correction while keeping the rest intact — reinforces "change one word only."
