#!/usr/bin/env python3
"""
Phase 2: Desk statistics (RQ1–RQ3).
Reads Phase 1 aggregated output and produces:
  - RQ1: Error-type frequency rankings + bar chart
  - RQ2: Error-rate threshold CDF + dual histogram
  - RQ3: Mann-Whitney U per error type + Cliff's δ heatmap
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("outputs/analysis")
CHART_DIR = Path("outputs/charts")
DATA_DIR = Path("outputs/analysis")


def load_data():
    by_file = pd.read_parquet(DATA_DIR / "by_file.parquet")
    by_student = pd.read_parquet(DATA_DIR / "by_student.parquet")
    by_long = pd.read_parquet(DATA_DIR / "by_file_long.parquet")
    return by_file, by_student, by_long


def rq1_error_rankings(by_student: pd.DataFrame, by_long: pd.DataFrame):
    """RQ1: Error-type frequency rankings by cohort."""
    print("=" * 60)
    print("RQ1: ERROR-TYPE FREQUENCY RANKINGS BY COHORT")
    print("=" * 60)

    # Exclude high-delta files from error-type analysis
    by_long_clean = by_long[~by_long["record_id"].isin(HIGH_DELTA_RECORDS)]

    # Aggregate per cohort: sum of errors per type
    cohort_totals = by_long_clean.groupby(["class", "error_type"])["count"].sum().reset_index()
    cohort_word_counts = by_student.groupby("class_label")["total_word_count"].sum()

    result = {}
    for cohort in ["M2", "M3"]:
        subset = cohort_totals[cohort_totals["class"] == cohort].copy()
        total_words = cohort_word_counts.get(cohort, 1)
        subset["per_100w"] = (subset["count"] / total_words * 100).round(2)
        subset = subset.sort_values("count", ascending=False).head(15)
        result[cohort] = subset
        print(f"\n--- {cohort} cohort (total words: {total_words:,}) ---")
        print(f"{'Rank':<5} {'Error Type':<25} {'Count':<8} {'Per 100w':<10}")
        for i, (_, row) in enumerate(subset.iterrows(), 1):
            print(f"{i:<5} {row['error_type']:<25} {row['count']:<8} {row['per_100w']:<10.2f}")

    return result


def rq2_thresholding(by_student: pd.DataFrame):
    """RQ2: Error-rate threshold CDF and dual histogram."""
    print("\n" + "=" * 60)
    print("RQ2: ERROR-RATE THRESHOLDING")
    print("=" * 60)

    thresholds = [10, 15, 20, 25]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, cohort in enumerate(["M2", "M3"]):
        subset = by_student[by_student["class_label"] == cohort]["mean_error_rate"]
        print(f"\n--- {cohort} cohort (n={len(subset)} students) ---")

        total = len(subset)
        for thresh in thresholds:
            count = (subset > thresh).sum()
            pct = count / total * 100
            print(f"  >{thresh}%: {count}/{total} ({pct:.1f}%)")

        # CDF
        sorted_vals = np.sort(subset)
        cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        axes[0].plot(sorted_vals, cdf, label=f"{cohort} (n={total})", linewidth=2)
        for thresh in thresholds:
            axes[0].axvline(thresh, color="gray", linestyle="--", alpha=0.4)

        # Histogram
        axes[1].hist(subset, bins=20, alpha=0.5, label=f"{cohort} (n={total})", density=True)

    axes[0].set_xlabel("Error rate (%)")
    axes[0].set_ylabel("CDF")
    axes[0].set_title("Cumulative Error-Rate Distribution")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].set_xlabel("Error rate (%)")
    axes[1].set_ylabel("Density")
    axes[1].set_title("Error-Rate Distribution")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    path = CHART_DIR / "rq2_thresholding.png"
    fig.savefig(path, dpi=150)
    print(f"\nChart saved: {path}")
    plt.close(fig)

    return {c: {"n": len(s), "mean": s.mean(), "median": s.median(), "std": s.std()}
            for c, s in [("M2", by_student[by_student["class_label"] == "M2"]["mean_error_rate"]),
                         ("M3", by_student[by_student["class_label"] == "M3"]["mean_error_rate"])]}


def cliff_delta(x, y):
    """Compute Cliff's delta (non-parametric effect size)."""
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return 0.0
    greater = sum(1 for xi in x for yj in y if xi > yj)
    less = sum(1 for xi in x for yj in y if xi < yj)
    return (greater - less) / (n1 * n2)


