"""Helpers for the bounded fixed-block FIR intervention."""
from __future__ import annotations

import json
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from decimal import Decimal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARTIAL = ROOT / "research" / "fir-sharing-probe" / "partial-direct"
DESIGN = ROOT / "research" / "fir-baseline" / "selection-design.json"
RESULTS = PARTIAL / "results.json"
INTERVENTION_BUILD = HERE / "build" / "intervention"
ORIGINAL_FIRMWARE_SHA = {
    "gcc10": "07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a",
    "gcc15": "114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470",
}
ORIGINAL_STDERR_SHA = {
    "gcc10": "83e89fe00b57b5d585c47ac41d9d37235490c3155ef2121b60ab287d1a1e67ba",
    "gcc15": "22ca6390cac14083a9bc9660932583b928ba401d51568a36066395a4b6a247bc",
}
ORIGINAL_STDOUT_SHA = {
    "gcc10": "f2959cca91d1bfe09a3531b8825baa98da3cfe89610fe3c5849e60e5dc517275",
    "gcc15": "638c3396f461b242c9b7c7fad1dca7a5aa538ecc5118ef6419e111de5280da83",
}
ORIGINAL_EVENTS = {
    "gcc10": {"bl": 258, "flash_fetches": 198928, "flash_reads": 1032,
              "flash_writes": 0, "instructions": 198670, "mul": 2827,
              "ram_reads": 29304, "ram_writes": 17225, "raw_tick_delta": 258049,
              "taken_branches": 13622},
    "gcc15": {"bl": 258, "flash_fetches": 242748, "flash_reads": 1032,
              "flash_writes": 0, "instructions": 242490, "mul": 2827,
              "ram_reads": 43182, "ram_writes": 36500, "raw_tick_delta": 335153,
              "taken_branches": 13753},
}
ORIGINAL_WRAPPER_SHA = "b5e473d75aa16caa25242215100b13c5ad6b60471ececf9057bca5e99c4d971c"
ORIGINAL_COMMANDS_SHA = {
    "gcc10": "e42afadef20aca57f9516a6618cd2dd469ef3f6d339b667e92a1dee862e11162",
    "gcc15": "dbf40fc8accc06c9b69a2333670af5849385247caf0bdc1ab4c514b921d04463",
}
SOURCE_SHA = {
    "kernel.c": "5832b52eaf1d5eb76e8087d47307feeccf74809cc0f22b288d111505851501cd",
    "kernel.h": "bfc6b12af730bad80afd51ab9b235dc9bd4fa12f7ad394d4082155891b5b08b6",
    "run.py": "6da706332e5a7663f872d6bdb09fa216df795b4faabcd86146692bbb98359864",
}
STARTUP_SHA = "8859527adcb9943e5a648fcea01fdf8a2506ee27173b08fc55d82cac3a5b4054"
LINKER_SHA = "37fd6a919b5887762492571804dc8cdfbc5f87afadae4b31734297d52b55d4ca"
ENERGY_MICRO = {"nonmul": 964258, "mul": 1652455, "taken_branches": 2091986,
                "ram_reads": 1109833, "ram_writes": 650563, "flash_reads": 633621}
LABELS = {"Executed insns": "instructions", "RAM data reads": "ram_reads",
          "RAM writes": "ram_writes", "Flash data reads": "flash_reads",
          "Flash writes": "flash_writes", "Taken branches": "taken_branches",
          "Flash insn reads": "flash_fetches", "BL insns": "bl"}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_checker(root: Path = ROOT):
    return _load_module("fir_intervention_raw_checker",
                        root / "research" / "fir-sharing-probe" / "independent-check" / "check.py")


def _original_runner(root: Path = ROOT):
    return _load_module("fir_intervention_original_runner",
                        root / "research" / "fir-sharing-probe" / "partial-direct" / "run.py")


def _strict_events(raw_checker, stderr: str, stage_root: Path = HERE) -> dict:
    # Re-derive using the independent Task 5 verifier, which validates the
    # historical raw grammar and corrected instruction/fetch counters.
    verifier = _load_module("fir_intervention_panel_verifier", stage_root / "panel_verify.py")
    return verifier.rederive_raw_events(stderr)


def _cost(events: dict, samples: int) -> dict:
    counts = dict(events)
    counts["nonmul"] = events["instructions"] - events["mul"]
    if counts["nonmul"] < 0:
        raise ValueError("MUL count exceeds corrected instruction count")
    weighted = sum(ENERGY_MICRO[key] * counts[key] for key in ENERGY_MICRO)
    cycles = (events["instructions"] + events["ram_reads"] + events["ram_writes"] +
              events["flash_reads"] + 2 * events["taken_branches"] + events["bl"])
    return {"weighted_energy_micro_nj": weighted,
            "energy_nj": str(Decimal(weighted) / Decimal(1_000_000)),
            "energy_nj_per_output": str(Decimal(weighted) / Decimal(1_000_000 * samples)),
            "arm_zero_ws_cycles": cycles,
            "cycles_per_output": str(Decimal(cycles) / Decimal(samples))}


def _output_admission(raw_checker, stdout: str, h: list[int], samples: list[int]) -> dict:
    outputs = raw_checker.decode_words(stdout, "O", 16)
    history = raw_checker.decode_words(stdout, "H", 64)
    guards = raw_checker.record(stdout, "G")
    allocation = raw_checker.record(stdout, "M")
    expected_outputs = raw_checker.reference(h, samples)
    expected_history = raw_checker.retained_state(h, samples)
    if outputs != expected_outputs:
        raise ValueError("target outputs differ from independent arbitrary-precision reference")
    if history != expected_history:
        raise ValueError("target retained history differs from independent reference")
    if guards != "5a5a5a5a" * 4 + "5a5a" * 4:
        raise ValueError("target output/state guards changed")
    if int(allocation, 16) != 98:
        raise ValueError("target state allocation differs from fixed BLOCK=1 ABI")
    return {"outputs_verified": len(outputs), "history_verified": True,
            "guards_verified": True, "state_allocation_bytes": int(allocation, 16)}


def _run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {command}\n{result.stdout}\n{result.stderr}")
    return result


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _new_attempt_directory(base: Path, identity: str) -> Path:
    """Create the next immutable attempt directory for one scientific identity."""
    parent = Path(base) / identity
    parent.mkdir(parents=True, exist_ok=True)
    for number in range(1, 10000):
        candidate = parent / f"attempt-{number:03d}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise RuntimeError(f"attempt directory limit exhausted for {identity}")


def _reject_incomplete_executed_attempts(parent: Path) -> None:
    if not parent.is_dir():
        return
    for attempt in parent.glob("attempt-*"):
        receipt = attempt / "execution-receipt.json"
        evidence = attempt / "evidence.json"
        raw_exists = (attempt / "firmware.stdout").exists() or (attempt / "firmware.stderr").exists()
        if receipt.exists():
            record = json.loads(receipt.read_text())
            if record.get("simulator_started"):
                raise RuntimeError(f"incomplete executed attempt requires offline recovery: {attempt}")
        elif raw_exists:
            raise RuntimeError(f"prior executed attempt requires offline recovery: {attempt}")


def _canonical_stack_paths(stack: dict, attempt_directory: Path, relative_directory: str,
                           fixture_compiler: str | None = None,
                           project_root: Path | None = None) -> dict:
    canonical = json.loads(json.dumps(stack))
    rel_parts = Path(relative_directory).parts
    expected_names = {"file": {"kernel.su", "firmware.su"},
                      "source": {"kernel.c", "firmware.c"}}
    for frame in canonical.get("frames", []):
        for field, allowed in expected_names.items():
            value = frame.get(field)
            if value in {None, "linked disassembly", "prologue"}:
                continue
            path = Path(value)
            if path.name not in allowed:
                raise ValueError("stack diagnostic path has an unexpected file identity")
            if path.is_absolute():
                if tuple(path.parts[-len(rel_parts)-1:-1]) != rel_parts:
                    archive = ("research", "fir-sharing-probe", "partial-direct", "build",
                               "target", f"{fixture_compiler}-b1")
                    if fixture_compiler not in {"gcc10", "gcc15"} or \
                            tuple(path.parts[-len(archive)-1:-1]) != archive:
                        raise ValueError("stack diagnostic path is outside the admitted attempt")
                    archived_file = project_root.joinpath(*archive, path.name) if project_root else None
                    if archived_file is None or not archived_file.is_file():
                        raise ValueError("historical fixture stack diagnostic has no copied source")
            elif tuple(path.parts[:-1]) != rel_parts:
                raise ValueError("stack diagnostic relative path differs from admitted attempt")
            if attempt_directory.name != rel_parts[-1]:
                raise ValueError("stack path normalization target differs from attempt directory")
            frame[field] = (Path(*rel_parts) / path.name).as_posix()
    return canonical


