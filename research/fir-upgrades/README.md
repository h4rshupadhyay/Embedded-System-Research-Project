# Portable FIR evidence

This directory contains the packaging utility for two explicit evidence scopes.
The default `pack` scope preserves Task 3's original 531-file evidence slice.
The optional `--include-upgrades` scope adds the admitted Task 2 analysis, Task 5
panel, Task 6 intervention, and paper sources/outputs. Repository-relative
paths let copied scripts resolve every input inside the restored tree. Each
archive embeds a file manifest and has a sidecar manifest with the archive
digest. SHA-256 checks detect inconsistency; they do not establish who created
the package or prove authenticity.

For an upgraded package, the embedded `evidence-manifest.json` lists every
payload file. The sidecar `evidence-manifest.json` and `artifact-check.json`
are distributed beside the archive in the checkout; they are intentionally not
payload files, which avoids a self-reference between the archive, its digest,
and its report. A restored check writes its report under the requested
`--output-dir`. The manuscript links to the checkout copies of these companion
files, so those convenience links resolve when the archive is accompanied by
the documented reports.

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
or claim performance reproducibility. Toolchain binaries are excluded; acquire
the pinned tools separately for new target execution. Follow
`research/fir-baseline/README.md` for the pinned GCC10.3.1 and GCC15.2.Rel1
install locations and acquisition details; it records the GCC15 archive
SHA-256. That README also pins the Thumbulator source commit and build
instructions, and identifies the CMSIS-DSP v1.14.4 dependency. Acquire the
toolchain binaries separately and verify recorded versions and digests before
running any future reproduction.

## Upgraded evidence scope

Create a candidate upgraded archive after the paper outputs are complete:

```sh
python research/fir-upgrades/artifacts.py pack \
  --repo-root . \
  --output-dir research/fir-upgrades/build/upgraded-candidate \
  --include-upgrades
```

Restore it at an unrelated path and run every saved-evidence verifier there:

```sh
python research/fir-upgrades/artifacts.py check \
  --archive research/fir-upgrades/build/upgraded-candidate/evidence.tar.gz \
  --destination /tmp/fir-upgraded-copy \
  --output-dir research/fir-upgrades/build/upgraded-copy-check
```

The upgraded manifest declares its scope. A declared upgraded archive must
contain the complete raw artifact maps and inventories. The copied-tree check
regenerates the original numerical export; admits the historical 24, peer 4,
and explanation 2/29-hash checks; rebuilds the exact U2 analysis; independently
audits the Task 5 performance and correctness evidence; and verifies all eight
Task 6 rows. Expected scientific unavailable identities remain visible as
8/288 performance and 2/72 correctness outcomes; they are not integration
skips. The check requires 280 admitted panel performance rows, 70 admitted
correctness rows, four intervention performance rows and four correctness-only
rows, with zero failures and zero integration skips. Every checker runs its
copied script with explicit copied roots; no target firmware or toolchain is
executed.

The package pins the raw files named by each admitted artifact map, all frozen
panel/source/graph manifests, the independent verifiers, relevant CMSIS-DSP
source headers and implementations with their upstream license, the original
Hcub source archive/notices, and the editable paper plus PNG/SVG figures and
rendered PDF/TeX. It excludes executable toolchains, simulator binaries,
unrelated caches and failed attempts. Its file manifest covers every regular
file in the archive. See the checkout-side `artifact-check.json` for the
copied-tree commands and actual file count; a new check writes a fresh report
to its requested output directory.
