"""Conservative accounting for the two frozen BLOCK=1 FIR binaries.

Aggregate MUL executions and direct SP LDR/STR instructions on the fixed
BLOCK=1 path are attributed from saved logs and control flow. Other dynamic
events remain an explicit residual.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


COUNTERS = ("instructions", "mul", "ram_reads", "ram_writes", "flash_reads",
            "flash_writes", "taken_branches", "bl")
COMPONENTS = ("stream_wrapper", "copy_in", "convolution", "quantize_store",
              "history_copy", "function_entry_exit", "unattributed")
EXPECTED = {
    "selection-design.json": "bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f",
    "sharing-results.json": "57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa",
    "partial-results.json": "eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f",
    "kernel.c": "5832b52eaf1d5eb76e8087d47307feeccf74809cc0f22b288d111505851501cd",
    "evidence-archive": "8aa24f417ff266a2be2a850750defe06d8cbc46766b03d0ba67639f0a154cb83",
    "gcc10-bin": "07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a",
    "gcc15-bin": "114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470",
}
LABELS = {
    "Executed insns": "instructions", "RAM data reads": "ram_reads",
    "RAM writes": "ram_writes", "Flash data reads": "flash_reads",
    "Flash writes": "flash_writes", "Taken branches": "taken_branches",
    "BL insns": "bl",
}
SYMBOL_RE = re.compile(r"^\s*([0-9a-fA-F]+) <([^>]+)>:\s*$")
SITE_RE = re.compile(r"^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{4}\s+){1,2}|[0-9a-fA-F]{8}\s+)(.*)$")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json_lf(path, value):
    """Write stable JSON bytes across Windows and POSIX checkouts."""
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def require_hash(path, expected):
    if not Path(path).is_file():
        raise ValueError(f"missing input: {path}")
    found = sha256(path)
    if found != expected:
        raise ValueError(f"SHA256 mismatch: {path}: expected {expected}, got {found}")


def parse_disassembly(contents):
    """Parse objdump -d, keeping code separate from explicit literal/data rows."""
    instructions, literals = [], []
    symbol = None
    for line in contents.splitlines():
        match = SYMBOL_RE.match(line)
        if match:
            symbol = match.group(2)
            continue
        match = SITE_RE.match(line)
        if not match:
            continue
        address = int(match.group(1), 16)
        tail = match.group(3).strip()
        if not tail:
            continue
        mnemonic = tail.split(None, 1)[0].lower()
        if re.fullmatch(r"[0-9a-f]{8}", mnemonic):
            continue  # objdump's raw bytes for a data symbol
        if mnemonic.startswith("."):
            literals.append(address)
            continue
        if not re.fullmatch(r"[a-z][a-z0-9.]*", mnemonic):
            continue
        instructions.append({"address": address, "symbol": symbol,
                             "mnemonic": mnemonic, "operands": tail[len(mnemonic):].strip()})
    addresses = [item["address"] for item in instructions]
    if len(addresses) != len(set(addresses)):
        raise ValueError("duplicate instruction address in disassembly")
    return {"instructions": instructions, "literal_sites": literals}


def parse_event_log(contents, *, check_opcode_sum=True):
    values = {}
    for label, field in LABELS.items():
        matches = re.findall(r"^" + re.escape(label) + r":\s*(\S+)\s*$", contents, re.M)
        if len(matches) != 1 or not re.fullmatch(r"[0-9]+", matches[0]):
            raise ValueError(f"missing, duplicated or malformed counter: {label}")
        values[field] = int(matches[0])
    markers = re.findall(r"^TeamPlay: GPIOC\[0\] (raised|cleared) at cycle (\d+), insn count (\d+), pc = ([0-9a-fA-F]+)\s*$", contents, re.M)
    if len(markers) != 2 or [item[0] for item in markers] != ["raised", "cleared"]:
        raise ValueError("expected one raised and one cleared GPIO marker")
    if int(markers[0][2]) != 0 or int(markers[1][2]) != values["instructions"]:
        raise ValueError("marker instruction count differs from raw total")
    opcode = re.findall(r"^16:\s*(\d+),\s*\[([^\]]+)\]\s*$", contents, re.M)
    if len(opcode) != 1:
        raise ValueError("missing or duplicated opcode 16 statistics")
    fields = [item.strip() for item in opcode[0][1].split(",")]
    if len(fields) != 16 or any(not re.fullmatch(r"[0-9]+", field) for field in fields):
        raise ValueError("malformed opcode 16 subcounters")
    values["mul"] = int(fields[13])
    if check_opcode_sum:
        opcode_rows = re.findall(r"^\s*(\d+):\s*(\d+),\s*\[([^\]]+)\]\s*$", contents, re.M)
        if len(opcode_rows) != 64 or {int(row[0]) for row in opcode_rows} != set(range(64)):
            raise ValueError("missing or duplicated opcode statistics row")
        if sum(int(row[1]) for row in opcode_rows) != values["instructions"]:
            raise ValueError("opcode counts do not sum to raw instructions")
    # The simulator logs the closing GPIO STR in Executed insns. The frozen
    # measured total excludes precisely this one instruction; its RAM write is
    # already outside the region in the saved event counters.
    values["instructions"] -= 1
    if values["instructions"] < 0 or values["mul"] > values["instructions"]:
        raise ValueError("impossible instruction or MUL count")
    return values


def classify_sites(sites, assignments):
    """Require exactly one valid component for each supplied instruction site."""
    if hasattr(assignments, "items"):
        assignments = list(assignments.items())
    addresses = [site["address"] for site in sites]
    if len(addresses) != len(set(addresses)):
        raise ValueError("duplicate disassembly site")
    found = {}
    for address, name in assignments:
        if address in found:
            raise ValueError(f"duplicate classification at {address:#x}")
        if name not in COMPONENTS:
            raise ValueError(f"unknown component: {name}")
        found[address] = name
    if set(found) != set(addresses):
        raise ValueError(f"missing or extra classifications: missing={set(addresses)-set(found)}, extra={set(found)-set(addresses)}")
    return found


def reconcile(totals, components):
    names = [component["name"] for component in components]
    if sorted(names) != sorted(COMPONENTS):
        # The helper also permits small literal fixtures with a subset.
        if len(names) != len(set(names)) or any(name not in COMPONENTS for name in names):
            raise ValueError("duplicate or unknown component")
    if set(totals) != set(COUNTERS):
        raise ValueError("counter fields differ from schema")
    for field in COUNTERS:
        if type(totals[field]) is not int or totals[field] < 0:
            raise ValueError(f"malformed total {field}")
        for component in components:
            events = component["events"]
            if set(events) != set(COUNTERS) or type(events[field]) is not int or events[field] < 0:
                raise ValueError(f"malformed component counter {field}")
        actual = sum(component["events"][field] for component in components)
        if actual != totals[field]:
            raise ValueError(f"{field} sum mismatch: {actual} != {totals[field]}")
    for component in components:
        if component["events"]["mul"] > component["events"]["instructions"]:
            raise ValueError(f"MUL exceeds instructions in {component['name']}")


def parse_frame(contents):
    frames = re.findall(r"(?:^|:)probe_process\t(\d+)\tstatic\s*$", contents, re.M)
    if len(frames) != 1:
        raise ValueError("missing or duplicated probe_process frame report")
    return int(frames[0])


def direct_sp_events(sites, compiler):
    """Count direct SP LDR/STR sites on the established BLOCK=1 path.

    The only direct SP site off the path is GCC10 0x08000406, reached from
    the b=0 entry. All other direct SP sites are outside the 47-iteration
    history loop and outside data-dependent quantizer alternatives. The
    convolution loop executes once because every saved call passes b=1.
    """
    if compiler not in ("gcc10", "gcc15"):
        raise ValueError("unknown compiler for path proof")
    included, excluded = [], []
    for site in sites:
        if site["symbol"] != "probe_process" or not re.search(r"\[sp(?:,|\])", site["operands"]):
            continue
        address = site["address"]
        if compiler == "gcc10" and address == 0x8000406:
            excluded.append(address)
            continue
        if site["mnemonic"] not in ("ldr", "str"):
            raise ValueError(f"unrecognized direct SP memory instruction at {address:#x}")
        included.append(site)
    return {"reads": sum(site["mnemonic"] == "ldr" for site in included),
            "writes": sum(site["mnemonic"] == "str" for site in included),
            "included": included, "excluded": excluded}


def sp_component(compiler, address):
    """Assign executed direct SP sites to the phase reached at that PC."""
    if compiler == "gcc10":
        if address <= 0x800004e:
            return "copy_in"
        if address <= 0x800039c:
            return "convolution"
        if address == 0x80003b4:
            return "quantize_store"
        return "history_copy"
    if address <= 0x800049c:
        return "convolution"
    if address <= 0x80004c8:
        return "quantize_store"
    if address <= 0x800052a:
        return "convolution"  # stack-held history rotation for the next output
    return "history_copy"      # 0x532/0x534/0x536 seed the copy loop


def analyze(root, output):
    root = Path(root).resolve()
    output = Path(output).resolve()
    project = root.parents[2]
    inputs = {
        "selection-design.json": project / "research/fir-baseline/selection-design.json",
        "sharing-results.json": project / "research/fir-sharing-probe/results.json",
        "partial-results.json": root / "results.json",
        "kernel.c": root / "kernel.c",
        "evidence-archive": project / "research/fir-sharing-probe/independent-check/partial-direct-target-evidence.tar.gz",
        "gcc10-bin": root / "build/target/gcc10-b1/firmware.bin",
        "gcc15-bin": root / "build/target/gcc15-b1/firmware.bin",
    }
    for key, path in inputs.items():
        require_hash(path, EXPECTED[key])
    annotation = output / "assembly-notes.md"
    if not annotation.is_file():
        raise ValueError(f"missing supporting annotation: {annotation}")
    annotation_hash = sha256(annotation)
    result = json.loads(inputs["partial-results.json"].read_text(encoding="utf-8"))
    if result.get("design_sha256") != EXPECTED["selection-design.json"] or result.get("sharing_results_sha256") != EXPECTED["sharing-results.json"] or result.get("source_sha256", {}).get("kernel.c") != EXPECTED["kernel.c"]:
        raise ValueError("frozen result source identities differ")
    rows = []
    evidence_files = {}
    evidence_dir = output / "evidence"
    # Complete input validation precedes any write to the deliverable.
    staged = []
    for compiler in ("gcc10", "gcc15"):
        case = root / "build/target" / f"{compiler}-b1"
        old_rows = [row for row in result["rows"] if row["compiler"] == compiler and row["block"] == 1]
        if len(old_rows) != 1:
            raise ValueError(f"expected one frozen row for {compiler}/block1")
        old = old_rows[0]
        for filename, digest in old["artifacts"].items():
            require_hash(case / filename, digest)
        disassembly_text = (case / "firmware.disasm").read_text(encoding="utf-8")
        disassembly = parse_disassembly(disassembly_text)
        sites = disassembly["instructions"]
        mul_sites = [site for site in sites if site["mnemonic"] in ("mul", "muls")]
        if not mul_sites or any(site["symbol"] != "probe_process" for site in mul_sites):
            raise ValueError(f"MUL appears outside probe_process or absent in {compiler}")
        sp_path = direct_sp_events(sites, compiler)
        expected_sp = {"gcc10": (9, 9, [0x8000406]), "gcc15": (63, 84, [])}[compiler]
        if (sp_path["reads"], sp_path["writes"], sp_path["excluded"]) != expected_sp:
            raise ValueError(f"direct SP sites differ from reviewed BLOCK=1 path for {compiler}")
        sp_by_address = {site["address"]: sp_component(compiler, site["address"]) for site in sp_path["included"]}
        assignments = classify_sites(sites, [(site["address"],
                "convolution" if site in mul_sites else sp_by_address.get(site["address"], "unattributed")) for site in sites])
        totals = parse_event_log((case / "firmware.stderr").read_text(encoding="utf-8"))
        for counter in COUNTERS:
            if totals[counter] != old[counter]:
                raise ValueError(f"raw {compiler} {counter} differs from frozen result")
        frame = parse_frame((case / "kernel.su").read_text(encoding="utf-8"))
        stack_report = [item for item in old["stack_usage"] if item["function"] == "probe_process"]
        if len(stack_report) != 1 or frame != stack_report[0]["bytes"]:
            raise ValueError(f"frame differs from frozen result for {compiler}")
        probe = [site for site in sites if site["symbol"] == "probe_process"]
        symbols = [(int(match.group(1), 16), match.group(2)) for line in disassembly_text.splitlines()
                   if (match := SYMBOL_RE.match(line))]
        probe_start = next(address for address, name in symbols if name == "probe_process")
        probe_end = min(address for address, _ in symbols if address > probe_start)
        sp_sites = [site["address"] for site in probe if re.search(r"\[sp(?:,|\])", site["operands"])]
        zero = {name: 0 for name in COUNTERS}
        components = []
        refs = [f"evidence/{compiler}-b1/{filename}" for filename in ("firmware.disasm", "firmware.stderr", "kernel.su", "commands.json", "firmware.bin", "site-classification.json")]
        for name in COMPONENTS:
            events = zero.copy()
            basis = "residual" if name == "unattributed" else "exact-control-flow"
            if name == "convolution":
                # The aggregate MUL count belongs here because every MUL
                # instruction in the complete linked code lies in this body.
                events["instructions"] = totals["mul"]
                events["mul"] = totals["mul"]
            if name != "unattributed":
                selected = [site for site in sp_path["included"] if sp_component(compiler, site["address"]) == name]
                events["instructions"] += len(selected) * 257
                events["ram_reads"] += sum(site["mnemonic"] == "ldr" for site in selected) * 257
                events["ram_writes"] += sum(site["mnemonic"] == "str" for site in selected) * 257
            components.append({"name": name, "events": events, "basis": basis,
                               "evidence_refs": refs if any(events.values()) or name == "unattributed" else []})
        residual = next(component for component in components if component["name"] == "unattributed")
        residual["events"] = {key: totals[key] - sum(component["events"][key] for component in components if component["name"] != "unattributed") for key in COUNTERS}
        reconcile(totals, components)
        rows.append({"compiler": compiler, "block": 1, "binary_sha256": EXPECTED[f"{compiler}-bin"],
                     "method": "saved-evidence", "totals": totals, "components": components,
                     "static_diagnostics": {"probe_process_symbol_bytes": probe_end - probe_start,
                                            "compiler_frame_bytes": frame,
                                            "sp_relative_instruction_sites": len(sp_sites)},
                     "causal_status": "partial",
                     "limitations": [
                         "Saved events are aggregate counters without an execution PC trace.",
                         "All linked MUL sites are in convolution arithmetic, so the aggregate MUL count is assigned there.",
                         "Direct SP LDR/STR sites on the reviewed BLOCK=1 path execute once per 257 probe_process calls; GCC10's b=0-only site is excluded. This is an exact-control-flow count, not a trace.",
                         "Other dynamic instructions, memory and branch events remain unattributed; zero component counts do not imply an absent operation.",
                         "Frame bytes and stack-relative traffic do not establish register-allocation spill cause.",
                     ]})
        staged.append((compiler, case, old, disassembly, mul_sites, sp_sites, assignments, sp_path))
    output.mkdir(parents=True, exist_ok=True)
    for compiler, case, old, disassembly, mul_sites, sp_sites, assignments, sp_path in staged:
        target = evidence_dir / f"{compiler}-b1"
        target.mkdir(parents=True, exist_ok=True)
        for filename in ("commands.json", "firmware.bin", "firmware.c", "firmware.disasm", "firmware.map",
                         "firmware.stderr", "firmware.stdout", "firmware.su", "kernel.c", "kernel.su",
                         "probe_process.disasm", "size.txt"):
            shutil.copyfile(case / filename, target / filename)
            relative = f"evidence/{compiler}-b1/{filename}"
            evidence_files[relative] = sha256(target / filename)
        detail = {"compiler": compiler,
                  "all_mul_sites": [f"0x{site['address']:08x}" for site in mul_sites],
                  "sp_relative_probe_sites": [f"0x{address:08x}" for address in sp_sites],
                  "literal_pool_sites": [f"0x{address:08x}" for address in disassembly["literal_sites"]],
                  "classification": {f"0x{address:08x}": name for address, name in assignments.items()},
                  "classification_rule": "MUL and direct SP sites on the reviewed BLOCK=1 path receive component labels; other code sites are unattributed. Static labels alone do not assign dynamic counts.",
                  "phase_boundaries": ({"copy_in": "0x08000024..0x08000056",
                                        "convolution": "0x08000058..0x080003a0",
                                        "quantize_store": "0x080003a2..0x080003c2",
                                        "history_copy": "0x080003c4..0x080003ee; b=0 0x08000406 excluded"}
                                       if compiler == "gcc10" else
                                       {"copy_in": "0x08000024..0x0800004a",
                                        "convolution": "0x0800004c..0x080004a0 plus loop-carried stack rotation 0x080004cc..0x0800052a",
                                        "quantize_store": "0x080004a2..0x080004ca, with alternatives rejoining",
                                        "history_copy": "0x08000532..0x08000556"}),
                  "block1_path_proof": {
                      "calls": 257,
                      "basis": "process_stream advances the input pointer by 2 through the saved 257-sample input and passes r3=1 to every probe_process call; one copy-in and one convolution iteration per call; 47 history-copy iterations; quantizer alternatives rejoin before tail SP sites",
                      "direct_sp_reads_per_call": sp_path["reads"],
                      "direct_sp_writes_per_call": sp_path["writes"],
                      "excluded_zero_block_sites": [f"0x{address:08x}" for address in sp_path["excluded"]],
                      "executed_direct_sp_sites": [f"0x{site['address']:08x}" for site in sp_path["included"]]},
                  "source_artifact_hashes": old["artifacts"]}
        detail_path = target / "site-classification.json"
        write_json_lf(detail_path, detail)
        evidence_files[f"evidence/{compiler}-b1/site-classification.json"] = sha256(detail_path)
    command_record = {
        "analyzer_invocation": ["python", "research/fir-sharing-probe/compiler-explanation/analyze.py",
                                "--evidence-root", "research/fir-sharing-probe/partial-direct",
                                "--output-dir", "research/fir-sharing-probe/compiler-explanation"],
        "source_input_hashes": {key: sha256(path) for key, path in inputs.items()},
        "diagnostic_replay": "not performed",
        "measurement_convention": "raw Executed insns includes the closing GPIO STR; subtract one instruction, with no RAM-write adjustment, matching the frozen result parser",
        "provenance": "two restored BLOCK=1 cases from the versioned six-case target-evidence archive; each source artifact verified against the frozen results manifest",
    }
    command_path = evidence_dir / "command-record.json"
    write_json_lf(command_path, command_record)
    evidence_files["evidence/command-record.json"] = sha256(command_path)
    if sha256(annotation) != annotation_hash:
        raise ValueError("assembly-notes.md changed during analysis")
    evidence_files["assembly-notes.md"] = annotation_hash
    transcript = evidence_dir / "test-first-transcript.md"
    if transcript.is_file():
        evidence_files["evidence/test-first-transcript.md"] = sha256(transcript)
    report = {"schema_version": 1, "stage": "post-join compiler explanation",
              "source_results_sha256": EXPECTED["partial-results.json"],
              "evidence": evidence_files, "rows": rows}
    report_path = output / "accounting.json"
    write_json_lf(report_path, report)
    return report_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        path = analyze(args.evidence_root, args.output_dir)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"error: {error}\n")
    print(path)


if __name__ == "__main__":
    main()
