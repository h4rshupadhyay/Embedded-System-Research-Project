"""Numerical contract tests for the C research baselines (host execution).

Run: python -m unittest discover -s research/fir-baseline -p 'test_*.py'
"""
import ctypes
import json
from pathlib import Path
import subprocess
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parent
FUNCTIONS = ("direct64", "direct32", "fold64", "fold32", "fold64_wide")
POINTER = ctypes.POINTER(ctypes.c_int16)


def eligible(name, h, maximum):
    if "fold" in name and not np.array_equal(h, h[::-1]):
        return False
    if name in ("direct32", "fold32") and maximum * sum(abs(int(c)) for c in h) > 2**31 - 1:
        return False
    if name in ("fold32", "fold64") and any(
            2 * maximum * abs(int(c)) > 2**31 - 1 for c in h[:len(h)//2]):
        return False
    return True


def pointer(x):
    return x.ctypes.data_as(POINTER)


class KernelContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT / "build"
        build.mkdir(exist_ok=True)
        subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-fPIC", "-shared", "-fsanitize=undefined",
                        "-fno-sanitize-recover=undefined", str(ROOT/"kernels.c"),
                        "-o", str(build/"kernels.so")], check=True)
        cls.library = ctypes.CDLL(str(build/"kernels.so"))
        for name in FUNCTIONS:
            function = getattr(cls.library, name)
            function.argtypes = [POINTER, POINTER, POINTER, POINTER, ctypes.c_uint32, ctypes.c_uint32]
            function.restype = None

    def check_stream(self, h, x, maximum, block):
        h = np.array(h, dtype=np.int16)
        x = np.array(x, dtype=np.int16)
        reference = np.clip(np.convolve(x.astype(np.int64), h.astype(np.int64))[:len(x)]
                            // 32768, -32768, 32767).astype(np.int16)
        for name in FUNCTIONS:
            if not eligible(name, h, maximum):
                continue
            with self.subTest(kernel=name, taps=len(h), block=block):
                state_guard = np.full(len(h)-1+block+2, 23130, dtype=np.int16)
                state = state_guard[1:-1]
                state[:] = 0
                output_guard = np.full(len(x)+2, 23130, dtype=np.int16)
                output = output_guard[1:-1]
                for offset in range(0, len(x), block):
                    size = min(block, len(x)-offset)
                    getattr(self.library, name)(pointer(state), pointer(h), pointer(x[offset:]),
                                               pointer(output[offset:]), len(h), size)
                self.assertTrue(np.array_equal(output, reference),
                                f"{name}: output differs from full quantized convolution")
                self.assertEqual(int(state_guard[0]), 23130)
                self.assertEqual(int(state_guard[-1]), 23130)
                self.assertEqual(int(output_guard[0]), 23130)
                self.assertEqual(int(output_guard[-1]), 23130)
                history = np.r_[np.zeros(len(h)-1, dtype=np.int16), x][-(len(h)-1):]
                if len(h)>1:
                    self.assertTrue(np.array_equal(state[:len(h)-1], history),
                                    f"{name}: retained stream history differs")

    def test_negative_floor_and_saturation(self):
        for block in (1, 3, 16):
            self.check_stream([32767], [3, -1, -32768, 32767, -3], 32768, block)
            self.check_stream([32767, 32767],
                              [-32768, -32768, 32767, 32767, 0, -1], 32768, block)
            self.check_stream([-32768, -32768], [-1024, -1024, 1023, 0, -1], 1024, block)

    def test_declared_domains_gate_unsafe_variants(self):
        h = np.array([-32768, -32768], dtype=np.int16)
        self.assertFalse(eligible("direct32", h, 32768))
        self.assertFalse(eligible("fold32", h, 32768))
        self.assertFalse(eligible("fold64", h, 32768))
        self.assertTrue(eligible("fold64_wide", h, 32768))
        self.check_stream(h, [-32768, -32768, 32767, 32767, -1], 32768, 3)

    def test_filter_bank_and_stream_partitions(self):
        data = json.loads((ROOT.parent/"fir-streaming-pilot.json").read_text())
        rng = np.random.default_rng(20261019)
        for item in data["filters"].values():
            h = item["coefficients"]
            for maximum in (1024, 32768):
                x = rng.integers(-maximum, maximum, 519, dtype=np.int16)
                for block in (1, 16, 64):
                    self.check_stream(h, x, maximum, block)

    def test_non_symmetric_filter_and_odd_center(self):
        rng = np.random.default_rng(17)
        x = rng.integers(-32768, 32768, 131, dtype=np.int16)
        for block in (1, 7, 32):
            self.check_stream([3, -7, 11, 31], x, 32768, block)
            self.check_stream([3, -7, 16384, -7, 3], x, 32768, block)


class DisassemblyScreen(unittest.TestCase):
    def test_data_words_are_not_instruction_mnemonics(self):
        from experiment import check_instruction_subset
        text=("08000200 <coefficients>:\n"
              " 8000200:\t00530056 001a0040 ff96ffe1 fee4ff3e     V.S.@.......>...\n"
              " 8000208:\tfff4 fffc 0005 0011 001f 0030 0041 004f     ..........0.A.O.\n"
              "08000300 <kernel>:\n"
              " 8000300:\t4350      \tmuls\tr0, r2\n"
              " 8000302:\t425b      \tnegs\tr3, r3\n")
        self.assertEqual(check_instruction_subset(text),["muls","negs"])


if __name__ == "__main__":
    unittest.main()
