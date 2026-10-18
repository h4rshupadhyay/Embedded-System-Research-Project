#!/usr/bin/env python3
"""Evaluate the energy-choice hypothesis against an uncalibrated virtual supply."""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path

from energy_model import Buck, Segment, circuit_energy, fit_history, history_energy, steady_energy
from run_sim_pilot import expected_checksum


ROOT = Path(__file__).resolve().parent


def score_choices(baseline, history, reference, tolerance_j=1e-10):
    if not reference or baseline.keys() != reference.keys() or history.keys() != reference.keys():
        raise ValueError("All models must score the same nonempty set of implementations")
    if any(not math.isfinite(x) or x < 0 for scores in (baseline, history, reference)
           for x in scores.values()):
        raise ValueError("Energies must be finite and nonnegative")
    # Deterministic lexical tie-break; reference ties are reported as a set.
    def choose(scores):
        best = min(scores.values())
        return min(name for name, value in scores.items() if value <= best + tolerance_j)
    base, hist = choose(baseline), choose(history)
    best = min(reference.values())
    improvement = reference[base] - reference[hist]
    return {"baseline_choice": base, "history_choice": hist,
            "reference_best": sorted(name for name, e in reference.items() if e <= best + tolerance_j),
            "baseline_regret_j": reference[base] - best,
            "history_regret_j": reference[hist] - best,
            "improvement_j": improvement,
            "relative_improvement": improvement / max(best, 1e-30)}


def checked_number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if value < 0 or (positive and value == 0):
        raise ValueError(f"{label} must be {'positive' if positive else 'nonnegative'}")
    return value


def load_inputs(profile_path, config_path):
    profile = json.loads(profile_path.read_text())
    config = json.loads(config_path.read_text())
    for key in ("clock_hz", "sleep_power_w", "wake_power_w", "wake_duration_s",
                "minimum_relative_improvement"):
        checked_number(config[key], key, positive=key == "clock_hz")
    for key in ("resistance_ohm_values", "period_multipliers", "tau_candidates_s", "calibration_pulses"):
        if not config[key]:
            raise ValueError(f"{key} cannot be empty")
    for resistance in config["resistance_ohm_values"]:
        checked_number(resistance, "resistance")
    for multiple in config["period_multipliers"]:
        checked_number(multiple, "period multiplier", positive=True)
        if multiple < 1:
            raise ValueError("period multiplier must be at least 1")
    for tau in config["tau_candidates_s"]:
        checked_number(tau, "time constant", positive=True)
    weights = config["event_weights_nj"]
    if set(weights) != {f"C{i}" for i in range(1, 7)}:
        raise ValueError("Exactly six named event weights C1..C6 are required")
    for weight in weights.values():
        checked_number(weight, "event weight")
    if profile.get("schema_version") != 1 or profile.get("physical_measurement") is not False:
        raise ValueError("Expected a schema-v1 simulator profile, not a measurement file")
    taps, block, jobs = profile["taps"], profile["block"], profile["jobs"]
    if any(type(x) is not int or x <= 0 for x in (taps, block, jobs)) or taps > 100 or block > 1024 or jobs > 1024:
        raise ValueError("Unsupported pilot dimensions")
    if not profile["variants"]:
        raise ValueError("No implementation profiles")
    expected = expected_checksum(taps, block, jobs)
    names = set()
    for row in profile["variants"]:
        if row["variant"] in names:
            raise ValueError("Duplicate implementation name")
        names.add(row["variant"])
        if row["checksum"] != expected or row["completed_jobs"] != jobs or len(row["jobs"]) != jobs:
            raise ValueError("Profile correctness/job-count gate failed")
        for job in row["jobs"]:
            if type(job["active_cycles"]) is not int or job["active_cycles"] <= 0:
                raise ValueError("Invalid active cycle count")
            if set(job["counters"]) != set(weights) or any(type(n) is not int or n < 0
                                                          for n in job["counters"].values()):
                raise ValueError("Invalid event counters")
    if len(names) < 2:
        raise ValueError("At least two equivalent implementations are needed")
    return profile, config


