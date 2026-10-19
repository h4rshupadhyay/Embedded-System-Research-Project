"""Deterministic derived analysis for the frozen Stage 1 FIR evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

INPUT_HASHES = {
    "research/fir-baseline/selection-design.json": "bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f",
    "research/fir-sharing-probe/results.json": "57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa",
    "research/fir-sharing-probe/partial-direct/results.json": "eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f",
    "research/fir-sharing-probe/independent-check/verification.json": "e8ce76157aee913d05f16219117a5f3b0ed4aa1a08423a9acf8282095ab326c7",
    "research/fir-sharing-probe/compiler-explanation/accounting.json": "f39dc297271e4d706196690884a91b7eaedb414661230bd6e678a2bfc593aad2",
    "research/fir-sharing-probe/explanation-check/verification.json": "64e975a82a978254596e6aa2b16753527cf9bd9d78887a90777f74f337c26003",
}
DOC_KEYS = ("design", "sharing", "partial", "verified", "accounting", "explanation")
VARIANTS = ("cmsis64_unroll", "spec_direct", "partial_direct32x2", "trans_const", "trans_hcub_demand")
COMPILERS = ("gcc10", "gcc15")
BLOCKS = (1, 64)
EVENTS = ("instructions", "mul", "ram_reads", "ram_writes", "flash_reads", "flash_writes", "taken_branches", "bl")
FILTER = "speech_minphase48"
MAXIMUM = 32768
SAMPLES = 257


def _d(value, label):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be a decimal number")
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


def assess_hypothesis(margins: Sequence[Decimal]) -> dict:
    values = list(margins)
    if len(values) != 4 or any(not isinstance(v, Decimal) or not v.is_finite() for v in values):
        raise ValueError("expected four finite Decimal margins in gcc10/b1, gcc10/b64, gcc15/b1, gcc15/b64 order")
    passes = [v < 0 for v in values]
    return {"status": "retained" if all(passes) else "rejected", "passes": passes}


def _identity(row):
    return (row.get("compiler"), row.get("block"), row.get("variant"))


def _canonical_energy(row, weights):
    ins = int(row["instructions"])
    mul = int(row["mul"])
    if mul > ins:
        raise ValueError("mul event count exceeds instructions")
    return (weights["nonmul"] * (ins - mul) + weights["mul"] * mul
            + weights["taken_branches"] * int(row["taken_branches"])
            + weights["ram_reads"] * int(row["ram_reads"])
            + weights["ram_writes"] * int(row["ram_writes"])
            + weights["flash_reads"] * int(row["flash_reads"]))


def _require_unique(rows, label):
    seen = set()
    for row in rows:
        key = _identity(row)
        if key in seen:
            raise ValueError(f"duplicate {label} row {key}")
        seen.add(key)
    return { _identity(r): r for r in rows }


def _validate_documents(documents):
    if set(documents) != set(DOC_KEYS):
        raise ValueError(f"documents keys must be exactly {', '.join(DOC_KEYS)}")
    design, sharing, partial, verified, accounting, explanation = (documents[k] for k in DOC_KEYS)
    if FILTER not in design.get("filters", {}):
        raise ValueError(f"design missing filter {FILTER}")
    if sharing.get("actual_input") is None or len(sharing["actual_input"]) != SAMPLES:
        raise ValueError("sharing actual input must contain 257 samples")
    if sharing.get("model") != partial.get("model") or sharing.get("model") != verified.get("model"):
        raise ValueError("conflicting cross-source model weights or configuration")
    weights = {k: _d(v, f"energy weight {k}") for k, v in sharing["model"]["energy_weights_nj"].items()}
    if set(weights) != {"nonmul", "mul", "taken_branches", "ram_reads", "ram_writes", "flash_reads"}:
        raise ValueError("unexpected energy weight names")
    full_rows = [r for r in sharing.get("rows", []) if r.get("filter") == FILTER and r.get("maximum") == MAXIMUM and r.get("variant") in VARIANTS]
    part_rows = [r for r in partial.get("rows", []) if r.get("filter") == FILTER and r.get("maximum") == MAXIMUM and r.get("variant") == "partial_direct32x2"]
    source_rows = _require_unique(full_rows + part_rows, "source")
    expected = {(c, b, v) for c in COMPILERS for b in BLOCKS for v in VARIANTS}
    if set(source_rows) != expected:
        missing = sorted(expected - set(source_rows))
        raise ValueError(f"selected rows must be exactly 20 unique compiler/block/variant combinations; missing {missing}")
    for key, row in source_rows.items():
        if row.get("samples") != SAMPLES or not row.get("outputs_verified", False) == SAMPLES or row.get("retained_state_verified") is not True or row.get("guards_verified") is not True:
            raise ValueError(f"source row {key} failed samples/output/history/guard admission")
        if any(not isinstance(row.get(e), int) or row[e] < 0 for e in EVENTS):
            raise ValueError(f"source row {key} has invalid event counts")
        if row.get("filter") != FILTER or row.get("maximum") != MAXIMUM:
            raise ValueError(f"source row {key} has incompatible filter or range")
        reconstructed_cycles = (int(row["instructions"]) + int(row["ram_reads"]) + int(row["ram_writes"])
                                + int(row["flash_reads"]) + 2 * int(row["taken_branches"]) + int(row["bl"]))
        if int(row.get("arm_zero_ws_cycles", -1)) != reconstructed_cycles:
            raise ValueError(f"cycles conflict with reconstructed event counts for {key}")
        serialized = _d(row.get("estimated_cpu_energy_nj"), f"source energy {key}")
        canonical = _canonical_energy(row, weights)
        if abs(serialized - canonical) > Decimal("0.000001"):
            raise ValueError(f"source row {key} energy conflicts with reconstructed event total")
    verified_rows = [r for r in verified.get("rows", []) if r.get("variant") in VARIANTS and r.get("variant") != "partial_direct32x2"]
    peer_rows = [r for r in verified.get("peer_rows", []) if r.get("variant") == "partial_direct32x2"]
    diagnostics = _require_unique(verified_rows + peer_rows, "verified")
    if set(diagnostics) != expected:
        raise ValueError("independent verification must contain exactly four partial peer rows and sixteen selected summary rows")
    if len(peer_rows) != 4:
        raise ValueError("independent verification must contain four partial peer rows")
    for key, diag in diagnostics.items():
        if diag.get("samples") != SAMPLES or int(diag.get("artifacts_verified", 0)) <= 0:
            raise ValueError(f"verification row {key} lacks admitted artifact/output summary")
        src = source_rows[key]
        if int(diag.get("arm_zero_ws_cycles", -1)) != int(src["arm_zero_ws_cycles"]):
            raise ValueError(f"conflicting cross-source cycle total for {key}")
        if abs(_d(diag.get("estimated_cpu_energy_nj"), f"verified energy {key}") - _d(src["estimated_cpu_energy_nj"], f"source energy {key}")) > Decimal("0.000001"):
            raise ValueError(f"conflicting cross-source energy total for {key}")
    explanation_rows = explanation.get("peer_rows", {})
    if set(explanation_rows) != set(COMPILERS):
        raise ValueError("explanation must contain GCC10 and GCC15 peer summaries")
    acc_rows = accounting.get("rows", [])
    if len(acc_rows) != 2 or {(r.get("compiler"), r.get("block")) for r in acc_rows} != {(c, 1) for c in COMPILERS}:
        raise ValueError("accounting rows must be exactly GCC10 and GCC15 block1")
    for ar in acc_rows:
        key = (ar.get("compiler"), 1, "partial_direct32x2")
        src = source_rows.get(key)
        if src is None or ar.get("binary_sha256") != src.get("artifacts", {}).get("firmware.bin"):
            raise ValueError(f"accounting binary identity mismatch for {key}")
        if any(ar.get("totals", {}).get(event) != src.get(event) for event in EVENTS):
            raise ValueError(f"accounting totals conflict with selected partial row for {key[0]}")
        exp = explanation_rows.get(ar["compiler"])
        if not exp or exp.get("totals") != ar.get("totals"):
            raise ValueError(f"accounting/explanation event totals conflict for {ar['compiler']}")
    expected_delta = {event: source_rows[("gcc15", 1, "partial_direct32x2")][event] - source_rows[("gcc10", 1, "partial_direct32x2")][event] for event in EVENTS}
    if explanation.get("delta") != expected_delta:
        raise ValueError("explanation delta conflicts with block1 raw rows")
    expected_delta_cycles = (expected_delta["instructions"] + expected_delta["ram_reads"] + expected_delta["ram_writes"]
                             + expected_delta["flash_reads"] + 2 * expected_delta["taken_branches"] + expected_delta["bl"])
    delta_energy = (weights["nonmul"] * (expected_delta["instructions"] - expected_delta["mul"])
                    + weights["mul"] * expected_delta["mul"]
                    + weights["taken_branches"] * expected_delta["taken_branches"]
                    + weights["ram_reads"] * expected_delta["ram_reads"]
                    + weights["ram_writes"] * expected_delta["ram_writes"]
                    + weights["flash_reads"] * expected_delta["flash_reads"])
    cost = explanation.get("cost_delta", {})
    if int(cost.get("estimated_cycles", -1)) != expected_delta_cycles or abs(_d(cost.get("modeled_cpu_energy_nj"), "explanation modeled energy") - delta_energy) > Decimal("0.000001"):
        raise ValueError("explanation cost conflicts with reconstructed block1 event delta")
    return source_rows, diagnostics, weights


def _s(value):
    return format(value, "f")


def build_report(documents: dict[str, dict]) -> dict:
    source_rows, diagnostics, weights = _validate_documents(documents)
    design, sharing, partial, verified, accounting, explanation = (documents[k] for k in DOC_KEYS)
    keys = [(c, b, v) for c in COMPILERS for b in BLOCKS for v in VARIANTS]
    rows = []
    bykey = {}
    source_paths = {"partial_direct32x2": "research/fir-sharing-probe/partial-direct/results.json"}
    for c, b, v in keys:
        r = source_rows[(c, b, v)]
        diag = diagnostics[(c, b, v)]
        energy = _canonical_energy(r, weights)
        cycles = Decimal(r["arm_zero_ws_cycles"])
        item = {
            "compiler": c, "block": b, "variant": v, "samples": SAMPLES,
            **{e: int(r[e]) for e in EVENTS},
            "arm_zero_ws_cycles": int(r["arm_zero_ws_cycles"]),
            "estimated_cpu_energy_nj": _s(energy),
            "cycles_per_output": _s(cycles / SAMPLES),
            "energy_nj_per_output": _s(energy / SAMPLES),
            "state_allocation_bytes": int(r["state_allocation_bytes"]),
            "probe_process_stack_bytes": int(diag["probe_process_stack_bytes"]),
            "kernel_and_coefficient_symbol_bytes": int(diag["kernel_and_coefficient_symbol_bytes"]),
            "source_path": source_paths.get(v, "research/fir-sharing-probe/results.json"),
            "diagnostic_source_path": "research/fir-sharing-probe/independent-check/verification.json",
            "diagnostic_source_array": "peer_rows" if v == "partial_direct32x2" else "rows",
            "binary_sha256": r.get("artifacts", {}).get("firmware.bin", diag.get("binary_sha256")),
        }
        rows.append(item)
        bykey[(c,b,v)] = energy
    order = [(c,b) for c in COMPILERS for b in BLOCKS]
    comparisons = []
    for c,b in order:
        h = bykey[(c,b,"trans_hcub_demand")]
        item = {"compiler": c, "block": b}
        for v, name in (("cmsis64_unroll", "hcub_vs_cmsis64_unroll_energy_percent"), ("spec_direct", "hcub_vs_spec_direct_energy_percent"), ("partial_direct32x2", "hcub_vs_partial_direct32x2_energy_percent")):
            item[name] = _s((h / bykey[(c,b,v)] - 1) * 100)
        comparisons.append(item)
    margins = [Decimal(x["hcub_vs_partial_direct32x2_energy_percent"]) for x in comparisons]
    assessment = assess_hypothesis(margins)
    wide_partial = []
    ordinary_delta = []
    for c,b in order:
        p, w = bykey[(c,b,"partial_direct32x2")], bykey[(c,b,"spec_direct")]
        h = bykey[(c,b,"trans_hcub_demand")]
        ordinary_delta.append({"compiler":c,"block":b,"trans_const_vs_partial_energy_percent":_s((bykey[(c,b,"trans_const")]/p-1)*100),"hcub_vs_trans_const_energy_percent":_s((h/bykey[(c,b,"trans_const")]-1)*100)})
        wide_partial.append({"compiler":c,"block":b,"partial_vs_spec_direct_energy_percent":_s((p/w-1)*100)})
    selectable = []
    for b in BLOCKS:
        by_comp = {c: bykey[(c,b,"trans_hcub_demand")] for c in COMPILERS}
        partial_comp = {c: bykey[(c,b,"partial_direct32x2")] for c in COMPILERS}
        best_hcub, best_partial = min(by_comp.values()), min(partial_comp.values())
        selectable.append({"block":b,"selected_compiler":min(by_comp,key=by_comp.get),"selected_energy_nj":_s(best_hcub),"selected_partial_compiler":min(partial_comp,key=partial_comp.get),"selected_partial_energy_nj":_s(best_partial),"gcc10_energy_nj":_s(by_comp["gcc10"]),"gcc15_energy_nj":_s(by_comp["gcc15"]),"gcc15_vs_gcc10_energy_percent":_s((by_comp["gcc15"]/by_comp["gcc10"]-1)*100),"selectable_saving_percent":_s((1-best_hcub/best_partial)*100)})
    expl = documents["explanation"]["delta"]
    cost = documents["explanation"]["cost_delta"]
    attributed = (Decimal(expl["ram_reads"] + expl["ram_writes"]) * weights["nonmul"]
                  + Decimal(expl["ram_reads"])*weights["ram_reads"]
                  + Decimal(expl["ram_writes"])*weights["ram_writes"])
    total = _d(cost["modeled_cpu_energy_nj"], "explanation energy delta")
    residual = total-attributed
    ratio = attributed/total*100
    # Frozen explanation arithmetic is checked against saved event/energy account.
    expected_attributed = Decimal("59909.909673")
    if attributed != expected_attributed or total != Decimal("70469.699925"):
        raise ValueError("explanation transfer attribution does not match admitted saved account")
    return {
        "schema_version":1,
        "scope":{"filter":FILTER,"maximum":MAXIMUM,"samples":SAMPLES,"row_order":"gcc10 then gcc15; block 1 then 64; variants in named order"},
        "rows":rows,
        "comparisons":comparisons,
        "hypothesis":{"id":"H_R","text":"For each of the four fixed compiler/block configurations, demand-Hcub transposition retains lower complete-stream modeled CPU energy than direct accumulation when the direct comparator is replaced by certified two-int32-partial implementation.","rule":"retained iff all four Hcub-relative energy margins are strictly below zero; equality fails strict superiority.",**assessment},
        "selectable_compiler":selectable,
        "derived_comparisons":{"partial_vs_wide_direct":wide_partial,"ordinary_transposed_vs_partial_and_hcub_vs_ordinary":ordinary_delta},
        "explanation":{"total_energy_delta_nj":_s(total),"attributed_transfer_energy_nj":_s(attributed),"residual_energy_nj":_s(residual),"attributed_fraction_percent":_s(ratio),"denominator":"GCC15 block1 minus GCC10 block1 modeled CPU energy delta"},
        "limitations":["retrospective finite-case assessment; not preregistered or population inference","event-weighted Cortex-M0 model energy; not measured board energy","simulator ticks are not physical cycles","single frozen filter and 257-sample zero-history stream","partial-direct implementation is a stronger comparator, not an optimal partition search"],
    }


def _load_documents(repo_root):
    names = dict(zip(DOC_KEYS, INPUT_HASHES))
    docs = {}
    for key, rel in names.items():
        with (repo_root / rel).open(encoding="utf-8") as f:
            docs[key] = json.load(f, parse_float=Decimal)
    return docs


def _manifest():
    return {"schema_version":1,"description":"Frozen source identities consumed by the stage 1 derived analysis; hashes record identity, not semantic validation.","files":dict(sorted(INPUT_HASHES.items()))}


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, default=lambda x: str(x) if isinstance(x, Decimal) else (_ for _ in ()).throw(TypeError(type(x).__name__))) + "\n").encode("utf-8")


def _tables(report):
    lines = ["# Derived results tables", "", "All reported energy margins use unrounded whole-stream modeled totals. Display values are rounded to two decimal places.", "", "| Compiler | Block | Variant | Cycles/output | Energy (nJ) |", "|---|---:|---|---:|---:|"]
    for r in report["rows"]:
        lines.append(f"| {r['compiler']} | {r['block']} | {r['variant']} | {Decimal(r['cycles_per_output']):.2f} | {Decimal(r['estimated_cpu_energy_nj']):.2f} |")
    lines += ["", "## H_R cell margins", "", "| Compiler | Block | Hcub vs partial-direct energy (%) | Passes strict superiority |", "|---|---:|---:|---|"]
    for x in report["comparisons"]:
        val=Decimal(x["hcub_vs_partial_direct32x2_energy_percent"])
        lines.append(f"| {x['compiler']} | {x['block']} | {val:.2f} | {'yes' if val < 0 else 'no'} |")
    return "\n".join(lines)+"\n"


def _atomic_outputs(output_dir, report):
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {"results.json":_json_bytes(report),"tables.md":_tables(report).encode("utf-8"),"source-manifest.json":_json_bytes(_manifest())}
    temps=[]
    try:
        for name,data in payloads.items():
            fd,tmp=tempfile.mkstemp(prefix="."+name+".",dir=output_dir)
            with os.fdopen(fd,"wb") as f: f.write(data)
            temps.append((Path(tmp),output_dir/name))
        for tmp,dest in temps: os.replace(tmp,dest)
    finally:
        for tmp,_ in temps:
            try: tmp.unlink()
            except FileNotFoundError: pass


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[2]))
    args=parser.parse_args(argv)
    root=Path(args.repo_root).resolve()
    for rel,expected in INPUT_HASHES.items():
        path=root/rel
        if not path.is_file(): raise ValueError(f"missing frozen input: {rel}")
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected: raise ValueError(f"frozen input identity mismatch for {rel}: expected {expected}, got {actual}")
    report=build_report(_load_documents(root))
    _atomic_outputs(Path(args.output_dir),report)


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"build_results: {exc}")
