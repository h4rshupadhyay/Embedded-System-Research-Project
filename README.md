# Exact-output FIR research

This project studies how exact arithmetic ranges and implementation choices
affect fixed-point FIR software on a pinned Cortex-M0 simulator and CPU cost model.

Start with the [project guide](README-FIR.md) and
[current proposal](professor-topic-proposal.md).

- [Experiment and independent-check plan](docs/superpowers/plans/2026-10-20-fir-baseline-check.md)
- [Independent verification and comparison](research/fir-sharing-probe/independent-check/README.md)
- [Peer baseline handoff](docs/peer-sol-6.1-handoff.md)

The independent verification task is complete. The peer's missing direct
baseline and final research comparison remain pending. Results are simulator
and model estimates, not physical energy measurements.
