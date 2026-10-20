# Render and figure log

## Figure preparation

On 2026-10-20 the vector helper was run with
`MPLCONFIGDIR=/tmp/mplconfig /tmp/fir-paper-render-env/bin/python
research/fir-upgrades/paper/make_figures.py --output-dir
research/fir-upgrades/paper/figures`. It produced the three required PNG and
SVG pairs from the saved analysis/panel JSON. All three PNGs were opened for
visual review; the representation diagram and panel legend were adjusted and
the latest images were re-rendered and viewed. Figure 3's four positions in
each group are ADC/startup, ADC/post-startup, full/startup, and
full/post-startup.

Environment observed: Python environment `/tmp/fir-paper-render-env`,
pypandoc 1.17 with Pandoc 3.9, NumPy 1.26.4, Matplotlib 3.10.9, Tectonic
0.17.0 at `/tmp/fir-paper-tools/tectonic`, and Poppler `pdftoppm` 22.02.0.

## Final paper render

Final render on 20 October 2026 used:

```sh
/tmp/fir-paper-render-env/bin/python research/fir-upgrades/paper/render_paper.py \
  --source research/fir-upgrades/paper/manuscript.md \
  --output-dir research/fir-upgrades/paper \
  --tectonic /tmp/fir-paper-tools/tectonic
pdftoppm -r 100 -png research/fir-upgrades/paper/manuscript.pdf \
  /tmp/fir-upgraded-final-page
```

The render exited 0 and produced 11 letter-size IEEEtran pages, with anonymous
authors, three figures and twelve tables. All eleven final page PNGs were
opened and visually inspected by the coordinator. Tables, mathematical
notation, captions, figure legends, citations and page numbers are legible;
no clipping, collisions, missing glyphs or empty float-only pages remain.
The appendix resource table uses one column with explicit compact headings;
the affine equation and event-vector headings were broken across lines or
moved into full-width captions. The final TeX log has no overfull boxes.
Ordinary underfull-box/font-substitution diagnostics remain; their rendered
output was inspected. No experiment or numerical result changed for layout.

Accepted anonymous-version SHA-256 values (before the author update below):

| File | SHA-256 |
|---|---|
| manuscript.md | `2e899f7b5f8c00c4a2fa78bf3cf236b758179b468b80aa4876728ed4229761c4` |
| manuscript.tex | `be76353d2b375fe96e9ca35127448a283f20a056f092aa25cbfca61233368987` |
| manuscript.pdf | `f7caacaefc40b5c02a7d487e245c85cf20a1ff11ccd8009b6d7ae11a68df8fb2` |

The PDF skill's operation marker was found in its own `container_tools/`
directory and executed successfully before this continuation's first render.
The earlier checkpoint's missing-helper limitation therefore does not apply
to the final render. Render and PNG logs are local scratch files under `/tmp`;
the editable sources, figure pairs and final TeX/PDF are included in the package.

## Named-author revision, 20 October 2026

At the user's request, the source now records Harsh Upadhyay, Aishwarya Singh
and Aryan Devpura, in that order, with their supplied registration numbers and roll
numbers. The IEEE template renders the manuscript's author metadata into three
aligned author blocks. No institution, email or affiliation was inferred.
The abstract and entire research body compare byte-for-byte with the accepted
manuscript from `## Abstract` onward.

The same render command above exited 0. `pdftotext -layout` confirms all nine
supplied author values and no anonymous-author label. The PDF remains eleven
letter-size pages and the render log contains no overfull boxes. All eleven
page PNGs, generated with `pdftoppm -r 90 -png` under `/tmp/fir-authors-page`,
were visually reviewed, with the title page also opened individually. Author
blocks, text, tables, figures and references are readable without collisions
or clipping. The operation marker executed successfully before rendering.

Named-author version SHA-256 values before the label correction below:

| File | SHA-256 |
|---|---|
| manuscript.md | `d89fc9a9f163ff81b8c4f972505b004853e0da35fe3e7ed3273189f5bf9edc03` |
| manuscript.tex | `0fc5b0f269f9edbcdf8eb344232dc15fca7dc15dcb099ba13f160c0fc0f8ae2d` |
| manuscript.pdf | `af8de169d666a34ad3be61efc97a925f21f5bb61559e311d2a0f76efc2fe76f2` |

