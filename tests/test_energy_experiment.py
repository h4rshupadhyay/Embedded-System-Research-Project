import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HypothesisExperimentTests(unittest.TestCase):
    def test_zero_energy_conditions_are_rejected_without_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = json.loads((ROOT / "configs/energy_model.json").read_text())
            config.update(event_weights_nj=dict.fromkeys(config["event_weights_nj"], 0),
                          sleep_power_w=0, wake_power_w=0,
                          resistance_ohm_values=[0], period_multipliers=[2],
                          tau_candidates_s=[0.00001])
            config["supply"]["iq_a"] = 0
            config["calibration_pulses"] = [config["calibration_pulses"][0]]
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config))
            output = Path(tmp) / "experiment"
            result = subprocess.run([
                "python3", str(ROOT / "run_energy_hypothesis.py"), "--config", str(path),
                "--output-dir", str(output)], cwd=ROOT, text=True, capture_output=True, timeout=60)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No valid evaluation conditions", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_lossless_run_reports_no_physical_validation_or_invented_gain(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "clock_hz": 48000000, "sleep_power_w": 0.00005,
                "wake_power_w": 0.005, "wake_duration_s": 0.00002,
                "event_weights_nj": dict.fromkeys([f"C{i}" for i in range(1, 7)], 1.0),
                "supply": {"resistance_ohm": 0}, "resistance_ohm_values": [0],
                "period_multipliers": [2], "tau_candidates_s": [0.00001],
                "calibration_pulses": [
                    {"period_s": 0.0002, "duty": 0.5, "active_power_w": 0.02}],
                "minimum_relative_improvement": 0.01,
            }
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps(config))
            output = Path(tmp) / "experiment"
            result = subprocess.run([
                "python3", str(ROOT / "run_energy_hypothesis.py"), "--profile",
                str(ROOT / "results/sim_pilot.json"), "--config", str(path),
                "--output-dir", str(output)], cwd=ROOT, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(report["physical_hypothesis_status"], "not_tested")
            self.assertFalse(report["parameters_calibrated_to_hardware"])
            self.assertEqual(report["reference_kind"], "synthetic_averaged_buck")
            self.assertEqual(report["evaluated_conditions"], 1)
            self.assertEqual(report["conditions"][0]["baseline_choice"],
                             report["conditions"][0]["history_choice"])
            self.assertAlmostEqual(report["mean_relative_improvement"], 0, delta=1e-12)
            self.assertTrue((output / "predictions.csv").exists())
            self.assertTrue((output / "SUMMARY.md").exists())

    def test_selection_metric_uses_independent_reference_energies(self):
        from run_energy_hypothesis import score_choices
        result = score_choices({"A": 10, "B": 11}, {"A": 12, "B": 11},
                               {"A": 13, "B": 10})
        self.assertEqual(result["baseline_choice"], "A")
        self.assertEqual(result["history_choice"], "B")
        self.assertEqual(result["baseline_regret_j"], 3)
        self.assertEqual(result["history_regret_j"], 0)
        self.assertEqual(result["improvement_j"], 3)

    def test_existing_output_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            sentinel = Path(tmp) / "keep.txt"
            sentinel.write_text("existing evidence")
            result = subprocess.run([
                "python3", str(ROOT / "run_energy_hypothesis.py"), "--output-dir", tmp],
                cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(sentinel.read_text(), "existing evidence")


if __name__ == "__main__":
    unittest.main()
