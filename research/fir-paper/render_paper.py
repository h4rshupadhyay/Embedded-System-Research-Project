#!/usr/bin/env python3
"""Render the manuscript source as an IEEEtran conference paper."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pypandoc


HERE = Path(__file__).resolve().parent


def find_images(source: Path) -> list[Path]:
    text = source.read_text(encoding="utf-8")
    found = []
    for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)", text):
        target = target.split()[0].strip("<>")
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", target) or target.startswith("data:"):
            continue
        image = (source.parent / target.split("#", 1)[0]).resolve()
        if not image.is_file():
            raise ValueError(f"referenced image does not exist: {target} (from {source})")
        found.append(image)
    return found


def pandoc_source(source: Path) -> tuple[str, str]:
    text = source.read_text(encoding="utf-8")
    title_match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if not title_match:
        raise ValueError("source must begin with a level-one Markdown title")
    title = title_match.group(1).strip()
    lines = text.splitlines()
    title_line = next(i for i, line in enumerate(lines) if re.match(r"^#\s+", line))
    next_line = title_line + 1
    while next_line < len(lines) and not lines[next_line].strip():
        next_line += 1
    if next_line < len(lines) and re.match(r"^##\s+", lines[next_line]):
        subtitle = re.sub(r"^##\s+", "", lines[next_line]).strip()
        separator = " " if title.endswith(("?", "!", ":")) else ": "
        title = f"{title}{separator}{subtitle}"
        del lines[title_line + 1:next_line + 1]
    lines[title_line] = f"# {title} {{#paper-title}}"
    text = "\n".join(lines) + "\n"
    # Source has an editorial author/date block; the IEEE rendering is anonymous.
    text = re.sub(r"(?m)^(?:Anonymous authors|\d{1,2} [A-Za-z]+ \d{4})\s*\n", "", text)
    return title, text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "manuscript.md")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--pandoc", type=Path)
    parser.add_argument("--tectonic", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_dir.resolve()
    try:
        if not source.is_file():
            raise ValueError(f"source manuscript does not exist: {source}")
        images = find_images(source)
        title, md = pandoc_source(source)
        pandoc = str(args.pandoc or pypandoc.get_pandoc_path())
        tectonic = str(args.tectonic) if args.tectonic else shutil.which("tectonic")
        if not tectonic or not Path(tectonic).is_file():
            raise ValueError("tectonic was not found; install it or pass --tectonic PATH")
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fir-paper-render-", dir=output) as temp:
            stage = Path(temp)
            for image in images:
                try:
                    relative = image.relative_to(source.parent)
                except ValueError:
                    raise ValueError(f"referenced image must be inside the manuscript directory: {image}")
                staged_image = stage / relative
                staged_image.parent.mkdir(parents=True, exist_ok=True)
                staged_image.symlink_to(image)
            mdfile = stage / "input.md"
            mdfile.write_text(md, encoding="utf-8")
            tex = stage / "manuscript.tex"
            command = [pandoc, str(mdfile), "--from=markdown+tex_math_dollars+pipe_tables+table_captions", "--to=latex",
                       f"--template={HERE / 'ieee-template.tex'}", f"--lua-filter={HERE / 'ieee-filter.lua'}",
                       f"--resource-path={source.parent}", f"--output={tex}", "--standalone", "--toc=false",
                       "--syntax-highlighting=none", "--variable", f"title={title}"]
            subprocess.run(command, check=True, cwd=source.parent)
            pdf = stage / "manuscript.pdf"
            subprocess.run([tectonic, "--keep-logs", "--outdir", str(stage), str(tex)],
                           check=True, cwd=source.parent)
            if not pdf.is_file() or pdf.stat().st_size == 0:
                raise RuntimeError("tectonic reported success but did not produce a PDF")
            os.replace(tex, output / "manuscript.tex")
            os.replace(pdf, output / "manuscript.pdf")
        print(f"Rendered {output / 'manuscript.pdf'}")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"render_paper: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