## Registration-number label correction

The user clarified the field label as `Reg No.`. The manuscript metadata and
IEEE author template now use registration numbers. The PDF was regenerated
with the same render command; all three labels and values were checked in
extracted text and the first page was visually inspected. Pages 2–11 are
pixel-identical to the inspected preceding render at 90 dpi. There are no
overfull boxes. Current SHA-256 values:

| File | SHA-256 |
|---|---|
| manuscript.md | `f5043851c8834ec01b78ced2661a5d9d54d6e132827eabf36814f3995169ba61` |
| manuscript.tex | `ade4dc9f63a130ccdf24c4eda3dcb7de686185c08e2aa27ca6a8a029b1e1a7c0` |
| manuscript.pdf | `4efa0c0f404c1e3770a1d10edb0091d6f171667d5654acc1aa153b9924e2ce48` |

## Clarity rewrite, 20 October 2026

The editorial revision is isolated on `research/fir-clarity-rewrite`, based on
`cf53328`. It applies the installed `research-paper-writing` package from
Master-cai/Research-Paper-Writing-Skills. The rewrite adds no target measurement
and does not replace the historical evidence archive or its reports. The
outline, paragraph roles, claim map, five-dimension self-review and source-access
limits are recorded in `clarity-rewrite-review.md`.

The PDF operation marker ran successfully once with operation `edit` before
authoring. The existing Pandoc/Tectonic renderer rebuilt the TeX and PDF; the
final command exited 0. The output is eleven letter-size pages, with three
figures, twelve tables and eleven references. Final Tectonic output contains
no overfull boxes. Ordinary underfull/font-substitution warnings remain and
were checked visually.

The first render revealed an overfull table page. Figure/table placement now
respects LaTeX float limits instead of overriding them. Appendices precede
references, and the final bibliography is balanced across columns. All table
values and figure data are unchanged.

The verification report `clarity-rewrite-validation.json` records 31 passing
checks. All 113 Markdown table lines, four displayed equations, the C code
example, author metadata and three figure targets match the starting paper.
All 19 protected files (first-paper artifacts, numerical inventories, protocol,
certificates, intervention review, archived manifest/report and figure files)
match commit `cf53328` byte-for-byte. Local evidence links and citation IDs
resolve. Total Markdown whitespace-separated words changed from 7,364 to
7,149; the new abstract has 178 words. These counts include tables and references.

The final PDF was rendered with Poppler at a 1200-pixel maximum page dimension.
All eleven pages were visually reviewed; unchanged pages between layout
iterations were additionally compared by PNG hash. Tables, figures, mathematical
notation, author fields, captions and references are readable, without observed
clipping, overlap or missing glyphs. The final reference correction identifies
Arm DDI 0432C §§1.4.1 and 3.3 (Table 3-1).

Final source/output SHA-256 values:

| File | SHA-256 |
|---|---|
| manuscript.md | `ef69c9163d18634e8343d5610852589e3f293091fd74076bdfb2c9fa1b67a057` |
| manuscript.tex | `a3f00aebc29c7aadce1d694d343f9a2799b97335c84a309955757a8369d5b3c0` |
| manuscript.pdf | `8feeb3e6b104122d1dd0b9c8a1a6f5961c33f0d1162de77ba83ce28c7e78788f` |
| ieee-filter.lua | `28e1a9a7a755e169f8bb59b99fa5824092f36b53cb006b128e74eb0da913ae63` |
| ieee-template.tex | `d647e00b72f83dfa009696c97b3fba8053e902139e8721bc1533fce8cbe96a32` |

Installed skill SKILL.md SHA-256: `62ef11c06f2796c74e55ab24908ed31bafebfa0f1b736499d1615ac374cf7f6d`.

## Timing-review correction, 20 October 2026

The current revision addresses all five findings in
`manuscript-review-2026-10-20.md`. It uses the installed PDF and
research-paper-writing skills to verify evidence placement and claim scope.
The PDF operation marker ran successfully with operation `edit` before this
continuation's first authoring command. No target measurement was run.

