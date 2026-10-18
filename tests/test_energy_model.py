"""Physical invariants and analytical controls for the supply models."""

import unittest


class EnergyModelTests(unittest.TestCase):
    def test_constant_load_matches_steady_energy(self):
        from energy_model import Buck, Segment, circuit_energy, steady_energy
        supply = Buck()
        trace = [Segment(0.001, 0.02)]
        result = circuit_energy(trace, supply)
        self.assertAlmostEqual(result.source_j, steady_energy(trace, supply), delta=1e-12)
        self.assertAlmostEqual(result.min_voltage_v, supply.vout_v, delta=1e-8)
        self.assertAlmostEqual(result.max_voltage_v, supply.vout_v, delta=1e-8)

    def test_nominal_operating_point_must_be_available(self):
        from energy_model import Buck, Segment, circuit_energy
        # Required duty exceeds 1: 3.3 + 100*(0.06/3.3) > 5 V.
        # Static undervoltage must not be mistaken for a history effect.
        with self.assertRaisesRegex(ValueError, "nominal operating point"):
            circuit_energy([Segment(0.01, 0.06)], Buck(resistance_ohm=100))

    def test_lossless_dynamic_source_energy_equals_load_plus_quiescent(self):
        from energy_model import Buck, Segment, circuit_energy
        supply = Buck(resistance_ohm=0)
        trace = [Segment(0.0002, 0.05), Segment(0.0003, 0.00005)]
        result = circuit_energy(trace, supply)
        expected = 0.0002 * 0.05 + 0.0003 * 0.00005 + supply.vin_v * supply.iq_a * 0.0005
        self.assertAlmostEqual(result.source_j, expected, delta=2e-11)
        self.assertAlmostEqual(result.conduction_j, 0, delta=1e-15)
        self.assertLess(abs(result.balance_error_j), 2e-11)

    def test_energy_conservation_with_resistance_and_storage(self):
        from energy_model import Buck, Segment, circuit_energy
        result = circuit_energy([Segment(0.00015, 0.05), Segment(0.00025, 0.001)],
                                Buck(resistance_ohm=2))
        self.assertGreater(result.conduction_j, 0)
        self.assertLess(abs(result.balance_error_j), 2e-11)
        self.assertAlmostEqual(result.raw_source_j - result.storage_delta_j,
                               result.source_j, delta=1e-15)

    def test_reference_energy_converges_with_tighter_solver_tolerance(self):
        from energy_model import Buck, Segment, circuit_energy
        trace = [Segment(0.00015, 0.05), Segment(0.00025, 0.001)]
        normal = circuit_energy(trace, Buck(resistance_ohm=2), rtol=1e-8)
        tighter = circuit_energy(trace, Buck(resistance_ohm=2), rtol=1e-10)
        self.assertAlmostEqual(normal.source_j, tighter.source_j, delta=1e-11)

    def test_equal_demand_energy_can_have_different_dynamic_loss(self):
        from energy_model import Buck, Segment, circuit_energy, steady_energy
        slow = [Segment(0.001, 0.05), Segment(0.001, 0.00005)]
        fast = [Segment(0.0001, 0.05), Segment(0.0001, 0.00005)] * 10
        supply = Buck(resistance_ohm=2)
        self.assertAlmostEqual(steady_energy(slow, supply), steady_energy(fast, supply), delta=1e-15)
        a, b = circuit_energy(slow, supply), circuit_energy(fast, supply)
        self.assertGreater(abs(a.source_j - b.source_j), 1e-10)

    def test_history_feature_has_exact_step_integral(self):
        from energy_model import Segment, history_feature
        # For a periodic 50%-duty unit-current square wave with exp(-T/tau)=1/2,
        # the high and low half-cycle starting errors are +/-2/3 A.
        # Each integral is (4/9)*(tau/2)*(1-1/4); total = tau/3.
        import math
        duration = math.log(2)
        self.assertAlmostEqual(history_feature([Segment(duration, 1), Segment(duration, 0)],
                                               tau_s=1, voltage_v=1), 1/3, places=12)

    def test_constant_demand_has_no_history_feature(self):
        from energy_model import Segment, history_feature
        self.assertEqual(history_feature([Segment(0.001, 0.03)], 0.00001, 3.3), 0)

    def test_history_fit_does_not_invent_loss_in_lossless_control(self):
        from energy_model import Buck, Segment, fit_history, history_energy, steady_energy
        supply = Buck(resistance_ohm=0)
        training = [[Segment(0.0001, 0.02), Segment(0.0002, 0.00005)],
                    [Segment(0.0003, 0.04), Segment(0.0002, 0.00005)]]
        fit = fit_history(training, supply, [0.00001, 0.0001])
        unseen = [Segment(0.00007, 0.03), Segment(0.00025, 0.00005)]
        self.assertAlmostEqual(history_energy(unseen, supply, fit),
                               steady_energy(unseen, supply), delta=2e-11)

    def test_invalid_segments_and_supply_are_rejected(self):
        from energy_model import Buck, Segment, circuit_energy
        for trace in ([], [Segment(-1, 0.02)], [Segment(1e-3, -0.02)]):
            with self.subTest(trace=trace), self.assertRaises(ValueError):
                circuit_energy(trace, Buck())
        with self.assertRaises(ValueError):
            circuit_energy([Segment(0.001, 0.02)], Buck(vin_v=2, vout_v=3.3))


if __name__ == "__main__":
    unittest.main()
