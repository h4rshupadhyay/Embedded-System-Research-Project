"""Safety and evaluation regressions for the held-out FIR experiment."""
import unittest

import selection_validation as v


class SelectionValidation(unittest.TestCase):
    def test_symmetric_extreme_pair_requires_wide_product(self):
        h = [-32768, -32768]
        self.assertFalse(v.is_admitted('fold64', h, 32768))
        self.assertTrue(v.is_admitted('fold64_wide', h, 32768))
        self.assertFalse(v.is_admitted('direct32', h, 32768))
        self.assertEqual(v.select_kernel(h, 32768), 'direct64')
        self.assertEqual(v.select_kernel(h, 1024), 'fold32')

    def test_nonsymmetric_and_odd_library_contracts(self):
        self.assertFalse(v.is_admitted('fold32', [1, 2, 3, 4], 1024))
        self.assertEqual(v.select_kernel([1, 2, 3, 4], 1024), 'direct32')
        self.assertFalse(v.is_admitted('cmsis64', [1, 2, 1], 32768))
        self.assertFalse(v.is_admitted('cmsis32_unroll', [1, 1], 1024))
        self.assertTrue(v.is_admitted('cmsis64_unroll', [1, 2, 3, 4], 32768))
        text = v.case_header([1, 2, 3, 4], [-2, 1, 0], 16)
        self.assertIn('cmsis_coefficients[TAPS]={4,3,2,1}', text)
        self.assertIn('coefficients[TAPS]={1,2,3,4}', text)

    def test_shifted_adc_does_not_reuse_raw_range(self):
        raw, shifted = v.make_inputs()
        self.assertEqual(len(raw), 513)
        self.assertEqual(min(raw), -1024)
        self.assertEqual(max(raw), 1023)
        self.assertEqual(shifted, [32*x for x in raw])
        self.assertEqual(min(shifted), -32768)
        self.assertEqual(max(shifted), 32736)
        self.assertFalse(v.is_admitted('direct32', [32767]*4, 32768))
        self.assertTrue(v.is_admitted('direct32', [32767]*4, 1024))

    def test_reference_has_lag_order_floor_and_saturation(self):
        self.assertEqual(v.reference_outputs([32767], [-1, 32767]), [-1, 32766])
        self.assertEqual(v.reference_outputs([16384, -8192], [2, -2, 0]), [1, -2, 0])
        self.assertEqual(v.reference_outputs([32767, 32767], [32767, 32767]), [32766, 32767])

    def test_regret_uses_strongest_valid_row_and_retains_failure(self):
        rows = [dict(kernel='fold32', arm_zero_ws_cycles=110, estimated_cpu_energy_nj=120),
                dict(kernel='cmsis32_unroll', arm_zero_ws_cycles=100, estimated_cpu_energy_nj=100)]
        result = v.evaluate_selection([100, 100, 100, 100], 1024, rows)
        self.assertEqual(result['chosen'], 'fold32')
        self.assertEqual(result['energy_best'], 'cmsis32_unroll')
        self.assertAlmostEqual(result['energy_regret'], .2)
        self.assertAlmostEqual(result['cycle_regret'], .1)
        with self.assertRaises(ValueError):
            v.evaluate_selection([100]*4, 1024, rows[1:])


if __name__ == '__main__':
    unittest.main()
