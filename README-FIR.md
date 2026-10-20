# Exact FIR research and peer handoff

This branch contains the current exact-output FIR research. Earlier supply-model
and ranking experiments are retained in Git history rather than this branch's
working tree. Use the files under
`research/fir-baseline/` and `research/fir-sharing-probe/` for this task.

**Current decision:** continue as a bounded empirical study. The equally
range-specialized direct baseline is now measured and independently checked:
partial direct wins both GCC 10 configurations; demand Hcub wins both GCC 15
configurations. No novel FIR algorithm or physical energy measurement is claimed.
The professor is the final evaluator, not a project guide.

## Start here

**Revised empirical paper:** [IEEE conference PDF](research/fir-upgrades/paper/manuscript.pdf),
[editable manuscript](research/fir-upgrades/paper/manuscript.md), and
[portable evidence and reproduction guide](research/fir-upgrades/README.md).
The revision adds exact incremental-sharing/sensitivity analysis, a frozen
three-design panel and the matched block1 intervention. Comparator correction
reverses 24/32 complete fresh wide-design cells, but Hcub loses every fresh wide
incremental-sharing comparison against ordinary transposition. Eight native
cases are unavailable; no population or hardware generality follows. The
[upgrade checkpoint](research/fir-upgrades/PROGRESS.md) records actual checks.

The [first IEEE version](research/fir-paper/manuscript.pdf),
[original editable manuscript](research/fir-paper/manuscript.md), and
[original reproduction guide](research/fir-paper/README.md) remain unchanged.
They record rejection of the retrospective all-four-cell robustness rule.

The compiler-explanation assignments are complete with accepted partial
attribution. See the [final decision](research/fir-sharing-probe/explanation-check/final-decision.md).
The [shared plan](docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md)
and historical [peer](docs/peer-sol-6.0-compiler-handoff.md)/[user](docs/user-fir-explanation-handoff.md)
prompts remain available for provenance. The separate
[Stage 2 formulation gate](research/fir-stage2-formulation-gate.md) is complete
with a no-go for the current H1 rule: its coarse search state loses relevant
location information, while the full-state repair establishes no new search
advantage. The note includes a checked symbolic example and three closest-method
comparisons; no optimizer or additional target measurements followed.

- [Current proposal](professor-topic-proposal.md).
- [Completed baseline comparison and research decision](research/fir-sharing-probe/independent-check/join-review.md).
- [Pursuit audit and decision gate](research/fir-sharing-pursuit-audit.md).
- [Two parallel assignments and result contract](docs/superpowers/plans/2026-10-20-fir-baseline-check.md).
- [Prompt to give the peer's coding agent](docs/peer-sol-6.1-handoff.md).
- [Sharing probe protocol](research/fir-sharing-probe/PROTOCOL.md) and
  [baseline reproduction environment](research/fir-baseline/README.md).

The peer owns `research/fir-sharing-probe/partial-direct/`. The original author
with Codex owns `research/fir-sharing-probe/independent-check/`. Task 2 is complete:
the [independent checker, reference cases and comparison](research/fir-sharing-probe/independent-check/README.md)
are ready, alongside the contribution-positioning note. On 20 October 2026,
all 26 checker tests passed and 24 historical rows (6,168 output comparisons)
were reverified from saved raw evidence; regenerated reports matched the saved
files exactly. That independent milestone used historical artifacts only.

Task 1 and the final join are now complete. Four target performance runs and two
signed-edge runs passed 1,750 output comparisons; the independent checker
accepted all four new performance rows. The final expanded peer suite passed
three UBSan tests and the checker passed 27 tests. Arithmetic and all four
emitted kernels were reviewed. See the [join record](research/fir-sharing-probe/independent-check/join-review.md)
for the corrected mixed result, resource costs, raw-evidence archive and limits.

## Host setup and checks

The recorded environment uses Python 3.10, NumPy 1.26.4, SciPy 1.15.3 and host GCC.
The host tests compile C with UBSan. From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-fir.txt
python3 -m unittest discover -s research/fir-baseline -p 'test_*.py' -v
```

The frozen coefficients and timed inputs are already in
`research/fir-baseline/selection-design.json`. Do not regenerate that file for
the peer task. Avoid running the old full experiment matrices: they write saved
results and are unnecessary for the four new measurements.

## Target environment and evidence

Target measurements require Arm GCC 10.3.1 and 15.2.Rel1, binutils, the audited
Thumbulator revision `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`, and the
measurement conventions documented in the baseline README and sharing protocol.
The old root-level simulator patch in Git history belongs to a different experiment: use
`research/fir-baseline/simulator.py` and its console-only patch for this fixture.
CMSIS-DSP v1.14.4 and core headers are needed to rebuild the historical library
controls; their recorded results can be read without rebuilding them.

Installed toolchains and generated working caches remain ignored. The
[portable evidence bundle](research/fir-upgrades/evidence.tar.gz) supplies the
finite historical and new raw evidence needed for the documented saved-byte
checks in a fresh directory. These checks use Python's standard library and
need no target toolchain. Rebuilding and executing firmware is a separate
reproduction level requiring the pinned tools and dependencies above. The
bundle's hashes check consistency, not authenticity.

Costs are architectural timing estimates and modeled CPU energy, not board
measurements. Do not interpret upstream raw ticks as Cortex-M0 cycles.

## Third-party material

The original Hcub source archive, extracted source, copyright/license files,
raw generated graphs and provenance are preserved under
`research/fir-sharing-probe/vendor/`. See its [build and licensing record](research/fir-sharing-probe/vendor/BUILD.md).
Generated graph notices and original source notices must be retained. Other
external simulator/CMSIS/toolchain sources are acquired separately as documented.

The legacy ECG pilot downloads its dataset from the URL recorded in
`research/fir-streaming-pilot.py`; that dataset is unrelated to the new peer task.
