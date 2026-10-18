"""Independent integer oracle for the real C kernels at every sweep opt level."""

import ctypes
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("direct", "circular", "unrolled4")


def reference(samples, coefficients, history):
    """Unbounded convolution, floor to Q15, then retain the low 16 bits."""
    stream = history + samples
    result = []
    for n in range(len(samples)):
        total = sum(stream[len(history) + n - k] * h
                    for k, h in enumerate(coefficients))
        bits = (total // 32768) & 0xffff
        result.append(bits if bits < 32768 else bits - 65536)
    return result


class FIRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.libraries = {}
        for opt in ("-O0", "-O1", "-O2", "-O3", "-Os"):
            path = Path(cls.directory.name) / (opt[1:] + ".so")
            subprocess.run([
                "gcc", "-std=c11", opt, "-Wall", "-Wextra", "-Werror",
                "-shared", "-fPIC", str(ROOT / "fir.c"), "-o", str(path),
            ], check=True)
            library = ctypes.CDLL(str(path))
            for variant in VARIANTS:
                function = getattr(library, "fir_" + variant + "_q15")
                function.argtypes = [ctypes.POINTER(ctypes.c_int16)] * 3 + [
                    ctypes.c_uint16, ctypes.c_uint16]
            cls.libraries[opt] = library

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def compute(self, library, variant, samples, coefficients, history):
        # Exactly taps-1 preceding samples: no hidden extra guard allocation.
        storage = (ctypes.c_int16 * (len(history) + len(samples)))(
            *(history + samples))
        taps = (ctypes.c_int16 * len(coefficients))(*coefficients)
        output = (ctypes.c_int16 * len(samples))()
        current = ctypes.cast(ctypes.byref(storage, 2 * len(history)),
                              ctypes.POINTER(ctypes.c_int16))
        getattr(library, "fir_" + variant + "_q15")(
            current, taps, output, len(samples), len(coefficients))
        return list(output)

    def check_case(self, samples, coefficients, history):
        expected = reference(samples, coefficients, history)
        for opt, library in self.libraries.items():
            for variant in VARIANTS:
                with self.subTest(opt=opt, variant=variant,
                                  taps=len(coefficients), block=len(samples)):
                    self.assertEqual(self.compute(library, variant, samples,
                                                  coefficients, history), expected)

    def test_nonzero_history_contributes_to_first_sample(self):
        # A half-scale historical sample times a half-scale tap gives 8192.
        self.assertEqual(reference([0, 0], [16384, 16384], [16384]), [8192, 0])
        self.check_case([0, 0], [16384, 16384], [16384])

    def test_negative_fraction_rounds_down(self):
        self.assertEqual(reference([-1, 1], [1], []), [-1, 0])
        self.check_case([-1, 1], [1], [])

    def test_extreme_products_and_overflow_have_defined_output_bits(self):
        cases = [
            ([-32768], [-32768], [], [-32768]),
            ([-32768], [-32768, -32768], [-32768], [0]),
            ([32767, -32768], [32767] * 7, [32767] * 6, [32754, 32757]),
        ]
        for samples, taps, history, expected in cases:
            self.assertEqual(reference(samples, taps, history), expected)
            self.check_case(samples, taps, history)

    def test_impulse_zero_and_random_cases_include_unrolled_tails(self):
        rng = random.Random(61024)
        for taps in (1, 2, 3, 4, 5, 7, 8, 16, 31, 32):
            for block in (0, 1, 3, 32, 64, 128):
                self.check_case([0] * block, [0] * taps, [0] * (taps - 1))
                samples = [32767] + [0] * (block - 1) if block else []
                self.check_case(samples, [1024] * taps, [0] * (taps - 1))
                self.check_case(
                    [rng.randint(-32768, 32767) for _ in range(block)],
                    [rng.randint(-32768, 32767) for _ in range(taps)],
                    [rng.randint(-32768, 32767) for _ in range(taps - 1)])

    def test_splitting_stream_preserves_outputs_with_carried_history(self):
        samples = [((i * 7919) % 65536) - 32768 for i in range(137)]
        taps = [2000, -3000, 32767, -32768, 123, 1000, -5]
        initial = [12000, -4000, 17, 0, -1, 30000]
        expected = reference(samples, taps, initial)
        for opt, library in self.libraries.items():
            for variant in VARIANTS:
                history = initial[:]
                actual = []
                start = 0
                for length in (1, 2, 5, 32, 64, 33):
                    chunk = samples[start:start + length]
                    actual.extend(self.compute(library, variant, chunk, taps, history))
                    history = (history + chunk)[-(len(taps) - 1):]
                    start += length
                with self.subTest(opt=opt, variant=variant):
                    self.assertEqual(actual, expected)

    def test_native_kernels_under_address_and_undefined_behavior_sanitizers(self):
        binary = Path(self.directory.name) / "sanitizer"
        subprocess.run([
            "gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-no-pie",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer", "-I", str(ROOT), str(ROOT / "fir.c"),
            str(ROOT / "tests/fir_sanitizer.c"), "-o", str(binary),
        ], check=True)
        environment = dict(os.environ)
        # LSan cannot run under this environment's ptrace sandbox. Bounds and
        # undefined-behavior checks remain enabled; this fixture frees its buffers.
        environment["ASAN_OPTIONS"] = environment.get("ASAN_OPTIONS", "") + ":detect_leaks=0"
        result = subprocess.run([str(binary)], capture_output=True, text=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
