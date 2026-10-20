import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal, localcontext

from analyze import affine_boundary, analyze_report


class AffineBoundaryTests(unittest.TestCase):
    def test_exact_rational_root_is_classified_inside_selected_region(self):
        result = affine_boundary(Decimal('-2'), Decimal('2'))
        self.assertEqual(result['root_exact'], {'numerator': 1, 'denominator': 1})
        self.assertEqual(result['root_decimal'], '1.000000')
        self.assertEqual(result['root_region'], 'within')

    def test_affine_constant_and_all_tie_paths_have_no_unique_root(self):
        all_ties = affine_boundary(Decimal('0'), Decimal('0'))
        constant = affine_boundary(Decimal('3'), Decimal('0'))
        self.assertEqual((all_ties['kind'], all_ties['root_exact'], all_ties['sign']), ('all_ties', None, 'zero'))
        self.assertEqual((constant['kind'], constant['root_exact'], constant['sign']), ('constant', None, 'positive'))

    def test_negative_and_region_endpoint_roots_use_exact_membership(self):
        negative = affine_boundary(Decimal('1'), Decimal('1'))
        low = affine_boundary(Decimal('-1'), Decimal('2'))
        high = affine_boundary(Decimal('4'), Decimal('-2'))
        self.assertEqual(negative['root_exact'], {'numerator': -1, 'denominator': 1})
        self.assertEqual(negative['root_domain'], 'outside')
        self.assertEqual(low['root_exact'], {'numerator': 1, 'denominator': 2})
        self.assertEqual(low['root_region'], 'within')
        self.assertEqual(high['root_exact'], {'numerator': 2, 'denominator': 1})
        self.assertEqual(high['root_region'], 'within')
        zero = affine_boundary(Decimal('0'), Decimal('7'))
        above = affine_boundary(Decimal('-10'), Decimal('1'))
        self.assertEqual((zero['root_exact'], zero['root_domain']), ({'numerator': 0, 'denominator': 1}, 'boundary'))
        self.assertEqual(above['root_region'], 'above')

    def test_exact_root_just_below_half_is_not_promoted_by_decimal_display(self):
        coefficient = Decimal('2.' + '0' * 50 + '1')
        result = affine_boundary(Decimal('-1'), coefficient)
        self.assertEqual(result['root_region'], 'below')
        self.assertEqual(result['root_decimal'], '0.500000')
        self.assertEqual(result['winner_at']['0.5'], 'right')

    def test_large_finite_root_can_be_displayed(self):
        result = affine_boundary(Decimal('-1e50'), Decimal('1'))
        self.assertEqual(result['root_exact'], {'numerator': 10**50, 'denominator': 1})
        self.assertEqual(result['root_decimal'], '100000000000000000000000000000000000000000000000000.000000')

    def test_root_with_more_than_python_integer_string_limit_can_be_displayed(self):
        result = affine_boundary(Decimal('-1e5000'), Decimal('1'))
        display = result['root_decimal']
        self.assertEqual(result['root_region'], 'above')
        self.assertEqual(display, '1' + '0' * 5000 + '.000000')

    def test_nonfinite_affine_coefficients_are_rejected(self):
        for value in (Decimal('NaN'), Decimal('Infinity'), Decimal('-Infinity')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                affine_boundary(value, Decimal('1'))


if __name__ == '__main__':
    unittest.main()


class ReportAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result_path = Path(__file__).resolve().parents[1] / "fir-paper" / "results.json"
        cls.report = json.loads(result_path.read_text(encoding="utf-8"))

    def test_incremental_sharing_and_affine_stress_match_literal_anchors(self):
        result = analyze_report(self.report)
        hcub_ordinary = [Decimal(pair["left_relative_percent"]) for pair in result["pairs"]
                        if pair["left_variant"] == "trans_hcub_demand" and pair["right_variant"] == "trans_const"]
        self.assertEqual([x.quantize(Decimal("0.000001")) for x in hcub_ordinary],
                         [Decimal("3.410536"), Decimal("-0.172202"), Decimal("-4.284890"), Decimal("-6.686823")])
        hcub_partial = [pair for pair in result["pairs"]
                        if pair["left_variant"] == "trans_hcub_demand" and pair["right_variant"] == "partial_direct32x2"]
        self.assertEqual([(p["affine"]["A_nj"], p["affine"]["B_nj"], p["affine"]["boundary"]["root_decimal"])
                          for p in hcub_partial],
                         [("-32436.319000", "43973.275423", "0.737637"),
                          ("-16661.004146", "24064.520307", "0.692347"),
                          ("-94335.682384", "13297.172804", "7.094417"),
                          ("-16351.634074", "8374.315001", "1.952594")])

    def test_twelve_pairs_have_frozen_orientation_and_strict_endpoint_outcomes(self):
        result = analyze_report(self.report)
        self.assertEqual(len(result['pairs']), 12)
        for pair in result['pairs']:
            affine = pair['affine']
            self.assertEqual(Decimal(affine['A_nj']) + Decimal(affine['B_nj']), Decimal(pair['delta_energy_nj']))
        self.assertEqual(len({(p['compiler'], p['block'], p['left_variant'], p['right_variant']) for p in result['pairs']}), 12)
        partial = [p for p in result['pairs'] if p['left_variant'] == 'trans_hcub_demand' and p['right_variant'] == 'partial_direct32x2']
        self.assertEqual([(p['affine']['stress']['at_0_5'], p['affine']['stress']['at_1'], p['affine']['stress']['at_2']) for p in partial],
                         [('left', 'right', 'right'), ('left', 'right', 'right'), ('left', 'left', 'left'), ('left', 'left', 'right')])
        self.assertEqual([p['delta_events']['mul'] for p in partial], [-2570, -2570, -2570, -2570])
        self.assertEqual(set(partial[0]['delta_events']), {'nonmul', 'mul', 'taken_branches', 'ram_reads', 'ram_writes', 'flash_reads', 'instructions', 'bl', 'flash_writes'})
        self.assertEqual(partial[0]['delta_events'], {'nonmul': -5141, 'mul': -2570, 'taken_branches': -10794,
                         'ram_reads': 21845, 'ram_writes': 30326, 'flash_reads': -1028,
                         'instructions': -7711, 'bl': 0, 'flash_writes': 0})

    def test_analysis_is_independent_of_callers_low_decimal_precision(self):
        expected = analyze_report(self.report)
        with localcontext() as ctx:
            ctx.prec = 6
            actual = analyze_report(self.report)
            self.assertEqual(ctx.prec, 6)
        self.assertEqual(actual, expected)

    def test_exact_stress_endpoint_ties_defeat_strict_throughout_flags(self):
        weights = {'nonmul': Decimal('0.964258'), 'mul': Decimal('1.652455'),
                   'taken_branches': Decimal('2.091986'), 'ram_reads': Decimal('1.109833'),
                   'ram_writes': Decimal('0.650563'), 'flash_reads': Decimal('0.633621')}
        right_events = {'instructions': 100, 'mul': 50, 'taken_branches': 100,
                        'ram_reads': 100, 'ram_writes': 100, 'flash_reads': 100,
                        'flash_writes': 0, 'bl': 10}
        fixtures = (
            ((1, -7, 17, -13, -19, -19), '16.723762', '-33.447524', 'at_0_5', 'strict_lower_throughout_region'),
            ((11, 0, 16, -14, -10, -10), '35.207920', '-17.603960', 'at_2', 'strict_higher_throughout_region'),
        )
        for delta, expected_a, expected_b, tie_key, strict_key in fixtures:
            with self.subTest(tie_key=tie_key):
                changed = json.loads(json.dumps(self.report))
                rows = {(r['compiler'], r['block'], r['variant']): r for r in changed['rows']}
                left = rows[('gcc10', 1, 'trans_hcub_demand')]
                right = rows[('gcc10', 1, 'trans_const')]
                for row in (left, right):
                    row.update(right_events)
                d_nonmul, d_mul, d_branch, d_flash, d_read, d_write = delta
                left.update({'instructions': right_events['instructions'] + d_nonmul + d_mul,
                             'mul': right_events['mul'] + d_mul,
                             'taken_branches': right_events['taken_branches'] + d_branch,
                             'ram_reads': right_events['ram_reads'] + d_read,
                             'ram_writes': right_events['ram_writes'] + d_write,
                             'flash_reads': right_events['flash_reads'] + d_flash})
                for row in (left, right):
                    row['estimated_cpu_energy_nj'] = str(sum((weights['nonmul'] * (row['instructions'] - row['mul']),
                        weights['mul'] * row['mul'], weights['taken_branches'] * row['taken_branches'],
                        weights['ram_reads'] * row['ram_reads'], weights['ram_writes'] * row['ram_writes'],
                        weights['flash_reads'] * row['flash_reads']), Decimal(0)))
                    row['arm_zero_ws_cycles'] = (row['instructions'] + row['ram_reads'] + row['ram_writes'] +
                                                 row['flash_reads'] + 2 * row['taken_branches'] + row['bl'])
                pair = next(p for p in analyze_report(changed)['pairs'] if p['compiler'] == 'gcc10' and p['block'] == 1 and p['left_variant'] == 'trans_hcub_demand' and p['right_variant'] == 'trans_const')
                self.assertEqual((pair['affine']['A_nj'], pair['affine']['B_nj']), (expected_a, expected_b))
                stress = pair['affine']['stress']
                self.assertEqual(stress[tie_key], 'tie')
                self.assertFalse(stress[strict_key])

    def test_swapping_oriented_rows_reverses_event_and_energy_signs(self):
        result = analyze_report(self.report)
        hcub_partial = next(p for p in result['pairs'] if p['compiler'] == 'gcc10' and p['block'] == 1 and p['left_variant'] == 'trans_hcub_demand' and p['right_variant'] == 'partial_direct32x2')
        self.assertEqual(hcub_partial['delta_events']['ram_reads'], 21845)
        self.assertEqual(hcub_partial['delta_energy_nj'], '11536.956423')
        changed = json.loads(json.dumps(self.report))
        rows = {(r['compiler'], r['block'], r['variant']): r for r in changed['rows']}
        left = rows[('gcc10', 1, 'trans_hcub_demand')]
        right = rows[('gcc10', 1, 'partial_direct32x2')]
        swapped_fields = ('instructions', 'mul', 'taken_branches', 'ram_reads', 'ram_writes', 'flash_reads',
                          'flash_writes', 'bl', 'arm_zero_ws_cycles', 'estimated_cpu_energy_nj',
                          'state_allocation_bytes', 'probe_process_stack_bytes', 'kernel_and_coefficient_symbol_bytes')
        for field in swapped_fields:
            left[field], right[field] = right[field], left[field]
        reversed_pair = next(p for p in analyze_report(changed)['pairs'] if p['compiler'] == 'gcc10' and p['block'] == 1 and p['left_variant'] == 'trans_hcub_demand' and p['right_variant'] == 'partial_direct32x2')
        self.assertEqual(reversed_pair['delta_events']['ram_reads'], -21845)
        self.assertEqual(reversed_pair['delta_energy_nj'], '-11536.956423')

    def test_left_right_and_mixed_event_dominance_are_reported(self):
        result = analyze_report(self.report)
        self.assertTrue(any(p['event_dominance'] == 'left_dominates' for p in result['pairs']))
        self.assertTrue(any(p['event_dominance'] == 'mixed' for p in result['pairs']))
        changed = json.loads(json.dumps(self.report))
        rows = {(r['compiler'], r['block'], r['variant']): r for r in changed['rows']}
        left = rows[('gcc10', 1, 'partial_direct32x2')]
        right = rows[('gcc10', 1, 'spec_direct')]
        for event in ('instructions', 'mul', 'taken_branches', 'ram_reads', 'ram_writes', 'flash_reads', 'flash_writes', 'bl'):
            left[event] = right[event]
        left['instructions'] += 10
        left['mul'] += 1
        left['taken_branches'] += 1
        left['ram_reads'] += 1
        left['ram_writes'] += 1
        left['flash_reads'] += 1
        left['arm_zero_ws_cycles'] = left['instructions'] + left['ram_reads'] + left['ram_writes'] + left['flash_reads'] + 2 * left['taken_branches'] + left['bl']
        left['estimated_cpu_energy_nj'] = str(Decimal('0.964258') * (left['instructions'] - left['mul']) + Decimal('1.652455') * left['mul'] + Decimal('2.091986') * left['taken_branches'] + Decimal('1.109833') * left['ram_reads'] + Decimal('0.650563') * left['ram_writes'] + Decimal('0.633621') * left['flash_reads'])
        pair = next(p for p in analyze_report(changed)['pairs'] if p['compiler'] == 'gcc10' and p['block'] == 1 and p['left_variant'] == 'partial_direct32x2' and p['right_variant'] == 'spec_direct')
        self.assertEqual(pair['event_dominance'], 'right_dominates')

    def test_event_or_energy_mutation_that_breaks_reconstruction_is_rejected(self):
        changed = json.loads(json.dumps(self.report))
        changed['rows'][0]['ram_reads'] += 1
        with self.assertRaisesRegex(ValueError, 'energy does not reconstruct'):
            analyze_report(changed)

    def test_malformed_serialized_energy_is_a_clean_admission_error(self):
        changed = json.loads(json.dumps(self.report))
        changed['rows'][0]['estimated_cpu_energy_nj'] = 'not-a-decimal'
        with self.assertRaises(ValueError):
            analyze_report(changed)

    def test_equal_event_fixture_reports_event_equal_and_an_affine_tie(self):
        changed = json.loads(json.dumps(self.report))
        rows = {(r['compiler'], r['block'], r['variant']): r for r in changed['rows']}
        left = rows[('gcc10', 1, 'trans_hcub_demand')]
        right = rows[('gcc10', 1, 'trans_const')]
        for name in ('instructions', 'mul', 'taken_branches', 'ram_reads', 'ram_writes', 'flash_reads', 'flash_writes', 'bl', 'arm_zero_ws_cycles', 'estimated_cpu_energy_nj'):
            left[name] = right[name]
        pair = next(p for p in analyze_report(changed)['pairs'] if p['compiler'] == 'gcc10' and p['block'] == 1 and p['left_variant'] == 'trans_hcub_demand' and p['right_variant'] == 'trans_const')
        self.assertEqual(pair['event_dominance'], 'event_equal')
        self.assertEqual(pair['affine']['boundary']['kind'], 'all_ties')
        self.assertEqual(pair['affine']['stress']['at_0_5'], 'tie')

    def test_analysis_serialization_is_deterministic(self):
        first = json.dumps(analyze_report(self.report), separators=(',', ':'))
        second = json.dumps(analyze_report(self.report), separators=(',', ':'))
        self.assertEqual(first, second)

    def test_cli_rejects_changed_frozen_source_without_replacing_prior_outputs(self):
        repo = Path(__file__).resolve().parents[2]
        source_root = repo / 'research'
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'repo'
            for rel in ('fir-baseline/selection-design.json', 'fir-sharing-probe/results.json',
                        'fir-sharing-probe/partial-direct/results.json',
                        'fir-sharing-probe/independent-check/verification.json',
                        'fir-sharing-probe/compiler-explanation/accounting.json',
                        'fir-sharing-probe/explanation-check/verification.json'):
                target = fake / 'research' / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_root / rel, target)
            paper = fake / 'research' / 'fir-paper'
            paper.mkdir(parents=True)
            shutil.copyfile(repo / 'research/fir-paper/results.json', paper / 'results.json')
            code = fake / 'research/fir-paper/build_results.py'
            shutil.copyfile(repo / 'research/fir-paper/build_results.py', code)
            output = fake / 'research/fir-upgrades/analysis'
            output.mkdir(parents=True)
            (output / 'analysis.json').write_bytes(b'old-json')
            (output / 'analysis.md').write_bytes(b'old-md')
            (fake / 'research/fir-sharing-probe/results.json').write_bytes(b'{ altered }')
            command = [sys.executable, str(repo / 'research/fir-upgrades/analyze.py'), '--repo-root', str(fake), '--output-dir', str(output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('frozen input identity mismatch', run.stderr)
            self.assertEqual((output / 'analysis.json').read_bytes(), b'old-json')
            self.assertEqual((output / 'analysis.md').read_bytes(), b'old-md')

    def test_cli_refuses_original_paper_output_directory(self):
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'repo'
            paper = fake / 'research/fir-paper'
            paper.mkdir(parents=True)
            original = paper / 'results.json'
            original.write_bytes(b'preserve me')
            command = [sys.executable, str(repo / 'research/fir-upgrades/analyze.py'), '--repo-root', str(fake), '--output-dir', str(paper)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('refusing to write', run.stderr)
            self.assertEqual(original.read_bytes(), b'preserve me')
