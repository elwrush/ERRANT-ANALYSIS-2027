#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import requests
import spacy
import errant

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from errant_analysis import (  # noqa: E402
    CORRECTION_PROMPT,
    SUMMARY_PROMPT,
    human_error_type,
    post_classify_other,
    _sanitize_unicode,
)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = 120

PRICING = {
    "google/gemini-2.5-flash-lite-preview-09-2025": {"input": 0.10, "output": 0.40},
    "google/gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

MODELS = ["google/gemini-2.5-flash-lite-preview-09-2025", "google/gemini-2.5-flash-lite", "openai/gpt-4o-mini"]
CORRECTION_TEMP = 0.1
SUMMARY_TEMP = 0.8

STUDENT_PATH = Path("outputs/research/29579.json")
LOCAL_WORKING_DIR = Path("local-working")


def calculate_cost(prompt_tokens, completion_tokens, model):
    rates = PRICING[model]
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000


def call_api(content, temperature, model):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": content},
        ],
    }
    start = time.time()
    r = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    elapsed = round(time.time() - start, 2)
    data = r.json()
    content_text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    return {
        "content": content_text,
        "time": elapsed,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


def run_errant(orig_text, cor_text, nlp, annotator):
    orig_text = orig_text.strip()
    cor_text = cor_text.strip()
    if not cor_text or orig_text == cor_text:
        return {"edits": 0, "errors": [], "identity": True, "error_rate": 0}

    orig_doc = nlp(orig_text)
    cor_doc = annotator.parse(cor_text)
    edits = annotator.annotate(orig_doc, cor_doc)

    error_groups = {}
    for e in edits:
        e_type = e.type
        if e_type in ("OTHER", "R:OTHER") and e.o_toks and e.c_toks:
            e_type = post_classify_other(e.o_str, e.c_str)
        if e_type in ("UNK", "U:SPACE"):
            continue
        example = f"{e.o_str.strip()} -> {e.c_str.strip()}" if e.o_str and e.c_str else str(e.c_str)
        if e_type not in error_groups:
            error_groups[e_type] = {"type": e_type, "example": example, "count": 0}
        error_groups[e_type]["count"] += 1

    errors_list = sorted(error_groups.values(), key=lambda x: x["count"], reverse=True)
    total_edits = sum(e["count"] for e in errors_list)
    word_count = len(orig_text.split())
    error_rate = round(total_edits / word_count * 100) if word_count > 0 else 0

    return {"edits": total_edits, "errors": errors_list, "identity": False, "error_rate": error_rate}


def build_error_list(errors):
    if not errors:
        return ""
    top5 = errors[:5]
    return "\n".join(
        f"- {human_error_type(e['type'])} ({e['type']}): {e['count']} time(s) (e.g. {e['example']})"
        for e in top5
    )


def fmt_cost(c):
    return f"${c:.4f}"


def fmt_time(t):
    return f"{t:.2f}s"


def main():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not set.")
        sys.exit(1)

    if not STUDENT_PATH.exists():
        print(f"Error: {STUDENT_PATH} not found.")
        sys.exit(1)

    with open(STUDENT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    student_id = data["student_id"]
    name = data.get("name", "Unknown")
    original_text = data["student_text"].strip()
    word_count = data.get("word_count", 0)

    print(f"Loaded {name} ({student_id}), {word_count} words\n")

    nlp = spacy.load("en_core_web_sm")
    annotator = errant.load("en")

    results = {}

    for model in MODELS:
        print(f"--- Testing model: {model} ---")
        model_result = {
            "model": model,
            "original_text": original_text,
            "word_count": word_count,
        }

        # --- Correction ---
        cor_ok = False
        corrected_text = None
        print("  Correction...")
        try:
            prompt = CORRECTION_PROMPT.format(text=original_text)
            cor_api = call_api(prompt, CORRECTION_TEMP, model)
            corrected_text = cor_api["content"]
            cost = round(calculate_cost(cor_api["prompt_tokens"], cor_api["completion_tokens"], model), 6)
            model_result["correction"] = {
                "time": cor_api["time"],
                "prompt_tokens": cor_api["prompt_tokens"],
                "completion_tokens": cor_api["completion_tokens"],
                "total_tokens": cor_api["total_tokens"],
                "cost": cost,
                "corrected_text": corrected_text,
            }
            print(f"    Time: {cor_api['time']}s, Tokens: {cor_api['total_tokens']}, Cost: ${cost:.4f}")
            cor_ok = True
        except Exception as e:
            print(f"    ERROR: {e}")
            model_result["correction"] = {"error": str(e)}

        # --- ERRANT analysis ---
        if cor_ok and corrected_text:
            print("  ERRANT analysis...")
            try:
                errant_result = run_errant(original_text, corrected_text, nlp, annotator)
                model_result["errant"] = errant_result
                print(f"    Edits: {errant_result['edits']}, Rate: {errant_result['error_rate']}%, Identity: {errant_result['identity']}")
            except Exception as e:
                print(f"    ERRANT ERROR: {e}")
                model_result["errant"] = {"error": str(e)}

        # --- Summary generation ---
        if cor_ok and corrected_text:
            print("  Summary...")
            try:
                errs = model_result.get("errant", {})
                if isinstance(errs, dict) and "error" not in errs:
                    errors = errs.get("errors", [])
                else:
                    errors = []
                error_list_str = build_error_list(errors)
                sample = original_text[:2000]
                err_rate_val = errs.get("error_rate", 0) if isinstance(errs, dict) else 0
                summary_prompt = SUMMARY_PROMPT.format(
                    name=name,
                    error_rate=err_rate_val,
                    error_list=error_list_str,
                    original_text=sample,
                )
                sum_api = call_api(summary_prompt, SUMMARY_TEMP, model)
                summary_text = _sanitize_unicode(sum_api["content"])
                cost = round(calculate_cost(sum_api["prompt_tokens"], sum_api["completion_tokens"], model), 6)
                model_result["summary"] = {
                    "time": sum_api["time"],
                    "prompt_tokens": sum_api["prompt_tokens"],
                    "completion_tokens": sum_api["completion_tokens"],
                    "total_tokens": sum_api["total_tokens"],
                    "cost": cost,
                    "summary_text": summary_text,
                }
                print(f"    Time: {sum_api['time']}s, Tokens: {sum_api['total_tokens']}, Cost: ${cost:.4f}")
            except Exception as e:
                print(f"    SUMMARY ERROR: {e}")
                model_result["summary"] = {"error": str(e)}

        results[model] = model_result

    # --- Save comparison JSON ---
    LOCAL_WORKING_DIR.mkdir(parents=True, exist_ok=True)
    comp_path = LOCAL_WORKING_DIR / "model_comparison.json"
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump({
            "student_id": student_id,
            "name": name,
            "word_count": word_count,
            "comparison_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved comparison to {comp_path}")

    # --- Print comparison tables ---
    print(f"\n=== Model Comparison: {name} ({student_id}) ===\n")

    # Correction table
    print("CORRECTION (temp=0.1):")
    cor_header = f"{'Model':>24}{'Time':>12}{'Prompt_tok':>12}{'Output_tok':>12}{'Cost':>12}{'Edits':>8}{'Error_rate':>10}{'Identity':>8}"
    print(cor_header)
    sep_len = len(cor_header)
    print("-" * sep_len)

    cor_rows = []
    for model in MODELS:
        mr = results.get(model, {})
        cor = mr.get("correction", {})
        err = mr.get("errant", {})
        if "error" in cor or not isinstance(err, dict) or "error" in err:
            cor_rows.append(f"  {model:<22}  {'ERROR':>7}")
        else:
            model_name = model.replace("google/", "").replace("openai/", "").replace("-preview-09-2025", "-preview")
            identity = "Yes" if err.get("identity") else "No"
            row = (
                f"  {model_name:<22}"
                f"  {fmt_time(cor['time']):>8}"
                f"  {cor['prompt_tokens']:>10d}"
                f"  {cor['completion_tokens']:>10d}"
                f"  {fmt_cost(cor['cost']):>10}"
                f"  {err['edits']:>6d}"
                f"  {err['error_rate']:>7d}%"
                f"  {identity:>6}"
            )
            cor_rows.append(row)
    for row in cor_rows:
        print(row)

    print()

    # Summary table
    print("SUMMARY (temp=0.8):")
    sum_header = f"{'Model':>24}{'Time':>12}{'Prompt_tok':>12}{'Output_tok':>12}{'Cost':>12}"
    print(sum_header)
    sep_len = len(sum_header)
    print("-" * sep_len)

    sum_rows = []
    for model in MODELS:
        mr = results.get(model, {})
        s = mr.get("summary", {})
        if "error" in s:
            sum_rows.append(f"  {model:<22}  {'ERROR':>7}")
        else:
            model_name = model.replace("google/", "").replace("openai/", "").replace("-preview-09-2025", "-preview")
            row = (
                f"  {model_name:<22}"
                f"  {fmt_time(s['time']):>8}"
                f"  {s['prompt_tokens']:>10d}"
                f"  {s['completion_tokens']:>10d}"
                f"  {fmt_cost(s['cost']):>10}"
            )
            sum_rows.append(row)
    for row in sum_rows:
        print(row)

    print()

    # --- VERDICT ---
    print("=== VERDICT ===")
    cor_data = {}
    for model in MODELS:
        mr = results.get(model, {})
        cor = mr.get("correction", {})
        err = mr.get("errant", {})
        if "error" not in cor and isinstance(err, dict) and "error" not in err:
            model_name = model.replace("google/", "").replace("openai/", "").replace("-preview-09-2025", "-preview")
            cor_data[model_name] = {"cost": cor["cost"], "edits": err["edits"]}
    sum_data = {}
    for model in MODELS:
        mr = results.get(model, {})
        s = mr.get("summary", {})
        if "error" not in s:
            model_name = model.replace("google/", "").replace("openai/", "").replace("-preview-09-2025", "-preview")
            sum_data[model_name] = {"cost": s["cost"]}

    if len(cor_data) == 2:
        names = list(cor_data.keys())
        m1, m2 = names
        c1, c2 = cor_data[m1], cor_data[m2]
        cheaper = m1 if c1["cost"] < c2["cost"] else m2
        cheaper_cost = min(c1["cost"], c2["cost"])
        costlier_cost = max(c1["cost"], c2["cost"])
        ratio = round(costlier_cost / cheaper_cost) if cheaper_cost > 0 else float("inf")
        edit_diff_pct = abs(c1["edits"] - c2["edits"]) / max(c1["edits"], c2["edits"], 1)
        edits_desc = "similar edits" if edit_diff_pct < 0.2 else f"{c1['edits']} vs {c2['edits']} edits"
        print(f"Best correction value: {cheaper} (${cheaper_cost:.4f} vs ${costlier_cost:.4f}, {ratio}x cheaper, {edits_desc})")

    if len(sum_data) == 2:
        names = list(sum_data.keys())
        m1, m2 = names
        s1, s2 = sum_data[m1], sum_data[m2]
        cheaper = m1 if s1["cost"] < s2["cost"] else m2
        cheaper_cost = min(s1["cost"], s2["cost"])
        costlier_cost = max(s1["cost"], s2["cost"])
        ratio = round(costlier_cost / cheaper_cost) if cheaper_cost > 0 else float("inf")
        print(f"Best summary value: {cheaper} (${cheaper_cost:.4f} vs ${costlier_cost:.4f}, {ratio}x cheaper)")


if __name__ == "__main__":
    main()
