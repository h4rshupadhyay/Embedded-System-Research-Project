from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from itertools import product
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


WEIGHTS = {
    "nonmul": Decimal("0.964258"), "mul": Decimal("1.652455"),
    "taken_branches": Decimal("2.091986"), "ram_reads": Decimal("1.109833"),
    "ram_writes": Decimal("0.650563"), "flash_reads": Decimal("0.633621"),
}
COMPILERS = ("gcc10", "gcc15")
BLOCKS = (1, 64)
VARIANTS = ("cmsis64_unroll", "spec_direct", "partial_direct32x2", "trans_const", "trans_hcub_demand")
CONTRASTS = (("partial_direct32x2", "spec_direct"),
             ("trans_hcub_demand", "trans_const"),
             ("trans_hcub_demand", "partial_direct32x2"))
EVENT_COORDINATES = ("nonmul", "mul", "taken_branches", "ram_reads", "ram_writes", "flash_reads")
SOURCE_DIGESTS = {
    "research/fir-baseline/selection-design.json": "bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f",
    "research/fir-sharing-probe/results.json": "57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa",
    "research/fir-sharing-probe/partial-direct/results.json": "eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f",
    "research/fir-sharing-probe/independent-check/verification.json": "e8ce76157aee913d05f16219117a5f3b0ed4aa1a08423a9acf8282095ab326c7",
    "research/fir-sharing-probe/compiler-explanation/accounting.json": "f39dc297271e4d706196690884a91b7eaedb414661230bd6e678a2bfc593aad2",
    "research/fir-sharing-probe/explanation-check/verification.json": "64e975a82a978254596e6aa2b16753527cf9bd9d78887a90777f74f337c26003",
}


def affine_boundary(A: Decimal, B: Decimal) -> dict:
    if not isinstance(A, Decimal) or not isinstance(B, Decimal) or not A.is_finite() or not B.is_finite():
        raise ValueError("A and B must be finite Decimal values")
    if B == 0:
        if A == 0:
            return {"kind": "all_ties", "root_exact": None, "root_decimal": None,
                    "root_domain": "all_nonnegative", "root_region": "all", "sign": "zero"}
        return {"kind": "constant", "root_exact": None, "root_decimal": None,
                "root_domain": "none", "root_region": "none", "sign": "positive" if A > 0 else "negative"}
    root = -Fraction(A) / Fraction(B)
    with localcontext() as ctx:
        ctx.prec = 50
        display = format((Decimal(root.numerator) / Decimal(root.denominator)).quantize(Decimal("0.000001")), "f")
    if root < 0:
        domain, region = "outside", "outside"
    elif root == 0:
        domain = "boundary"
        region = "below"
    elif root < Fraction(1, 2):
        domain, region = "inside_domain", "below"
    elif root <= 2:
        domain, region = "inside_domain", "within"
    else:
        domain, region = "inside_domain", "above"
    return {"kind": "root", "root_exact": {"numerator": root.numerator, "denominator": root.denominator},
            "root_decimal": display, "root_domain": domain, "root_region": region, "sign": None}


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _cost(row: dict) -> dict:
    counts = {name: row[name] for name in ("instructions", "mul", "taken_branches", "ram_reads", "ram_writes", "flash_reads")}
    counts["nonmul"] = row["instructions"] - row["mul"]
    return {name: WEIGHTS[name] * counts[name] for name in WEIGHTS}


def _validate_report(report: dict) -> dict:
    if not isinstance(report, dict) or report.get("schema_version") != 1 or not isinstance(report.get("rows"), list):
        raise ValueError("report must be a schema-version-1 paper report with rows")
    bykey = {}
    expected = set(product(COMPILERS, BLOCKS, VARIANTS))
    for row in report["rows"]:
        if not isinstance(row, dict):
            raise ValueError("report rows must be objects")
        key = (row.get("compiler"), row.get("block"), row.get("variant"))
        if key not in expected or key in bykey:
            raise ValueError(f"unexpected or duplicate report row {key}")
        if row.get("samples") != 257:
            raise ValueError(f"report row {key} does not describe all 257 outputs")
        for name in ("instructions", "mul", "taken_branches", "ram_reads", "ram_writes", "flash_reads", "flash_writes", "bl", "arm_zero_ws_cycles", "state_allocation_bytes", "probe_process_stack_bytes", "kernel_and_coefficient_symbol_bytes"):
            if type(row.get(name)) is not int:
                raise ValueError(f"report row {key} has invalid {name}")
        if min(row[name] for name in ("instructions", "mul", "taken_branches", "ram_reads", "ram_writes", "flash_reads", "flash_writes", "bl")) < 0 or row["mul"] > row["instructions"]:
            raise ValueError(f"report row {key} has invalid event counts")
        energy = sum(_cost(row).values(), Decimal(0))
        try:
            serialized_energy = Decimal(str(row.get("estimated_cpu_energy_nj")))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"report row {key} has invalid serialized energy")
        if not serialized_energy.is_finite() or serialized_energy != energy:
            raise ValueError(f"report row {key} energy does not reconstruct from its event counts")
        cycles = row["instructions"] + row["ram_reads"] + row["ram_writes"] + row["flash_reads"] + 2 * row["taken_branches"] + row["bl"]
        if row["arm_zero_ws_cycles"] != cycles:
            raise ValueError(f"report row {key} cycles do not reconstruct from its events")
        bykey[key] = row
    if set(bykey) != expected:
        raise ValueError("report must contain the exact 20 admitted compiler/block/variant rows")
    return bykey


