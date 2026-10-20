"""Task 6 source and saved-evidence contract tests."""
import importlib.util
import json
import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "intervention.py"


def load_intervention():
    spec = importlib.util.spec_from_file_location("fir_intervention", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_specialization_changes_only_runtime_block_expressions_in_probe_body():
    module = load_intervention()
    original = (HERE.parent / "fir-sharing-probe" / "partial-direct" / "kernel.c").read_bytes()
    specialized = module.specialize_kernel(original)
    assert module.verify_specialization_delta(original, specialized)
    assert specialized.count(b"(void)b;") == 1
    assert b"for (uint32_t j = 0; j < 1; ++j)" in specialized
    assert b"s->history[1 + j]" in specialized
    assert b"s->history[1 + j]" in specialized


def test_general_and_specialized_host_ubsan_match_reference_on_one_sample_calls():
    module = load_intervention()
    original = (HERE.parent / "fir-sharing-probe" / "partial-direct" / "kernel.c").read_bytes()
    kernels = [original, module.specialize_kernel(original)]
    samples = module.edge_input(module.coefficients())
    samples += [0] * 48
    # Exercise exact negative floor boundaries at n=47 in independent windows.
    h = module.coefficients()
    for exact in (-32769, -32768, -32767, -1, 0, 1):
        a = (4 * exact) % 39
        b = (10 * a - exact) // 39
        window = [0] * 48
        window[7], window[0] = a, b
        assert sum(h[k] * window[47-k] for k in range(48)) == exact
        samples += window
    samples += [32767, -32768, -1, 1] * 12
    for kernel in kernels:
        result = module.run_host_ubsan(kernel, samples, [1] * len(samples))
        assert result["outputs"] == module.reference(module.coefficients(), samples)
        assert result["history"] == samples[-47:]
        assert result["history_rows"] == [([0] * 47 + samples[:i+1])[-47:]
                                          for i in range(len(samples))]
        assert result["guards"] is True
        assert result["state_bytes"] == 98
        assert result["ubsan_clean"] is True


def test_independent_event_audit_rejects_duplicate_counter_mutation():
    module = load_intervention()
    original = json.loads((HERE.parent / "fir-sharing-probe" / "partial-direct" /
                           "results.json").read_text())
    row = next(r for r in original["rows"] if r["compiler"] == "gcc10" and r["block"] == 1)
    raw = (HERE.parent / "fir-sharing-probe" / "partial-direct" / row["directory"] /
           "firmware.stderr").read_text()
    assert module._strict_events(module._raw_checker(), raw)["instructions"] > 0
    with pytest.raises(ValueError, match="missing/duplicate"):
        module._strict_events(module._raw_checker(), raw + "Executed insns: 1\n")


def _copied_historical_control(tmp_path, compiler="gcc10"):
    module = load_intervention()
    repo = HERE.parents[1]
    project = tmp_path / "portable" / "project"
    stage = project / "research" / "fir-upgrades"
    stage.mkdir(parents=True)
    sibling = project / "research" / "fir-sharing-probe"
    partial = sibling / "partial-direct"
    partial.mkdir(parents=True)
    checker_dir = sibling / "independent-check"
    checker_dir.mkdir()
    base = project / "research" / "fir-baseline"
    base.mkdir(parents=True)
    shutil.copyfile(HERE / "panel_verify.py", stage / "panel_verify.py")
    shutil.copyfile(HERE / "panel-protocol.json", stage / "panel-protocol.json")
    shutil.copyfile(HERE / "intervention.py", stage / "intervention.py")
    for filename in ("run.py", "kernel.c", "kernel.h", "host_harness.c", "results.json"):
        shutil.copyfile(repo / "research/fir-sharing-probe/partial-direct" / filename,
                        partial / filename)
    shutil.copyfile(repo / "research/fir-sharing-probe/independent-check/check.py",
                    checker_dir / "check.py")
    for filename in ("selection-design.json", "startup.s", "link.ld", "simulator.py"):
        shutil.copyfile(repo / "research/fir-baseline" / filename, base / filename)
    results = json.loads((partial / "results.json").read_text())
    historical = next(row for row in results["rows"] if row["compiler"] == compiler and row["block"] == 1)
    source_partial = repo / "research/fir-sharing-probe/partial-direct"
    original_dir = source_partial / historical["directory"]
    shutil.copytree(original_dir, partial / historical["directory"])
    directory = stage / "build/intervention" / f"fixture-performance-{compiler}-general"
    directory.mkdir(parents=True)
    for filename in ("kernel.c", "kernel.h", "firmware.c", "firmware.elf", "firmware.bin",
                     "firmware.disasm", "firmware.map", "firmware.stdout", "firmware.stderr",
                     "commands.json", "kernel.su", "firmware.su", "size.txt"):
        shutil.copyfile(original_dir / filename, directory / filename)
    shutil.copyfile(base / "startup.s", directory / "startup.s")
    shutil.copyfile(base / "link.ld", directory / "link.ld")
    artifacts = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in directory.iterdir() if p.is_file()}
    verifier = module._load_module("fir_intervention_fixture_verifier", stage / "panel_verify.py")
    expected = results["compilers"][compiler]
    compiler_path = Path(json.loads((stage / "panel-protocol.json").read_text())
                         ["toolchain_identities"][compiler]["path"])
    tools = {}
    for name in ("as", "ld", "objcopy", "objdump", "size", "readelf", "nm"):
        digest = (verifier.BINUTIL_SHA256[compiler].get(name) if name in verifier.BINUTIL_SHA256[compiler]
                  else "a" * 64)
        tools[name] = {"path": str(compiler_path.with_name(f"arm-none-eabi-{name}")),
                       "sha256": digest}
    tools["libgcc"] = {"path": f"/pinned/{compiler}/libgcc.a",
                       "sha256": verifier.LIBGCC_SHA256[compiler],
                       "query_flags": ["-mcpu=cortex-m0", "-mthumb"]}
    checker = module._raw_checker(project)
    design = json.loads((base / "selection-design.json").read_text())
    samples = design["inputs"]["adc_raw"][:257]
    h = design["filters"]["speech_minphase48"]["coefficients"]
    events = module._strict_events(checker, (directory / "firmware.stderr").read_text(), stage)
    cost = module._cost(events, len(samples))
    layout = verifier._elf_layout(directory / "firmware.elf")
    disassembly = (directory / "firmware.disasm").read_text()
    binary_binding = verifier._audit_binary_binding(directory / "firmware.elf", directory / "firmware.bin",
                                                   disassembly, layout, samples)
    stack = verifier._independent_stack_chain([directory / "kernel.su", directory / "firmware.su"],
                                               disassembly, layout["symbols"])
    row = {
        "fixture_kind": "historical-control",
        "identity": {"run_kind": "performance", "compiler": compiler, "variant": "general",
                     "block": 1, "samples": 257},
        "directory": directory.relative_to(stage).as_posix(),
        "artifacts": artifacts,
        "compiler": {**expected, "path": str(compiler_path), "tools": tools},
        "simulator_path": json.loads((directory / "commands.json").read_text())[6][0],
        "simulator_sha256": verifier.SIMULATOR_SHA256,
        "commands": json.loads((directory / "commands.json").read_text()),
        "events": events, "cost": cost,
        "admission": module._output_admission(checker, (directory / "firmware.stdout").read_text(), h, samples),
        "instruction_subset": verifier.instruction_subset(disassembly),
        "binary_binding": binary_binding, "stack": stack,
        "memory": {"initial_sp": layout["initial_sp"], "ram_end": layout["ram_end"],
                   "flash_end": layout["flash_end"]},
        "kernel_delta_verified": True,
        "kernel_sha256": hashlib.sha256((directory / "kernel.c").read_bytes()).hexdigest(),
        "source_fixture_sha256": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                  for name in ("kernel.h", "startup.s", "link.ld")},
        "elf_size_bytes": module._elf_sections(directory / "firmware.elf"),
        "size_output": (directory / "size.txt").read_text(),
        "stack_usage": [
            {"file": su.name, "function": name, "bytes": int(n), "kind": kind}
            for su in sorted((directory / "kernel.su", directory / "firmware.su"))
            for name, n, kind in __import__("re").findall(
                r"\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)", su.read_text())],
        "firmware_source_sha256": hashlib.sha256((directory / "firmware.c").read_bytes()).hexdigest(),
        "firmware_sha256": hashlib.sha256((directory / "firmware.bin").read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(",".join(map(str, samples)).encode()).hexdigest(),
    }
    row["anchor_comparison"] = {
        "expected_binary_sha256": module.ORIGINAL_FIRMWARE_SHA[compiler],
        "observed_binary_sha256": row["firmware_sha256"],
        "expected_events": module.ORIGINAL_EVENTS[compiler], "observed_events": events,
        "binary_match": row["firmware_sha256"] == module.ORIGINAL_FIRMWARE_SHA[compiler],
        "events_match": events == module.ORIGINAL_EVENTS[compiler],
    }
    return module, stage, directory, row


