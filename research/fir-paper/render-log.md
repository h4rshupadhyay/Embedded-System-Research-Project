# IEEE rendering work log

The rendering CLI converts `manuscript.md` to a two-column IEEEtran conference
paper and replaces `manuscript.tex` and `manuscript.pdf` only after compilation
succeeds. The title regression covers the manuscript's actual question title;
the existing ordinary-title CLI fixture continues to require the colon
separator.

The title test was first run red: `pandoc_source` produced `Baseline?: A
Cortex...`. The renderer now inserts a space after a title ending in `?`, `!`,
or `:`, and retains `: ` for ordinary titles. The focused test then passed.

The Appendix C concern was checked against the PDF image and Poppler word
bounds. Archive-path fragments end at x=556.38 pt; the right-column body edge
is about x=563 pt. The visible break marks are normal wraps, and no text crosses
the column edge, so the Lua code-block settings were left unchanged.

Final render command:

```bash
/tmp/fir-paper-render-env/bin/python research/fir-paper/render_paper.py \
  --source research/fir-paper/manuscript.md \
  --output-dir research/fir-paper \
  --tectonic /tmp/fir-paper-tools/tectonic
```

The sandboxed invocation ended in a Tectonic 0.17.0 SIGSEGV while scanning
system fonts; the old outputs were preserved by the renderer's staging. The
same command was rerun with escalation and completed, producing a nine-page
letter-size PDF. Tectonic reported the `lineno.sty` invalid UTF-8 replacement,
font requests, and underfull hbox/vbox warnings at generated TeX lines 385,
540, 549 and 706. There were no overfull-box warnings. The successful output
and warnings are captured in `/tmp/fir-final-render-escalated.out`.

Renderer verification:

```bash
FIR_PAPER_TECTONIC=/tmp/fir-paper-tools/tectonic /tmp/fir-paper-render-env/bin/python -m pytest -q research/fir-paper/test_render_paper.py
```

Result: `3 passed`. The title regression uses the question-title fixture `Can
it survive?` with `Subtitle`; the plain-title CLI fixture still verifies the
colon behavior. The final PDF page count was checked with `pdfinfo`, the
question title with `pdftotext`, and Appendix C was rendered with `pdftoppm`
and visually inspected. No source manuscript, Lua filter or template changes
were made for this renderer fix.

The coordinator's combined paper suite also passed:

```bash
FIR_PAPER_TECTONIC=/tmp/fir-paper-tools/tectonic /tmp/fir-paper-render-env/bin/python -m pytest research/fir-paper -q
```

Result: `18 passed`.
