"""Arm-table timing regressions and saved-evidence correction checks."""
import hashlib
from pathlib import Path

import pytest

from timing_correction import (
    audit_instruction_subset, bound_read, build_report, corrected_cycles,
    parse_events,
)

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'research/fir-upgrades/build/intervention/performance-gcc15-general/attempt-001/firmware.stderr'


def test_pop_return_sequence_matches_arm_table_sixteen_cycles():
    # Independent instruction sum: BL4 + B3 + PUSH(1+2) + POP-PC(4+2).
    events = dict(instructions=4, ram_reads=2, ram_writes=2, flash_reads=0,
                  flash_writes=0, taken_branches=3, bl=1, pop_pc=1)
    assert corrected_cycles(events) == 16


def test_nonreturn_pop_does_not_receive_return_penalty():
    events = dict(instructions=2, ram_reads=4, ram_writes=4, flash_reads=0,
                  flash_writes=0, taken_branches=0, bl=0, pop_pc=0)
    assert corrected_cycles(events) == 10


def test_missing_pop_count_never_silently_uses_legacy_formula():
    with pytest.raises(ValueError, match='pop_pc'):
        corrected_cycles(dict(instructions=4, ram_reads=2, ram_writes=2,
                              flash_reads=0, flash_writes=0, taken_branches=3, bl=1))


def test_saved_general_row_recovers_omitted_return_cycles():
    events = parse_events(RAW.read_text())
    assert events['pop_pc'] == 258
    assert corrected_cycles(events) == 351226


def test_missing_or_duplicate_return_counter_is_rejected():
    text = RAW.read_text()
    line = next(line for line in text.splitlines() if line.startswith('PUSH/POP PC/LR:'))
    with pytest.raises(ValueError, match='POP'):
        parse_events(text.replace(line, ''))
    with pytest.raises(ValueError, match='POP'):
        parse_events(text + '\n' + line + '\n')


def test_unmodeled_instruction_is_not_assigned_scalar_cost():
    disassembly = '08000000 <probe_process>:\n 8000000:\tf3ef 8000\tmrs\tr0, CPSR\n'
    with pytest.raises(ValueError, match='instruction|subset|mnemonic'):
        audit_instruction_subset(disassembly)


def test_changed_evidence_bytes_fail_binding(tmp_path):
    raw = RAW.read_bytes()
    copied = tmp_path / 'firmware.stderr'
    copied.write_bytes(raw + b'\n')
    with pytest.raises(ValueError, match='hash|identity'):
        bound_read(copied, hashlib.sha256(raw).hexdigest())


def test_campaign_correction_preserves_energy_and_missing_cases():
    result = build_report(ROOT)
    assert result['counts'] == {'original': 20, 'panel': 280, 'intervention': 4,
                                'panel_unavailable': 8}
    row = next(r for r in result['rows'] if r['group'] == 'intervention'
               and r['identity']['compiler'] == 'gcc15'
               and r['identity']['variant'] == 'general')
    assert row['legacy_cycles'] == 350968
    assert row['corrected_cycles'] == 351226
    assert row['energy_nj'] == '336863.793775'
    assert result['intervention']['cycle_reductions'] == {'gcc10': 24929, 'gcc15': 114501}
    assert result['explanation']['compiler_cycle_gap'] == 77235