def _compile_and_measure(label: str, specialized: bool, samples: list[int],
                         h: list[int], simulator: Path, compiler: Path,
                         compiler_identity: dict, raw_checker, run_kind: str) -> dict:
    tag = f"{run_kind}-{label}-{'specialized' if specialized else 'general'}"
    _reject_incomplete_executed_attempts(INTERVENTION_BUILD / tag)
    directory = _new_attempt_directory(INTERVENTION_BUILD, tag)
    original_kernel = (PARTIAL / "kernel.c").read_bytes()
    kernel = specialize_kernel(original_kernel) if specialized else original_kernel
    (directory / "kernel.c").write_bytes(kernel)
    shutil.copyfile(PARTIAL / "kernel.h", directory / "kernel.h")
    shutil.copyfile(ROOT / "research" / "fir-baseline" / "startup.s", directory / "startup.s")
    shutil.copyfile(ROOT / "research" / "fir-baseline" / "link.ld", directory / "link.ld")
    firmware = _original_runner().firmware(samples, 1)
    (directory / "firmware.c").write_text(firmware)
    flags = ["-mcpu=cortex-m0", "-mthumb", "-std=c11", "-ffreestanding", "-fno-builtin",
             "-ffunction-sections", "-fdata-sections", "-g0"]
    compile_flags = [*flags, "-O2", "-Wall", "-Wextra", "-Werror", "-fstack-usage"]
    common = [str(compiler), *compile_flags, "-DBLOCK=1", "-I", str(directory)]
    commands, command_log = [], []

    def invoke(argv):
        argv = [str(x) for x in argv]
        commands.append(argv)
        result = _run_command(argv)
        command_log.append({"argv": argv,
                            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()})
        return result

    objects = []
    # Keep original partial-direct compilation and link order exactly.
    for source_name, object_name in (("kernel.c", "kernel.o"),
                                     ("firmware.c", "firmware.o"),
                                     ("startup.s", "startup.o")):
        source, output = directory / source_name, directory / object_name
        invoke([*common, "-c", source, "-o", output])
        objects.append(output)
    elf = directory / "firmware.elf"
    invoke([str(compiler), *flags, "-nostdlib", "-T", directory / "link.ld",
            "-Wl,--gc-sections", f"-Wl,-Map={directory / 'firmware.map'}",
            *objects, "-lgcc", "-o", elf])
    objcopy = compiler.with_name("arm-none-eabi-objcopy")
    objdump = compiler.with_name("arm-none-eabi-objdump")
    size = compiler.with_name("arm-none-eabi-size")
    binary = directory / "firmware.bin"
    invoke([objcopy, "-O", "binary", elf, binary])
    disassembly = invoke([objdump, "-d", elf]).stdout
    (directory / "firmware.disasm").write_text(disassembly)
    match = re.search(r"^[0-9a-f]+ <probe_process>:\n.*?(?=^[0-9a-f]+ <|\Z)",
                      disassembly, re.M | re.S)
    if match is None:
        raise ValueError("probe_process missing from target disassembly")
    (directory / "probe_process.disasm").write_text(match[0])
    sim_argv = [str(simulator), "-s", str(binary.resolve())]
    commands.append(sim_argv)
    receipt_path = directory / "execution-receipt.json"
    receipt = {"identity": {"run_kind": run_kind, "compiler": label,
                            "variant": "specialized" if specialized else "general",
                            "block": 1, "samples": len(samples)},
               "commands_before_simulator": commands[:-1], "simulator_argv": sim_argv,
               "simulator_started": True, "status": "simulator-intent"}
    _write_json(receipt_path, receipt)
    simulated = _run_command(sim_argv)
    (directory / "firmware.stdout").write_text(simulated.stdout)
    (directory / "firmware.stderr").write_text(simulated.stderr)
    receipt.update({"status": "simulator-complete", "returncode": simulated.returncode,
                    "stdout_sha256": _sha(directory / "firmware.stdout"),
                    "stderr_sha256": _sha(directory / "firmware.stderr")})
    _write_json(receipt_path, receipt)
    size_text = invoke([size, elf]).stdout
    (directory / "size.txt").write_text(size_text)
    receipt["status"] = "complete"
    _write_json(receipt_path, receipt)
    _write_json(directory / "commands.json", {"commands": commands, "toolchain": compiler_identity,
                                               "simulator_sha256": _sha(simulator)})
    events = _strict_events(raw_checker, simulated.stderr)
    admission = _output_admission(raw_checker, simulated.stdout, h, samples)
    costs = _cost(events, len(samples))
    stack_usage = []
    for su in sorted(directory.glob("*.su")):
        stack_usage.extend({"file": su.name, "function": name, "bytes": int(n), "kind": kind}
                           for name, n, kind in re.findall(r"\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)", su.read_text()))
    verifier = _load_module("fir_intervention_panel_verifier", HERE / "panel_verify.py")
    layout = verifier._elf_layout(directory / "firmware.elf")
    binary_binding = verifier._audit_binary_binding(directory / "firmware.elf", binary,
                                                    disassembly, layout, samples)
    stack = verifier._independent_stack_chain([directory / "kernel.su", directory / "firmware.su"],
                                               disassembly, layout["symbols"])
    artifact_hashes = {p.name: _sha(p) for p in sorted(directory.iterdir()) if p.is_file()}
    record = {"identity": {"run_kind": run_kind, "compiler": label,
                           "variant": "specialized" if specialized else "general",
                           "block": 1, "samples": len(samples)},
              "directory": directory.relative_to(HERE).as_posix(),
              "compiler": compiler_identity, "simulator_path": str(simulator.resolve()),
              "simulator_sha256": _sha(simulator), "simulation": {
                  "returncode": simulated.returncode,
                  "stdout_sha256": _sha(directory / "firmware.stdout"),
                  "stderr_sha256": _sha(directory / "firmware.stderr")},
              "commands": commands, "command_log": command_log,
              "instruction_subset": verifier.instruction_subset(disassembly),
              "kernel_sha256": _sha(directory / "kernel.c"),
              "kernel_delta_verified": verify_specialization_delta(original_kernel, kernel)
                 if specialized else kernel == original_kernel,
              "firmware_source_sha256": _sha(directory / "firmware.c"),
              "input_sha256": hashlib.sha256(",".join(map(str, samples)).encode()).hexdigest(),
              "source_fixture_sha256": {name: _sha(directory / name)
                                         for name in ("kernel.h", "startup.s", "link.ld")},
              "artifacts": artifact_hashes, "events": events, "cost": costs,
              "admission": admission, "stack_usage": stack_usage,
              "binary_binding": binary_binding, "stack": stack,
              "memory": {"initial_sp": layout["initial_sp"], "ram_end": layout["ram_end"],
                         "flash_end": layout["flash_end"]},
              "firmware_sha256": _sha(binary),
              "size_output": size_text,
              "elf_size_bytes": _elf_sections(directory / "firmware.elf"),
              "assembly_review_status": "pending independent Sol review"}
    _write_json(directory / "evidence.json", record)
    return record


def _elf_sections(path: Path) -> dict:
    data = path.read_bytes()
    if data[:7] != b"\x7fELF\x01\x01\x01":
        raise ValueError("expected little-endian ELF32 target")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", data)
    section_offset, section_size, section_count = header[6], header[11], header[12]
    sections = [struct.unpack_from("<IIIIIIIIII", data, section_offset + i * section_size)
                for i in range(section_count)]
    shstr = sections[header[13]]
    names = data[shstr[4]:shstr[4] + shstr[5]]
    result = {}
    for section in sections:
        name = names[section[0]:names.index(b"\0", section[0])].decode() if section[0] else ""
        if section[1] != 8 and section[5]:
            result[name] = section[5]
    return result


