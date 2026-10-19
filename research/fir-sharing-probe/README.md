# FIR sharing/state-cost research probe

Throwaway exploratory fixture. Start with [findings](../fir-sharing-findings.md) and [protocol](PROTOCOL.md). No new FIR algorithm, physical energy measurement or universal winner is claimed.

The fixture reuses the tools/artifacts from [the baseline](../fir-baseline/README.md): host GCC/UBSan, Python with NumPy/SciPy, pinned Arm GCC 10/15 toolchains, the audited Thumbulator binary, and CMSIS-DSP v1.14.4 sources. These are already present in this workspace. Primary execution compares three frozen filters, two magnitude contracts, blocks 1/64 and two compilers. Existing results are preserved separately.

From the workspace root:

```bash
python3 research/fir-sharing-probe/probe.py --host
python3 research/fir-sharing-probe/probe.py
python3 research/fir-sharing-probe/probe.py --ablate
python3 research/fir-sharing-probe/probe.py --verify
python3 research/fir-sharing-probe/analyze.py
python3 -m unittest discover -s research/fir-baseline -p 'test_*.py'
```

The plain command repeats host checks, then regenerates/rebuilds/runs the primary and target-edge cases. `--ablate` adds four explicitly post hoc uniform64-state controls. `--verify` checks saved artifacts/references/raw events without executing target binaries. Analysis recomputes descriptive group comparisons and resource diagnostics. `build/` holds generated sources, ELF/bin/map/disassembly, stack reports and raw logs; it is excluded from version control by the local `.gitignore`.

The original Hcub source archive, raw generated graphs and invocation manifest are in `vendor/`; [BUILD.md](vendor/BUILD.md) records the exact source hash, GPL source license and separate BSD-style generated-output notice. To regenerate graphs, build the unchanged CLI as documented and repeat commands from `vendor/examples-manifest.json`. The frozen raw graphs suffice to reproduce this probe; the runner independently checks their algebra and native arithmetic bounds.

Files:

- `results.json`: counted primary/edge/post hoc executions, compiler/model/dependency identities, outputs/state checks and per-case artifact hashes.
- `certificates.json`: exact graph identities, bounds and retained-state widths. The scalar-access estimate is **not a lower bound** and cannot exclude a kernel.
- `host-checks.json`: UBSan output/state/guard check totals.
- `analysis.json` / `comparison.md`: derived results, all primary group comparisons and symbol/frame diagnostics.
- `probe.py`: bounded source emitter, executor and artifact verifier; not a reusable optimizer.

The first run's execution-runner/protocol hashes are retained separately from the post-review reproduction-runner hashes. Review corrected an invalid interpretation of scalar-access estimates and strengthened provenance verification. All original generated target kernels, binary hashes and raw traces remained unchanged; the post hoc width controls are a separate labeled stage.
