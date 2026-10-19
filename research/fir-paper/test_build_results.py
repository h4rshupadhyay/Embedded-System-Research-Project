import unittest
import json
import copy
import subprocess
import sys
import tempfile
from pathlib import Path
from decimal import Decimal

import build_results
from build_results import assess_hypothesis


class HypothesisTests(unittest.TestCase):
    def test_all_negative_margins_retain_hypothesis(self):
        self.assertEqual(assess_hypothesis([Decimal('-1'), Decimal('-0.1'), Decimal('-2'), Decimal('-3')]), {'status': 'retained', 'passes': [True, True, True, True]})

    def test_positive_margin_rejects_hypothesis(self):
        self.assertEqual(assess_hypothesis([Decimal('-1'), Decimal('0.1'), Decimal('-2'), Decimal('-3')]), {'status': 'rejected', 'passes': [True, False, True, True]})

    def test_wrong_count_non_decimal_and_nonfinite_margins_raise(self):
        for values in ([Decimal('-1')], [Decimal('-1'), Decimal('-2'), Decimal('-3'), 0], [Decimal('-1'), Decimal('-2'), Decimal('-3'), Decimal('NaN')]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                assess_hypothesis(values)

    def test_hypothesis_requires_strictly_negative_margin_in_every_cell(self):
        self.assertEqual(
            assess_hypothesis([Decimal('-1'), Decimal('0'), Decimal('-2'), Decimal('-3')]),
            {'status': 'rejected', 'passes': [True, False, True, True]},
        )


class SemanticValidationTests(unittest.TestCase):
    def test_duplicate_requested_source_row_is_rejected(self):
        root = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        documents = {k: json.loads((root / p).read_text()) for k, p in rels.items()}
        chosen = next(r for r in documents['sharing']['rows'] if r.get('filter') == 'speech_minphase48' and r.get('maximum') == 32768 and r.get('variant') == 'cmsis64_unroll')
        documents['sharing']['rows'].append(dict(chosen))
        with self.assertRaisesRegex(ValueError, 'duplicate source row'):
            build_results._validate_documents(documents)


class SelectionValidationTests(unittest.TestCase):
    def test_accounting_and_explanation_cannot_agree_away_from_selected_raw_events(self):
        project = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        docs = {k: json.loads((project / p).read_text()) for k, p in rels.items()}
        docs['accounting']['rows'][0]['totals']['instructions'] += 1
        docs['explanation']['peer_rows']['gcc10']['totals']['instructions'] += 1
        with self.assertRaisesRegex(ValueError, 'accounting totals conflict with selected partial row'):
            build_results.build_report(docs)

    def test_accounting_requires_exactly_gcc10_and_gcc15_block1_rows(self):
        project = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        docs = {k: json.loads((project / p).read_text()) for k, p in rels.items()}
        docs['accounting']['rows'][1] = copy.deepcopy(docs['accounting']['rows'][0])
        with self.assertRaisesRegex(ValueError, 'accounting rows must be exactly GCC10 and GCC15 block1'):
            build_results.build_report(docs)

    def test_explanation_delta_and_cost_are_reconstructed_from_block1_rows(self):
        project = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        docs = {k: json.loads((project / p).read_text()) for k, p in rels.items()}
        docs['explanation']['delta']['instructions'] += 1
        with self.assertRaisesRegex(ValueError, 'explanation delta conflicts with block1 raw rows'):
            build_results.build_report(docs)

    def test_event_reconstructed_cycles_are_checked_across_raw_and_verified_rows(self):
        project = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        docs = {k: json.loads((project / p).read_text()) for k, p in rels.items()}
        row = next(r for r in docs['sharing']['rows'] if r.get('filter') == 'speech_minphase48' and r.get('maximum') == 32768 and r.get('variant') == 'cmsis64_unroll')
        row['arm_zero_ws_cycles'] += 1
        diag = next(r for r in docs['verified']['rows'] if r.get('compiler') == row['compiler'] and r.get('block') == row['block'] and r.get('variant') == row['variant'])
        diag['arm_zero_ws_cycles'] += 1
        with self.assertRaisesRegex(ValueError, 'cycles conflict with reconstructed event counts'):
            build_results.build_report(docs)

    def test_selection_and_cross_source_contract_rejects_invalid_rows(self):
        project = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        for defect in ('missing', 'samples', 'filter', 'range', 'cross_source'):
            with self.subTest(defect=defect):
                docs = {k: json.loads((project / p).read_text()) for k, p in rels.items()}
                row = next(r for r in docs['sharing']['rows'] if r.get('filter') == 'speech_minphase48' and r.get('maximum') == 32768 and r.get('variant') == 'cmsis64_unroll')
                if defect == 'missing':
                    docs['sharing']['rows'].remove(row)
                elif defect == 'samples':
                    row['samples'] = 256
                elif defect == 'filter':
                    row['filter'] = 'speech_lp48'
                elif defect == 'range':
                    row['maximum'] = 1024
                else:
                    diag = next(r for r in docs['verified']['rows'] if r.get('compiler') == row['compiler'] and r.get('block') == row['block'] and r.get('variant') == row['variant'])
                    diag['estimated_cpu_energy_nj'] = '1'
                with self.assertRaises(ValueError):
                    build_results.build_report(docs)

    def test_changed_source_energy_is_rejected_by_pure_semantic_validation(self):
        root = Path(__file__).resolve().parents[2]
        rels = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        documents = {k: json.loads((root / p).read_text()) for k, p in rels.items()}
        row = next(r for r in documents['sharing']['rows'] if r.get('filter') == 'speech_minphase48' and r.get('maximum') == 32768 and r.get('variant') == 'cmsis64_unroll')
        row['estimated_cpu_energy_nj'] = '1'
        with self.assertRaisesRegex(ValueError, 'energy conflicts'):
            build_results.build_report(documents)


class CliIdentityTests(unittest.TestCase):
    def test_changed_frozen_source_rejects_without_replacing_output_sentinel(self):
        project = Path(__file__).resolve().parents[2]
        files = [
            'research/fir-baseline/selection-design.json',
            'research/fir-sharing-probe/results.json',
            'research/fir-sharing-probe/partial-direct/results.json',
            'research/fir-sharing-probe/independent-check/verification.json',
            'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'research/fir-sharing-probe/explanation-check/verification.json',
        ]
        for edit in ('identity', 'numeric'):
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'repo'
                for rel in files:
                    dest = root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes((project / rel).read_bytes())
                sharing_path = root / 'research/fir-sharing-probe/results.json'
                data = json.loads(sharing_path.read_text())
                if edit == 'identity':
                    data['status'] = 'changed identity field'
                else:
                    row = next(r for r in data['rows'] if r.get('filter') == 'speech_minphase48' and r.get('maximum') == 32768 and r.get('variant') == 'cmsis64_unroll')
                    row['estimated_cpu_energy_nj'] = '1'
                sharing_path.write_text(json.dumps(data))
                out = Path(tmp) / 'output'
                out.mkdir()
                sentinel = out / 'results.json'
                sentinel.write_bytes(b'KEEP-ME\n')
                result = subprocess.run([sys.executable, str(project / 'research/fir-paper/build_results.py'), '--output-dir', str(out), '--repo-root', str(root)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('frozen input identity mismatch', result.stderr)
                self.assertEqual(sentinel.read_bytes(), b'KEEP-ME\n')


class ReportTests(unittest.TestCase):
    def test_build_report_selects_twenty_rows_and_rejects_hypothesis(self):
        root = Path(__file__).resolve().parents[2]
        relative = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        documents = {key: json.loads((root / path).read_text()) for key, path in relative.items()}
        self.assertTrue(hasattr(build_results, 'build_report'))
        report = build_results.build_report(documents)
        self.assertEqual(len(report['rows']), 20)
        regular = report['rows'][0]
        partial = next(r for r in report['rows'] if r['variant'] == 'partial_direct32x2')
        self.assertEqual(regular.get('diagnostic_source_path'), 'research/fir-sharing-probe/independent-check/verification.json')
        self.assertEqual(regular.get('diagnostic_source_array'), 'rows')
        self.assertEqual(partial.get('diagnostic_source_array'), 'peer_rows')
        self.assertEqual(report['hypothesis']['status'], 'rejected')
        self.assertEqual(report['hypothesis']['passes'], [False, False, True, True])
        self.assertEqual(set(report['comparisons'][0]), {'compiler', 'block', 'hcub_vs_cmsis64_unroll_energy_percent', 'hcub_vs_spec_direct_energy_percent', 'hcub_vs_partial_direct32x2_energy_percent'})
        self.assertEqual(len(report['derived_comparisons']['ordinary_transposed_vs_partial_and_hcub_vs_ordinary']), 4)
        self.assertLess(abs(Decimal(report['comparisons'][0]['hcub_vs_cmsis64_unroll_energy_percent']) - Decimal('-29.6491')), Decimal('0.0001'))
        expected_margins = [Decimal('4.330785'), Decimal('5.002907'), Decimal('-24.056759'), Decimal('-5.229188')]
        for actual, expected in zip(report['comparisons'], expected_margins):
            self.assertLess(abs(Decimal(actual['hcub_vs_partial_direct32x2_energy_percent']) - expected), Decimal('0.000001'))
        self.assertEqual(report['explanation']['residual_energy_nj'], '10559.790252')
        self.assertLess(abs(Decimal(report['explanation']['attributed_fraction_percent']) - Decimal('85.0151')), Decimal('0.0001'))
        self.assertLess(abs(Decimal(report['selectable_compiler'][0]['selectable_saving_percent']) - Decimal('3.96735885')), Decimal('0.00000001'))
        table = build_results._tables(report)
        self.assertIn('| Compiler | Block | Variant | Cycles/output | Energy (nJ) |', table)
        self.assertIn('| gcc10 | 1 | cmsis64_unroll | 1585.11 | 395063.83 |', table)

    def test_incremental_hcub_margins_use_each_cells_frozen_event_energy(self):
        root = Path(__file__).resolve().parents[2]
        relative = {
            'design': 'research/fir-baseline/selection-design.json',
            'sharing': 'research/fir-sharing-probe/results.json',
            'partial': 'research/fir-sharing-probe/partial-direct/results.json',
            'verified': 'research/fir-sharing-probe/independent-check/verification.json',
            'accounting': 'research/fir-sharing-probe/compiler-explanation/accounting.json',
            'explanation': 'research/fir-sharing-probe/explanation-check/verification.json',
        }
        documents = {key: json.loads((root / path).read_text()) for key, path in relative.items()}
        report = build_results.build_report(documents)
        # Independent canonical energies reconstructed from the frozen event rows.
        expected = [
            (Decimal('277931.050273'), Decimal('268764.731503')),
            (Decimal('155387.796582'), Decimal('155655.839196')),
            (Decimal('255825.284195'), Decimal('267277.845667')),
            (Decimal('144576.380656'), Decimal('154936.724484')),
        ]
        actual = report['derived_comparisons']['ordinary_transposed_vs_partial_and_hcub_vs_ordinary']
        for row, (hcub, ordinary) in zip(actual, expected):
            independent_margin = (hcub / ordinary - 1) * 100
            self.assertEqual(Decimal(row['hcub_vs_trans_const_energy_percent']), independent_margin)


class DeterminismTests(unittest.TestCase):
    def test_valid_generation_is_byte_identical_across_runs(self):
        project = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [Path(tmp) / 'one', Path(tmp) / 'two']
            for output in outputs:
                subprocess.run([sys.executable, str(project / 'research/fir-paper/build_results.py'), '--output-dir', str(output), '--repo-root', str(project)], check=True, capture_output=True, text=True)
            for name in ('results.json', 'tables.md', 'source-manifest.json'):
                self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
