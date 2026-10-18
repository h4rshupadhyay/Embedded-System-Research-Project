import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS_AVAILABLE = all(shutil.which(name) for name in (
    "arm-none-eabi-gcc", "arm-none-eabi-objcopy")) and (ROOT / "thumbulator").is_file()


class BoundedStudyTests(unittest.TestCase):
    def test_replay_is_excluded_and_missing_conditions_block_conclusions(self):
        from run_bounded_energy_study import summarize
        rows = [
            {"role": "evaluation", "relative_improvement": 0.02,
             "baseline_choice": "A", "history_choice": "B", "reference_best": ["B"],
             "baseline_regret_j": 2e-7, "history_regret_j": 0,
             "baseline_gap_relative": 0.005},
            {"role": "evaluation", "relative_improvement": -0.01,
             "baseline_choice": "A", "history_choice": "B", "reference_best": ["A"],
             "baseline_regret_j": 0, "history_regret_j": 1e-7,
             "baseline_gap_relative": 0.02},
            {"role": "replay_control", "relative_improvement": 1,
             "baseline_choice": "A", "history_choice": "B", "reference_best": ["B"],
             "baseline_regret_j": 1, "history_regret_j": 0,
             "baseline_gap_relative": 0},
        ]
        result = summarize(rows, planned_primary=2, threshold=0.01, near_gap=0.01)
        self.assertAlmostEqual(result["mean_relative_improvement"], 0.005)
        self.assertEqual(result["recommendation"], "stop_current_model_in_simulated_domain")
        self.assertEqual(result["near_tie_conditions"], 1)
        self.assertEqual(result["evaluated_primary_conditions"], 2)
        self.assertEqual(result["improved_choices"], 1)
        self.assertEqual(result["worsened_choices"], 1)
        partial = summarize(rows[:1], planned_primary=2, threshold=0.01, near_gap=0.01)
        self.assertEqual(partial["recommendation"], "incomplete_evidence")
        empty = summarize([], planned_primary=2, threshold=0.01, near_gap=0.01)
        self.assertIsNone(empty["mean_relative_improvement"])
        self.assertEqual(empty["recommendation"], "incomplete_evidence")

    @unittest.skipUnless(TOOLS_AVAILABLE, "Cortex-M0 compiler and patched Thumbulator required")
    def test_real_mini_study_saves_frozen_inputs_and_scores_circuit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            config = json.loads((ROOT / "configs/energy_model.json").read_text())
            config["resistance_ohm_values"] = [0]
            config["period_multipliers"] = [2]
            config["tau_candidates_s"] = [0.00001]
            config["calibration_pulses"] = [config["calibration_pulses"][0]]
            supply = tmp / "supply.json"
            supply.write_text(json.dumps(config))
            plan = json.loads((ROOT / "configs/bounded_energy_study.json").read_text())
            plan.update(taps=[7], blocks=[8], opts=["O2"], jobs=2,
                        supply_config=str(supply))
            plan_path = tmp / "plan.json"
            plan_path.write_text(json.dumps(plan))
            output = tmp / "study"
            cli = ["python3", str(ROOT / "run_bounded_energy_study.py"),
                   "--plan", str(plan_path), "--output-dir", str(output)]
            result = subprocess.run(cli, cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "report.json").read_text())
            self.assertEqual(report["summary"]["planned_primary_conditions"], 1)
            self.assertEqual(report["summary"]["evaluated_primary_conditions"], 1)
            self.assertEqual(report["summary"]["mean_relative_improvement"], 0)
            self.assertEqual(report["physical_hypothesis_status"], "not_tested")
            self.assertEqual(len(report["predictions"]), 3)
            self.assertTrue((output / "frozen_inputs.json").exists())
            frozen = (output / "frozen_inputs.json").read_bytes()
            repeated = subprocess.run(cli, cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("already exists", repeated.stderr)
            self.assertEqual((output / "frozen_inputs.json").read_bytes(), frozen)

    def test_duplicate_grid_entries_rejected(self):
        from run_bounded_energy_study import workload_grid
        plan = json.loads((ROOT / "configs/bounded_energy_study.json").read_text())
        plan["taps"] = [7, 7]
        with self.assertRaises(ValueError):
            workload_grid(plan)


if __name__ == "__main__":
    unittest.main()