def _instruction_subset(disassembly: str) -> list[str]:
    allowed = set("adc adcs add adds adr and ands asr asrs bic bics bl blx bx cmn cmp "
                  "eor eors ldm ldmia ldr ldrb ldrh ldrsb ldrsh lsl lsls lsr lsrs mov "
                  "movs mul muls mvn mvns neg negs nop orr orrs pop push rev rev16 revsh "
                  "ror rors rsb rsbs sbc sbcs stm stmia str strb strh sub subs sxtb sxth "
                  "tst uxtb uxth".split())
    function, seen = "", set()
    for line in disassembly.splitlines():
        label = re.match(r"^[0-9a-f]+ <([^>]+)>:", line)
        if label:
            function = label[1]
        fields = line.split("\t")
        if len(fields) < 3 or not re.fullmatch(r"[0-9a-f]{4}(?: [0-9a-f]{4})?", fields[1].strip()):
            continue
        mnemonic = fields[2].split()[0].split(".")[0]
        if mnemonic == "svc" and function == "Reset_Handler":
            continue
        if not (mnemonic in allowed or re.fullmatch(r"b(eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?", mnemonic)):
            raise ValueError(f"unsupported instruction in {function}: {mnemonic}")
        seen.add(mnemonic)
    if not seen:
        raise ValueError("no decoded instructions in target disassembly")
    return sorted(seen)


def _toolchain_identity(compiler: Path, expected: dict) -> dict:
    actual = {"path": str(compiler.resolve()), "sha256": _sha(compiler),
              "version": _run_command([compiler, "--version"]).stdout.splitlines()[0]}
    if {k: actual[k] for k in ("sha256", "version")} != expected:
        raise RuntimeError(f"{compiler} identity differs from frozen compiler")
    tools = {}
    for name in ("as", "ld"):
        path = Path(_run_command([compiler, f"-print-prog-name={name}"]).stdout.strip())
        tools[name] = {"path": str(path.resolve()), "sha256": _sha(path)}
    for name in ("objcopy", "objdump", "size", "readelf", "nm"):
        path = compiler.with_name(f"arm-none-eabi-{name}")
        tools[name] = {"path": str(path.resolve()), "sha256": _sha(path)}
    libgcc = Path(_run_command([compiler, "-mcpu=cortex-m0", "-mthumb",
                                "-print-file-name=libgcc.a"]).stdout.strip())
    tools["libgcc"] = {"path": str(libgcc.resolve()), "sha256": _sha(libgcc),
                       "query_flags": ["-mcpu=cortex-m0", "-mthumb"]}
    return {**actual, "tools": tools}


def _anchor_evidence(raw_checker, x: list[int], h: list[int], label: str,
                     root: Path = ROOT) -> dict:
    partial = root / "research" / "fir-sharing-probe" / "partial-direct"
    saved = json.loads((partial / "results.json").read_text())
    original_row = next(row for row in saved["rows"]
                        if row["compiler"] == label and row["block"] == 1)
    original_dir = partial / original_row["directory"]
    if _sha(original_dir / "firmware.bin") != ORIGINAL_FIRMWARE_SHA[label]:
        raise ValueError(f"frozen {label} original general firmware binary hash mismatch")
    if _sha(original_dir / "firmware.stderr") != ORIGINAL_STDERR_SHA[label]:
        raise ValueError(f"frozen {label} original raw event bytes hash mismatch")
    if _sha(original_dir / "firmware.stdout") != ORIGINAL_STDOUT_SHA[label]:
        raise ValueError(f"frozen {label} original stdout bytes hash mismatch")
    events = _strict_events(raw_checker, (original_dir / "firmware.stderr").read_text())
    if events != ORIGINAL_EVENTS[label]:
        raise ValueError(f"frozen {label} strict raw event vector differs from anchor")
    admission = _output_admission(raw_checker, (original_dir / "firmware.stdout").read_text(), h, x)
    for name in ("firmware.bin", "firmware.stderr", "firmware.stdout"):
        expected_hash = original_row["artifacts"].get(name)
        if expected_hash is not None and _sha(original_dir / name) != expected_hash:
            raise ValueError(f"original result record disagrees with frozen {label} {name}")
    return {"firmware_sha256": ORIGINAL_FIRMWARE_SHA[label],
            "stderr_sha256": ORIGINAL_STDERR_SHA[label],
            "stdout_sha256": ORIGINAL_STDOUT_SHA[label], "events": events,
            "admission": admission,
            "modeled_energy_nj": str(_cost(events, len(x))["energy_nj"]),
            "saved_directory": original_row["directory"]}


def _project_root_from_stage(stage_root: Path) -> Path:
    stage_root = stage_root.resolve()
    if stage_root.name != "fir-upgrades" or stage_root.parent.name != "research":
        raise ValueError("intervention root must be a relocated research/fir-upgrades tree")
    return stage_root.parents[1]


def _toolchain_admission(row: dict, label: str, verifier, stage_root: Path) -> None:
    baseline = row["compiler"]
    if baseline.get("sha256") != verifier.COMPILER_SHA256[label]:
        raise ValueError("saved compiler hash differs from frozen compiler identity")
    expected_version = "10.3.1" if label == "gcc10" else "15.2.1"
    if expected_version not in baseline.get("version", ""):
        raise ValueError("saved compiler version differs from frozen compiler identity")
    tools = baseline.get("tools", {})
    if set(tools) != {"as", "ld", "objcopy", "objdump", "size", "readelf", "nm", "libgcc"}:
        raise ValueError("saved toolchain inventory is incomplete")
    expected_hashes = {**verifier.BINUTIL_SHA256[label], "libgcc": verifier.LIBGCC_SHA256[label]}
    for name, digest in expected_hashes.items():
        if tools[name].get("sha256") != digest:
            raise ValueError(f"saved pinned tool identity differs: {label}/{name}")
    size = tools["size"]
    if not re.fullmatch(r"[0-9a-f]{64}", size.get("sha256", "")):
        raise ValueError("saved size utility identity is malformed")
    for item in tools.values():
        if not Path(item.get("path", "")).is_absolute():
            raise ValueError("saved tool path must be absolute")
    protocol = json.loads((stage_root / "panel-protocol.json").read_text())
    if baseline.get("path") != protocol["toolchain_identities"][label]["path"]:
        raise ValueError("saved compiler path differs from frozen toolchain manifest")
    for name in ("as", "ld", "objcopy", "objdump", "size", "readelf", "nm"):
        allowed_names = {f"arm-none-eabi-{name}"}
        if name in {"as", "ld"}:
            allowed_names.add(name)
        if Path(tools[name]["path"]).name not in allowed_names:
            raise ValueError(f"saved tool path does not identify {name}")
    if Path(tools["libgcc"]["path"]).name != "libgcc.a":
        raise ValueError("saved libgcc path does not identify the runtime archive")
    if tools["libgcc"].get("query_flags") != ["-mcpu=cortex-m0", "-mthumb"]:
        raise ValueError("saved libgcc query did not select the frozen Cortex-M0 ABI")


