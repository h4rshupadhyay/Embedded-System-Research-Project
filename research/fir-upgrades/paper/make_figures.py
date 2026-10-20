"""Build editable vector and publication PNG figures from admitted JSON inputs."""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

matplotlib.rcParams["svg.hashsalt"] = "fir-upgrades-paper"
BLUE, ORANGE, GREEN, GREY = "#356A8A", "#D47B35", "#4C8B69", "#58616A"


def _save(fig, output: Path, name: str) -> None:
    fig.savefig(output / f"{name}.png", dpi=300, facecolor="white", bbox_inches="tight")
    fig.savefig(output / f"{name}.svg", format="svg", facecolor="white",
                bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def representation_figure(output: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.1, 3.15))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.0); ax.axis("off")

    def box(x, y, w, h, title, body, color):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.08",
                               linewidth=1.1, edgecolor=color, facecolor="white")
        ax.add_patch(patch)
        ax.text(x+w/2, y+h*.68, title, ha="center", va="center", fontsize=8,
                weight="bold", color=color)
        ax.text(x+w/2, y+h*.29, body, ha="center", va="center", fontsize=6.6)

    box(.15, 3.55, 2.3, 1.05, "Direct history", "x[n], x[n−1], …\nx[n−47]", BLUE)
    box(3.05, 3.55, 2.35, 1.05, "Native groups", "g₀ and g₁ accumulate\nin int32", GREEN)
    box(6.0, 3.55, 2.25, 1.05, "Widen, then\nreduce", "int64(g₀) + int64(g₁)", ORANGE)
    box(9.0, 3.55, 2.65, 1.05, "One final Q", "floor / 2¹⁵,\nthen saturate", GREY)
    for x0, x1 in [(2.48, 2.98), (5.43, 5.93), (8.28, 8.93)]:
        ax.add_patch(FancyArrowPatch((x0, 4.08), (x1, 4.08), arrowstyle="-|>",
                                     mutation_scale=10, color=GREY, linewidth=1))
    box(.65, .8, 4.2, 1.4, "Transposed state", "weighted suffix sums zᵢ are retained\nold values feed each update", GREEN)
    box(7.15, .8, 4.2, 1.4, "Cross-representation\ncomparison", "sharing, state representation and\nrealization change together", ORANGE)
    ax.text(6, 2.55, "Hcub vs ordinary transposed: suffix equations and layout are fixed",
            ha="center", va="center", fontsize=8, color=GREY)
    ax.text(6, .32, "Each representation reconstructs the same exact sum before final quantization",
            ha="center", va="center", fontsize=7.5, color=GREY)
    _save(fig, output, "representation-lifetime")


def sensitivity_figure(analysis_path: Path, output: Path) -> None:
    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    pairs = data["pairs"]
    order = [(c, b) for c in ("gcc10", "gcc15") for b in (1, 64)]
    specs = [("trans_const", "Hcub − ordinary transposed"),
             ("partial_direct32x2", "Hcub − partial direct")]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.65), sharey=True)
    lam = np.linspace(.5, 2, 151)
    cell_colors = ["#356A8A", "#6C91A8", "#4C8B69", "#9A7746"]
    for ax, (control, title) in zip(axes, specs):
        rows = {(p["compiler"], p["block"]): p for p in pairs
                if p["left_variant"] == "trans_hcub_demand" and p["right_variant"] == control}
        for i, key in enumerate(order):
            row = rows[key]
            a, b = Decimal(row["affine"]["A_nj"]), Decimal(row["affine"]["B_nj"])
            values = [float(a + b * Decimal(str(v))) for v in lam]
            ax.plot(lam, values, color=cell_colors[i], linewidth=1.6,
                    label=f"{key[0].upper()} block {key[1]}")
            ax.scatter([1], [float(a+b)], color=cell_colors[i], edgecolor="white", s=22, zorder=3)
        ax.axhline(0, color="#333333", linewidth=.75)
        ax.axvline(1, color="#777777", linewidth=.65, linestyle="--")
        ax.set_title(title, fontsize=8.5)
        ax.set_xlabel("RAM-weight multiplier λ", fontsize=8)
        ax.grid(color="#E1E4E6", linewidth=.45)
        ax.tick_params(labelsize=7)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Hcub minus control (nJ / 257 outputs)", fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, ncol=4, loc="lower center",
               bbox_to_anchor=(.5, -.04), fontsize=7)
    fig.tight_layout(rect=(0, .12, 1, 1), pad=.7)
    _save(fig, output, "ram-sensitivity")


