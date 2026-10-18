#!/usr/bin/env python3
"""Run the frozen broader FIR study without retuning the virtual supply."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys

from energy_model import Buck, circuit_energy, fit_history, history_energy, steady_energy
from run_energy_hypothesis import calibration_traces, demand_trace, load_inputs, score_choices


ROOT = Path(__file__).resolve().parent


def workload_grid(plan):
    for key, maximum in (("taps", 100), ("blocks", 1024)):
        values = plan[key]
        if not values or any(type(x) is not int or not 0 < x <= maximum for x in values):
            raise ValueError(f"Invalid {key} grid")
        if len(set(values)) != len(values):
            raise ValueError(f"Duplicate {key} entries would overweight conditions")
    opts = plan["opts"]
    if not opts or any(x not in ("O0", "O1", "O2", "O3", "Os") for x in opts) or len(set(opts)) != len(opts):
        raise ValueError("Invalid or duplicate compiler settings")
    if type(plan["jobs"]) is not int or not 0 < plan["jobs"] <= 1024:
        raise ValueError("Invalid streaming job count")
    for key in ("minimum_relative_improvement", "near_tie_relative_gap"):
        value = plan[key]
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid {key}")
    grid = []
    for taps, block, opt in itertools.product(plan["taps"], plan["blocks"], opts):
        spec = {"taps": taps, "block": block, "opt": opt}
        grid.append({**spec, "jobs": plan["jobs"],
                     "workload_id": f"t{taps}_b{block}_{opt}",
                     "role": "replay_control" if spec == plan["replay_control"] else "evaluation"})
    if not any(w["role"] == "evaluation" for w in grid):
        raise ValueError("Study needs at least one non-control workload")
    return grid


def summarize(conditions, planned_primary, threshold, near_gap):
    rows = [r for r in conditions if r["role"] == "evaluation"]
    count = len(rows)
    mean = sum(r["relative_improvement"] for r in rows) / count if count else None
    complete = count == planned_primary and count > 0
    recommendation = "incomplete_evidence"
    if complete:
        recommendation = ("continue_to_better_traces_and_calibration" if mean > threshold else
                          "stop_current_model_in_simulated_domain")
    return {
        "planned_primary_conditions": planned_primary, "evaluated_primary_conditions": count,
        "complete": complete, "mean_relative_improvement": mean,
        "recommendation": recommendation, "minimum_relative_improvement": threshold,
        "changed_choices": sum(r["baseline_choice"] != r["history_choice"] for r in rows),
        "improved_choices": sum(bool(r["relative_improvement"] > 0) for r in rows),
        "worsened_choices": sum(bool(r["relative_improvement"] < 0) for r in rows),
        "near_tie_conditions": sum(r["baseline_gap_relative"] <= near_gap for r in rows),
        "near_tie_relative_gap": near_gap,
        "baseline_reference_best_agreements": sum(r["baseline_choice"] in r["reference_best"] for r in rows),
        "history_reference_best_agreements": sum(r["history_choice"] in r["reference_best"] for r in rows),
        "max_baseline_regret_j": max((r["baseline_regret_j"] for r in rows), default=None),
        "max_history_regret_j": max((r["history_regret_j"] for r in rows), default=None),
    }


def evaluate_workload(workload, output_dir, config_path, fits):
    """Worker writes a checked profile, then scores frozen predictors against the circuit."""
    output = Path(output_dir)
    wid = workload["workload_id"]
    profile_path = output / "profiles" / f"{wid}.json"
    rows, predictions, failures = [], [], []
    metadata = {"workload_id": wid, "role": workload["role"]}
    try:
        command = [sys.executable, str(ROOT / "run_sim_pilot.py"), "--output", str(profile_path)]
        for flag, key in (("--taps", "taps"), ("--block", "block"), ("--jobs", "jobs"), ("--opt", "opt")):
            command.extend([flag, str(workload[key])])
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
        if process.returncode:
            raise ValueError(process.stdout + process.stderr)
        profile, config = load_inputs(profile_path, Path(config_path))
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        return {"workload": workload, "conditions": [], "predictions": [],
                "failures": [{**metadata, "stage": "profile", "reason": str(error)}]}
    longest = max(j["active_cycles"] / config["clock_hz"]
                  for variant in profile["variants"] for j in variant["jobs"])
    jobs = profile["jobs"]
    for resistance in config["resistance_ohm_values"]:
        supply = replace(Buck(**config.get("supply", {})), resistance_ohm=resistance)
        for factor in config["period_multipliers"]:
            case = {**metadata, "case_id": f"{wid};R={resistance:g};period_factor={factor:g}",
                    "resistance_ohm": resistance, "period_factor": factor,
                    "period_s": (longest + config["wake_duration_s"]) * factor}
            baseline, history, reference, pending = {}, {}, {}, []
            try:
                if resistance not in fits:
                    raise ValueError("Supply calibration failed; no frozen predictor")
                for variant in profile["variants"]:
                    name = variant["variant"]
                    trace = demand_trace(variant, config, case["period_s"])
                    circuit = circuit_energy(trace, supply)
                    baseline[name] = steady_energy(trace, supply) / jobs
                    history[name] = history_energy(trace, supply, fits[resistance]) / jobs
                    reference[name] = circuit.source_j / jobs
                    if reference[name] <= 0:
                        raise ValueError("Relative metrics require positive reference energy")
                    pending.append({**case, "variant": name,
                                    "baseline_j_per_job": baseline[name],
                                    "history_j_per_job": history[name],
                                    "reference_j_per_job": reference[name],
                                    "baseline_error_pct": 100*(baseline[name]/reference[name]-1),
                                    "history_error_pct": 100*(history[name]/reference[name]-1),
                                    **asdict(circuit)})
                ordered = sorted(baseline.values())
                rows.append({**case, **score_choices(baseline, history, reference),
                             "baseline_gap_relative": (ordered[1]-ordered[0])/ordered[0]})
                predictions.extend(pending)
            except (ValueError, ZeroDivisionError) as error:
                failures.append({**case, "stage": "evaluation", "reason": str(error)})
    return {"workload": workload, "conditions": rows, "predictions": predictions,
            "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
            "failures": failures}


def write_results(output, report):
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    for key in ("conditions", "predictions"):
        rows = report[key]
        if rows:
            with (output / f"{key}.csv").open("w", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    s = report["summary"]
    mean = "undefined" if s["mean_relative_improvement"] is None else f"{100*s['mean_relative_improvement']:.6f}%"
    lines = ["# Bounded broader simulation result", "",
             "**Physical hypothesis: not tested. All supply parameters/reference energies are synthetic.**", "",
             f"Primary coverage: {s['evaluated_primary_conditions']} / {s['planned_primary_conditions']} conditions.",
             f"Mean selection savings: {mean}; fixed useful-improvement criterion: {100*s['minimum_relative_improvement']:.2f}%.",
             f"Recommendation: `{s['recommendation']}`.", "",
             f"Changed choices: {s['changed_choices']}; improved: {s['improved_choices']}; worsened: {s['worsened_choices']}.",
             f"Baseline/reference-best agreement: {s['baseline_reference_best_agreements']} / {s['evaluated_primary_conditions']}.",
             f"History/reference-best agreement: {s['history_reference_best_agreements']} / {s['evaluated_primary_conditions']}.",
             f"Near-tie conditions (baseline best-two gap ≤ {100*s['near_tie_relative_gap']:.2f}%): "
             f"{s['near_tie_conditions']} / {s['evaluated_primary_conditions']}.", "",
             "The already inspected original workload is a replay control, excluded from these primary metrics.", "",
             "| Workload | Role | Valid conditions | Mean selection savings |",
             "|---|---|---:|---:|"]
    for result in report["workload_results"]:
        rows = result["conditions"]
        mean = f"{100*sum(r['relative_improvement'] for r in rows)/len(rows):.6f}%" if rows else "undefined"
        lines.append(f"| {result['workload']['workload_id']} | {result['workload']['role']} | {len(rows)} | {mean} |")
    lines.extend(["", "## Interpretation", "",
                  "This result covers the fixed FIR grid and flat per-job demand assumption only. "
                  "It does not validate or generally reject the physical regulator-history hypothesis. "
                  "There is no hardware calibration, finer instruction-current trace or statistical confidence interval. "
                  "See BOUNDED_STUDY_PROTOCOL.md and frozen_inputs.json for the decision rule and scope.", "",
                  f"Recorded failures: {len(report['failures'])}. All failures are retained in report.json."])
    (output / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/bounded_energy_study.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/bounded_energy_study")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3, 4), default=1)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("output directory already exists; choose a new --output-dir")
    try:
        plan = json.loads(args.plan.read_text())
        if plan["schema_version"] != 1:
            raise ValueError("Unsupported study schema")
        workloads = workload_grid(plan)
        config_path = ROOT / plan["supply_config"]
        _, config = load_inputs(ROOT / "results/sim_pilot.json", config_path)
        for key in ("resistance_ohm_values", "period_multipliers"):
            if len(config[key]) != len(set(config[key])):
                raise ValueError(f"Duplicate {key} entries would overweight conditions")
        if config["minimum_relative_improvement"] != plan["minimum_relative_improvement"]:
            raise ValueError("Supply and study success thresholds must match")
        sources = ("run_bounded_energy_study.py", "run_energy_hypothesis.py", "energy_model.py",
                   "run_sim_pilot.py", "fir.c", "fir.h", "main.c", "startup.s", "stm32f051.ld",
                   "patches/thumbulator_stm32f0x.patch")
        source_hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
        frozen = {"started_utc": datetime.now(timezone.utc).isoformat(), "plan": plan, "config": config,
                  "plan_sha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
                  "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                  "source_sha256": source_hashes, "workers": args.workers,
                  "workloads": workloads, "physical_measurement": False}
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=False)
        (output / "profiles").mkdir()
        (output / "workloads").mkdir()
        (output / "frozen_inputs.json").write_text(json.dumps(frozen, indent=2, allow_nan=False)+"\n")
        frozen_config = output / "supply_config.json"
        frozen_config.write_text(json.dumps(config, indent=2, allow_nan=False)+"\n")
        fits, failures = {}, []
        for resistance in config["resistance_ohm_values"]:
            print(f"Freeze pulse-only calibration for R={resistance:g} ohm", flush=True)
            try:
                fits[resistance] = fit_history(calibration_traces(config),
                    replace(Buck(**config.get("supply", {})), resistance_ohm=resistance),
                    config["tau_candidates_s"])
            except ValueError as error:
                failures.append({"stage": "calibration", "resistance_ohm": resistance, "reason": str(error)})
        (output / "frozen_fits.json").write_text(json.dumps(
            {str(r): asdict(fit) for r, fit in fits.items()}, indent=2, allow_nan=False)+"\n")
        results = []
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            pending = {pool.submit(evaluate_workload, w, output, frozen_config, fits): w for w in workloads}
            for future in as_completed(pending):
                result = future.result()
                results.append(result)
                wid = result["workload"]["workload_id"]
                (output / "workloads" / f"{wid}.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
                print(f"{len(results)}/{len(workloads)} {wid}: {len(result['conditions'])} valid, "
                      f"{len(result['failures'])} failures", flush=True)
        results.sort(key=lambda r: r["workload"]["workload_id"])
        conditions = [row for r in results for row in r["conditions"]]
        predictions = [row for r in results for row in r["predictions"]]
        failures.extend(row for r in results for row in r["failures"])
        count = len(config["resistance_ohm_values"]) * len(config["period_multipliers"])
        summary = summarize(conditions, count*sum(w["role"] == "evaluation" for w in workloads),
                            plan["minimum_relative_improvement"], plan["near_tie_relative_gap"])
        primary_predictions = [p for p in predictions if p["role"] == "evaluation"]
        for model in ("baseline", "history"):
            summary[f"mean_absolute_{model}_error_pct"] = (sum(abs(p[f"{model}_error_pct"])
                for p in primary_predictions) / len(primary_predictions) if primary_predictions else None)
        intact = all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == digest
                     for p, digest in source_hashes.items())
        if not intact:
            failures.append({"stage": "provenance", "reason": "Source changed during the study"})
            summary["recommendation"] = "incomplete_evidence"
        report = {"schema_version": 1, "physical_hypothesis_status": "not_tested", "summary": summary,
                  "finished_utc": datetime.now(timezone.utc).isoformat(),
                  "source_integrity_verified": intact, "workload_results": results,
                  "conditions": conditions, "predictions": predictions, "failures": failures,
                  "frozen_inputs_sha256": hashlib.sha256((output/"frozen_inputs.json").read_bytes()).hexdigest(),
                  "frozen_fits_sha256": hashlib.sha256((output/"frozen_fits.json").read_bytes()).hexdigest()}
        write_results(output, report)
        print(f"Wrote {output}: {summary['recommendation']}", flush=True)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