The render command remains the one documented above. Its final invocation
exited 0 and produced 12 letter-size IEEEtran pages, three figures, twelve
tables and twelve references. The render output has no overfull boxes.
Ordinary underfull-box and font-substitution diagnostics remain; the rendered
pages were checked. The `lineno.sty` package's cached-source UTF-8 warning
also remains, without an observed missing glyph in the output.

Final page rasterization used:

```sh
pdftoppm -scale-to 1400 -png research/fir-upgrades/paper/manuscript.pdf \
  /tmp/fir-timing-final3-page
```

The coordinator opened every final page individually. Text, mathematics,
figures, all table values and author details are legible without observed
clipping or overlap. Tables III/IV now appear inline on page 5; Figure 2
finishes the original-results evidence on page 6 before the compiler section
on page 7. Tables VIII/IX precede the panel section on page 8; Figure 3
precedes discussion on page 10. `FloatBarrier` bounds these sections and
`raggedbottom` prevents stretched paragraphs. The final reference page is
balanced at reference [7]. All preceding eleven page rasters are byte-identical
to the independently inspected preceding render.

Host verification (Tectonic integration enabled) used:

```sh
env FIR_PAPER_TECTONIC=/tmp/fir-paper-tools/tectonic \
  PYTHONPATH=research/fir-upgrades:research/fir-baseline:research/fir-paper:/tmp/fir-paper-render-env/lib/python3.10/site-packages \
  python3 -m pytest -q --import-mode=importlib
python3 research/fir-upgrades/timing_correction.py --verify
```

The full suite passes 249 tests, with zero skips. A direct initial collection
without the repository's module paths/render dependencies failed to import
four test modules; the successful command above resolves that environment
setup. An earlier complete run passed 248 and skipped the optional renderer;
explicitly setting `FIR_PAPER_TECTONIC` closes that skip.
The eight timing regressions pass independently. The frozen legacy helper
returns 15 for the literal BL/B/PUSH/POP-PC fixture, versus the correction's
Arm-table total of 16. The frozen helper remains unchanged for historical
reproduction; its cycle fields are superseded for current timing claims.

The corrected report regenerates byte-for-byte, and production verification
passes from a relocated 920-file tree with `PATH=/nonexistent`. It preserves
all energy totals and eight unavailable identities. All 24 changed paper
cycle cells agree with the corrected report; every other table cell and all
author metadata are unchanged. The 19 protected payload hashes from
`clarity-rewrite-validation.json` still match. The first paper, numerical
inventories, protocol, certificates, figure files and archived evidence are
unchanged. The new timing report is separate from that historical archive.

One fresh-context independent scientific/code review returned PASS with zero
actionable findings. It separately reconstructed all 304 timing/energy rows,
checked all bound raw/disassembly/binary hashes and all 24 changed cycle cells,
and verified 680 panel, 40 original and two intervention cycle orderings. It
ran the eight focused tests and report verification and inspected all twelve
pages before the final reference balancing; the coordinator inspected that
last change. Broader physical validity, fresh target reproduction, exhaustive
arithmetic/compiler correctness and publication suitability remain outside
what this saved-data correction establishes.

Current source/output SHA-256 values:

| File | SHA-256 |
|---|---|
| manuscript.md | `a807a98aac573189d899437c10862ca5835e0755b966535ca5de501512c598d0` |
| manuscript.tex | `0d40eeb18aa82ae49fadf6a4738f006ffb2b1a462fa498c3b379874271f1f598` |
| manuscript.pdf | `153d188a4f1c5cdd2f0734f68988d8a502433a9be0a829a7c19fd92236e8610e` |
| ieee-filter.lua | `821606915e475cab8f5c165fb7e3e16bf053a36fb5613c2e1e1d50334046c136` |
| ieee-template.tex | `d15ed054480a38223b00dd25a61b9fae87c441d70d82e9e161eb1c22fbc84087` |

Corrected report SHA-256: `b6d144ace8447d8192351f574096eb005c6814b944124338de2a4debfa218fcf`.
