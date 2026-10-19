"""Independent numerical and evidence-integrity checks; no target execution."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('independent_fir_check', HERE / 'check.py')
checker = importlib.util.module_from_spec(SPEC) if SPEC else None
if SPEC and SPEC.loader and (HERE / 'check.py').exists():
    SPEC.loader.exec_module(checker)
else:
    checker = None


class ReferenceTests(unittest.TestCase):
    def test_independent_checker_exists(self):
        self.assertIsNotNone(checker, 'Independent reference/checker has not been implemented')

    def test_negative_floor_saturation_and_zero_history(self):
        self.assertEqual(checker.reference([16384, -8192], [2, -2, 0]), [1, -2, 0])
        self.assertEqual(checker.reference([32767], [-1, 32767]), [-1, 32766])
        self.assertEqual(checker.reference([32767, 32767], [32767, 32767, -32768, -32768]),
                         [32766, 32767, -1, -32768])

    def test_history_and_transposed_state_use_correct_order(self):
        self.assertEqual(checker.retained_state([2, -3, 5], [7], False), [0, 7])
        self.assertEqual(checker.retained_state([2, -3, 5], [7, 11], False), [7, 11])
        self.assertEqual(checker.retained_state([2, -3, 5], [7, 11], True), [2, 55])

    def test_mixed_partitions_do_not_reset_history(self):
        # Dropping state at block boundaries changes this literal convolution.
        x = [2, -2, 0, 4, -4, 1, -1]
        out, histories = checker.partition_reference([16384, -8192], x, [1, 3, 2, 1])
        self.assertEqual(out, [1, -2, 0, 2, -3, 1, -1])
        self.assertEqual(histories, [[2], [4], [1], [-1]])

    def test_full_block64_mixed_sequence_has_short_final_call(self):
        x = list(range(-43, 44))
        out, histories = checker.partition_reference([16384, 16384], x, [1, 64, 3, 16, 3])
        self.assertEqual(out, [-22] + list(range(-43, 43)))
        self.assertEqual(histories, [[-43], [21], [24], [40], [43]])


class RawEvidenceTests(unittest.TestCase):
    def test_decoder_rejects_truncated_signed_words_and_duplicate_records(self):
        self.assertEqual(checker.decode_words('O:8000ffff00007fff\n', 'O', 16),
                         [-32768, -1, 0, 32767])
        with self.assertRaises(ValueError):
            checker.decode_words('H:fffffffffffffff\n', 'H', 64)
        with self.assertRaises(ValueError):
            checker.decode_words('O:0000\nO:0001\n', 'O', 16)

    def test_costs_use_documented_model_and_ignore_raw_ticks(self):
        events = dict(instructions=10, ram_reads=2, ram_writes=3, flash_reads=1,
                      flash_writes=0, taken_branches=2, bl=1, mul=2, raw_tick_delta=999)
        cycles, energy = checker.costs(events)
        self.assertEqual(cycles, 21)
        self.assertAlmostEqual(energy, 20.007922)

    def test_instruction_screen_ignores_data_and_rejects_unsupported_instructions(self):
        data = '08000008 <probe_process>:\n 8000008:\t4770      \tbx\tlr\n'
        data += ' 800000a:\t12345678 \tascii text that is data\n'
        self.assertEqual(checker.instruction_subset(data), ['bx'])
        with self.assertRaisesRegex(ValueError, 'instruction'):
            checker.instruction_subset('08000008 <probe_process>:\n 8000008:\tfbb0 f0f1\tudiv\tr0,r1\n')


RAW_ROOT = Path(os.environ.get('FIR_PROBE_ROOT', str(HERE.parent)))
HAS_ARTIFACTS = (RAW_ROOT / 'build/cases').is_dir()


@unittest.skipUnless(HAS_ARTIFACTS, 'Historical raw artifacts absent; set FIR_PROBE_ROOT')
class HistoricalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((RAW_ROOT / 'results.json').read_text())
        cls.design = json.loads((RAW_ROOT.parent / 'fir-baseline/selection-design.json').read_text())
        cls.h = cls.design['filters']['speech_minphase48']['coefficients']
        cls.x = cls.design['inputs']['adc_raw'][:257]
        cls.row = next(r for r in cls.data['rows'] if
                       (r['compiler'], r['filter'], r['maximum'], r['block'], r['variant']) ==
                       ('gcc15', 'speech_minphase48', 32768, 64, 'spec_direct'))

    def test_all_matching_controls_are_verified_without_target_execution(self):
        result = checker.verify_existing(RAW_ROOT)
        self.assertEqual(len(result['rows']), 24)
        self.assertEqual(result['verified_output_comparisons'], 6168)

    def test_full_sum_exceeds_int32_but_both_partial_prefixes_fit(self):
        proof = checker.arithmetic_certificate(self.h)
        self.assertEqual(proof['partial_absolute_bounds'], [418709504, 1957265408])
        self.assertGreater(proof['positive_aligned_sum'], 2147483647)
        self.assertLess(proof['negative_aligned_sum'], -2147483648)
        self.assertEqual(checker.reference(self.h, proof['positive_window'])[-1], 32767)
        self.assertEqual(checker.reference(self.h, proof['negative_window'])[-1], -32768)

    def changed_artifacts(self, filename, transform):
        """Copy real evidence so corruption tests never touch frozen files."""
        import shutil
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        row = copy.deepcopy(self.row)
        source = RAW_ROOT / row['directory']
        dest = root / row['directory']
        shutil.copytree(source, dest)
        path = dest / filename
        path.write_text(transform(path.read_text()))
        # Renew the checksum: reject a semantic error even with an updated manifest.
        row['artifacts'][filename] = checker.sha(path)
        return root, row

    def test_rejects_changed_output_even_with_updated_checksum(self):
        root, row = self.changed_artifacts('firmware.stdout', lambda s: s.replace('O:ff91', 'O:ff90', 1))
        with self.assertRaisesRegex(ValueError, 'output'):
            checker.verify_row(row, root, self.h, self.x)

    def test_rejects_shortened_history_even_with_updated_checksum(self):
        import re
        root, row = self.changed_artifacts('firmware.stdout',
            lambda s: re.sub(r'(?m)^(H:)[0-9a-f]{16}', r'\1', s, count=1))
        with self.assertRaisesRegex(ValueError, 'history|state'):
            checker.verify_row(row, root, self.h, self.x)

    def test_rejects_changed_firmware_input_even_with_updated_checksum(self):
        root, row = self.changed_artifacts('firmware.c', lambda s: s.replace('{-1024,1023,', '{-1023,1023,', 1))
        with self.assertRaisesRegex(ValueError, 'input'):
            checker.verify_row(row, root, self.h, self.x)

    def test_rejects_counter_change_and_cost_change(self):
        for key in ('instructions', 'arm_zero_ws_cycles', 'estimated_cpu_energy_nj'):
            row = copy.deepcopy(self.row)
            row[key] += 100
            with self.subTest(key=key), self.assertRaises(ValueError):
                checker.verify_row(row, RAW_ROOT, self.h, self.x)

    def test_rejects_unhashed_binary(self):
        row = copy.deepcopy(self.row)
        del row['artifacts']['firmware.bin']
        with self.assertRaisesRegex(ValueError, 'artifact|binary'):
            checker.verify_row(row, RAW_ROOT, self.h, self.x)

    def test_rejects_guard_damage(self):
        root, row = self.changed_artifacts('firmware.stdout', lambda s: s.replace('G:5a5a', 'G:0000', 1))
        with self.assertRaisesRegex(ValueError, 'guard'):
            checker.verify_row(row, root, self.h, self.x)

    def test_rejects_raw_histogram_disagreement(self):
        root, row = self.changed_artifacts('firmware.stderr',
            lambda s: s.replace('Executed insns:', 'Unexpected insns:', 1))
        with self.assertRaisesRegex(ValueError, 'counter'):
            checker.verify_row(row, root, self.h, self.x)

    def test_resource_sizes_are_derived_from_raw_elf_and_stack_reports(self):
        row = next(r for r in self.data['rows'] if
                   (r['compiler'], r['filter'], r['maximum'], r['block'], r['variant']) ==
                   ('gcc15', 'speech_minphase48', 32768, 64, 'trans_hcub_demand'))
        checked = checker.verify_row(row, RAW_ROOT, self.h, self.x)
        self.assertEqual(checked['state_allocation_bytes'], 192)
        self.assertEqual(checked['probe_process_stack_bytes'], 344)
        row = copy.deepcopy(row)
        row['stack_usage'][0]['bytes'] += 4
        with self.assertRaisesRegex(ValueError, 'stack'):
            checker.verify_row(row, RAW_ROOT, self.h, self.x)

    def peer_metadata(self):
        return {'stage': 'post-audit missing-control', 'design_sha256': checker.DESIGN_SHA,
                'sharing_results_sha256': checker.RESULTS_SHA,
                'compilers': copy.deepcopy(self.data['compilers']),
                'model': copy.deepcopy(self.data['model']),
                'flags': ['-mcpu=cortex-m0', '-mthumb', '-std=c11', '-ffreestanding',
                          '-fno-builtin', '-ffunction-sections', '-fdata-sections', '-g0', '-O2'],
                'rows': []}

    def test_peer_acceptance_requires_exactly_four_distinct_configurations(self):
        data = self.peer_metadata()
        rows = [copy.deepcopy(self.row) for _ in range(4)]
        for row in rows:
            row['variant'] = 'partial_direct32x2'
        data['rows'] = rows
        with self.assertRaisesRegex(ValueError, 'configuration'):
            checker.verify_peer(data, RAW_ROOT, self.data, self.h, self.x)

    def test_peer_rejects_changed_design_compiler_flags_or_model(self):
        for mutation in ('design', 'compiler', 'flags', 'model'):
            data = self.peer_metadata()
            if mutation == 'design': data['design_sha256'] = '0'*64
            if mutation == 'compiler': data['compilers']['gcc15']['sha256'] = '0'*64
            if mutation == 'flags': data['flags'].append('-flto')
            if mutation == 'model': data['model']['energy_weights_nj']['mul'] = 0
            reason = 'hash' if mutation == 'design' else mutation
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, reason):
                checker.verify_peer(data, RAW_ROOT, self.data, self.h, self.x)

    def test_peer_ingestion_accepts_four_reused_direct_fixtures_without_claiming_new_measurements(self):
        # Exercise the evidence format with real wide-direct files. These are NOT
        # partial-direct measurements and are never written to research reports.
        data = self.peer_metadata()
        for r in self.data['rows']:
            if r['filter'] == 'speech_minphase48' and r['maximum'] == 32768 and r['variant'] == 'spec_direct':
                row = copy.deepcopy(r)
                row['variant'] = 'partial_direct32x2'
                data['rows'].append(row)
        rows = checker.verify_peer(data, RAW_ROOT, self.data, self.h, self.x)
        self.assertEqual({(r['compiler'], r['block']) for r in rows},
                         {('gcc10', 1), ('gcc10', 64), ('gcc15', 1), ('gcc15', 64)})
        result = checker.verify_existing(RAW_ROOT)
        result['peer_rows'] = rows
        text = checker.comparison_markdown(result)
        self.assertNotIn('| partial_direct32x2 | pending |', text)
        self.assertNotIn('peer result remains pending', text)
        self.assertIn('Hcub cost relative to new direct:', text)

    def test_rejects_artifact_path_outside_the_result_directory(self):
        row = copy.deepcopy(self.row)
        row['directory'] = '../outside-the-probe'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            checker.verify_row(row, RAW_ROOT, self.h, self.x)

    def test_comparison_keeps_peer_values_pending(self):
        result = checker.verify_existing(RAW_ROOT)
        text = checker.comparison_markdown(result)
        self.assertEqual(text.count('| partial_direct32x2 | pending |'), 4)
        self.assertIn('562.55', text)
        self.assertIn('not peak stack', text)

    def test_cli_writes_reports_to_requested_directory_without_modifying_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            done = subprocess.run([sys.executable, str(HERE/'check.py'), '--probe-root',
                                   str(RAW_ROOT), '--output-dir', tmp], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            report = json.loads((Path(tmp)/'verification.json').read_text())
            self.assertEqual(report['verified_output_comparisons'], 6168)
            self.assertTrue((Path(tmp)/'comparison.md').exists())
            self.assertTrue((Path(tmp)/'reference-cases.json').exists())
        self.assertEqual(checker.sha(RAW_ROOT/'results.json'), checker.RESULTS_SHA)


if __name__ == '__main__':
    unittest.main()