HIGH_DELTA_RECORDS = {"28997", "28859", "28887", "29579", "28858", "28849", "28984", "29508", "29382"}


def rq3_cohort_comparison(by_file: pd.DataFrame, by_long: pd.DataFrame):
    """RQ3: Between-cohort error-type divergence (per-student, per-type
    mean normalised counts, Mann-Whitney U, Cliff's delta).
    Excludes V7 high-delta files from error-type-level analysis."""
    print("\n" + "=" * 60)
    print("RQ3: BETWEEN-COHORT ERROR-TYPE DIVERGENCE (per-student)")
    print("=" * 60)

    # Exclude high-delta files per validation plan
    n_before = len(by_long)
    by_long_clean = by_long[~by_long["record_id"].isin(HIGH_DELTA_RECORDS)].copy()
    n_excluded = n_before - len(by_long_clean)
    print(f"Excluded {n_excluded} records with V7 high-delta from error-type analysis")

    # Per-student mean normalised counts (not per-file — avoids pseudoreplication)
    student_type_means = by_long_clean.groupby(["student_id", "class", "error_type"])["count_per_100w"].mean().reset_index()
    m2_students = student_type_means[student_type_means["class"] == "M2"]
    m3_students = student_type_means[student_type_means["class"] == "M3"]

    all_types = sorted(by_long["error_type"].unique())
    results = []
    for err_type in all_types:
        m2_vals = m2_students[m2_students["error_type"] == err_type]["count_per_100w"].values
        m3_vals = m3_students[m3_students["error_type"] == err_type]["count_per_100w"].values

        # Require at least 5 students in each cohort with this error type
        if len(m2_vals) < 5 or len(m3_vals) < 5:
            continue

        stat, p = mannwhitneyu(m2_vals, m3_vals, alternative="two-sided")
        cd = cliff_delta(m2_vals, m3_vals)

        results.append({
            "error_type": err_type,
            "m2_n_students": len(m2_vals),
            "m3_n_students": len(m3_vals),
            "m2_mean_per_100w": round(m2_vals.mean(), 4),
            "m3_mean_per_100w": round(m3_vals.mean(), 4),
            "delta": round(m3_vals.mean() - m2_vals.mean(), 4),
            "mannwhitney_u": stat,
            "p_value": p,
            "cliffs_delta": round(cd, 4),
            "dominant_cohort": "M3" if cd < 0 else "M2",
        })

    df = pd.DataFrame(results)
    n_tests = len(df)
    bonferroni_alpha = 0.05 / n_tests if n_tests > 0 else 0.05
    df["significant"] = df["p_value"] < bonferroni_alpha
    df["p_adjusted"] = (df["p_value"] * n_tests).clip(upper=1.0).round(4)

    df = df.sort_values("cliffs_delta", key=abs, ascending=False).reset_index(drop=True)

    print(f"Tests performed: {n_tests} (Bonferroni alpha = {bonferroni_alpha:.6f})")
    print(f"Significant after correction: {df['significant'].sum()}")
    print(f"\n{'Rank':<5} {'Error Type':<25} {'M2/100w':<10} {'M3/100w':<10} {'Cliff δ':<10} {'p_adj':<10} {'Sig':<5}")
    for i, (_, row) in enumerate(df.iterrows(), 1):
        sig = "*" if row["significant"] else ""
        print(f"{i:<5} {row['error_type']:<25} {row['m2_mean_per_100w']:<10.4f} {row['m3_mean_per_100w']:<10.4f} {row['cliffs_delta']:<10.4f} {row['p_adjusted']:<10.4f} {sig:<5}")

    return df


