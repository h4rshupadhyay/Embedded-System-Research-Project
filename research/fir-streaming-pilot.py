"""Throwaway numerical research probe, not an embedded implementation.

Run: python research/fir-streaming-pilot.py
Writes fir-streaming-pilot.json and fir-streaming-pilot.csv beside this file.
Counts logical work; makes NO timing or energy claims. Actual residuals and
full products are computed off-line to validate certificates, not charged as
work to a hypothetical early-exit execution. Bound-maintenance work is
reported separately. No parameters are fitted to these data.
"""

from collections import deque
import csv
import hashlib
import json
from pathlib import Path
import platform
import urllib.request

import numpy as np
import scipy
from scipy.signal import firwin

ROOT = Path(__file__).resolve().parent
SEED = 20261019
ECG_URL = "https://raw.githubusercontent.com/scipy/dataset-ecg/main/ecg.dat"
ECG_SHA = "f20ad3365fb9b7f845d0e5c48b6fe67081377ee466c3a220b7f69f35c8958baf"


def q15(value):
    return np.clip(value // 32768, -32768, 32767)


def digest(array):
    return hashlib.sha256(np.asarray(array, dtype="<i8").tobytes()).hexdigest()


def filters():
    for family in ("lowpass", "bandpass", "halfband"):
        for size in (64, 128, 256):
            taps = size - 1 if family == "halfband" else size
            if family == "bandpass":
                designed = firwin(taps, [.20, .35], pass_zero=False, window="hamming")
            else:
                designed = firwin(taps, .50 if family == "halfband" else .10,
                                  window="hamming")
            h = np.rint(32768 * designed).astype(np.int64)
            assert np.array_equal(h, h[::-1])
            assert 32768 * int(np.abs(h).sum()) < 2**63 - 1
            yield f"{family}_{taps}", h


def signals():
    rng = np.random.default_rng(SEED)
    length = 4096
    time = np.arange(length)
    tone = .65 * np.sin(2 * np.pi * .013 * time) + .35 * np.sin(2 * np.pi * .13 * time)
    for amplitude in (8, 128, 8192):
        yield f"uniform_{amplitude}", rng.integers(-amplitude, amplitude + 1,
                                                   length, dtype=np.int64)
        yield f"tones_{amplitude}", np.rint(amplitude * tone).astype(np.int64)
    mixed = np.r_[rng.integers(-8, 9, 1024), rng.integers(-8192, 8193, 2048),
                  rng.integers(-8, 9, 1024)].astype(np.int64)
    yield "quiet_active_quiet", mixed
    yield "dc8192_noise8", 8192 + rng.integers(-8, 9, length, dtype=np.int64)
    yield "constant8192_diagnostic", np.full(length, 8192, dtype=np.int64)
    impulses = np.zeros(length, dtype=np.int64)
    impulses[::512] = 16384
    yield "impulses_diagnostic", impulses
    yield "fullscale_edges_diagnostic", rng.choice(
        np.array([-32768, -32767, -1, 0, 1, 32766, 32767], dtype=np.int64), length)
    data_path = ROOT / "data" / "ecg.dat"
    data_path.parent.mkdir(exist_ok=True)
    if not data_path.exists():
        with urllib.request.urlopen(ECG_URL, timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != ECG_SHA:
            raise ValueError("Unexpected ECG dataset checksum")
        data_path.write_bytes(data)
    assert hashlib.sha256(data_path.read_bytes()).hexdigest() == ECG_SHA
    with np.load(data_path) as data:
        # Inverse of SciPy's documented conversion (raw - 1024) / 200 mV.
        adc = data["ecg"].astype(np.int64) - 1024
    for start in (0, 36000, 72000):
        for gain in (1, 16):
            x = adc[start:start + length] * gain
            assert len(x) == length and np.max(np.abs(x)) <= 32767
            yield f"ecg_adc_x{gain}_at{start}", x


def rolling_extrema(x, taps, mode):
    """Reference deque algorithm, including zero history; counts comparisons."""
    padded = np.r_[np.zeros(taps - 1, dtype=np.int64), x]
    queues = [deque()] if mode == "absolute" else [deque(), deque()]
    out = []
    comparisons = pushes = pops = 0
    for index, raw in enumerate(padded):
        value = abs(int(raw)) if mode == "absolute" else int(raw)
        for qindex, queue in enumerate(queues):
            while queue and queue[0][0] <= index - taps:
                queue.popleft()
                pops += 1
            while queue:
                comparisons += 1
                dominated = queue[-1][1] <= value if qindex == 0 else queue[-1][1] >= value
                if not dominated:
                    break
                queue.pop()
                pops += 1
            queue.append((index, value))
            pushes += 1
        if index >= taps - 1:
            out.append([queue[0][1] for queue in queues])
    out = np.array(out, dtype=np.int64)
    return out, {"value_comparisons": comparisons, "queue_pushes": pushes,
                 "queue_pops": pops, "absolute_values": len(padded) if mode == "absolute" else 0,
                 "includes_initial_zero_history": True}


def evaluate(partial, full_sum, coeff, multiplicity, bound_data, bound, schedule):
    count = len(coeff)
    if schedule.startswith("late"):
        checkpoints = [max(0, count - int(schedule[4:]))]
    else:
        checkpoints = list(range(0, count, int(schedule[5:])))
    used = np.full(len(full_sum), count, dtype=np.int64)
    checks = np.zeros(len(full_sum), dtype=np.int64)
    bound_multiplies = np.zeros(len(full_sum), dtype=np.int64)
    predicted = q15(full_sum).copy()
    active = np.ones(len(full_sum), dtype=bool)
    weighted = coeff * multiplicity
    tail_abs = np.r_[np.cumsum(np.abs(weighted)[::-1])[::-1], 0]
    tail_pos = np.r_[np.cumsum(np.maximum(weighted, 0)[::-1])[::-1], 0]
    tail_neg = np.r_[np.cumsum(np.minimum(weighted, 0)[::-1])[::-1], 0]
    for k in checkpoints:
        p = np.zeros(len(full_sum), dtype=np.int64) if k == 0 else partial[:, k - 1]
        if bound == "absolute":
            radius = bound_data[:, 0] * tail_abs[k]
            low, high = -radius, radius
            multiplies = int(tail_abs[k] != 0)
        elif bound == "range":
            maximum, minimum = bound_data[:, 0], bound_data[:, 1]
            signed_sum = tail_pos[k] + tail_neg[k]
            twice_center = (minimum + maximum) * signed_sum
            twice_radius = (maximum - minimum) * tail_abs[k]
            # Exactly equal to min*Cplus + max*Cminus and its upper bound:
            # these numerators are even, since A and C have equal parity.
            assert np.all((twice_center - twice_radius) % 2 == 0)
            low = (twice_center - twice_radius) // 2
            high = (twice_center + twice_radius) // 2
            multiplies = int(signed_sum != 0) + int(tail_abs[k] != 0)
        else:
            minimum, maximum = bound_data
            # These are precomputed coefficient-only arrays for an externally
            # declared input domain. No running extrema and no per-check mul.
            low = minimum * tail_pos[k] + maximum * tail_neg[k]
            high = maximum * tail_pos[k] + minimum * tail_neg[k]
            multiplies = 0
        # Diagnostic oracle only: establish bound validity even on inactive rows.
        residual = full_sum - p
        assert np.all(low <= residual) and np.all(residual <= high)
        checks[active] += 1
        bound_multiplies[active] += multiplies
        lo = q15(p + low)
        hi = q15(p + high)
        exit_now = active & (lo == hi)
        used[exit_now] = k
        predicted[exit_now] = lo[exit_now]
        active[exit_now] = False
    assert np.array_equal(predicted, q15(full_sum))
    # Executed folded pre-additions, not merely MAC counts.
    pair_prefix = np.r_[0, np.cumsum(multiplicity == 2)]
    return {
        "mean_fir_products": float(used.mean()),
        "mean_folded_preadds": float(pair_prefix[used].mean()),
        "products_omitted_percent": float(100 * (1 - used.mean() / count)),
        "early_exit_percent": float(100 * np.mean(used < count)),
        "mean_certificate_checks": float(checks.mean()),
        "max_certificate_checks": int(checks.max()),
        "mean_bound_multiplications": float(bound_multiplies.mean()),
        "logical_multiplications_reduction_percent": float(
            100 * (1 - (used + bound_multiplies).mean() / count)),
        "max_fir_plus_bound_multiplications": int((used + bound_multiplies).max()),
        "outputs_verified": len(predicted), "output_mismatches": 0,
    }


def validate_toy_contract():
    # Exhaust all length-4 windows over {-2,-1,0,1,2}, including rounded
    # boundaries and saturating cells with a smaller analogous quantizer.
    import itertools
    checked = 0
    for coefficients in ([3, -2, -2, 3], [4, 1, 1, 4]):
        h = np.array(coefficients, dtype=np.int64)
        for values in itertools.product(range(-2, 3), repeat=4):
            x = np.array(values, dtype=np.int64)
            full = int(h @ x)
            quantize = lambda v: min(3, max(-4, v // 4))
            for k in range(4):
                p = int(h[:k] @ x[:k])
                tail = h[k:]
                for low, high in [
                    (-int(np.abs(x).max() * np.abs(tail).sum()),
                     int(np.abs(x).max() * np.abs(tail).sum())),
                    (int(x.min() * np.maximum(tail, 0).sum() + x.max() * np.minimum(tail, 0).sum()),
                     int(x.max() * np.maximum(tail, 0).sum() + x.min() * np.minimum(tail, 0).sum())),
                ]:
                    assert low <= full - p <= high
                    if quantize(p + low) == quantize(p + high):
                        assert quantize(p + low) == quantize(full)
                    checked += 1
    return checked


def main():
    toy_checks = validate_toy_contract()
    streams = list(signals())
    results, filter_metadata, maintenance = [], {}, []
    for name, h in filters():
        print(f"Analysing {name}", flush=True)
        indices = np.array([i for i in range((len(h) + 1) // 2) if h[i] != 0])
        paired = (indices != len(h) - 1 - indices).astype(np.int64)
        coeff = h[indices]
        multiplicity = paired + 1
        filter_metadata[name] = {
            "taps": len(h), "coefficients": h.tolist(), "coefficient_sha256": digest(h),
            "nonzero_unfolded_products": int(np.count_nonzero(h)),
            "folded_products": len(indices), "folded_preadds": int(paired.sum()),
            "absolute_coefficient_sum": int(np.abs(h).sum()),
        }
        for signal_name, x in streams:
            windows = np.lib.stride_tricks.sliding_window_view(
                np.r_[np.zeros(len(h) - 1, dtype=np.int64), x], len(h))[:, ::-1]
            full_sum = np.convolve(x, h)[:len(x)]
            terms = windows[:, indices].copy()
            terms[:, paired == 1] += windows[:, len(h) - 1 - indices[paired == 1]]
            terms *= coeff
            assert np.array_equal(terms.sum(axis=1), full_sum)
            bound_arrays = {}
            for mode in ("absolute", "range"):
                extrema, work = rolling_extrema(x, len(h), mode)
                if mode == "absolute":
                    assert np.array_equal(extrema[:, 0], np.abs(windows).max(axis=1))
                else:
                    assert np.array_equal(extrema[:, 0], windows.max(axis=1))
                    assert np.array_equal(extrema[:, 1], windows.min(axis=1))
                bound_arrays[mode] = extrema
                maintenance.append({"filter": name, "signal": signal_name, "bound": mode,
                                    "outputs": len(x), **work})
            for order in ("natural", "magnitude"):
                permutation = np.arange(len(coeff)) if order == "natural" else np.argsort(
                    -np.abs(coeff * multiplicity), kind="stable")
                partial = np.cumsum(terms[:, permutation], axis=1)
                for bound in ("absolute", "range"):
                    for schedule in ("every1", "every4", "every8", "late4", "late8", "late16"):
                        row = evaluate(partial, full_sum, coeff[permutation],
                                       multiplicity[permutation], bound_arrays[bound], bound, schedule)
                        results.append({
                            "filter": name, "signal": signal_name, "order": order,
                            "bound": bound, "schedule": schedule,
                            "folded_baseline_products": len(coeff),
                            "fraction_output_zero_or_minus_one": float(np.mean(
                                (q15(full_sum) == 0) | (q15(full_sum) == -1))),
                            "fraction_saturated_outputs": float(np.mean(
                                (q15(full_sum) == 32767) | (q15(full_sum) == -32768))),
                            **row,
                        })
                # Static bounds are an important no-maintenance baseline.
                # The ADC11 domain is justified only for native ADC streams;
                # x16 streams get that same declared ADC domain scaled by 16.
                domains = {"static_int16": (-32768, 32767)}
                if signal_name.startswith("ecg_adc_x1_"):
                    domains["static_adc"] = (-1024, 1023)
                elif signal_name.startswith("ecg_adc_x16_"):
                    domains["static_adc"] = (-16384, 16368)
                for bound, domain in domains.items():
                    assert np.all((x >= domain[0]) & (x <= domain[1]))
                    for schedule in ("every1", "every4", "every8", "late4", "late8", "late16"):
                        row = evaluate(partial, full_sum, coeff[permutation],
                                       multiplicity[permutation], domain, bound, schedule)
                        results.append({
                            "filter": name, "signal": signal_name, "order": order,
                            "bound": bound, "schedule": schedule,
                            "folded_baseline_products": len(coeff),
                            "fraction_output_zero_or_minus_one": float(np.mean(
                                (q15(full_sum) == 0) | (q15(full_sum) == -1))),
                            "fraction_saturated_outputs": float(np.mean(
                                (q15(full_sum) == 32767) | (q15(full_sum) == -32768))),
                            **row,
                        })
    output = {
        "description": "Exploratory numerical FIR feasibility probe, NOT timing/energy results",
        "seed": SEED, "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "toy_interval_checks": toy_checks,
        "ecg_source": ECG_URL, "ecg_file_sha256": ECG_SHA,
        "signals": {name: {"samples": len(x), "sha256": digest(x),
                           "minimum": int(x.min()), "maximum": int(x.max()),
                           "zero_fraction": float(np.mean(x == 0))} for name, x in streams},
        "filters": filter_metadata, "bound_maintenance": maintenance,
        "rows": results,
        "limitations": [
            "Logical operations are not ISA instructions, timing or energy.",
            "Operation reduction includes bound multiplies only; other checking/state/locality costs excluded.",
            "Static bounds rely on declared full-int16 or original ADC11 input domains, not observed extrema.",
            "Rolling-extrema work reported separately; no costs assigned to it.",
            "No threshold tuning, no adaptive bypass policy, no application filter-spec validation.",
            "Constant/sparse diagnostic streams need specialized baselines before any performance claim.",
            "Only one public ECG record; gains x1 and x16 preserve distinct but fixed input contracts.",
        ],
    }
    (ROOT / "fir-streaming-pilot.json").write_text(json.dumps(output, indent=2))
    with (ROOT / "fir-streaming-pilot.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(json.dumps({"conditions": len(results),
                      "output_comparisons": sum(r["outputs_verified"] for r in results),
                      "mismatches": sum(r["output_mismatches"] for r in results),
                      "toy_checks": toy_checks}))


if __name__ == "__main__":
    main()