def calibration_traces(config):
    traces = []
    for pulse in config["calibration_pulses"]:
        duration = checked_number(pulse["period_s"], "calibration period", True)
        duty = checked_number(pulse["duty"], "calibration duty", True)
        power = checked_number(pulse["active_power_w"], "calibration power", True)
        if duty >= 1:
            raise ValueError("Calibration duty must be strictly between 0 and 1")
        traces.append([Segment(duration * duty, power),
                       Segment(duration * (1 - duty), config["sleep_power_w"])])
    return traces


def demand_trace(row, config, period_s):
    trace = []
    for job in row["jobs"]:
        active_s = job["active_cycles"] / config["clock_hz"]
        energy_j = sum(config["event_weights_nj"][key] * count
                       for key, count in job["counters"].items()) * 1e-9
        idle_s = period_s - active_s - config["wake_duration_s"]
        if idle_s < -1e-15:
            raise ValueError("Period cannot contain wake plus active interval")
        if config["wake_duration_s"]:
            trace.append(Segment(config["wake_duration_s"], config["wake_power_w"]))
        trace.append(Segment(active_s, energy_j / active_s))
        if idle_s > 0:
            trace.append(Segment(idle_s, config["sleep_power_w"]))
    return trace


def experiment(profile, config):
    supply = Buck(**config.get("supply", {}))
    training = calibration_traces(config)
    longest_s = max(j["active_cycles"] / config["clock_hz"]
                    for row in profile["variants"] for j in row["jobs"])
    predictions, conditions, invalid, fits = [], [], [], []
    jobs = profile["jobs"]
    for resistance in config["resistance_ohm_values"]:
        current_supply = replace(supply, resistance_ohm=resistance)
        print(f"Calibrating virtual supply R={resistance:g} ohm on separate pulse traces...", flush=True)
        try:
            fitted = fit_history(training, current_supply, config["tau_candidates_s"])
        except ValueError as error:
            invalid.append({"resistance_ohm": resistance, "stage": "calibration", "reason": str(error)})
            continue
        fits.append({"supply": asdict(current_supply), **asdict(fitted),
                     "calibration_source": "synthetic pulse experiments, no FIR test energies"})
        for multiplier in config["period_multipliers"]:
            period_s = (longest_s + config["wake_duration_s"]) * multiplier
            case_id = f"R={resistance:g};period_factor={multiplier:g}"
            case_predictions = []
            baseline, history, reference = {}, {}, {}
            try:
                for row in profile["variants"]:
                    trace = demand_trace(row, config, period_s)
                    circuit = circuit_energy(trace, current_supply)
                    name = row["variant"]
                    baseline[name] = steady_energy(trace, current_supply) / jobs
                    history[name] = history_energy(trace, current_supply, fitted) / jobs
                    reference[name] = circuit.source_j / jobs
                    if reference[name] <= 0:
                        raise ValueError("Relative energy metrics require positive reference energy")
                    case_predictions.append({
                        "case_id": case_id, "variant": name,
                        "baseline_j_per_job": baseline[name], "history_j_per_job": history[name],
                        "reference_j_per_job": reference[name],
                        "baseline_error_pct": 100 * (baseline[name] / reference[name] - 1),
                        "history_error_pct": 100 * (history[name] / reference[name] - 1),
                        **asdict(circuit),
                    })
                choice = score_choices(baseline, history, reference)
                conditions.append({"case_id": case_id, "resistance_ohm": resistance,
                                   "period_s": period_s, **choice})
                predictions.extend(case_predictions)
            except ValueError as error:
                invalid.append({"case_id": case_id, "stage": "evaluation", "reason": str(error)})
    if not conditions:
        raise ValueError("No valid evaluation conditions; inspect circuit/configuration bounds")
    average = sum(c["relative_improvement"] for c in conditions) / len(conditions)
    threshold = config["minimum_relative_improvement"]
    return {
        "schema_version": 1, "physical_hypothesis_status": "not_tested",
        "parameters_calibrated_to_hardware": False, "reference_kind": "synthetic_averaged_buck",
        "demand_kind": "assumed constant power per marked job, no within-job current trace",
        "scope": "Conditional virtual-circuit experiment; not STM32/LDO hardware validation",
        "calibration_policy": "Fit only synthetic calibration pulses; freeze before FIR scoring",
        "evaluation_weighting": "Equal weight per valid configured supply/cadence case",
        "mean_relative_improvement": average,
        "mean_absolute_baseline_error_pct": sum(abs(p["baseline_error_pct"]) for p in predictions) / len(predictions),
        "mean_absolute_history_error_pct": sum(abs(p["history_error_pct"]) for p in predictions) / len(predictions),
        "minimum_relative_improvement": threshold,
        "conditional_result": ("material_simulated_improvement" if average > threshold else
                               "no_material_simulated_improvement"),
        "evaluated_conditions": len(conditions), "invalid_cases": invalid,
        "planned_conditions": len(config["resistance_ohm_values"]) * len(config["period_multipliers"]),
        "conditions": conditions, "predictions": predictions, "calibration_fits": fits,
        "config": config, "supply_defaults": asdict(supply),
        "limitations": [
            "Event weights are assumed nominal MCU-pin energy; boundary/applicability unvalidated.",
            "Within-job demand is flat; preparation and first-call MCU behavior are not modeled.",
            "Wake/sleep powers and all circuit parameters are illustrative, not measured.",
            "Reference is a bidirectional averaged synchronous buck, not STM32 internal LDO.",
            "No switching ripple, switching loss, package inductance or temperature model.",
            "No physical significance test or uncertainty confidence interval follows from this grid.",
            "Invalid cases are excluded and listed; conclusions cover valid simulated conditions only.",
        ],
    }


