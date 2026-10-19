"""Arbitrary-precision checks for the fixed speech_minphase48 direct kernel."""
import json
import os
from pathlib import Path
import random
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent.parent / "fir-baseline" / "selection-design.json"
COEFFICIENTS = json.loads(DESIGN.read_text())["filters"]["speech_minphase48"]["coefficients"]
TAPS = 48
CAPACITY = 64


def reference(samples):
    result = []
    for n in range(len(samples)):
        exact = sum(COEFFICIENTS[k] * samples[n - k]
                    for k in range(min(n + 1, TAPS)))
        result.append(max(-32768, min(32767, exact // 32768)))
    return result


def sign_aligned_window(sign=1):
    # At output 47, input[47-k] gives each coefficient its extremal sign.
    return [sign * (-32768 if c < 0 else 32767)
            for c in reversed(COEFFICIENTS)]


class KernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = HERE / "build" / "host"
        cls.build.mkdir(parents=True, exist_ok=True)
        cls.executable = cls.build / ("host_harness.exe" if os.name == "nt" else "host_harness")
        flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-DBLOCK=64"]
        if os.environ.get("FIR_UBSAN") == "1":
            flags += ["-fsanitize=undefined", "-fno-sanitize-recover=undefined"]
        command = [os.environ.get("CC", "gcc"), *flags, str(HERE / "kernel.c"),
                   str(HERE / "host_harness.c"), "-o", str(cls.executable)]
        compiled = subprocess.run(command, capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(f"host compile failed ({compiled.returncode}):\n{compiled.stdout}{compiled.stderr}")

    def check_stream(self, samples, partitions):
        calls = []
        remaining = len(samples)
        for requested in partitions:
            if remaining == 0:
                break
            calls.append(min(requested, remaining))
            remaining -= calls[-1]
        self.assertEqual(remaining, 0)
        payload = f"{len(samples)} {len(calls)}\n" + " ".join(map(str, samples)) + "\n"
        payload += " ".join(map(str, calls)) + "\n"
        process = subprocess.run([str(self.executable)], input=payload, capture_output=True,
                                 text=True, check=True,
                                 env={**os.environ, "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"})
        lines = process.stdout.splitlines()
        self.assertEqual(len(lines), len(calls) + 4)
        self.assertEqual(lines[0], "I" + " 0" * 47)
        offset = 0
        for call, line in zip(calls, lines[1:-3]):
            offset += call
            self.assertEqual([int(v) for v in line.split()[1:]],
                             ([0] * 47 + samples[:offset])[-47:])
        self.assertEqual(offset, len(samples))
        self.assertEqual([int(v) for v in lines[-3].split()[1:]], reference(samples))
        self.assertEqual(lines[-2], "G 1")
        self.assertEqual(lines[-1], f"B {2 * (TAPS + CAPACITY)}")

    def test_full_scale_overflow_and_saturation(self):
        positive = sign_aligned_window(1)
        negative = [-x if x != -32768 else 32767 for x in positive]
        self.assertGreater(sum(c * positive[47 - k] for k, c in enumerate(COEFFICIENTS)),
                           2**31 - 1)
        self.assertLess(sum(c * negative[47 - k] for k, c in enumerate(COEFFICIENTS)),
                        -2**31)
        self.check_stream(positive + [0] * 49 + negative + [0] * 9,
                          [1, 64, 3, 16] * 10)

    def test_signed_extrema_and_short_final_call(self):
        samples = ([-32768, 32767, 0, -1, 1] * 51) + [-32768, 32767]
        self.assertEqual(len(samples), 257)
        self.check_stream(samples, [64] * 5)
        self.check_stream(samples, [1] * 257)

    def test_negative_floor_boundaries_and_mixed_calls(self):
        # h[40]=10 and h[47]=-39 have gcd 1. Choose their two samples so
        # the exact sum at n=47 straddles zero and a Q15 floor boundary.
        self.assertEqual((COEFFICIENTS[40], COEFFICIENTS[47]), (10, -39))
        for exact in (-32769, -32768, -32767, -1, 0, 1):
            a = (4 * exact) % 39
            b = (10 * a - exact) // 39
            self.assertTrue(-32768 <= a <= 32767 and -32768 <= b <= 32767)
            window = [0] * 48
            window[7], window[0] = a, b
            self.assertEqual(sum(COEFFICIENTS[k] * window[47-k]
                                 for k in range(48)), exact)
            self.assertEqual(reference(window)[47], exact // 32768)
            self.check_stream(window, [1, 3, 16, 28])
        # Exhaust small signed values plus a deterministic full-domain stream.
        random_values = random.Random(20261020)
        samples = list(range(-160, 161)) + [random_values.randint(-32768, 32767)
                                            for _ in range(255)]
        self.assertTrue(any(-32768 < sum(COEFFICIENTS[k] * samples[n-k]
                                            for k in range(min(n+1, TAPS))) < 0
                            for n in range(len(samples))))
        self.check_stream(samples, [1, 64, 3, 16] * 100)


if __name__ == "__main__":
    unittest.main()
