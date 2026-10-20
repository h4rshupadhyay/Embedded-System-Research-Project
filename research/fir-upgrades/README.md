# Portable FIR raw evidence

This directory contains the central packaging utility for the finite original FIR
raw-evidence slice. It preserves repository-relative paths so the copied
historical scripts resolve all dependencies from the restored tree. The archive
contains its own `evidence-manifest.json`; the output directory also receives a
sidecar manifest with the archive digest. SHA-256 checks detect inconsistency and
do not establish who created the package or prove authenticity.

Create the package from a repository root:

```sh
python research/fir-upgrades/artifacts.py pack \
  --repo-root . \
  --output-dir research/fir-upgrades/build/central
```

Restore and exercise it in an empty destination:

```sh
python research/fir-upgrades/artifacts.py check \
  --archive research/fir-upgrades/build/central/evidence.tar.gz \
  --destination /tmp/fir-evidence-copy \
  --output-dir research/fir-upgrades/build/central-check
```

`pack` admits the six frozen numerical-export inputs, saved results/tables and
unchanged exporter; the 24 `speech_minphase48`/32768 historical control rows;
the four partial-direct rows; their artifact maps and ten historical dependency
sources; and all 29 paths in the compiler-explanation evidence map. It also
includes the raw decoder/checker, fixed reports, arithmetic certificates, Hcub
provenance and necessary manuals. Hcub provenance includes the original source
archive, GPL source notice, raw minimum-phase output with its BSD-style output
notice, invocation manifest and build notes. It excludes build caches and
executable vendor/toolchain trees. Missing or changed manifest-listed raw bytes
stop the pack operation.

`check` validates the archive before extraction, regenerates the numerical
report in the restored copy and compares it byte-structured with the saved
results, runs the historical plus peer checker, and runs the unchanged
explanation checker. Its report records all commands, row counts, evidence hashes
and skips. These checks reuse saved bytes; they do not execute target firmware
or claim performance reproducibility. Toolchain acquisition is outside the
archive because executable toolchains are not redistributable. Follow
`research/fir-baseline/README.md` for the pinned GCC10.3.1 and GCC15.2.Rel1
install locations and acquisition details; it records the GCC15 archive
SHA-256. That README also pins the Thumbulator source commit and build
instructions, and identifies the CMSIS-DSP v1.14.4 dependency. Acquire the
toolchain binaries separately and verify recorded versions and digests before
running any future reproduction.
