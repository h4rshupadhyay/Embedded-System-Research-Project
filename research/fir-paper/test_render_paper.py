from pathlib import Path
import os
import shutil
import subprocess
import sys
import importlib.util

import pytest

from pypdf import PdfReader


ROOT = Path(__file__).parent
RENDERER = ROOT / "render_paper.py"
PYTHON = Path(sys.executable)
TECTONIC = os.environ.get("FIR_PAPER_TECTONIC") or shutil.which("tectonic")

SPEC = importlib.util.spec_from_file_location("render_paper", RENDERER)
RENDER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDER_MODULE)


def test_question_title_keeps_sentence_punctuation_when_joining_subtitle(tmp_path):
    source = tmp_path / "question-title.md"
    source.write_text("# Can it survive?\n\n## Subtitle\n", encoding="utf-8")

    title, _ = RENDER_MODULE.pandoc_source(source)

    assert title == "Can it survive? Subtitle"


def test_cli_renders_ieee_pdf_and_preserves_readable_content(tmp_path):
    if not TECTONIC:
        pytest.skip("tectonic is unavailable; set FIR_PAPER_TECTONIC or add it to PATH")
    source = tmp_path / "sample.md"
    source.write_text(
        """# Sample FIR Paper

## Subtitle fixture

Anonymous authors

## Abstract
Short abstract for rendering.

## 1. Introduction
The token readable-render-token must survive PDF rendering.

| Case | Value | Note |
|:--|--:|:--|
| A | **12** | baseline |
Table: Sample table caption.

```c
int sample = 12;
3f4e5d6c7b8a90123f4e5d6c7b8a90123f4e5d6c7b8a90123f4e5d6c7b8a9012
```

## References
[1] A. Author, “A paper,” Journal, 2020.
""",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = subprocess.run(
        [str(PYTHON), str(RENDERER), "--source", str(source), "--output-dir", str(out), "--tectonic", str(TECTONIC)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    tex = (out / "manuscript.tex").read_text(encoding="utf-8")
    assert r"\documentclass[conference]{IEEEtran}" in tex
    assert "Sample FIR Paper: Subtitle fixture" in tex
    assert "\\begin{tabularx}" in tex
    assert r"\textbf{12}" in tex
    assert r"\caption{Sample table caption.}" in tex
    extracted = " ".join(p.extract_text() or "" for p in PdfReader(out / "manuscript.pdf").pages)
    assert "readable-render-token" in extracted
    assert "3f4e5d6c7b8a90123f4e5d6c7b8a90123f4e5d6c7b8a90123f4e5d6c7b8a9012" in extracted.replace("\n", "").replace(" ", "")


def test_missing_image_fails_without_replacing_existing_pdf(tmp_path):
    source = tmp_path / "missing-image.md"
    source.write_text("# Image test\n\n![missing](absent.png)\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    pdf = out / "manuscript.pdf"
    pdf.write_bytes(b"previous successful artifact")
    result = subprocess.run(
        [str(PYTHON), str(RENDERER), "--source", str(source), "--output-dir", str(out)],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "absent.png" in result.stderr
    assert pdf.read_bytes() == b"previous successful artifact"