def _admit_commands(row: dict, directory: Path, stage_root: Path, verifier) -> None:
    commands = row.get("commands")
    if not isinstance(commands, list) or len(commands) != 8:
        raise ValueError("exact eight-command inventory required")
    label = row["identity"]["compiler"]
    compiler = row["compiler"].get("path")
    if not isinstance(compiler, str) or not Path(compiler).is_absolute():
        raise ValueError("compiler command path is malformed")
    if row.get("fixture_kind") == "historical-control":
        if _sha(directory / "commands.json") != ORIGINAL_COMMANDS_SHA[label] or \
                json.loads((directory / "commands.json").read_text()) != commands:
            raise ValueError("historical fixture command record differs from frozen anchor")
        if len(commands) != 8 or commands[0][0] != compiler or commands[3][0] != compiler or \
                [Path(command[0]).name for command in commands[4:]] != [
                    "arm-none-eabi-objcopy", "arm-none-eabi-objdump", "sim_main", "arm-none-eabi-size"]:
            raise ValueError("historical fixture command sequence differs from frozen runner")
        if commands[0][1:10] != ["-mcpu=cortex-m0", "-mthumb", "-std=c11", "-ffreestanding",
                                  "-fno-builtin", "-ffunction-sections", "-fdata-sections", "-g0", "-O2"]:
            raise ValueError("historical fixture command options differ from frozen flags")
        return
    # The seven compiler/binutils invocations match the historical build order;
    # simulation is the eighth command and occurs before the size diagnostic.
    actual_case = Path(commands[0][commands[0].index("-I") + 1])
    expected_case_suffix = f"/research/fir-upgrades/{row['directory']}"
    if not str(actual_case).endswith(expected_case_suffix):
        raise ValueError("command case directory does not match saved stage identity")
    flags = ["-mcpu=cortex-m0", "-mthumb", "-std=c11", "-ffreestanding", "-fno-builtin",
             "-ffunction-sections", "-fdata-sections", "-g0"]
    compile_flags = [*flags, "-O2", "-Wall", "-Wextra", "-Werror", "-fstack-usage"]
    common = [compiler, *compile_flags, "-DBLOCK=1", "-I", str(actual_case)]
    expected = []
    objects = []
    for source, obj in (("kernel.c", "kernel.o"), ("firmware.c", "firmware.o"),
                        ("startup.s", "startup.o")):
        expected.append([*common, "-c", str(actual_case / source), "-o", str(actual_case / obj)])
        objects.append(str(actual_case / obj))
    elf, binary = actual_case / "firmware.elf", actual_case / "firmware.bin"
    expected.append([compiler, *flags, "-nostdlib", "-T", str(actual_case / "link.ld"),
                     "-Wl,--gc-sections", f"-Wl,-Map={actual_case / 'firmware.map'}",
                     *objects, "-lgcc", "-o", str(elf)])
    tools = row["compiler"]["tools"]
    expected.extend([
        [tools["objcopy"]["path"], "-O", "binary", str(elf), str(binary)],
        [tools["objdump"]["path"], "-d", str(elf)],
        [row["simulator_path"], "-s", str(binary.resolve())],
        [tools["size"]["path"], str(elf)],
    ])
    if commands != expected:
        raise ValueError("saved command order/options differ from frozen build grammar")
    if not str(row.get("simulator_path", "")).endswith("/research/fir-baseline/build/thumbulator/sim_main"):
        raise ValueError("saved simulator path differs from frozen fixture location")
    if row.get("simulator_sha256") != verifier.SIMULATOR_SHA256:
        raise ValueError("saved simulator identity differs from pinned fixture")
    if row.get("fixture_kind") == "historical-control":
        return
    logs = row.get("command_log")
    expected_logged = commands[:6] + [commands[7]]
    if not isinstance(logs, list) or len(logs) != 7 or [x.get("argv") for x in logs] != expected_logged:
        raise ValueError("saved compiler/binutils command log differs from argv inventory")
    for item in logs:
        if not re.fullmatch(r"[0-9a-f]{64}", item.get("stdout_sha256", "")) or not re.fullmatch(
                r"[0-9a-f]{64}", item.get("stderr_sha256", "")):
            raise ValueError("saved command output digest is malformed")
    sim = row.get("simulation", {})
    if sim.get("returncode") != 0 or sim.get("stdout_sha256") != row["artifacts"].get("firmware.stdout") or \
            sim.get("stderr_sha256") != row["artifacts"].get("firmware.stderr"):
        raise ValueError("saved simulator completion/raw output binding differs")
    record = json.loads((directory / "commands.json").read_text())
    if record.get("commands") != commands or record.get("toolchain") != row["compiler"] or \
            record.get("simulator_sha256") != row["simulator_sha256"]:
        raise ValueError("commands.json differs from independently admitted command identity")


