"""Generate the two deterministic Stage 1 evidence plots from results.json."""
import argparse
import json
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["svg.hashsalt"] = "fir-stage1-paper"

BLUE = "#4C78A8"
ORANGE = "#F58518"
GREEN = "#54A24B"


def make_figures(results_path: Path, output_dir: Path) -> None:
    report = json.loads(results_path.read_text(encoding="utf-8"))
    comparisons = report["comparisons"]
    order = [("gcc10", 1), ("gcc10", 64), ("gcc15", 1), ("gcc15", 64)]
    by_cell = {(row["compiler"], row["block"]): row for row in comparisons}
    series = [
        ("spec_direct", "Wide specialized direct", "hcub_vs_spec_direct_energy_percent", BLUE),
        ("cmsis64_unroll", "CMSIS64 unroll", "hcub_vs_cmsis64_unroll_energy_percent", ORANGE),
        ("partial_direct32x2", "Two int32 partials", "hcub_vs_partial_direct32x2_energy_percent", GREEN),
    ]
    x = np.arange(len(order), dtype=float)
    width = 0.24
    fig, ax = plt.subplots(figsize=(7.1, 3.0), dpi=300, facecolor="white")
    ax.set_facecolor("white")
    hatches = ("//", "..", "xx")
    for idx, (_, label, key, color) in enumerate(series):
        values = [float(Decimal(by_cell[cell][key])) for cell in order]
        ax.bar(x + (idx - 1) * width, values, width, color=color, edgecolor="#333333", linewidth=0.35, hatch=hatches[idx], label=label)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, ["GCC 10\nblock 1", "GCC 10\nblock 64", "GCC 15\nblock 1", "GCC 15\nblock 64"], fontsize=9)
    ax.set_ylabel("Hcub energy relative to comparator (%)", fontsize=9)
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.01), fontsize=8)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.7)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "baseline-robustness.png", dpi=300, facecolor="white", bbox_inches="tight")
    fig.savefig(output_dir / "baseline-robustness.svg", format="svg", facecolor="white", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)

    expl = report["explanation"]
    attributed_nj = Decimal(expl["attributed_transfer_energy_nj"])
    residual_nj = Decimal(expl["residual_energy_nj"])
    total_nj = Decimal(expl["total_energy_delta_nj"])
    attributed_pct = attributed_nj / total_nj * 100
    residual_pct = residual_nj / total_nj * 100
    attributed_uj = float(attributed_nj / 1000)
    residual_uj = float(residual_nj / 1000)
    total_uj = float(total_nj / 1000)
    fig, ax = plt.subplots(figsize=(7.1, 3.0), dpi=300, facecolor="white")
    ax.set_facecolor("white")
    ax.barh([0], [attributed_uj], color=BLUE, height=0.44, label="Direct-SP transfers")
    ax.barh([0], [residual_uj], left=[attributed_uj], color=ORANGE, height=0.44, label="Residual")
    ax.text(attributed_uj / 2, 0, f"Additional SP transfers\n{attributed_pct:.2f}% ({attributed_uj:.2f} µJ)", ha="center", va="center", fontsize=9, color="white")
    ax.text(attributed_uj + residual_uj / 2, 0, f"Residual\n{residual_pct:.2f}%\n{residual_uj:.2f} µJ", ha="center", va="center", fontsize=9, color="#222222")
    ax.set_xlim(0, total_uj * 1.08)
    ax.set_yticks([])
    ax.set_xlabel("Modeled CPU energy increase (µJ)", fontsize=9)
    ax.set_title("Block 1 direct: GCC15 - GCC10", fontsize=9, pad=10)
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    fig.tight_layout(pad=0.7)
    fig.savefig(output_dir / "stack-attribution.png", dpi=300, facecolor="white", bbox_inches="tight")
    fig.savefig(output_dir / "stack-attribution.svg", format="svg", facecolor="white", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--results", type=Path, default=here / "results.json")
    parser.add_argument("--output-dir", type=Path, default=here / "figures")
    args = parser.parse_args()
    make_figures(args.results, args.output_dir)


if __name__ == "__main__":
    main()