@pytest.mark.parametrize("compiler", ["gcc10", "gcc15"])
def test_copied_historical_general_controls_admit_without_target_tools(tmp_path, compiler):
    module, stage, _, row = _copied_historical_control(tmp_path, compiler)
    admitted = module.audit_row(row, stage)
    assert admitted["events"] == module.ORIGINAL_EVENTS[compiler]
    assert admitted["anchor_admitted"] is True


def test_relocated_saved_audit_succeeds_with_no_target_tools_on_path(tmp_path):
    module, stage, _, row = _copied_historical_control(tmp_path)
    row_path = stage / "fixture-row.json"
    row_path.write_text(json.dumps(row))
    script = (
        "import importlib.util,json,pathlib,sys; "
        "p=pathlib.Path(sys.argv[1]); s=importlib.util.spec_from_file_location('relocated_intervention',p/'intervention.py'); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "r=json.loads((p/'fixture-row.json').read_text()); "
        "print(m.audit_row(r,p)['anchor_admitted'])"
    )
    env = {"PATH": "/nonexistent", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, "-c", script, str(stage)], env=env,
                            text=True, capture_output=True, check=True)
    assert result.stdout.strip() == "True"


def _copy_actual_complete_package(tmp_path):
    source_project = HERE.parents[1]
    project = tmp_path / "relocated" / "project"
    stage = project / "research/fir-upgrades"
    stage.mkdir(parents=True)
    shutil.copyfile(HERE / "intervention.py", stage / "intervention.py")
    shutil.copyfile(HERE / "panel_verify.py", stage / "panel_verify.py")
    shutil.copyfile(HERE / "panel-protocol.json", stage / "panel-protocol.json")
    shutil.copytree(HERE / "build/intervention", stage / "build/intervention")
    shutil.copyfile(HERE / "intervention-results.json", stage / "intervention-results.json")
    sibling = project / "research/fir-sharing-probe"
    partial = sibling / "partial-direct"
    partial.mkdir(parents=True)
    checker = sibling / "independent-check"
    checker.mkdir()
    for name in ("run.py", "kernel.c", "kernel.h", "results.json"):
        shutil.copyfile(source_project / "research/fir-sharing-probe/partial-direct" / name,
                        partial / name)
    shutil.copyfile(source_project / "research/fir-sharing-probe/independent-check/check.py",
                    checker / "check.py")
    shutil.copyfile(source_project / "research/fir-sharing-probe/results.json",
                    sibling / "results.json")
    original_results = json.loads((partial / "results.json").read_text())
    original_root = source_project / "research/fir-sharing-probe/partial-direct"
    for compiler in ("gcc10", "gcc15"):
        row = next(r for r in original_results["rows"]
                   if r["compiler"] == compiler and r["block"] == 1)
        shutil.copytree(original_root / row["directory"], partial / row["directory"])
    baseline = project / "research/fir-baseline"
    baseline.mkdir(parents=True)
    for name in ("selection-design.json", "startup.s", "link.ld", "simulator.py"):
        shutil.copyfile(source_project / "research/fir-baseline" / name, baseline / name)
    return stage