def _strict_at(A: Decimal, B: Decimal, lam: Decimal) -> str:
    value = A + B * lam
    return "left" if value < 0 else "right" if value > 0 else "tie"


def analyze_report(report: dict) -> dict:
    bykey = _validate_report(report)
    pairs = []
    for compiler, block in product(COMPILERS, BLOCKS):
        for left_variant, right_variant in CONTRASTS:
            left = bykey[(compiler, block, left_variant)]
            right = bykey[(compiler, block, right_variant)]
            left_events, right_events = _cost(left), _cost(right)
            component_deltas = {name: left_events[name] - right_events[name] for name in WEIGHTS}
            delta_energy = sum(component_deltas.values(), Decimal(0))
            A = component_deltas["nonmul"] + component_deltas["mul"] + component_deltas["taken_branches"] + component_deltas["flash_reads"]
            B = component_deltas["ram_reads"] + component_deltas["ram_writes"]
            with localcontext() as ctx:
                ctx.prec = 50
                relative = (left_events["nonmul"] + left_events["mul"] + left_events["taken_branches"] + left_events["ram_reads"] + left_events["ram_writes"] + left_events["flash_reads"]) / sum(right_events.values(), Decimal(0))
                relative = (relative - 1) * 100
                per_output = delta_energy / Decimal(257)
            coordinates = {
                "nonmul": (left["instructions"] - left["mul"]) - (right["instructions"] - right["mul"]),
                "mul": left["mul"] - right["mul"],
                "taken_branches": left["taken_branches"] - right["taken_branches"],
                "ram_reads": left["ram_reads"] - right["ram_reads"],
                "ram_writes": left["ram_writes"] - right["ram_writes"],
                "flash_reads": left["flash_reads"] - right["flash_reads"],
                "instructions": left["instructions"] - right["instructions"],
                "bl": left["bl"] - right["bl"],
                "flash_writes": left["flash_writes"] - right["flash_writes"],
            }
            vals = [coordinates[name] for name in EVENT_COORDINATES]
            dominance = "left_dominates" if all(x <= 0 for x in vals) and any(x < 0 for x in vals) else "right_dominates" if all(x >= 0 for x in vals) and any(x > 0 for x in vals) else "event_equal" if all(x == 0 for x in vals) else "mixed"
            boundary = affine_boundary(A, B)
            stress = {"at_0_5": _strict_at(A, B, Decimal("0.5")), "at_1": _strict_at(A, B, Decimal(1)), "at_2": _strict_at(A, B, Decimal(2)),
                      "strict_lower_throughout_region": A + B * Decimal("0.5") < 0 and A + 2 * B < 0,
                      "strict_higher_throughout_region": A + B * Decimal("0.5") > 0 and A + 2 * B > 0}
            pairs.append({"compiler": compiler, "block": block, "left_variant": left_variant, "right_variant": right_variant,
                          "samples": 257, "source_digests": dict(SOURCE_DIGESTS), "delta_events": coordinates,
                          "delta_instructions": left["instructions"] - right["instructions"], "delta_bl": left["bl"] - right["bl"],
                          "delta_flash_writes": left["flash_writes"] - right["flash_writes"], "cost_components_nj": {k: _decimal_text(v) for k, v in component_deltas.items()},
                          "delta_energy_nj": _decimal_text(delta_energy), "delta_energy_nj_per_output": _decimal_text(per_output),
                          "left_relative_percent": _decimal_text(relative), "delta_cycles": left["arm_zero_ws_cycles"] - right["arm_zero_ws_cycles"],
                          "delta_state_allocation_bytes": left["state_allocation_bytes"] - right["state_allocation_bytes"],
                          "delta_probe_process_stack_bytes": left["probe_process_stack_bytes"] - right["probe_process_stack_bytes"],
                          "delta_kernel_and_coefficient_symbol_bytes": left["kernel_and_coefficient_symbol_bytes"] - right["kernel_and_coefficient_symbol_bytes"],
                          "event_dominance": dominance, "affine": {"A_nj": _decimal_text(A), "B_nj": _decimal_text(B), "boundary": boundary, "stress": stress}})
    return {"schema_version": 1, "scope": {"samples": 257, "pair_count": 12, "order": "gcc10 then gcc15; block 1 then 64; partial-minus-wide, Hcub-minus-ordinary, Hcub-minus-partial", "lambda_domain": "lambda >= 0", "selected_region": ["0.5", "2"], "stress_interpretation": "arbitrary uncalibrated RAM-weight sensitivity; not a confidence interval, hardware configuration, or physical price"},
            "source_digests": dict(SOURCE_DIGESTS), "pairs": pairs}


