"""Exploratory FIR omission counts; neither MCU timing nor an energy model.

Run from the repository root:
    python research/fir-skipping-opportunity.py > research/fir-skipping-opportunity.json

Independent random windows deliberately isolate mathematical opportunity.
Input-bound maintenance, permutation loads, checks, state work and symmetry
are NOT costed. Output precisions are separate reference contracts.
"""

import json
import platform

import numpy as np
import scipy
from scipy.signal import firwin


def main():
    rng = np.random.default_rng(20261019)
    rows = []
    for n in (64, 128, 256):
        h = np.rint(32768 * firwin(n, .10, window="hamming")).astype(np.int64)
        h = h[h != 0]
        h = h[np.argsort(-np.abs(h), kind="stable")]
        tails = np.r_[np.cumsum(np.abs(h)[::-1])[::-1], 0]
        for amplitude in (8, 128, 8192):
            x = rng.integers(-amplitude, amplitude + 1,
                             size=(2000, len(h)), dtype=np.int64)
            partial = np.cumsum(x * h, axis=1)
            maximum = np.max(np.abs(x), axis=1)
            for bits in (16, 12, 8):
                shift = 15 + 16 - bits

                def quantize(value):
                    return np.clip(value // (1 << shift),
                                   -(1 << (bits - 1)), (1 << (bits - 1)) - 1)

                reference = quantize(partial[:, -1])
                used = np.full(len(x), len(h))
                exited = np.zeros(len(x), dtype=bool)
                for count in range(8, len(h), 8):
                    radius = maximum * tails[count]
                    low = quantize(partial[:, count - 1] - radius)
                    high = quantize(partial[:, count - 1] + radius)
                    selected = (~exited) & (low == high)
                    if not np.array_equal(low[selected], reference[selected]):
                        raise AssertionError("Certified output differs from full FIR")
                    used[selected] = count
                    exited[selected] = True
                rows.append({
                    "nonzero_taps": int(len(h)), "input_amplitude": amplitude,
                    "output_bits": bits, "shift": shift,
                    "mean_products_omitted_percent": float(100 * (1 - used.mean() / len(h))),
                    "early_exit_percent": float(100 * exited.mean()),
                })
    print(json.dumps({
        "seed": 20261019, "windows_per_condition": 2000,
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__,
        "warning": "Opportunity counts only; all implementation overhead excluded; independent windows; no symmetry baseline.",
        "rows": rows,
    }, indent=2))


if __name__ == "__main__":
    main()