def audit_row(row: dict, copied_root: Path) -> dict:
    """Admit one saved target row without invoking or locating any target tool."""
    stage = Path(copied_root).resolve()
    project_root = _project_root_from_stage(stage)
    identity = row.get("identity", {})
    if set(identity) != {"run_kind", "compiler", "variant", "block", "samples"}:
        raise ValueError("saved row identity fields are incomplete or unexpected")
    run_kind, label, variant = identity["run_kind"], identity["compiler"], identity["variant"]
    if run_kind not in {"performance", "correctness"} or label not in {"gcc10", "gcc15"} or \
            variant not in {"general", "specialized"} or identity["block"] != 1:
        raise ValueError("saved row identity is outside the finite Task 6 contract")
    expected_samples = 257 if run_kind == "performance" else 361
    if identity["samples"] != expected_samples:
        raise ValueError("saved row sample count differs from run kind")
    directory = (stage / row.get("directory", "")).resolve()
    if not directory.is_relative_to(stage) or not directory.is_dir():
        raise ValueError("saved attempt path escapes or is missing under stage root")
    required = {"kernel.c", "kernel.h", "firmware.c", "startup.s", "link.ld", "firmware.elf",
                "firmware.bin", "firmware.disasm", "firmware.map", "firmware.stdout",
                "firmware.stderr", "commands.json", "kernel.su", "firmware.su"}
    artifacts = row.get("artifacts")
    if not isinstance(artifacts, dict) or not required <= set(artifacts):
        raise ValueError("saved row artifact inventory is incomplete")
    for name, digest in artifacts.items():
        if Path(name).name != name or name in {".", ".."}:
            raise ValueError("artifact filename escapes attempt directory")
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError(f"required saved artifact missing or escaping: {name}")
        if _sha(path) != digest:
            raise ValueError(f"saved artifact hash differs: {name}")
    receipt_path = directory / "execution-receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("identity") != identity or receipt.get("simulator_started") is not True or \
                receipt.get("status") != "complete" or receipt.get("returncode") != 0:
            raise ValueError("execution receipt does not record a completed simulator run")
        if receipt.get("stdout_sha256") != artifacts.get("firmware.stdout") or \
                receipt.get("stderr_sha256") != artifacts.get("firmware.stderr"):
            raise ValueError("execution receipt raw output digests differ from saved outputs")
    source_dir = project_root / "research/fir-sharing-probe/partial-direct"
    runner_path = source_dir / "run.py"
    if _sha(runner_path) != SOURCE_SHA["run.py"]:
        raise ValueError("original wrapper source runner hash differs")
    original = _original_runner(project_root)
    design = json.loads((project_root / "research/fir-baseline/selection-design.json").read_text())
    h = design["filters"]["speech_minphase48"]["coefficients"]
    if _sha(project_root / "research/fir-baseline/selection-design.json") != original.DESIGN_SHA:
        raise ValueError("frozen input/design identity differs")
    adc = design["inputs"]["adc_raw"][:257]
    samples = adc if run_kind == "performance" else original.edge_input(h)
    if len(samples) != expected_samples:
        raise ValueError("frozen input stream cardinality differs")
    kernel = (directory / "kernel.c").read_bytes()
    original_kernel = (source_dir / "kernel.c").read_bytes()
    if _sha(source_dir / "kernel.c") != SOURCE_SHA["kernel.c"]:
        raise ValueError("frozen general kernel hash differs")
    if variant == "general" and kernel != original_kernel:
        raise ValueError("general row kernel bytes differ from frozen source")
    if variant == "specialized" and not verify_specialization_delta(original_kernel, kernel):
        raise ValueError("specialized row violates literal-b=1 source contract")
    expected_kernel_sha = hashlib.sha256(kernel).hexdigest()
    expected_delta = (kernel == original_kernel if variant == "general" else
                      verify_specialization_delta(original_kernel, kernel))
    if row.get("kernel_sha256") != expected_kernel_sha or row.get("kernel_delta_verified") is not expected_delta:
        raise ValueError("serialized kernel identity/delta differs from frozen source bytes")
    for filename, digest in (("kernel.h", SOURCE_SHA["kernel.h"]),
                             ("startup.s", STARTUP_SHA), ("link.ld", LINKER_SHA)):
        expected = source_dir / filename if filename in {"kernel.h"} else \
            project_root / "research/fir-baseline" / filename
        if _sha(directory / filename) != digest or _sha(expected) != digest:
            raise ValueError(f"saved fixture source differs: {filename}")
    expected_fixture_hashes = {name: _sha(directory / name)
                               for name in ("kernel.h", "startup.s", "link.ld")}
    if row.get("source_fixture_sha256") != expected_fixture_hashes:
        raise ValueError("serialized fixture source hashes differ from admitted files")
    expected_wrapper = original.firmware(samples, 1).encode()
    if (directory / "firmware.c").read_bytes() != expected_wrapper:
        raise ValueError("saved wrapper differs from frozen original for exact input/block")
    if row.get("firmware_source_sha256") != _sha(directory / "firmware.c"):
        raise ValueError("serialized wrapper hash differs from saved wrapper")
    expected_input_sha = hashlib.sha256(",".join(map(str, samples)).encode()).hexdigest()
    if row.get("input_sha256") != expected_input_sha:
        raise ValueError("saved input digest differs from frozen stream")
    label = identity["compiler"]
    baseline = json.loads((source_dir / "results.json").read_text())
    verifier = _load_module("fir_intervention_panel_verifier", stage / "panel_verify.py")
    _toolchain_admission(row, label, verifier, stage)
    if row.get("compiler", {}).get("sha256") != baseline["compilers"][label]["sha256"]:
        raise ValueError("compiler identity differs from historical pinned compiler")
    if row.get("simulator_sha256") != baseline["simulator_sha256"]:
        raise ValueError("simulator identity differs from frozen fixture")
    _admit_commands(row, directory, stage, verifier)
    if receipt_path.exists() and receipt.get("simulator_argv") != row["commands"][6]:
        raise ValueError("execution receipt simulator command differs from admitted argv")
    checker = _raw_checker(project_root)
    events = _strict_events(checker, (directory / "firmware.stderr").read_text(), stage)
    if events != row.get("events"):
        raise ValueError("saved raw event vector differs from row")
    cost = _cost(events, expected_samples)
    if cost != row.get("cost"):
        raise ValueError("saved energy/cycle summary differs from corrected raw events")
    admission = _output_admission(checker, (directory / "firmware.stdout").read_text(), h, samples)
    if admission != row.get("admission"):
        raise ValueError("saved O/H/G/M admission differs from independent reference")
    disassembly = (directory / "firmware.disasm").read_text()
    mnemonics = verifier.instruction_subset(disassembly)
    if mnemonics != row.get("instruction_subset"):
        raise ValueError("saved instruction subset differs from linked disassembly")
    layout = verifier._elf_layout(directory / "firmware.elf")
    binary_binding = verifier._audit_binary_binding(directory / "firmware.elf", directory / "firmware.bin",
                                                   disassembly, layout, samples)
    stack = verifier._independent_stack_chain([directory / "kernel.su", directory / "firmware.su"],
                                               disassembly, layout["symbols"])
    fixture_compiler = label if row.get("fixture_kind") == "historical-control" else None
    normalized_stack = _canonical_stack_paths(stack, directory, row["directory"],
                                               fixture_compiler, project_root)
    recorded_stack = _canonical_stack_paths(row.get("stack", {}), directory, row["directory"],
                                             fixture_compiler, project_root)
    if row.get("binary_binding") != binary_binding or recorded_stack != normalized_stack:
        raise ValueError("saved ELF/binary/stack resource summary differs from independent reconstruction")
    expected_sections = _elf_sections(directory / "firmware.elf")
    if row.get("elf_size_bytes") != expected_sections:
        raise ValueError("serialized ELF section sizes differ from the actual ELF")
    expected_size_text = (directory / "size.txt").read_text()
    if row.get("size_output") != expected_size_text:
        raise ValueError("serialized size diagnostic differs from its saved artifact")
    expected_stack_usage = []
    for su in sorted((directory / "kernel.su", directory / "firmware.su")):
        expected_stack_usage.extend({"file": su.name, "function": name, "bytes": int(n), "kind": kind}
                                   for name, n, kind in re.findall(
                                       r"\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)", su.read_text()))
    if row.get("stack_usage") != expected_stack_usage:
        raise ValueError("serialized stack usage diagnostics differ from saved .su files")
    actual_binary_sha = _sha(directory / "firmware.bin")
    if row.get("firmware_sha256") != actual_binary_sha:
        raise ValueError("saved firmware binary digest differs from actual firmware.bin")
    if row.get("memory") != {"initial_sp": layout["initial_sp"], "ram_end": layout["ram_end"],
                             "flash_end": layout["flash_end"]}:
        raise ValueError("saved ELF memory summary differs from independent reconstruction")
    anchor_admitted = True
    if run_kind == "performance" and variant == "general":
        anchor = _anchor_evidence(checker, samples, h, label, project_root)
        expected_anchor = {"expected_binary_sha256": anchor["firmware_sha256"],
                           "observed_binary_sha256": row.get("firmware_sha256"),
                           "expected_events": anchor["events"], "observed_events": events,
                           "binary_match": row.get("firmware_sha256") == anchor["firmware_sha256"],
                           "events_match": events == anchor["events"]}
        if row.get("anchor_comparison") != expected_anchor:
            raise ValueError("saved general-control anchor flags differ from independent comparison")
        anchor_admitted = expected_anchor["binary_match"] and expected_anchor["events_match"]
    return {"identity": identity, "events": events, "cost": cost, "admission": admission,
            "instruction_subset": mnemonics, "binary_binding": binary_binding,
            "stack": stack, "memory": row["memory"], "anchor_admitted":
            anchor_admitted}


def derive_comparisons(rows: list[dict]) -> dict:
    indexed = {(row["identity"]["compiler"], row["identity"]["variant"]): row for row in rows}
    if len(indexed) != 4:
        raise ValueError("comparisons require exactly four unique performance conditions")
    deltas = {}
    energies = {}
    for compiler in ("gcc10", "gcc15"):
        general, specialized = indexed[(compiler, "general")], indexed[(compiler, "specialized")]
        for row in (general, specialized):
            if _cost(row["events"], row["identity"]["samples"]) != row["cost"]:
                raise ValueError("comparison row cost differs from raw event reconstruction")
        event_delta = {key: general["events"][key] - specialized["events"][key]
                       for key in sorted(general["events"])}
        deltas[compiler] = {"events_general_minus_specialized": event_delta,
                            "cycles_general_minus_specialized":
                            general["cost"]["arm_zero_ws_cycles"] - specialized["cost"]["arm_zero_ws_cycles"],
                            "energy_general_minus_specialized_nj": str(
                                Decimal(general["cost"]["energy_nj"]) -
                                Decimal(specialized["cost"]["energy_nj"])),
                            "general_nj_per_output": general["cost"]["energy_nj_per_output"],
                            "specialized_nj_per_output": specialized["cost"]["energy_nj_per_output"],
                            "resources": {
                                "general": {"stack_peak_bytes": general["stack"]["maximum_live_stack_bytes"],
                                             "memory": general["memory"],
                                             "state_allocation_bytes": general["admission"]["state_allocation_bytes"],
                                             "instruction_subset": general["instruction_subset"]},
                                "specialized": {"stack_peak_bytes": specialized["stack"]["maximum_live_stack_bytes"],
                                                 "memory": specialized["memory"],
                                                 "state_allocation_bytes": specialized["admission"]["state_allocation_bytes"],
                                                 "instruction_subset": specialized["instruction_subset"]}}}
        energies[compiler] = {v: Decimal(indexed[(compiler, v)]["cost"]["energy_nj"])
                              for v in ("general", "specialized")}
    g_general = energies["gcc15"]["general"] - energies["gcc10"]["general"]
    g_specialized = energies["gcc15"]["specialized"] - energies["gcc10"]["specialized"]
    if g_general != Decimal("70469.699925"):
        raise ValueError("reconstructed general compiler gap differs from frozen anchor")
    return {"per_compiler": deltas, "G_general_nj": str(g_general),
            "G_specialized_nj": str(g_specialized),
            "G_general_minus_G_specialized_nj": str(g_general - g_specialized),
            "G_general_anchor_nj": "70469.699925",
            "stronger_conjunction": {
                "identified_preparation_removal": "pending independent Sol review",
                "gcc15_specialized_below_general": energies["gcc15"]["specialized"] < energies["gcc15"]["general"],
                "G_specialized_below_G_general": g_specialized < g_general}}