def test_actual_complete_campaign_relocates_and_verifies_without_tools(tmp_path):
    stage = _copy_actual_complete_package(tmp_path)
    env = {"PATH": "/nonexistent", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, str(stage / "intervention.py"), "--verify"],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    verified = json.loads(result.stdout)
    assert (verified["performance_rows"], verified["correctness_only_rows"]) == (4, 4)
    assert verified["toolchains_executed"] is False


def test_actual_one_general_control_checkpoint_verifies_and_retains_both_toolchains(tmp_path):
    module = load_intervention()
    data = json.loads((HERE / "intervention-results.json").read_text())
    data["rows"] = data["rows"][:1]
    data["correctness_only"] = []
    data["comparisons"] = None
    data["status"] = "incomplete"
    data["comparability"] = "pending"
    data["historical_anchor"]["rows"] = {"gcc10": data["historical_anchor"]["rows"]["gcc10"]}
    checkpoint = tmp_path / "one-control.json"
    checkpoint.write_text(json.dumps(data))
    verified = module.verify_saved(HERE, checkpoint)
    assert verified["performance_rows"] == 1
    assert verified["comparability"] == "pending"
    assert set(data["toolchains"]) == {"gcc10", "gcc15"}


def test_corrupt_completed_attempt_fails_closed_before_compile(tmp_path, monkeypatch):
    stage = _copy_actual_complete_package(tmp_path)
    module_spec = importlib.util.spec_from_file_location("copied_task6_fix2", stage / "intervention.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    evidence = stage / "build/intervention/performance-gcc10-specialized/attempt-001/evidence.json"
    row = json.loads(evidence.read_text())
    row["cost"]["energy_nj"] = "0"
    evidence.write_text(json.dumps(row))
    compile_calls = []

    def forbidden_compile():
        compile_calls.append(True)
        raise AssertionError("invalid prior execution must never trigger a new compile")

    with pytest.raises(RuntimeError, match="prior executed attempt requires offline recovery"):
        module._reuse_or_compile("performance", "gcc10", "specialized", forbidden_compile)
    assert compile_calls == []


@pytest.mark.parametrize("mutation", ["anchor", "anchor_row", "elf_size", "source_fixture",
                                      "toolchain_header", "source_header", "fixture_header"])
def test_verify_saved_rejects_rewritten_duplicate_summary_claim(tmp_path, mutation):
    module = load_intervention()
    data = json.loads((HERE / "intervention-results.json").read_text())
    if mutation == "anchor":
        data["historical_anchor"]["G_general_nj"] = "0"
    elif mutation == "anchor_row":
        data["historical_anchor"]["rows"]["gcc10"]["events"]["instructions"] += 1
    elif mutation == "elf_size":
        data["rows"][0]["elf_size_bytes"][".text"] = 1
    elif mutation == "source_fixture":
        data["rows"][0]["source_fixture_sha256"]["kernel.h"] = "0" * 64
    elif mutation == "toolchain_header":
        data["toolchains"]["gcc10"]["sha256"] = "0" * 64
    elif mutation == "source_header":
        data["source_identities"]["kernel.c"] = "0" * 64
    else:
        data["bound"]["samples"] = 258
    result = tmp_path / f"{mutation}.json"
    result.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        module.verify_saved(HERE, result)


def test_post_simulation_failure_receipt_blocks_repeated_target_execution(monkeypatch, tmp_path):
    module = load_intervention()
    monkeypatch.setattr(module, "INTERVENTION_BUILD", tmp_path / "build/intervention")
    simulator = Path("/fake/thumbulator/sim_main")
    compiler = Path("/fake/toolchain/bin/arm-none-eabi-gcc")
    original_sha = module._sha
    monkeypatch.setattr(module, "_sha", lambda path: "f" * 64
                        if Path(path) == simulator else original_sha(path))
    calls = []

    def mock_command(command, cwd=None):
        argv = [str(x) for x in command]
        calls.append(argv)
        if "-c" in argv:
            Path(argv[argv.index("-o") + 1]).write_bytes(b"object")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if "-nostdlib" in argv:
            Path(argv[argv.index("-o") + 1]).write_bytes(b"elf")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if Path(argv[0]).name == "arm-none-eabi-objcopy":
            Path(argv[-1]).write_bytes(b"binary")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if Path(argv[0]).name == "arm-none-eabi-objdump":
            return subprocess.CompletedProcess(argv, 0,
                "00000000 <probe_process>:\n", "")
        if argv[0] == str(simulator):
            return subprocess.CompletedProcess(argv, 0, "raw stdout", "raw stderr")
        if Path(argv[0]).name == "arm-none-eabi-size":
            raise RuntimeError("synthetic size failure after successful simulator")
        raise AssertionError(argv)

    monkeypatch.setattr(module, "_run_command", mock_command)
    args = ("gcc10", False, [0] * 257, module.coefficients(), simulator, compiler,
            {"path": str(compiler), "tools": {}}, module._raw_checker(), "performance")
    with pytest.raises(RuntimeError, match="synthetic size failure"):
        module._compile_and_measure(*args)
    attempt = next((tmp_path / "build/intervention/performance-gcc10-general").glob("attempt-*"))
    assert (attempt / "firmware.stdout").read_text() == "raw stdout"
    assert (attempt / "firmware.stderr").read_text() == "raw stderr"
    receipt = json.loads((attempt / "execution-receipt.json").read_text())
    assert receipt["simulator_started"] is True
    assert receipt["status"] == "simulator-complete"
    assert receipt["stdout_sha256"] == hashlib.sha256(b"raw stdout").hexdigest()
    simulator_calls = sum(call[0] == str(simulator) for call in calls)
    with pytest.raises(RuntimeError, match="incomplete executed attempt"):
        module._compile_and_measure(*args)
    assert sum(call[0] == str(simulator) for call in calls) == simulator_calls == 1


def test_copied_saved_row_rejects_wrapper_change_even_when_artifact_hashes_are_rewritten(tmp_path):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    path = directory / "firmware.c"
    path.write_bytes(path.read_bytes() + b"/* changed ROI */\n")
    row["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    row["firmware_source_sha256"] = row["artifacts"][path.name]
    with pytest.raises(ValueError, match="wrapper differs from frozen original"):
        module.audit_row(row, stage)


def test_copied_saved_row_rejects_changed_input_identity(tmp_path):
    module, stage, _, row = _copied_historical_control(tmp_path)
    row["input_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="input digest"):
        module.audit_row(row, stage)


def test_copied_saved_row_rejects_rewritten_binary_identity(tmp_path):
    module, stage, _, row = _copied_historical_control(tmp_path)
    row["firmware_sha256"] = "0" * 64
    row["anchor_comparison"]["observed_binary_sha256"] = "0" * 64
    row["anchor_comparison"]["binary_match"] = False
    with pytest.raises(ValueError, match="binary digest"):
        module.audit_row(row, stage)


@pytest.mark.parametrize("record", ["O", "H", "G", "M"])
def test_copied_saved_row_rejects_duplicate_target_trace_record(tmp_path, record):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    path = directory / "firmware.stdout"
    original = path.read_text()
    selected = next(line for line in original.splitlines() if line.startswith(record + ":"))
    path.write_text(original + selected + "\n")
    row["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        module.audit_row(row, stage)


@pytest.mark.parametrize("record", ["O", "H", "G", "M"])
def test_copied_saved_row_rejects_damaged_target_trace_record(tmp_path, record):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    path = directory / "firmware.stdout"
    lines = path.read_text().splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith(record + ":"))
    line = lines[index]
    lines[index] = line[:-1] + ("0" if line[-1] != "0" else "1")
    path.write_text("\n".join(lines) + "\n")
    row["artifacts"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        module.audit_row(row, stage)


@pytest.mark.parametrize("field", ["events", "cost"])
def test_copied_saved_row_rejects_wrong_raw_event_or_cost_summary(tmp_path, field):
    module, stage, _, row = _copied_historical_control(tmp_path)
    if field == "events":
        row["events"]["instructions"] += 1
        message = "raw event vector"
    else:
        row["cost"]["arm_zero_ws_cycles"] += 1
        message = "energy/cycle summary"
    with pytest.raises(ValueError, match=message):
        module.audit_row(row, stage)


def test_copied_saved_row_rejects_source_delta_violation(tmp_path):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    row["identity"]["variant"] = "specialized"
    source = module.specialize_kernel((directory / "kernel.c").read_bytes())
    source = source.replace(b"history[1 + j]", b"history[2 + j]", 1)
    (directory / "kernel.c").write_bytes(source)
    row["artifacts"]["kernel.c"] = hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError, match="literal-b=1 source contract"):
        module.audit_row(row, stage)


@pytest.mark.parametrize("mutation", ["missing", "escape"])
def test_copied_saved_row_rejects_missing_or_escaping_required_artifact(tmp_path, mutation):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    if mutation == "missing":
        (directory / "firmware.map").unlink()
        with pytest.raises(ValueError, match="missing or escaping"):
            module.audit_row(row, stage)
    else:
        row["artifacts"]["../escape"] = "0" * 64
        with pytest.raises(ValueError, match="escapes attempt"):
            module.audit_row(row, stage)


def _checkpoint(rows=(), correctness=(), status="incomplete", comparisons=None):
    return {"schema": "fir-task6-intervention-v1", "status": status,
            "rows": [{"identity": {"run_kind": "performance", "compiler": c,
                                     "variant": v, "block": 1, "samples": 257}}
                     for c, v in rows],
            "correctness_only": [{"identity": {"run_kind": "correctness", "compiler": c,
                                                 "variant": v, "block": 1, "samples": 361}}
                                 for c, v in correctness],
            "comparisons": comparisons}


def test_checkpoint_accepts_declared_partial_performance_prefix():
    module = load_intervention()
    admitted = module.audit_checkpoint(_checkpoint([("gcc10", "general"),
                                                     ("gcc15", "general")]))
    assert admitted["performance_count"] == 2
    assert admitted["complete"] is False


def test_checkpoint_rejects_fixture_adapter_rows():
    module = load_intervention()
    data = _checkpoint([("gcc10", "general")])
    data["rows"][0]["fixture_kind"] = "historical-control"
    with pytest.raises(ValueError, match="fixture"):
        module.audit_checkpoint(data)


def test_four_performance_rows_without_correctness_remain_resumable(tmp_path, monkeypatch):
    module = load_intervention()
    data = json.loads((HERE / "intervention-results.json").read_text())
    data["correctness_only"] = []
    data["status"] = "incomplete"
    data["comparisons"] = None
    data["comparability"] = "admitted"
    result_path = tmp_path / "intervention-results.json"
    result_path.write_text(json.dumps(data))
    monkeypatch.setattr(module, "audit_row", lambda row, stage:
                        {"identity": row["identity"], "anchor_admitted": True})
    def forbidden(_rows):
        raise AssertionError("partial inventory must not derive the final comparison")
    monkeypatch.setattr(module, "derive_comparisons", forbidden)
    checked = module.verify_saved(HERE, result_path)
    assert checked["performance_rows"] == 4
    assert checked["correctness_only_rows"] == 0
    assert checked["status"] == "incomplete"


def test_attempt_directories_are_unique_and_preserve_prior_evidence(tmp_path):
    module = load_intervention()
    base = tmp_path / "campaign"
    first = module._new_attempt_directory(base, "performance-gcc10-general")
    (first / "sentinel").write_text("kept")
    second = module._new_attempt_directory(base, "performance-gcc10-general")
    assert first != second
    assert (first / "sentinel").read_text() == "kept"
    assert second.is_dir()


def _mock_campaign_environment(monkeypatch, tmp_path, fail_first_audit=False):
    module = load_intervention()
    actual = module._original_runner(module.ROOT)
    design, baseline, h = actual.frozen_data()

    class Runner:
        DESIGN_SHA = actual.DESIGN_SHA

        def frozen_data(self):
            return design, baseline, h

        def prerequisites(self, _baseline):
            return Path("/tmp/task6-test-simulator"), {
                "gcc10": Path("/tmp/task6-gcc10"), "gcc15": Path("/tmp/task6-gcc15")}, {}, []

    monkeypatch.setattr(module, "HERE", tmp_path / "research/fir-upgrades")
    module.HERE.mkdir(parents=True)
    monkeypatch.setattr(module, "INTERVENTION_BUILD", module.HERE / "build/intervention")
    monkeypatch.setattr(module, "_original_runner", lambda _root=None: Runner())
    monkeypatch.setattr(module, "_toolchain_identity", lambda path, expected:
                        {**expected, "path": str(path), "tools": {}})
    original_sha = module._sha
    monkeypatch.setattr(module, "_sha", lambda path: baseline["simulator_sha256"]
                        if Path(path) == Path("/tmp/task6-test-simulator") else original_sha(path))
    monkeypatch.setattr(module, "_anchor_evidence", lambda checker, samples, coeffs, label, root:
                        {"firmware_sha256": hashlib.sha256(
                            f"{label}-False-performance".encode()).hexdigest(),
                         "events": {"instructions": 7}})
    compile_calls = []
    compile_identities = set()

    def fake_compile(label, specialized, samples, coeffs, simulator, compiler,
                     compiler_identity, raw_checker, run_kind):
        compile_calls.append((run_kind, label, specialized))
        key = (run_kind, label, specialized)
        if specialized:
            raise AssertionError("controls-only attempted a specialized target build")
        if key in compile_identities:
            raise AssertionError("campaign repeated an already executed target identity")
        compile_identities.add(key)
        tag = f"{run_kind}-{label}-{'specialized' if specialized else 'general'}"
        attempt = module._new_attempt_directory(module.INTERVENTION_BUILD, tag)
        binary = attempt / "firmware.bin"
        binary.write_bytes(f"{label}-{specialized}-{run_kind}".encode())
        return {"identity": {"run_kind": run_kind, "compiler": label,
                             "variant": "specialized" if specialized else "general",
                             "block": 1, "samples": len(samples)},
                "directory": attempt.relative_to(module.HERE).as_posix(),
                "compiler": compiler_identity,
                "artifacts": {"firmware.bin": hashlib.sha256(binary.read_bytes()).hexdigest()},
                "firmware_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "events": {"instructions": 7}, "cost": {"energy_nj": "1"}}

    monkeypatch.setattr(module, "_compile_and_measure", fake_compile)
    audit_calls = []

    def fake_audit(row, stage):
        audit_calls.append(row["identity"]["variant"])
        if fail_first_audit and len(audit_calls) == 1:
            raise ValueError("simulated interruption before checkpoint")
        return {"identity": row["identity"], "anchor_admitted": True}

    monkeypatch.setattr(module, "audit_row", fake_audit)
    monkeypatch.setattr(module, "verify_saved", lambda root=None, result_path=None:
                        {"toolchains_executed": False})
    return module, compile_calls, audit_calls


def test_run_controls_only_executes_controls_once_and_reuses_checkpoint(monkeypatch, tmp_path):
    module, compile_calls, _ = _mock_campaign_environment(monkeypatch, tmp_path)
    module.main(["--run", "--controls-only"])
    assert compile_calls == [("performance", "gcc10", False),
                             ("performance", "gcc15", False)]
    module.main(["--run", "--controls-only"])
    assert compile_calls == [("performance", "gcc10", False),
                             ("performance", "gcc15", False)]


def test_run_recovers_complete_attempt_written_before_checkpoint(monkeypatch, tmp_path):
    module, compile_calls, _ = _mock_campaign_environment(monkeypatch, tmp_path,
                                                          fail_first_audit=True)
    with pytest.raises(ValueError, match="simulated interruption"):
        module.main(["--run", "--controls-only"])
    module.main(["--run", "--controls-only"])
    assert compile_calls == [("performance", "gcc10", False),
                             ("performance", "gcc15", False)]
    checkpoint = json.loads((module.HERE / "intervention-results.json").read_text())
    assert len(checkpoint["rows"]) == 2


@pytest.mark.parametrize("data", [
    _checkpoint([("gcc10", "general"), ("gcc10", "general")]),
    _checkpoint([("gcc15", "general")]),
    _checkpoint([("gcc10", "general")], status="mystery"),
    _checkpoint([("gcc10", "general")], comparisons={}),
    _checkpoint([("gcc10", "general")], [("gcc10", "general")]),
])
def test_checkpoint_rejects_invalid_identity_or_status(data):
    module = load_intervention()
    with pytest.raises(ValueError):
        module.audit_checkpoint(data)


def test_cli_exposes_bounded_controls_only_selection(capsys):
    module = load_intervention()
    with pytest.raises(SystemExit) as result:
        module.main(["--help"])
    assert result.value.code == 0
    assert "--controls-only" in capsys.readouterr().out


def test_reducer_treats_equal_energy_and_gap_as_false_and_rejects_rewritten_summary(tmp_path):
    module, _, _, gcc10 = _copied_historical_control(tmp_path, "gcc10")
    module2, _, _, gcc15 = _copied_historical_control(tmp_path / "second", "gcc15")
    assert module is module2 or module.derive_comparisons is not module2.derive_comparisons
    rows = []
    for source in (gcc10, gcc15):
        general = {**source, "identity": {**source["identity"], "variant": "general"}}
        specialized = {**source, "identity": {**source["identity"], "variant": "specialized"}}
        rows.extend((general, specialized))
    summary = module.derive_comparisons(rows)
    conditions = summary["stronger_conjunction"]
    assert conditions["gcc15_specialized_below_general"] is False
    assert conditions["G_specialized_below_G_general"] is False
    changed = json.loads(json.dumps(summary))
    changed["G_specialized_nj"] = "0"
    with pytest.raises(ValueError, match="serialized comparisons"):
        module.verify_comparisons(rows, changed)


@pytest.mark.parametrize("mutation", ["order", "option"])
def test_copied_saved_row_rejects_rewritten_historical_command_record(tmp_path, mutation):
    module, stage, directory, row = _copied_historical_control(tmp_path)
    commands = row["commands"]
    if mutation == "order":
        commands[4], commands[5] = commands[5], commands[4]
    else:
        commands[0].append("-fno-strict-aliasing")
    row["commands"] = commands
    data = (json.dumps(commands, indent=2, sort_keys=True) + "\n").encode()
    (directory / "commands.json").write_bytes(data)
    row["artifacts"]["commands.json"] = hashlib.sha256(data).hexdigest()
    with pytest.raises(ValueError, match="historical fixture command record"):
        module.audit_row(row, stage)


def test_copied_saved_row_rejects_wrong_pinned_tool_identity(tmp_path):
    module, stage, _, row = _copied_historical_control(tmp_path)
    row["compiler"]["tools"]["libgcc"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="pinned tool identity"):
        module.audit_row(row, stage)


def test_saved_toolchain_accepts_compiler_reported_as_and_ld_paths(tmp_path):
    module, stage, _, row = _copied_historical_control(tmp_path)
    row["compiler"]["tools"]["as"]["path"] = "/usr/lib/arm-none-eabi/bin/as"
    row["compiler"]["tools"]["ld"]["path"] = "/usr/lib/arm-none-eabi/bin/ld"
    admitted = module.audit_row(row, stage)
    assert admitted["anchor_admitted"] is True