def _markdown(analysis: dict) -> str:
    lines = ["# Saved-event contrast analysis", "",
             "All pairs use left minus right and the original 257-output stream. Negative modeled energy favors the left variant. RAM stress multiplies both RAM weights by λ over [0.5, 2]; this is arbitrary model sensitivity, not physical uncertainty.", "",
             "| Compiler | Block | Contrast | ΔE (nJ) | Left relative (%) | A (nJ) | B (nJ) | Root | λ=.5 / 1 / 2 | Event relation |", "|---|---:|---|---:|---:|---:|---:|---:|---|---|"]
    for pair in analysis["pairs"]:
        name = f"{pair['left_variant']} − {pair['right_variant']}"
        a = pair["affine"]
        stress = a["stress"]
        lines.append(f"| {pair['compiler']} | {pair['block']} | {name} | {pair['delta_energy_nj']} | {Decimal(pair['left_relative_percent']):.6f} | {a['A_nj']} | {a['B_nj']} | {a['boundary']['root_decimal']} ({a['boundary']['root_region']}) | {stress['at_0_5']} / {stress['at_1']} / {stress['at_2']} | {pair['event_dominance']} |")
    lines.extend(["", "The six event coordinates determine event-wise dominance only. State allocation, probe process stack, and kernel/coefficient symbol bytes are reported separately in `analysis.json`; they are not summed as memory use.", ""])
    return "\n".join(lines)


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def _atomic_outputs(output_dir: Path, analysis: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {"analysis.json": _json_bytes(analysis), "analysis.md": _markdown(analysis).encode("utf-8")}
    staged = []
    try:
        for name, payload in payloads.items():
            fd, tmp = tempfile.mkstemp(prefix=f".{name}.", dir=output_dir)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
            staged.append((Path(tmp), output_dir / name))
        for source, destination in staged:
            os.replace(source, destination)
    finally:
        for source, _ in staged:
            source.unlink(missing_ok=True)


def _frozen_report(repo_root: Path) -> dict:
    for relative, expected in SOURCE_DIGESTS.items():
        source = repo_root / relative
        if not source.is_file():
            raise ValueError(f"missing frozen input: {relative}")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen input identity mismatch for {relative}: expected {expected}, got {actual}")
    sys.path.insert(0, str(repo_root / "research" / "fir-paper"))
    try:
        import build_results
        rebuilt = build_results.build_report(build_results._load_documents(repo_root))
    finally:
        sys.path.pop(0)
        sys.modules.pop("build_results", None)
    saved_path = repo_root / "research" / "fir-paper" / "results.json"
    with saved_path.open(encoding="utf-8") as stream:
        saved = json.load(stream)
    if saved != rebuilt:
        raise ValueError("saved 20-row paper report differs from reconstruction from the six frozen sources")
    return rebuilt


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Analyze the frozen 20-row FIR paper report")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    output = Path(args.output_dir).resolve()
    if output == (root / "research" / "fir-paper").resolve():
        raise ValueError("refusing to write analysis outputs into the original paper directory")
    report = _frozen_report(root)
    analysis = analyze_report(report)
    _atomic_outputs(output, analysis)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError, ImportError) as error:
        raise SystemExit(f"analyze: {error}")
