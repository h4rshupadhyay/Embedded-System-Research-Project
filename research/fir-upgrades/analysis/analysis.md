# Saved-event contrast analysis

All pairs use left minus right and the original 257-output stream. Negative modeled energy favors the left variant. RAM stress multiplies both RAM weights by λ over [0.5, 2]; this is arbitrary model sensitivity, not physical uncertainty.

| Compiler | Block | Contrast | ΔE (nJ) | Left relative (%) | A (nJ) | B (nJ) | Root | λ=.5 / 1 / 2 | Event relation |
|---|---:|---|---:|---:|---:|---:|---:|---|---|
| gcc10 | 1 | partial_direct32x2 − spec_direct | -130166.140766 | -32.823801 | -87520.461808 | -42645.678958 | -2.052270 (outside) | left / left / left | left_dominates |
| gcc10 | 1 | trans_hcub_demand − trans_const | 9166.318770 | 3.410536 | -4898.171738 | 14064.490508 | 0.348265 (below) | right / right / right | mixed |
| gcc10 | 1 | trans_hcub_demand − partial_direct32x2 | 11536.956423 | 4.330785 | -32436.319000 | 43973.275423 | 0.737637 (within) | left / right / right | mixed |
| gcc10 | 64 | partial_direct32x2 − spec_direct | -106547.324427 | -41.860155 | -64652.689002 | -41894.635425 | -1.543221 (outside) | left / left / left | left_dominates |
| gcc10 | 64 | trans_hcub_demand − trans_const | -268.042614 | -0.172202 | -13888.913330 | 13620.870716 | 1.019679 (within) | left / left / right | mixed |
| gcc10 | 64 | trans_hcub_demand − partial_direct32x2 | 7403.516161 | 5.002907 | -16661.004146 | 24064.520307 | 0.692347 (within) | left / right / right | mixed |
| gcc15 | 1 | partial_direct32x2 − spec_direct | -103138.843706 | -23.440506 | -62253.689535 | -40885.154171 | -1.522648 (outside) | left / left / left | left_dominates |
| gcc15 | 1 | trans_hcub_demand − trans_const | -11452.561472 | -4.284890 | -22782.813560 | 11330.252088 | 2.010795 (above) | left / left / left | mixed |
| gcc15 | 1 | trans_hcub_demand − partial_direct32x2 | -81038.509580 | -24.056759 | -94335.682384 | 13297.172804 | 7.094417 (above) | left / left / left | mixed |
| gcc15 | 64 | partial_direct32x2 − spec_direct | -110382.398727 | -41.980694 | -69714.748911 | -40667.649816 | -1.714256 (outside) | left / left / left | left_dominates |
| gcc15 | 64 | trans_hcub_demand − trans_const | -10360.343828 | -6.686823 | -21526.654040 | 11166.310212 | 1.927822 (within) | left / left / right | mixed |
| gcc15 | 64 | trans_hcub_demand − partial_direct32x2 | -7977.319073 | -5.229188 | -16351.634074 | 8374.315001 | 1.952594 (within) | left / left / right | mixed |

The six event coordinates determine event-wise dominance only. State allocation, probe process stack, and kernel/coefficient symbol bytes are reported separately in `analysis.json`; they are not summed as memory use.