def verify_comparisons(rows: list[dict], stored: dict) -> dict:
    derived = derive_comparisons(rows)
    if stored != derived:
        raise ValueError("serialized comparisons differ from independent raw-row reducer")
    return derived


PERFORMANCE_ORDER = (("gcc10", "general"), ("gcc15", "general"),
                    ("gcc10", "specialized"), ("gcc15", "specialized"))
CORRECTNESS_ORDER = (("gcc10", "general"), ("gcc10", "specialized"),
                     ("gcc15", "general"), ("gcc15", "specialized"))
ALLOWED_STATUSES = {"incomplete", "running", "stopped-general-mismatch", "complete"}


def audit_checkpoint(data: dict) -> dict:
    if data.get("schema") != "fir-task6-intervention-v1":
        raise ValueError("unexpected intervention checkpoint schema")
    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        raise ValueError("unknown checkpoint status")
    rows, correctness = data.get("rows"), data.get("correctness_only")
    if not isinstance(rows, list) or not isinstance(correctness, list):
        raise ValueError("checkpoint row inventories must be arrays")
    if len(rows) > 4 or len(correctness) > 4:
        raise ValueError("bounded campaign row budget exceeded")
    perf_ids = [(r.get("identity", {}).get("compiler"), r.get("identity", {}).get("variant"))
                for r in rows]
    if perf_ids != list(PERFORMANCE_ORDER[:len(perf_ids)]):
        raise ValueError("performance rows must be a unique declared-order prefix")
    for row in rows:
        if "fixture_kind" in row:
            raise ValueError("historical fixture adapter rows cannot enter a campaign checkpoint")
        if row.get("identity", {}).get("run_kind") != "performance":
            raise ValueError("performance inventory contains unknown run_kind")
    correctness_ids = [(r.get("identity", {}).get("compiler"), r.get("identity", {}).get("variant"))
                       for r in correctness]
    if correctness and len(rows) != 4:
        raise ValueError("correctness-only rows cannot precede all four performance conditions")
    if correctness_ids != list(CORRECTNESS_ORDER[:len(correctness_ids)]):
        raise ValueError("correctness rows must be a unique declared-order prefix")
    for row in correctness:
        if "fixture_kind" in row:
            raise ValueError("historical fixture adapter rows cannot enter a campaign checkpoint")
        if row.get("identity", {}).get("run_kind") != "correctness":
            raise ValueError("correctness inventory contains unknown run_kind")
    is_complete = len(rows) == 4 and len(correctness) == 4
    if status == "complete" and not is_complete:
        raise ValueError("complete status requires exact performance and correctness inventories")
    if not is_complete and data.get("comparisons") is not None:
        raise ValueError("partial checkpoint cannot publish completed comparisons")
    if status == "stopped-general-mismatch" and len(rows) not in {1, 2}:
        raise ValueError("stopped control mismatch requires a saved general control")
    return {"performance_count": len(rows), "correctness_count": len(correctness),
            "complete": is_complete, "performance_ids": perf_ids,
            "correctness_ids": correctness_ids}


def _row_key(row: dict) -> tuple[str, str, str]:
    ident = row["identity"]
    return ident["run_kind"], ident["compiler"], ident["variant"]


def _recover_attempt(run_kind: str, compiler: str, variant: str) -> dict | None:
    tag = f"{run_kind}-{compiler}-{variant}"
    parent = INTERVENTION_BUILD / tag
    if not parent.is_dir():
        return None
    for evidence in sorted(parent.glob("attempt-*/evidence.json"), reverse=True):
        row = json.loads(evidence.read_text())
        if _row_key(row) != (run_kind, compiler, variant):
            continue
        try:
            if run_kind == "performance" and variant == "general":
                original = _original_runner(ROOT)
                design, _, h = original.frozen_data()
                samples = design["inputs"]["adc_raw"][:257]
                anchor = _anchor_evidence(_raw_checker(ROOT), samples, h, compiler, ROOT)
                observed = _sha(HERE / row["directory"] / "firmware.bin")
                row["firmware_sha256"] = observed
                row["anchor_comparison"] = {
                    "expected_binary_sha256": anchor["firmware_sha256"],
                    "observed_binary_sha256": observed,
                    "expected_events": anchor["events"], "observed_events": row["events"],
                    "binary_match": observed == anchor["firmware_sha256"],
                    "events_match": row["events"] == anchor["events"]}
                _write_json(evidence, row)
            audit_row(row, HERE)
        except (KeyError, ValueError):
            continue
        return row
    return None


def _recover_or_block(run_kind: str, compiler: str, variant: str) -> dict | None:
    recovered = _recover_attempt(run_kind, compiler, variant)
    if recovered is not None:
        return recovered
    tag = f"{run_kind}-{compiler}-{'specialized' if variant == 'specialized' else 'general'}"
    _reject_incomplete_executed_attempts(INTERVENTION_BUILD / tag)
    return None


def _reuse_or_compile(run_kind: str, compiler: str, variant: str, compile_condition):
    recovered = _recover_or_block(run_kind, compiler, variant)
    if recovered is not None:
        return recovered
    return compile_condition()


def _publish_row(data: dict, row: dict, correctness: bool = False) -> None:
    # The complete raw attempt is durable before the checkpoint references it.
    attempt = HERE / row["directory"]
    _write_json(attempt / "evidence.json", row)
    audit_row(row, HERE)
    inventory = data["correctness_only"] if correctness else data["rows"]
    inventory.append(row)
    _write_json(HERE / "intervention-results.json", data)


