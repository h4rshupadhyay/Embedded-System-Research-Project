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

Final SHA-256 values:

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
