# Exact-output FIR research

This project studies how exact arithmetic ranges and implementation choices
affect fixed-point FIR software on a pinned Cortex-M0 simulator and CPU cost model.

Start with the [project guide](README-FIR.md) and
[current proposal](professor-topic-proposal.md).

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
