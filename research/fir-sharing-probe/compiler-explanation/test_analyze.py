"""Small literal fixtures for the saved-evidence analyzer."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fir_compiler_analyze", HERE / "analyze.py")
analyze = importlib.util.module_from_spec(spec)
if spec.loader is not None:
    # Loading is delayed until tests execute, so a missing implementation is a real red test.
    pass


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec.loader.exec_module(analyze)

    def test_disassembly_excludes_literal_pool_and_data(self):
        sample = """08000020 <probe_process>:
 8000020: 435a       muls r2, r3
 8000022: 9b01       ldr r3, [sp, #4]
 8000024: 000032be   .word 0x000032be
08000028 <input_data>:
 8000028: 12345678 abcdef00   ....
"""
        parsed = analyze.parse_disassembly(sample)
        self.assertEqual([site["mnemonic"] for site in parsed["instructions"]], ["muls", "ldr"])
        self.assertEqual(parsed["literal_sites"], [0x8000024])
        self.assertEqual(parsed["instructions"][0]["symbol"], "probe_process")

    def test_event_log_rejects_malformed_and_duplicate_counters(self):
        good = """TeamPlay: GPIOC[0] raised at cycle 1, insn count 0, pc = 8000011
TeamPlay: GPIOC[0] cleared at cycle 10, insn count 6, pc = 8000021
Executed insns: 6
RAM data reads: 2
RAM writes: 3
Flash data reads: 1
Flash writes: 0
Taken branches: 2
BL insns: 1
Opcode statistics:
16: 2, [0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0]
"""
        got = analyze.parse_event_log(good, check_opcode_sum=False)
        self.assertEqual(got["instructions"], 5)
        self.assertEqual(got["mul"], 2)
        with self.assertRaises(ValueError):
            analyze.parse_event_log(good.replace("RAM writes: 3", "RAM writes: -3"), check_opcode_sum=False)
        with self.assertRaises(ValueError):
            analyze.parse_event_log(good + "RAM writes: 3\n", check_opcode_sum=False)
        with self.assertRaises(ValueError):
            analyze.parse_event_log(good.replace("BL insns: 1\n", ""), check_opcode_sum=False)

    def test_missing_duplicate_classification_and_sum(self):
        sites = [{"address": 0x20}, {"address": 0x22}]
        self.assertEqual(analyze.classify_sites(sites, {0x20: "convolution", 0x22: "copy_in"}),
                         {0x20: "convolution", 0x22: "copy_in"})
        with self.assertRaises(ValueError):
            analyze.classify_sites(sites, {0x20: "convolution"})
        with self.assertRaises(ValueError):
            analyze.classify_sites(sites, [(0x20, "convolution"), (0x20, "copy_in"), (0x22, "copy_in")])
        with self.assertRaises(ValueError):
            analyze.classify_sites(sites, {0x20: "convolution", 0x22: "wrong"})
        totals = {key: 0 for key in analyze.COUNTERS}
        totals["instructions"] = 5
        parts = [{"name": "convolution", "events": {**totals, "instructions": 2}},
                 {"name": "unattributed", "events": {**totals, "instructions": 2}}]
        with self.assertRaises(ValueError):
            analyze.reconcile(totals, parts)
        parts[1]["events"]["instructions"] = 3
        analyze.reconcile(totals, parts)

    def test_direct_sp_sites_distinguish_unreachable_path(self):
        sample = """08000024 <probe_process>:
 8000032: 9307       str r3, [sp, #28]
 800003e: 9b07       ldr r3, [sp, #28]
 8000406: 9305       str r3, [sp, #20]
"""
        sites = analyze.parse_disassembly(sample)["instructions"]
        paths = analyze.direct_sp_events(sites, "gcc10")
        self.assertEqual(paths["reads"], 1)
        self.assertEqual(paths["writes"], 1)
        self.assertEqual(paths["excluded"], [0x8000406])

    def test_generated_certificates_keep_each_compilers_path(self):
        build = HERE / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as scratch:
            output = Path(scratch)
            shutil.copyfile(HERE / "assembly-notes.md", output / "assembly-notes.md")
            analyze.analyze(HERE.parent / "partial-direct", output)
            for generated in (output / "accounting.json",
                              output / "evidence" / "command-record.json",
                              output / "evidence" / "gcc10-b1" / "site-classification.json",
                              output / "evidence" / "gcc15-b1" / "site-classification.json"):
                self.assertNotIn(b"\r\n", generated.read_bytes(), str(generated))
            report = json.loads((output / "accounting.json").read_text(encoding="utf-8"))
            self.assertEqual(report["evidence"]["assembly-notes.md"],
                             analyze.sha256(output / "assembly-notes.md"))
            proofs = {}
            for compiler in ("gcc10", "gcc15"):
                detail = json.loads((output / "evidence" / f"{compiler}-b1" /
                                     "site-classification.json").read_text(encoding="utf-8"))
                proofs[compiler] = detail["block1_path_proof"]
            self.assertEqual((proofs["gcc10"]["direct_sp_reads_per_call"],
                              proofs["gcc10"]["direct_sp_writes_per_call"]), (9, 9))
            self.assertEqual(proofs["gcc10"]["excluded_zero_block_sites"], ["0x08000406"])
            self.assertEqual(len(proofs["gcc10"]["executed_direct_sp_sites"]), 18)
            self.assertEqual((proofs["gcc15"]["direct_sp_reads_per_call"],
                              proofs["gcc15"]["direct_sp_writes_per_call"]), (63, 84))
            self.assertEqual(proofs["gcc15"]["excluded_zero_block_sites"], [])
            self.assertEqual(len(proofs["gcc15"]["executed_direct_sp_sites"]), 147)

    def test_missing_annotation_fails_before_report_write(self):
        build = HERE / "build"
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build) as scratch:
            output = Path(scratch)
            with self.assertRaisesRegex(ValueError, "assembly-notes.md"):
                analyze.analyze(HERE.parent / "partial-direct", output)
            self.assertFalse((output / "accounting.json").exists())


if __name__ == "__main__":
    unittest.main()
