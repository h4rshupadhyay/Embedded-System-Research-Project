# Stage 1 IEEE FIR paper

The paper assesses whether an actual four-configuration Hcub modeled-energy
advantage survives an equally range-specialized direct comparator. Its explicit
retrospective hypothesis is rejected: corrected direct wins both GCC10 cases;
Hcub wins both GCC15 cases. The paper defends the comparison, exact arithmetic,
complete-stream costs and bounded generated-code explanation.

- [Editable manuscript](manuscript.md)
- [IEEE conference PDF](manuscript.pdf) and [LaTeX source](manuscript.tex)
- [Auditable selected results](results.json), [generated tables](tables.md) and
  [source identities](source-manifest.json)
- [Independent scientific/numerical review](review.md)
- [Execution checkpoint and resume instructions](PROGRESS.md)

The format is IEEEtran conference, two columns, with anonymous authors. No venue
or page limit was specified. The document is an empirical case study, with
explicit model and single-filter limits; it does not claim a new FIR algorithm
or measured board energy. The original exploratory protocol, later fixed control
and post hoc explanation remain distinct.

## Regenerate numbers without target tools

Python 3.10 or later and the standard library suffice:

```bash
python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v
python3 research/fir-paper/build_results.py --output-dir research/fir-paper
```

The CLI freezes six input byte identities, selects twenty admitted rows,
reconstructs timing and modeled energy from integer events, cross-checks sources,
and emits deterministic results and tables. It validates all inputs before
replacing output files. An altered source is an error, not a failed hypothesis.
Public pure helpers support isolated semantic rejection tests; they do not
certify file identities. Numerical Decimal values serialize as decimal strings.

`hcub_vs_*_energy_percent` means `100*(E_Hcub/E_named_comparator - 1)`;
negative favors Hcub. Selectable-compiler savings use the best partial-direct
energy as denominator. The 85.0151% fraction uses the GCC15-minus-GCC10 block1
direct energy increase, not either binary's total energy or a predicted saving.
Per-row raw and diagnostic source fields record their different provenance.

Historical automated files still describe manual review as pending. Manual
acceptance is separately recorded in the [baseline join](../fir-sharing-probe/independent-check/join-review.md)
and [explanation decision](../fir-sharing-probe/explanation-check/final-decision.md).
Table generation uses that admitted evidence and does not repeat target runs.

## Figures and IEEE PDF

Create an isolated environment and install the recorded paper dependencies:

```bash
python3 -m venv research/fir-paper/build/venv
research/fir-paper/build/venv/bin/python -m pip install -r research/fir-paper/requirements-paper.txt
research/fir-paper/build/venv/bin/python research/fir-paper/make_figures.py
```

Install [Tectonic 0.17.0](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0)
from its official release for your platform and make it available on PATH, or
supply its executable path using `--tectonic`. The installed `pypandoc-binary`
package supplies Pandoc. Tectonic retrieves its TeX bundle and IEEEtran class on
the first build; cached builds can reuse those files.

```bash
research/fir-paper/build/venv/bin/python -m pytest research/fir-paper/test_render_paper.py -q
research/fir-paper/build/venv/bin/python research/fir-paper/render_paper.py --source research/fir-paper/manuscript.md --output-dir research/fir-paper
```

Rendering tests are pytest functions; unittest discovery alone does not run them.
If Tectonic is installed outside PATH, set `FIR_PAPER_TECTONIC` to its executable
for the pytest command, and pass `--tectonic` to the rendering command. A missing
Tectonic executable skips the compile fixture rather than validating it; the
recorded completed run must show the fixture actually passed.
The renderer stages output and preserves an existing PDF on failure. The checked
build uses IEEEtran, its local template and Lua filter; it keeps reference links,
tables and figures in the editable TeX. PNG and SVG plots are supplied, with
stable SVG IDs and no date metadata. [Render log](render-log.md) records actual
integration and layout checks. Generated timestamps can affect PDF bytes;
determinism of the numerical export and plots does not promise identical PDF
bytes across TeX installations.

## Evidence and recovery

All numerical inputs are versioned. Recreating tables requires no Arm compiler
or simulator. Rechecking historical raw evidence has additional requirements
documented in the [independent-check README](../fir-sharing-probe/independent-check/README.md).
The partial-direct target archive is versioned; original historical raw build
directories are ignored and are not guaranteed in a fresh clone. New target
execution is a separate reproduction level, not part of this paper build.

After interruption, read `PROGRESS.md`, the [plan](../../docs/superpowers/plans/2026-10-20-fir-stage1-paper.md)
and the [scientific design](../../docs/superpowers/specs/2026-10-20-fir-stage1-paper-design.md).
Check completed files, Git history and live agents before resuming the first
unfinished task. Sol 6.1 owns scientific decisions and review; Luna 6 handles
specified mechanical tasks. The requested model settings are recorded; backend
routing telemetry is unavailable. The separate
[Stage 2 formulation gate](../fir-stage2-formulation-gate.md) subsequently
concluded no-go for the current search-state rule; no optimizer was implemented.