def run_campaign(controls_only: bool = False) -> dict:
    """Run controls first, then the fixed specialization and bounded edge checks."""
    raw_checker = _raw_checker(ROOT)
    original = _original_runner(ROOT)
    design, baseline, h = original.frozen_data()
    x = design["inputs"]["adc_raw"][:257]
    if len(x) != 257 or x != baseline["actual_input"]:
        raise ValueError("original ADC input prefix differs from frozen b1 fixture")
    for name, expected in SOURCE_SHA.items():
        if _sha(PARTIAL / name) != expected:
            raise ValueError(f"frozen original source hash mismatch: {name}")
    if _sha(ROOT / "research" / "fir-baseline" / "startup.s") != STARTUP_SHA:
        raise ValueError("frozen startup source hash mismatch")
    if _sha(ROOT / "research" / "fir-baseline" / "link.ld") != LINKER_SHA:
        raise ValueError("frozen linker source hash mismatch")
    if _sha(DESIGN) != original.DESIGN_SHA:
        raise ValueError("frozen filter/input design hash mismatch")
    result_path = HERE / "intervention-results.json"
    resume_data = None
    if result_path.exists():
        resume_data = json.loads(result_path.read_text())
        audit_checkpoint(resume_data)
        verify_saved(HERE, result_path)
        requested_perf = PERFORMANCE_ORDER[:2 if controls_only else 4]
        requested_correct = () if controls_only else CORRECTNESS_ORDER
        present = {_row_key(r) for r in resume_data["rows"] + resume_data["correctness_only"]}
        for kind, compiler, variant in [("performance", c, v) for c, v in requested_perf] + \
                                       [("correctness", c, v) for c, v in requested_correct]:
            if (kind, compiler, variant) in present:
                continue
            recovered = _recover_or_block(kind, compiler, variant)
            if recovered is None:
                continue
            target = resume_data["correctness_only"] if kind == "correctness" else resume_data["rows"]
            if kind == "performance" and variant == "general":
                original_data = _original_runner(ROOT)
                design_data, _, coeffs = original_data.frozen_data()
                samples_data = design_data["inputs"]["adc_raw"][:257]
                anchor = _anchor_evidence(raw_checker, samples_data, coeffs, compiler, ROOT)
                observed = recovered["firmware_sha256"]
                recovered["anchor_comparison"] = {
                    "expected_binary_sha256": anchor["firmware_sha256"],
                    "observed_binary_sha256": observed, "expected_events": anchor["events"],
                    "observed_events": recovered["events"],
                    "binary_match": observed == anchor["firmware_sha256"],
                    "events_match": recovered["events"] == anchor["events"]}
                resume_data["historical_anchor"]["rows"][compiler] = anchor
                _write_json(HERE / recovered["directory"] / "evidence.json", recovered)
                audit_row(recovered, HERE)
            target.append(recovered)
            present.add((kind, compiler, variant))
            _write_json(result_path, resume_data)
        if all(("performance", c, v) in present for c, v in requested_perf) and \
                all(("correctness", c, v) in present for c, v in requested_correct):
            return resume_data
    simulator, compiler_paths, compiler_versions, missing = original.prerequisites(baseline)
    if missing:
        raise RuntimeError("pinned target prerequisites missing: " + "; ".join(missing))
    toolchains = {name: _toolchain_identity(path, baseline["compilers"][name])
                  for name, path in compiler_paths.items()}
    if _sha(simulator) != baseline["simulator_sha256"]:
        raise RuntimeError("pinned simulator hash differs from original fixture")
    INTERVENTION_BUILD.mkdir(parents=True, exist_ok=True)
    if resume_data is not None:
        data = resume_data
    else:
        data = {"schema": "fir-task6-intervention-v1", "status": "incomplete",
            "bound": {"fixture": "speech_minphase48", "samples": 257, "block": 1,
                      "conditions": ["gcc10/general", "gcc15/general",
                                     "gcc10/specialized", "gcc15/specialized"],
                      "correctness_only_max": 4, "correctness_stream": "original signed-edge 361 samples"},
            "source_identities": {**SOURCE_SHA, "startup.s": STARTUP_SHA,
                                  "link.ld": LINKER_SHA, "design": _sha(DESIGN)},
            "toolchains": toolchains, "simulator_sha256": _sha(simulator),
            "historical_anchor": {"G_general_nj": "70469.699925",
                                  "definition": "E_gcc15,general - E_gcc10,general",
                                  "rows": {}},
            "rows": [], "correctness_only": [], "comparability": "pending",
            "comparisons": None}
        _write_json(result_path, data)

    # Recover a complete raw attempt that finished before a checkpoint crash.
    present = {_row_key(row) for row in data["rows"] + data["correctness_only"]}
    for kind, label, variant in [("performance", c, v) for c, v in PERFORMANCE_ORDER] + \
                                [("correctness", c, v) for c, v in CORRECTNESS_ORDER]:
        if (kind, label, variant) in present:
            continue
        recovered = _recover_or_block(kind, label, variant)
        if recovered is None:
            continue
        if kind == "performance" and variant == "general":
            anchor = _anchor_evidence(raw_checker, x, h, label, ROOT)
            observed = recovered["firmware_sha256"]
            recovered["anchor_comparison"] = {
                "expected_binary_sha256": anchor["firmware_sha256"],
                "observed_binary_sha256": observed, "expected_events": anchor["events"],
                "observed_events": recovered["events"],
                "binary_match": observed == anchor["firmware_sha256"],
                "events_match": recovered["events"] == anchor["events"]}
            _write_json(HERE / recovered["directory"] / "evidence.json", recovered)
            audit_row(recovered, HERE)
        target = data["correctness_only"] if kind == "correctness" else data["rows"]
        target.append(recovered)
        present.add((kind, label, variant))
        _write_json(result_path, data)

    # Only resolve target prerequisites for conditions still missing.
    existing = {_row_key(row) for row in data["rows"] + data["correctness_only"]}
    needs_target = any(("performance", c, v) not in existing
                       for c, v in PERFORMANCE_ORDER[:2 if controls_only else 4])
    needs_target = needs_target or (not controls_only and any(
        ("correctness", c, v) not in existing for c, v in CORRECTNESS_ORDER))
    if not needs_target:
        return data
    controls = []
    for label, variant in PERFORMANCE_ORDER[:2 if controls_only else 4]:
        key = ("performance", label, variant)
        saved = next((r for r in data["rows"] if _row_key(r) == key), None)
        if saved is not None:
            controls.append(saved)
            continue
        if variant == "specialized" and data.get("comparability") != "admitted":
            raise ValueError("specialized builds are blocked until both general controls are admitted")
        anchor = _anchor_evidence(raw_checker, x, h, label, ROOT)
        row = _reuse_or_compile(
            "performance", label, variant,
            lambda: _compile_and_measure(label, variant == "specialized", x, h,
                                         simulator, compiler_paths[label],
                                         toolchains[label], raw_checker, "performance"))
        observed_hash = row["firmware_sha256"]
        observed_events = row["events"]
        if variant == "general":
            row["anchor_comparison"] = {"expected_binary_sha256": anchor["firmware_sha256"],
                                        "observed_binary_sha256": observed_hash,
                                        "expected_events": anchor["events"],
                                        "observed_events": observed_events,
                                        "binary_match": observed_hash == anchor["firmware_sha256"],
                                        "events_match": observed_events == anchor["events"]}
            data["historical_anchor"]["rows"][label] = anchor
            _write_json(HERE / row["directory"] / "evidence.json", row)
        else:
            row["anchor_comparison"] = None
        audit_row(row, HERE)
        controls.append(row)
        _publish_row(data, row)
        if variant == "general" and (not row["anchor_comparison"]["binary_match"] or
                                      not row["anchor_comparison"]["events_match"]):
            data["status"] = "stopped-general-mismatch"
            data["comparability"] = "failed"
            _write_json(HERE / "intervention-results.json", data)
            return data
        if variant == "general" and sum(1 for r in controls if r["identity"]["variant"] == "general") == 2:
            data["comparability"] = "admitted"
            _write_json(HERE / "intervention-results.json", data)
    if controls_only:
        data["status"] = "incomplete"
        _write_json(HERE / "intervention-results.json", data)
        return data
    specialized = [r for r in data["rows"] if r["identity"]["variant"] == "specialized"]
    edge = original.edge_input(h)
    for label in ("gcc10", "gcc15"):
        for is_specialized in (False, True):
            variant = "specialized" if is_specialized else "general"
            if any(_row_key(r) == ("correctness", label, variant) for r in data["correctness_only"]):
                continue
            row = _reuse_or_compile(
                "correctness", label, variant,
                lambda: _compile_and_measure(label, is_specialized, edge, h, simulator,
                                             compiler_paths[label], toolchains[label],
                                             raw_checker, "correctness"))
            row["anchor_comparison"] = None
            _publish_row(data, row, correctness=True)
    data["comparisons"] = derive_comparisons(data["rows"])
    data["status"] = "complete"
    _write_json(HERE / "intervention-results.json", data)
    return data


