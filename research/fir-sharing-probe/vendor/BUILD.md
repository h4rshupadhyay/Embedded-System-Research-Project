# Official Hcub source build

20 October 2026.

Source: https://spiral.ece.cmu.edu/mcm/dl/synth-jan-14-2009.tar.gz

SHA256: `24b3fd41181f2e5443f0324a4138096dfce91fa2514b0f96b25b5a1da6c33bc2`

The archive was checked for path traversal, links and special devices before extraction into this directory. All 38 members extracted. All archived files were subsequently compared byte-for-byte against their extracted counterparts; none changed.

From `synth-jan-14-2009/`:

```bash
make acm CXXFLAGS='-O2 -std=gnu++98 -include cstdlib -include algorithm' CFLAGS=-O2
./acm 3 5 7 -b 15 -seed 1 -nofs -gc
```

Compatibility changes are compiler flags only: GNU C++98 dialect and forced standard headers for declarations omitted by the old source. The separate `CFLAGS=-O2` prevents C++ headers from being forced into `21.costs.c`. Initial builds without those headers failed on undeclared `abs`/`sort`; sharing C++ flags with C also failed. No source/algorithm/Makefile patches were made. Compiler warnings about old string-literal-to-char-pointer conversions remain.

Source `COPYRIGHT`: Yevgen Voronenko, 2006, Spiral Project, Carnegie Mellon University; GNU GPL version 2 or later. Generated output explicitly states CMU copyright 2006 and a BSD style output license, linking the historical BSD-license page. Preserve that output notice; do not silently assign a more precise SPDX BSD variant than the source states.

`examples-manifest.json` records exact commands, positive odd fundamentals from the frozen `research/fir-baseline/selection-design.json`, return codes and output hashes. Each example `.txt` is raw stdout; `.stderr.txt` is raw stderr. Default algorithm is Hcub; no depth limit was requested. `-nofs` disables randomness according to README; `-seed 1` is retained in the reproducible command. The bitwidth bound is 15. The 23/45/52-constant examples demonstrate that the online form's 20-constant cap is not a CLI restriction.

Each assignment comment and declared output coefficient was independently reconstructed with Python arbitrary-precision integer arithmetic, with exact divisibility required at every `shr`. This is an algebraic graph check, not target C execution or width certification. The nonminimum-phase filters use add/sub/shl/copy; the minimum-phase filter also uses shr. Never treat the comments as a proof without reconstructing the operations.