def panel_figure(summary_path: Path, output: Path) -> None:
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = [r for r in data["fixed_compiler_cells"] if r["filter"].startswith("wide_")]
    group_order = [(f, c, b) for f in ("wide_lp2800", "wide_lp4600")
                   for c in ("gcc10", "gcc15") for b in (1, 64)]
    condition_order = [(s, regime) for s in ("adc", "full")
                       for regime in ("startup", "post_startup")]
    xbase = {key: i for i, key in enumerate(group_order)}
    jitter = {key: (i - 1.5) * .12 for i, key in enumerate(condition_order)}
    fig, ax = plt.subplots(figsize=(7.1, 3.0))
    for r in rows:
        group = (r["filter"], r["compiler"], r["block"])
        cond = (r["stimulus"], r["regime"])
        x = xbase[group] + jitter[cond]
        hcub = Decimal(r["all_form_winner"]["energy_nj_per_output"])
        # all_form_winner is the cell minimum, so recover Hcub from the admitted
        # summary's per-form energy where present in the saved cell record.
        # The panel summary explicitly retains Hcub/ordinary but not Hcub energy;
        # derive its absolute energy using the matched ordinary and percentage.
        ordinary = Decimal(r["all_form_winner"]["energy_nj_per_output"])
        # The all-form minimum can be another form; use the per-row results below
        # in the enriched plot input generated alongside the summary.
        h_margin = Decimal(r["hcub_vs_ordinary_percent"])
        # Hcub-minus-D_old/new energy margins are generated from panel-results.
        # Keep plotted values in relative percent so zero retains the decision boundary.
        old = Decimal(r["D_old"]["energy_nj_per_output"])
        new = Decimal(r["D_new"]["energy_nj_per_output"])
        # Summary's Hcub energy is recoverable only when the full raw inventory is
        # supplied; this function gets the enriched rows written by main().
        if "hcub_energy_nj_per_output" not in r:
            continue
        h = Decimal(r["hcub_energy_nj_per_output"])
        old_pct, new_pct = float((h / old - 1) * 100), float((h / new - 1) * 100)
        ax.scatter([x], [old_pct], color=BLUE, marker="o", s=19, zorder=3)
        ax.scatter([x], [new_pct], color=ORANGE, marker="s", s=19, zorder=3)
    ax.axhline(0, color="#333333", linewidth=.8)
    ax.set_xticks(range(8), [f"{f[-4:]}\n{c.upper()} / {b}" for f,c,b in group_order], fontsize=7)
    ax.set_ylabel("Hcub energy vs comparator (%)", fontsize=8)
    ax.set_xlabel("Wide design / fixed compiler / block; four paired conditions per group", fontsize=8)
    ax.grid(axis="y", color="#E1E4E6", linewidth=.45); ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0],[0], color=BLUE, marker="o", linestyle="", label="Hcub vs D_old"),
                       Line2D([0],[0], color=ORANGE, marker="s", linestyle="", label="Hcub vs D_new")],
              frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(.5, 1.01), fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, .94), pad=.75)
    _save(fig, output, "panel-boundaries")


def make_figures(analysis: Path, panel_results: Path, panel_summary: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    representation_figure(output)
    sensitivity_figure(analysis, output)
    summary = json.loads(panel_summary.read_text(encoding="utf-8"))
    raw = json.loads(panel_results.read_text(encoding="utf-8"))
    admitted = {tuple(r["identity"][k] for k in ("filter", "compiler", "block", "stimulus", "regime", "variant")): r
                for r in raw["rows"] if r["status"] == "admitted"}
    for cell in summary["fixed_compiler_cells"]:
        if not cell["filter"].startswith("wide_"):
            continue
        key = (cell["filter"], cell["compiler"], cell["block"], cell["stimulus"], cell["regime"], "trans_hcub_demand")
        row = admitted.get(key)
        if row is None:
            continue
        cell["hcub_energy_nj_per_output"] = row["energy_nj_per_output"]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        enriched = Path(tmp) / "summary.json"
        enriched.write_text(json.dumps(summary), encoding="utf-8")
        panel_figure(enriched, output)


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", type=Path, default=here.parent / "analysis/analysis.json")
    parser.add_argument("--panel-results", type=Path, default=here.parent / "panel-results.json")
    parser.add_argument("--panel-summary", type=Path, default=here.parent / "panel-summary.json")
    parser.add_argument("--output-dir", type=Path, default=here / "figures")
    args = parser.parse_args()
    make_figures(args.analysis, args.panel_results, args.panel_summary, args.output_dir)


if __name__ == "__main__":
    main()
