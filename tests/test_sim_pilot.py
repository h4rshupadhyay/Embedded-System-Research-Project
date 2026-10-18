"""Run real Cortex-M0 binaries; validate work and marked intervals."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_fir import reference
from run_sim_pilot import parse_profile


ROOT = Path(__file__).resolve().parents[1]
TOOLS_AVAILABLE = all(shutil.which(name) for name in (
    "arm-none-eabi-gcc", "arm-none-eabi-objcopy")) and (ROOT / "thumbulator").exists()


def expected_checksum(taps, block, jobs):
    def sample(index):
        bits = (index * 100) & 0xffff
        return bits if bits < 32768 else bits - 65536
    stream = [sample(i) for i in range(taps + block * jobs)]
    outputs = reference(stream[taps:], [1000 - 10 * k for k in range(taps)],
                        stream[:taps])
    checksum = 2166136261
    for value in outputs:
        checksum = ((checksum ^ (value & 0xffff)) * 16777619) & 0xffffffff
    return checksum


class ProfileParserTests(unittest.TestCase):
    def test_interval_counters_are_not_replaced_by_final_program_totals(self):
        trace = """TeamPlay: GPIOC[0] raised at cycle 10, insn count 1, pc = 8000000
TeamPlay: GPIOC[0] cleared at cycle 40, insn count 21, pc = 8000000
Executed insns: 20
RAM data reads: 5
RAM writes: 2
Flash data reads: 0
Taken branches: 3
Opcode statistics:
Executed insns: 500
Mul insns: 100
"""
        with self.assertRaisesRegex(ValueError, "Mul insns"):
            parse_profile(trace, 1)

    def test_nonmultiplication_counter_uses_interval_multiply_count(self):
        trace = """TeamPlay: GPIOC[0] raised at cycle 10, insn count 1, pc = 8000000
TeamPlay: GPIOC[0] cleared at cycle 40, insn count 21, pc = 8000000
Executed insns: 20
Mul insns: 4
RAM data reads: 5
RAM writes: 2
Flash data reads: 0
Taken branches: 3
Opcode statistics:
"""
        job, = parse_profile(trace, 1)
        self.assertEqual(job["active_cycles"], 30)
        self.assertEqual(job["counters"], {"C1": 16, "C2": 5, "C3": 2,
                                            "C4": 0, "C5": 3, "C6": 4})

    def test_missing_end_marker_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "markers"):
            parse_profile("TeamPlay: GPIOC[0] raised at cycle 10,", 1)

    def test_reversed_markers_are_rejected(self):
        trace = ("TeamPlay: GPIOC[0] cleared at cycle 10,\n"
                 "TeamPlay: GPIOC[0] raised at cycle 40,\n")
        with self.assertRaisesRegex(ValueError, "Unpaired"):
            parse_profile(trace, 1)


@unittest.skipUnless(TOOLS_AVAILABLE, "Cortex-M0 compiler and patched Thumbulator required")
class SimulationPilotTests(unittest.TestCase):
    def run_cli(self, output, *arguments):
        return subprocess.run([
            "python3", str(ROOT / "run_sim_pilot.py"), "--output", str(output),
            *arguments], cwd=ROOT, capture_output=True, text=True, timeout=90)

    def test_marked_jobs_match_stream_reference_on_cortex_m0(self):
        for taps, block, jobs, opt in ((7, 5, 3, "O0"), (16, 32, 4, "O3")):
            with self.subTest(taps=taps, block=block, opt=opt), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "pilot.json"
                result = self.run_cli(output, "--taps", str(taps), "--block", str(block),
                                      "--jobs", str(jobs), "--opt", opt,
                                      "--period-cycles", "1000000")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report = json.loads(output.read_text())
                self.assertFalse(report["physical_measurement"])
                self.assertFalse(report["idle_simulated"])
                self.assertEqual(len(report["variants"]), 3)
                for row in report["variants"]:
                    self.assertEqual(row["checksum"], expected_checksum(taps, block, jobs))
                    self.assertEqual(row["completed_jobs"], jobs)
                    self.assertEqual(len(row["jobs"]), jobs)
                    for index, job in enumerate(row["jobs"]):
                        self.assertEqual(job["release_cycle"], index * 1000000)
                        self.assertGreater(job["active_cycles"], 0)
                        self.assertEqual(job["idle_cycles"], 1000000 - job["active_cycles"])
                        self.assertEqual(job["counters"]["C6"], taps * block)
                        self.assertGreater(job["counters"]["C1"], 0)
                        self.assertGreater(job["counters"]["C2"], 0)
                        self.assertGreater(job["counters"]["C3"], 0)
                        self.assertLess(job["sim_start_cycle"], job["sim_end_cycle"])
                        if index:
                            self.assertGreater(job["sim_start_cycle"],
                                               row["jobs"][index - 1]["sim_end_cycle"])

    def test_infeasible_period_is_rejected_without_a_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pilot.json"
            result = self.run_cli(output, "--period-cycles", "1")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("period", result.stderr.lower())
            self.assertFalse(output.exists())

    def test_existing_report_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pilot.json"
            output.write_text("existing evidence\n")
            result = self.run_cli(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(output.read_text(), "existing evidence\n")


if __name__ == "__main__":
    unittest.main()
