# Exact-output FIR research

This project studies how exact arithmetic ranges and implementation choices
affect fixed-point FIR software on a pinned Cortex-M0 simulator and CPU cost model.

Start with the [project guide](README-FIR.md) and
[current proposal](professor-topic-proposal.md).

The revised [IEEE paper](research/fir-upgrades/paper/manuscript.pdf),
[editable manuscript](research/fir-upgrades/paper/manuscript.md), and
[evidence guide](research/fir-upgrades/README.md) extend the original study with
exact saved-event sensitivity, a frozen prospective panel, and a matched
block1 intervention. Strengthening the direct comparator reverses 24 of 32
complete fresh wide-design comparisons, while incremental sharing loses to
ordinary transposition in all 32. The eight unavailable native cases remain
explicit. The intervention supports a bounded generated-code explanation.
[Upgrade checkpoint](research/fir-upgrades/PROGRESS.md).

The [first-version paper](research/fir-paper/manuscript.pdf) and its
[reproduction guide](research/fir-paper/README.md) are preserved byte-for-byte.
Its four-cell result remains: corrected direct wins both GCC10 cases, while
Hcub wins both GCC15 cases.

The [Stage 2 formulation gate](research/fir-stage2-formulation-gate.md) is also
complete: the proposed search state omits instruction-relevant locations in its
specified model. Its repair establishes no new search advantage, so the current
formulation does not justify implementing an optimizer.

- [Experiment and independent-check plan](docs/superpowers/plans/2026-10-20-fir-baseline-check.md)
- [Independent verification and comparison](research/fir-sharing-probe/independent-check/README.md)
- [Peer baseline handoff](docs/peer-sol-6.1-handoff.md)

The peer baseline and final comparison are complete: partial direct wins both
GCC 10 configurations; demand Hcub wins both GCC 15 configurations. See the
[verified decision and evidence](research/fir-sharing-probe/independent-check/join-review.md).
Results are simulator and model estimates, not physical energy measurements.

The [two-binary compiler explanation](research/fir-sharing-probe/explanation-check/final-decision.md)
is also complete with partial attribution: GCC15's extra stack transfers explain
all additional RAM traffic and 85.02% of the modeled energy increase over GCC10
for block1 direct. The remaining costs and responsible compiler pass are
unresolved. The [paper outline](research/fir-sharing-probe/explanation-check/paper-outline.md)
includes the corrected comparison and this bounded explanation.