def verify_saved(root: Path | None = None, result_path: Path | None = None) -> dict:
    """Independently verify a checkpoint; this path never locates target tools."""
    given = Path(root or HERE).resolve()
    stage = given if given.name == "fir-upgrades" else given / "research/fir-upgrades"
    result_path = Path(result_path) if result_path else stage / "intervention-results.json"
    data = json.loads(result_path.read_text())
    inventory = audit_checkpoint(data)
    derived_rows = []
    for row in data["rows"] + data["correctness_only"]:
        derived_rows.append(audit_row(row, stage))
    project_root = _project_root_from_stage(stage)
    original = _original_runner(project_root)
    design, baseline, h = original.frozen_data()
    expected_bound = {"fixture": "speech_minphase48", "samples": 257, "block": 1,
                      "conditions": ["gcc10/general", "gcc15/general",
                                     "gcc10/specialized", "gcc15/specialized"],
                      "correctness_only_max": 4,
                      "correctness_stream": "original signed-edge 361 samples"}
    if data.get("bound") != expected_bound:
        raise ValueError("saved intervention fixture header differs from frozen protocol")
    expected_sources = {**SOURCE_SHA, "startup.s": STARTUP_SHA,
                        "link.ld": LINKER_SHA,
                        "design": _sha(project_root / "research/fir-baseline/selection-design.json")}
    if data.get("source_identities") != expected_sources:
        raise ValueError("saved source identity header differs from frozen inputs")
    if data.get("simulator_sha256") != baseline["simulator_sha256"]:
        raise ValueError("saved simulator header differs from frozen fixture")
    toolchain_header = data.get("toolchains")
    if not isinstance(toolchain_header, dict) or set(toolchain_header) != {"gcc10", "gcc15"}:
        raise ValueError("saved toolchain header differs from frozen toolchain identities")
    verifier = _load_module("fir_intervention_panel_verifier", stage / "panel_verify.py")
    for label in ("gcc10", "gcc15"):
        _toolchain_admission({"compiler": toolchain_header[label]}, label, verifier, stage)
    for row in data["rows"] + data["correctness_only"]:
        label = row["identity"]["compiler"]
        if row.get("compiler") != toolchain_header[label]:
            raise ValueError("saved row compiler identity differs from toolchain header")
    historical = data.get("historical_anchor", {})
    if historical.get("G_general_nj") != "70469.699925" or historical.get("definition") != \
            "E_gcc15,general - E_gcc10,general":
        raise ValueError("saved historical anchor header differs from frozen protocol")
    expected_anchor_rows = {}
    for row in data["rows"]:
        ident = row["identity"]
        if ident["variant"] == "general":
            samples = design["inputs"]["adc_raw"][:257]
            expected_anchor_rows[ident["compiler"]] = _anchor_evidence(
                _raw_checker(project_root), samples, h, ident["compiler"], project_root)
    if historical.get("rows") != expected_anchor_rows:
        raise ValueError("saved historical anchor rows differ from frozen raw controls")
    perf_rows = data["rows"]
    if inventory["complete"]:
        comparisons = derive_comparisons(perf_rows)
        if data.get("comparisons") != comparisons:
            raise ValueError("serialized comparisons differ from independent raw-row reducer")
    elif data.get("comparisons") is not None:
        raise ValueError("partial checkpoint contains unverified comparison summary")
    general = [row for row in perf_rows if row["identity"]["variant"] == "general"]
    expected_comparability = "pending" if len(general) < 2 else "admitted"
    if any(not r.get("anchor_admitted") for r in derived_rows
           if r["identity"]["run_kind"] == "performance" and
           r["identity"]["variant"] == "general"):
        expected_comparability = "failed"
    if data.get("comparability") != expected_comparability:
        raise ValueError("saved comparability status differs from independently admitted controls")
    return {"verified_rows": len(derived_rows), "performance_rows": inventory["performance_count"],
            "correctness_only_rows": inventory["correctness_count"],
            "status": data["status"], "toolchains_executed": False,
            "comparability": expected_comparability}


def _expected_commands(directory: Path, compiler: Path, tag: str,
                       simulator: Path) -> list[list[str]]:
    flags = ["-mcpu=cortex-m0", "-mthumb", "-std=c11", "-ffreestanding", "-fno-builtin",
             "-ffunction-sections", "-fdata-sections", "-g0"]
    compile_flags = [*flags, "-O2", "-Wall", "-Wextra", "-Werror", "-fstack-usage"]
    common = [str(compiler), *compile_flags, "-DBLOCK=1", "-I", str(directory)]
    commands = []
    objects = []
    for source, obj in (("kernel.c", "kernel.o"), ("firmware.c", "firmware.o"),
                        ("startup.s", "startup.o")):
        commands.append([*common, "-c", str(directory / source), "-o", str(directory / obj)])
        objects.append(str(directory / obj))
    elf, binary = directory / "firmware.elf", directory / "firmware.bin"
    commands.append([str(compiler), *flags, "-nostdlib", "-T", str(directory / "link.ld"),
                     "-Wl,--gc-sections", f"-Wl,-Map={directory / 'firmware.map'}",
                     *objects, "-lgcc", "-o", str(elf)])
    for tool, args in (("objcopy", ["-O", "binary", str(elf), str(binary)]),
                       ("objdump", ["-d", str(elf)]), ("size", [str(elf)])):
        commands.append([str(compiler.with_name(f"arm-none-eabi-{tool}")), *args])
    commands.append([str(simulator.resolve()), "-s", str(binary.resolve())])
    return commands


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true", help="execute the bounded target campaign")
    group.add_argument("--verify", action="store_true", help="audit saved evidence only")
    parser.add_argument("--controls-only", action="store_true",
                        help="limit --run to the two general compiler controls")
    args = parser.parse_args(argv)
    result = run_campaign(controls_only=args.controls_only) if args.run else verify_saved()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def specialize_kernel(source: bytes) -> bytes:
    """Replace only the three runtime b expressions in probe_process; precondition b=1."""
    text = source.decode("ascii")
    start = text.index("void probe_process(")
    end = text.index("\n}", start) + 2
    body = text[start:end]
    replacements = {
        "for (uint32_t j = 0; j < b; ++j) s->history[TAPS - 1 + j] = x[j];":
            "for (uint32_t j = 0; j < 1; ++j) s->history[TAPS - 1 + j] = x[j];",
        "for (uint32_t j = 0; j < b; ++j) {":
            "for (uint32_t j = 0; j < 1; ++j) {",
        "s->history[j] = s->history[b + j];":
            "s->history[j] = s->history[1 + j];",
    }
    for old, new in replacements.items():
        if body.count(old) != 1:
            raise ValueError(f"expected one source expression: {old}")
        body = body.replace(old, new)
    body = body.replace("    for (uint32_t j = 0; j < 1; ++j) s->history[TAPS - 1 + j] = x[j];",
                        "    (void)b;\n    for (uint32_t j = 0; j < 1; ++j) s->history[TAPS - 1 + j] = x[j];", 1)
    return (text[:start] + body + text[end:]).encode("ascii")


def verify_specialization_delta(original: bytes, specialized: bytes) -> bool:
    try:
        return specialized == specialize_kernel(original)
    except (UnicodeDecodeError, ValueError):
        return False


def coefficients() -> list[int]:
    return json.loads(DESIGN.read_text())["filters"]["speech_minphase48"]["coefficients"]


def edge_input(h: list[int]) -> list[int]:
    aligned = [-32768 if c < 0 else 32767 for c in reversed(h)]
    return [-32768, 32767, 0, -1, 1] * 53 + [0] * 48 + aligned


def reference(h: list[int], samples: list[int]) -> list[int]:
    return [max(-32768, min(32767,
            sum(h[k] * samples[n-k] for k in range(min(n + 1, 48))) // 32768))
            for n in range(len(samples))]


def run_host_ubsan(kernel: bytes, samples: list[int], calls: list[int]) -> dict:
    """Compile and run exact source with host UBSan and the original guard harness."""
    if any(call != 1 for call in calls) or sum(calls) != len(samples):
        raise ValueError("specialized host calls require a complete b=1 partition")
    with tempfile.TemporaryDirectory(prefix="fir-intervention-ubsan-") as temp:
        build = Path(temp)
        (build / "kernel.c").write_bytes(kernel)
        (build / "kernel.h").write_bytes((PARTIAL / "kernel.h").read_bytes())
        executable = build / "host-harness"
        command = [os.environ.get("CC", "gcc"), "-std=c11", "-O2", "-Wall", "-Wextra",
                   "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=undefined",
                   "-DBLOCK=1", "-I", str(build), str(build / "kernel.c"),
                   str(PARTIAL / "host_harness.c"), "-o", str(executable)]
        compiled = subprocess.run(command, capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(f"host UBSan compile failed: {compiled.stdout}{compiled.stderr}")
        payload = f"{len(samples)} {len(calls)}\n" + " ".join(map(str, samples)) + "\n"
        payload += " ".join(map(str, calls)) + "\n"
        process = subprocess.run([str(executable)], input=payload, capture_output=True,
                                 text=True, env={**os.environ,
                                 "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"})
        if process.returncode:
            raise RuntimeError(f"host UBSan run failed: {process.stdout}{process.stderr}")
        lines = process.stdout.splitlines()
        if len(lines) != len(calls) + 4:
            raise AssertionError("host harness output cardinality differs")
        history_rows = [[int(v) for v in line.split()[1:]] for line in lines[1:-3]]
        return {"outputs": [int(v) for v in lines[-3].split()[1:]],
                "history": history_rows[-1] if history_rows else [int(v) for v in lines[0].split()[1:]],
                "history_rows": history_rows, "guards": lines[-2] == "G 1",
                "state_bytes": int(lines[-1].split()[1]), "ubsan_clean": True,
                "compile_command": command}


if __name__ == "__main__":
    raise SystemExit(main())