def write_outputs(output, report):
    # Exclusive directory creation protects both previous evidence and concurrent writers.
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    for name in ("conditions", "predictions"):
        rows = report[name]
        with (output / f"{name}.csv").open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    lines = ["# Conditional energy-model experiment", "",
             "**Physical hypothesis: not tested. All supply parameters and reference energies are synthetic.**", "",
             f"Valid conditions: {report['evaluated_conditions']} / {report['planned_conditions']}.",
             f"Mean reference-energy improvement from history choices: {100 * report['mean_relative_improvement']:.6f}%.",
             f"Mean absolute energy prediction error: steady {report['mean_absolute_baseline_error_pct']:.6f}%, "
             f"history {report['mean_absolute_history_error_pct']:.6f}%.",
             f"Configured useful-improvement threshold: {100 * report['minimum_relative_improvement']:.3f}% (illustrative).",
             f"Conditional result: `{report['conditional_result']}`.", "",
             "| Condition | Steady choice | History choice | Reference best | Improvement |",
             "|---|---|---|---|---:|"]
    for row in report["conditions"]:
        lines.append(f"| {row['case_id']} | {row['baseline_choice']} | {row['history_choice']} | "
                     f"{', '.join(row['reference_best'])} | {100 * row['relative_improvement']:.6f}% |")
    lines += ["", "No measurement confidence interval is inferred from these deterministic simulations.", "",
              "## Limitations", ""] + [f"- {item}" for item in report["limitations"]]
    if report["invalid_cases"]:
        lines += ["", "## Invalid cases", "", "```json",
                  json.dumps(report["invalid_cases"], indent=2), "```"]
    (output / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=ROOT / "results/sim_pilot.json")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/energy_model.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/energy_hypothesis")
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("output directory already exists; choose a new --output-dir")
    try:
        profile, config = load_inputs(args.profile, args.config)
        report = experiment(profile, config)
        report["input_sha256"] = {"profile": hashlib.sha256(args.profile.read_bytes()).hexdigest(),
                                  "config": hashlib.sha256(args.config.read_bytes()).hexdigest()}
        report["source_sha256"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                   for name in ("energy_model.py", "run_energy_hypothesis.py", "run_sim_pilot.py")}
        write_outputs(args.output_dir, report)
        print(f"Wrote {args.output_dir}: {report['conditional_result']}; physical hypothesis not tested")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
