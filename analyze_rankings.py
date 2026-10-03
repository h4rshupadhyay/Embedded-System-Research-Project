#!/usr/bin/env python3
"""
analyze_rankings.py
===================
Statistical and rank-flip analysis of the FIR energy experiment results.

Metrics computed
----------------
1. Kendall's τ_b  — global rank correlation between Cycles and Energy_nJ
2. Spearman's ρ   — global rank correlation (monotonicity)
3. Top-1 agreement — fraction of conditions where the fastest variant is
                     also the most energy-efficient
4. Pairwise rank-flip frequency — fraction of (condition, variant-pair)
   comparisons where the Cycles ordering contradicts the Energy ordering,
   broken down by relative cycle gap Δt = |tA−tB| / min(tA,tB)
5. Rank-flip rate vs Δt threshold table — shows how rank-flip probability
   decays as the gap between variants widens
"""

import sys
import pandas as pd
import numpy as np
from scipy.stats import kendalltau, spearmanr
import itertools

CSV_FILE = "experiment_results.csv"

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
try:
    df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    print(f"ERROR: '{CSV_FILE}' not found. Run 'python3 run_experiments.py' first.")
    sys.exit(1)

print(f"Loaded {len(df)} rows from '{CSV_FILE}'")
print(f"Columns: {list(df.columns)}\n")

VARIANTS = df["Variant"].unique().tolist()
CONDITIONS = ["Opt", "Taps", "Block"]

# ─────────────────────────────────────────────────────────────────────────────
# 1. Global rank correlation
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("1. Global Rank Correlation (all rows)")
print("=" * 60)

tau_b, p_tau = kendalltau(df["Cycles"], df["Energy_nJ"])
rho,   p_rho = spearmanr(df["Cycles"], df["Energy_nJ"])

print(f"  Kendall τ_b : {tau_b:.4f}  (p = {p_tau:.2e})")
print(f"  Spearman ρ  : {rho:.4f}  (p = {p_rho:.2e})\n")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Per-condition Kendall τ distribution
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("2. Per-Condition Kendall τ Distribution")
print("=" * 60)

per_cond_tau = []
for name, grp in df.groupby(CONDITIONS):
    if len(grp) < 2:
        continue
    tau, _ = kendalltau(grp["Cycles"].values, grp["Energy_nJ"].values)
    per_cond_tau.append({"Condition": name, "tau": tau})

tau_series = pd.DataFrame(per_cond_tau)["tau"]
print(f"  N conditions : {len(tau_series)}")
print(f"  Mean τ       : {tau_series.mean():.4f}")
print(f"  Median τ     : {tau_series.median():.4f}")
print(f"  Std τ        : {tau_series.std():.4f}")
print(f"  Min τ        : {tau_series.min():.4f}")
print(f"  Max τ        : {tau_series.max():.4f}")
print(f"  Conditions with τ  < 1.0 (any rank flip)  : {(tau_series < 1.0).sum()}")
print(f"  Conditions with τ  < 0.0 (majority flips) : {(tau_series < 0.0).sum()}\n")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Top-1 agreement
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("3. Top-1 Agreement (fastest by Cycles == lowest Energy)")
print("=" * 60)

top1_agree = 0
top1_total = 0
for name, grp in df.groupby(CONDITIONS):
    if len(grp) < 2:
        continue
    top1_total += 1
    fastest_cycle  = grp.loc[grp["Cycles"].idxmin(),    "Variant"]
    lowest_energy  = grp.loc[grp["Energy_nJ"].idxmin(), "Variant"]
    if fastest_cycle == lowest_energy:
        top1_agree += 1

print(f"  Top-1 agreement: {top1_agree}/{top1_total} "
      f"({100*top1_agree/top1_total:.1f}%)\n")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Pairwise rank-flip analysis
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("4. Pairwise Rank-Flip Analysis")
print("=" * 60)

records = []   # (delta_t, is_flip)

for name, grp in df.groupby(CONDITIONS):
    grp = grp.reset_index(drop=True)
    n   = len(grp)
    for i, j in itertools.combinations(range(n), 2):
        t_i = grp.loc[i, "Cycles"]
        t_j = grp.loc[j, "Cycles"]
        e_i = grp.loc[i, "Energy_nJ"]
        e_j = grp.loc[j, "Energy_nJ"]

        if t_i == 0 or t_j == 0 or e_i == 0 or e_j == 0:
            continue

        t_ratio = t_i / t_j
        e_ratio = e_i / e_j

        is_flip = (t_ratio > 1.0 and e_ratio < 1.0) or \
                  (t_ratio < 1.0 and e_ratio > 1.0)

        # Relative cycle gap Δt = |tA − tB| / min(tA, tB)
        delta_t = abs(t_i - t_j) / min(t_i, t_j)

        records.append({"delta_t": delta_t, "flip": int(is_flip)})

pairs_df    = pd.DataFrame(records)
rank_flips  = pairs_df["flip"].sum()
total_pairs = len(pairs_df)

print(f"  Total pairwise comparisons : {total_pairs}")
print(f"  Rank flips                 : {rank_flips}")
print(f"  Overall flip rate          : {rank_flips/total_pairs*100:.2f}%\n")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Rank-flip rate vs cycle-gap threshold
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("5. Rank-Flip Rate vs Cycle-Gap Threshold Δt")
print("=" * 60)
print(f"  {'Δt threshold':>14}  {'Pairs ≤ Δt':>12}  {'Flips':>8}  {'Flip Rate':>10}")
print(f"  {'-'*14}  {'-'*12}  {'-'*8}  {'-'*10}")

thresholds = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.00, 2.00, float("inf")]
for thr in thresholds:
    subset = pairs_df[pairs_df["delta_t"] <= thr]
    n_pairs = len(subset)
    n_flips = subset["flip"].sum()
    rate    = (n_flips / n_pairs * 100) if n_pairs > 0 else float("nan")
    thr_str = f"≤ {thr:.2f}" if thr != float("inf") else "  all"
    print(f"  {thr_str:>14}  {n_pairs:>12,}  {n_flips:>8,}  {rate:>9.2f}%")

print()

# ─────────────────────────────────────────────────────────────────────────────
# 6. Per-variant energy summary
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("6. Per-Variant Mean Energy (nJ) by Optimisation Level")
print("=" * 60)

pivot = df.pivot_table(
    values="Energy_nJ",
    index="Opt",
    columns="Variant",
    aggfunc="mean"
)
print(pivot.to_string())
print()

# ─────────────────────────────────────────────────────────────────────────────
# 7. Save summary to CSV
# ─────────────────────────────────────────────────────────────────────────────
pairs_df.to_csv("rank_flip_analysis.csv", index=False)
print("✓ Pairwise flip data saved to 'rank_flip_analysis.csv'")
print("  Done.")