def rq3_heatmap(df: pd.DataFrame):
    """Differential heatmap: M2-dominant vs M3-dominant error types."""
    if df.empty:
        print("No data for heatmap.")
        return

    top = df.head(20).copy()
    top["direction"] = top["cliffs_delta"].apply(lambda x: "← M2" if x > 0 else "M3 →")
    top["abs_delta"] = top["cliffs_delta"].abs()

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = top["cliffs_delta"].apply(lambda x: "#3498db" if x > 0 else "#e74c3c")
    ax.barh(range(len(top)), top["abs_delta"], color=colors, edgecolor="white")

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"{t}  {d}" for t, d in zip(top["error_type"], top["direction"])])
    ax.set_xlabel("|Cliff's δ|")
    ax.set_title("Top 20 Error Types by Between-Cohort Divergence")
    ax.axvline(0.147, color="gray", linestyle=":", alpha=0.6, label="small threshold")
    ax.axvline(0.33, color="gray", linestyle=":", alpha=0.4, label="medium threshold")
    ax.axvline(0.474, color="gray", linestyle=":", alpha=0.2, label="large threshold")
    ax.legend(fontsize=8)
    fig.tight_layout()

    path = CHART_DIR / "rq3_differential_heatmap.png"
    fig.savefig(path, dpi=150)
    print(f"Heatmap saved: {path}")
    plt.close(fig)


def rq1_bar_chart(rankings: dict):
    """Grouped horizontal bar chart: top-15 error types side by side."""
    m2_data = rankings.get("M2")
    m3_data = rankings.get("M3")

    if m2_data is None or m3_data is None:
        return

    # Get union of top-15 types from both cohorts (to align bars)
    m2_types = set(m2_data["error_type"])
    m3_types = set(m3_data["error_type"])
    all_types = sorted(m2_types | m3_types, key=lambda t: (
        m2_data[m2_data["error_type"] == t]["per_100w"].values[0]
        if t in m2_types else 0
    ), reverse=True)[:20]

    m2_vals = [m2_data[m2_data["error_type"] == t]["per_100w"].values[0] if t in m2_types else 0 for t in all_types]
    m3_vals = [m3_data[m3_data["error_type"] == t]["per_100w"].values[0] if t in m3_types else 0 for t in all_types]

    fig, ax = plt.subplots(figsize=(12, 8))
    y = np.arange(len(all_types))
    h = 0.35

    ax.barh(y - h / 2, m2_vals, h, label="M2 (active)", color="#3498db", alpha=0.85)
    ax.barh(y + h / 2, m3_vals, h, label="M3 (former)", color="#e74c3c", alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(all_types)
    ax.set_xlabel("Errors per 100 words")
    ax.set_title("Top Error-Type Frequencies by Cohort")
    ax.legend()
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()

    path = CHART_DIR / "rq1_error_rankings.png"
    fig.savefig(path, dpi=150)
    print(f"Bar chart saved: {path}")
    plt.close(fig)


def main():
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Phase 1 data...")
    by_file, by_student, by_long = load_data()
    print(f"  by_file: {len(by_file)} rows x {len(by_file.columns)} cols")
    print(f"  by_student: {len(by_student)} rows x {len(by_student.columns)} cols")
    print(f"  by_long: {len(by_long)} rows x {len(by_long.columns)} cols")
    print(f"  Error types in long data: {by_long['error_type'].nunique()}")

    # RQ1
    rankings = rq1_error_rankings(by_student, by_long)
    rq1_bar_chart(rankings)

    # RQ2
    threshold_stats = rq2_thresholding(by_student)

    # RQ3
    rq3_df = rq3_cohort_comparison(by_file, by_long)
    rq3_heatmap(rq3_df)

    # Save results
    results = {
        "rq1": {
            c: {
                "total_words": int(
                    by_student[by_student["class_label"] == c]["total_word_count"].sum()
                ),
                "top_15": rankings[c].to_dict("records") if c in rankings else [],
            }
            for c in ["M2", "M3"]
        },
        "rq2": {
            c: threshold_stats[c]
            for c in ["M2", "M3"]
        },
        "rq3": {
            "bonferroni_alpha": round(0.05 / max(len(rq3_df), 1), 6),
            "n_tests": len(rq3_df),
            "n_significant": int(rq3_df["significant"].sum()),
            "results": rq3_df.to_dict("records"),
        },
    }

    with open(OUTPUT_DIR / "desk_statistics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDesk statistics saved: {OUTPUT_DIR / 'desk_statistics.json'}")
    print("\nPhase 2 complete.")


if __name__ == "__main__":
    main()
