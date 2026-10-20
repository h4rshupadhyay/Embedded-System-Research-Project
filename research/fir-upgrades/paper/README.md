# FIR upgrades paper sources

The clarity revision on `research/fir-clarity-rewrite` applies the installed
`research-paper-writing` skill. Its outline, paragraph roles, claim/evidence
map and reviewer questions are in [clarity-rewrite-review.md](clarity-rewrite-review.md).
The numerical tables, exact contract, authors and underlying measurements are
preserved in that first editorial commit. The later review-fix revision corrects
the timing equation and 24 cycle cells from saved logs, using the
[version 2 timing report](../timing/README.md); energy cells, arithmetic,
authors and raw evidence remain unchanged. The original and panel cycle
inventories retain their historical values and are superseded for timing.
The saved evidence archive, manifest and copied-tree check report
remain historical snapshots from before this editorial revision; the revised
paper has not been repackaged into that archive.

This directory contains the editable Markdown manuscript, the IEEEtran render
template and filter, the plot helper and its PNG/SVG outputs. The PDF and TeX
are generated from this source; numeric source files and admitted results live
one directory above in `research/fir-upgrades/`.

The manuscript's YAML `author` list supplies the three names, registration numbers and
roll numbers for the IEEE title block. Edit that list before rendering to keep
the source and PDF consistent.

From the repository root, regenerate the figures with:

```sh
/tmp/fir-paper-render-env/bin/python research/fir-upgrades/paper/make_figures.py
```

The helper reads only the saved U2 analysis, the admitted panel inventory and
the independently derived panel summary. It does not execute a target binary.
The PNGs are the paper-ready versions; the paired SVGs remain editable vector
artifacts.

Render the PDF and TeX with the existing local tools:

```sh
/tmp/fir-paper-render-env/bin/python research/fir-upgrades/paper/render_paper.py \
  --source research/fir-upgrades/paper/manuscript.md \
  --output-dir research/fir-upgrades/paper \
  --tectonic /tmp/fir-paper-tools/tectonic
```

The renderer uses the `pypandoc` package and bundled Pandoc executable from the
existing render environment, plus the separately installed Tectonic binary.
For visual inspection, render every page with Poppler `pdftoppm`; the archived
final render log records the exact commands, tool versions, page count and
inspection result. These tools are not part of the evidence archive. Rebuilding
the target measurements requires separately acquired pinned Arm GCC 10/15,
Thumbulator and CMSIS-DSP dependencies as described in the experiment README;
paper rendering does not rebuild measurements.

The small principal energy/percentage and compiler-account tables render
inline beside their discussion. Pending wide evidence is flushed before the
next results section. This prevents the RAM-sensitivity figure from crossing
into the compiler section and keeps intervention evidence before panel results.

The [review and closure](manuscript-review-2026-10-20.md) records the five
findings and their resolution. The [correction validation](timing-review-validation.json)
records preserved hashes, the 24 corrected cycle cells and final paper hashes.
The current PDF has 12 pages; the render log records its final visual inspection
and the 249-test host verification.
