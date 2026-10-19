"""Contract tests using an explicitly illustrative, hand-calculated report."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'verify.py'
FIXTURE = HERE / 'fixtures'


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.peer = self.root / 'accounting.json'
        self.output = self.root / 'out'
        shutil.copy(FIXTURE / 'fixture-counts.txt', self.root / 'fixture-counts.txt')
        self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())

    def run_checker(self, present=True):
        if present:
            self.peer.write_text(json.dumps(self.report))
        return subprocess.run([sys.executable, str(SCRIPT), '--peer-report', str(self.peer),
                               '--output-dir', str(self.output)], text=True, capture_output=True)

    def reject(self, fragment):
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(fragment, result.stderr)

    def test_absent_peer_is_pending_with_no_checked_rows(self):
        result = self.run_checker(present=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.output / 'verification.json').read_text())
        self.assertEqual((report['status'], report['peer_rows_checked']), ('pending', 0))
        self.assertIsNone(report['peer_report_sha256'])
        self.assertEqual(report['source_rows']['gcc10'].get('reconstructed_totals', {}).get('instructions'), 198670)
        self.assertEqual(report['manual_causal_review'], 'pending')
        self.assertIn('pending', (self.output / 'comparison.md').read_text().lower())

    def test_literal_fixture_reconciles_two_rows_without_causal_certificate(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.output / 'verification.json').read_text())
        self.assertEqual((report['status'], report['peer_rows_checked']), ('consistent', 2))
        self.assertEqual(report['delta']['instructions'], 43820)
        self.assertEqual(report['delta']['ram_reads'], 13878)
        self.assertEqual(report['delta']['ram_writes'], 19275)
        self.assertEqual(report['delta']['taken_branches'], 131)
        self.assertEqual(report['cost_delta']['estimated_cycles'], 77235)
        self.assertEqual(report['cost_delta']['modeled_cpu_energy_nj'], '70469.699925')
        self.assertEqual(report.get('peer_component_deltas', {}).get('unattributed', {}).get('instructions'), 43820)
        self.assertEqual(report.get('peer_component_deltas', {}).get('stream_wrapper', {}).get('instructions'), 0)
        self.assertEqual(report['manual_causal_review'], 'pending')
        self.assertEqual(len(report['evidence_files_checked']), 1)
        self.assertEqual([r['winner'] for r in report.get('candidate_comparisons', [])],
                         ['partial_direct32x2', 'partial_direct32x2',
                          'trans_hcub_demand', 'trans_hcub_demand'])
        self.assertEqual(report['within_gcc15_block1_hcub_saving_percent'], '24.06')
        self.assertEqual(report['selectable_compiler_hcub_saving_percent'],
                         {'block1': '3.97', 'block64': '2.30'})

    def test_positive_dynamic_component_can_reconcile_but_remains_manual(self):
        trace = self.root / 'illustrative-trace.jsonl'
        trace.write_text('{"pc":"0x08000000","instructions":1}\n')
        self.report['evidence'][trace.name] = hashlib.sha256(trace.read_bytes()).hexdigest()
        row = self.report['rows'][0]
        row['components'][0]['events']['instructions'] = 1
        row['components'][0]['basis'] = 'dynamic-trace'
        row['components'][0]['evidence_refs'] = [trace.name]
        row['components'][-1]['events']['instructions'] -= 1
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.output / 'verification.json').read_text())
        self.assertEqual(report['manual_causal_review'], 'pending')

    def test_changed_total_rejected_even_after_evidence_hash_renewal(self):
        evidence = self.root / 'fixture-counts.txt'
        evidence.write_text('Illustrative revised fixture.\n')
        self.report['evidence']['fixture-counts.txt'] = hashlib.sha256(evidence.read_bytes()).hexdigest()
        self.report['rows'][0]['totals']['instructions'] += 1
        self.reject('total')

    def test_altered_component_rejected_even_after_evidence_hash_renewal(self):
        evidence = self.root / 'fixture-counts.txt'
        evidence.write_text('Illustrative revised component.\n')
        self.report['evidence']['fixture-counts.txt'] = hashlib.sha256(evidence.read_bytes()).hexdigest()
        self.report['rows'][0]['components'][-1]['events']['ram_reads'] -= 1
        self.reject('component sum')

    def test_missing_duplicate_and_extra_compiler_rejected(self):
        for rows in (self.report['rows'][:1], [self.report['rows'][0]] * 2,
                     self.report['rows'] + [dict(self.report['rows'][0], compiler='clang')]):
            with self.subTest(count=len(rows), names=[r['compiler'] for r in rows]):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                self.report['rows'] = rows
                self.reject('compiler')

    def test_wrong_source_binary_and_block_rejected(self):
        for path, value, fragment in (
            (('source_results_sha256',), '0'*64, 'source'),
            (('rows', 0, 'binary_sha256'), '0'*64, 'binary'),
            (('rows', 1, 'block'), 64, 'block'),
        ):
            with self.subTest(path=path):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                target = self.report
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                self.reject(fragment)

    def test_schema_enums_and_types_rejected(self):
        cases = (
            (('schema_version',), 2, 'schema'),
            (('stage',), 'elsewhere', 'stage'),
            (('rows', 0, 'method'), 'guessed', 'method'),
            (('rows', 0, 'causal_status'), 'proven', 'causal_status'),
            (('rows', 0, 'totals', 'mul'), True, 'integer'),
            (('rows', 0, 'static_diagnostics', 'compiler_frame_bytes'), True, 'integer'),
            (('rows', 0, 'components', 0, 'name'), 'unknown', 'component'),
            (('rows', 0, 'components', 0, 'basis'), 'static-only', 'basis'),
        )
        for path, value, fragment in cases:
            with self.subTest(path=path):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                target = self.report
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                self.reject(fragment)

    def test_missing_and_duplicate_components_rejected(self):
        for components in (self.report['rows'][0]['components'][:-1],
                           self.report['rows'][0]['components'] + [self.report['rows'][0]['components'][0]]):
            with self.subTest(count=len(components)):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                self.report['rows'][0]['components'] = components
                self.reject('component')

    def test_negative_counter_rejected(self):
        self.report['rows'][1]['components'][-1]['events']['bl'] = -1
        self.reject('nonnegative')

    def test_missing_malformed_or_wrong_hashed_evidence_rejected(self):
        for mutation in ('missing', 'malformed', 'hash'):
            with self.subTest(mutation=mutation):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                if mutation == 'missing':
                    (self.root / 'fixture-counts.txt').unlink()
                elif mutation == 'malformed':
                    self.report['evidence']['fixture-counts.txt'] = 'bad-hash'
                else:
                    self.report['evidence']['fixture-counts.txt'] = '0'*64
                self.reject('evidence')
                shutil.copy(FIXTURE / 'fixture-counts.txt', self.root / 'fixture-counts.txt')

    def test_absolute_traversal_and_symlink_escape_rejected(self):
        for name in ('/tmp/elsewhere', '../elsewhere', 'escape.txt'):
            with self.subTest(name=name):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                if name == 'escape.txt':
                    (self.root / name).symlink_to(FIXTURE / 'fixture-counts.txt')
                digest = self.report['evidence'].pop('fixture-counts.txt')
                self.report['evidence'][name] = digest
                self.reject('evidence path')

    def test_static_disassembly_alone_cannot_support_dynamic_event(self):
        (self.root / 'listing.disasm').write_text('0000: str r0, [sp]\n')
        self.report['evidence']['listing.disasm'] = hashlib.sha256((self.root / 'listing.disasm').read_bytes()).hexdigest()
        row = self.report['rows'][0]
        row['components'][0]['events']['instructions'] = 1
        row['components'][0]['evidence_refs'] = ['listing.disasm']
        row['components'][-1]['events']['instructions'] -= 1
        self.reject('static-only')

    def test_dynamic_trace_count_requires_hashed_evidence_reference(self):
        row = self.report['rows'][0]
        row['components'][0]['events']['instructions'] = 1
        row['components'][0]['basis'] = 'dynamic-trace'
        row['components'][-1]['events']['instructions'] -= 1
        self.reject('evidence_refs')

    def test_zero_instruction_component_cannot_own_execution_events(self):
        for event in ('ram_writes', 'taken_branches', 'bl'):
            with self.subTest(event=event):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                row = self.report['rows'][0]
                row['components'][0]['events'][event] = 1
                row['components'][0]['evidence_refs'] = ['fixture-counts.txt']
                row['components'][-1]['events'][event] -= 1
                self.reject('zero instructions')

    def test_branch_and_bl_counts_cannot_exceed_component_instructions(self):
        for event in ('taken_branches', 'bl'):
            with self.subTest(event=event):
                self.report = json.loads((FIXTURE / 'literal-accounting.json').read_text())
                row = self.report['rows'][0]
                row['components'][0]['events']['instructions'] = 1
                row['components'][0]['events'][event] = 2
                row['components'][0]['evidence_refs'] = ['fixture-counts.txt']
                row['components'][-1]['events']['instructions'] -= 1
                row['components'][-1]['events'][event] -= 2
                self.reject('exceeds instructions')

    def test_one_instruction_can_have_multiple_ram_transfers(self):
        row = self.report['rows'][0]
        row['components'][0]['events']['instructions'] = 1
        row['components'][0]['events']['ram_writes'] = 2
        row['components'][0]['evidence_refs'] = ['fixture-counts.txt']
        row['components'][-1]['events']['instructions'] -= 1
        row['components'][-1]['events']['ram_writes'] -= 2
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = json.loads((self.output / 'verification.json').read_text())
        self.assertEqual(checked['status'], 'consistent')
        self.assertEqual(checked['manual_causal_review'], 'pending')

    def test_rejected_peer_does_not_overwrite_valid_reports(self):
        self.assertEqual(self.run_checker().returncode, 0)
        old = {name: (self.output / name).read_bytes() for name in ('verification.json', 'comparison.md')}
        self.report['rows'][0]['totals']['instructions'] += 1
        self.assertNotEqual(self.run_checker().returncode, 0)
        self.assertEqual(old, {name: (self.output / name).read_bytes() for name in old})


if __name__ == '__main__':
    unittest.main()
