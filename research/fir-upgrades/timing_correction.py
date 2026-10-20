"""Versioned timing correction from saved FIR evidence; never runs target tools.

Frozen campaign inventories retain their historical cycle proxy. This report
supersedes those cycle fields for the current manuscript, without changing raw
events, energy weights, binaries, protocol or historical artifact checks.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = 'arm-ddi0432c-zero-wait-mul1-pop-pc-v2'
PINNED = {
    'research/fir-paper/results.json': '3161d9a01ae81d0cb1ae38b81bc0ea2d02bd1e3cb8ca604e13f5a2f72defe6fd',
    'research/fir-sharing-probe/results.json': '57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa',
    'research/fir-sharing-probe/partial-direct/results.json': 'eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f',
    'research/fir-upgrades/panel-results.json': 'b1b35ba2cafe03cc3c67949fccee3c16267b3bd259584b8d1cf005be77dc1f2d',
    'research/fir-upgrades/intervention-results.json': '6bfb0cf3d7159dff812c036c5272d296b94f252a62b7dacf6105688d09068aa9',
    'research/fir-sharing-probe/independent-check/check.py': 'b96bc54469dcda343ea0339ae94381398829e84d8546420750bf49e6cf244803',
}
ENERGY_MICRO = {'nonmul': 964258, 'mul': 1652455, 'taken_branches': 2091986,
                'ram_reads': 1109833, 'ram_writes': 650563, 'flash_reads': 633621}


def bound_read(path: Path, expected_sha: str) -> bytes:
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError(f'evidence hash/identity mismatch: {path}')
    return data


def _checker():
    path = ROOT / 'research/fir-sharing-probe/independent-check/check.py'
    bound_read(path, PINNED['research/fir-sharing-probe/independent-check/check.py'])
    spec = importlib.util.spec_from_file_location('frozen_timing_raw_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_RAW = _checker()


def parse_events(stderr: str) -> dict:
    events = _RAW.raw_events(stderr)
    matches = re.findall(r'^PUSH/POP PC/LR:\s*(\d+)\s*$', stderr, re.M)
    if len(matches) != 1:
        raise ValueError('missing/duplicate POP-PC counter')
    events['pop_pc'] = int(matches[0])
    # Primary opcode 47 includes POP and BKPT; the latter is not in the
    # measured admitted subset. A return is also a RAM read/control transfer.
    pop_row = re.findall(r'^\s*47:\s*(\d+),', stderr, re.M)
    if len(pop_row) != 1 or events['pop_pc'] > min(
            int(pop_row[0]), events['ram_reads'], events['taken_branches']):
        raise ValueError('POP-PC counter exceeds recorded POP/read/branch counts')
    return events


def corrected_cycles(events: dict) -> int:
    fields = ('instructions', 'ram_reads', 'ram_writes', 'flash_reads',
              'flash_writes', 'taken_branches', 'bl', 'pop_pc')
    for key in fields:
        if type(events.get(key)) is not int or events[key] < 0:
            raise ValueError(f'invalid or missing {key}')
    if events['flash_writes']:
        raise ValueError('Flash writes are outside the admitted timing subset')
    if events['pop_pc'] > min(events['instructions'], events['ram_reads'], events['taken_branches']):
        raise ValueError('invalid pop_pc count')
    return (events['instructions'] + events['ram_reads'] + events['ram_writes']
            + events['flash_reads'] + 2 * events['taken_branches']
            + events['bl'] + events['pop_pc'])


def audit_instruction_subset(disassembly: str) -> list[str]:
    # The frozen checker screens the complete linked scalar subset, including
    # transfer, ALU, branch and single-cycle-MUL instructions. In particular it
    # excludes MRS/MSR, barriers, waits and unsupported multi-cycle operations.
    return _RAW.instruction_subset(disassembly)


def _decimal_ratio(value: int, samples: int) -> str:
    with localcontext() as context:
        context.prec = 40
        return format(Decimal(value) / samples, 'f')


def _row(root, group, identity, directory, hashes, legacy, samples, energy, expected_events):
    directory = (root / directory).resolve()
    if not directory.is_relative_to(root.resolve()):
        raise ValueError('evidence directory escapes repository')
    raw = bound_read(directory / 'firmware.stderr', hashes['firmware.stderr']).decode()
    disasm = bound_read(directory / 'firmware.disasm', hashes['firmware.disasm']).decode()
    bound_read(directory / 'firmware.bin', hashes['firmware.bin'])
    events = parse_events(raw)
    for key in ENERGY_MICRO.keys() - {'nonmul'} | {'instructions', 'bl'}:
        if events[key] != expected_events[key]:
            raise ValueError(f'raw events disagree with frozen row: {identity}/{key}')
    mnemonics = audit_instruction_subset(disasm)
    if events['pop_pc'] and 'pop' not in mnemonics:
        raise ValueError('recorded return counter without POP instruction')
    cycles = corrected_cycles(events)
    if cycles - events['pop_pc'] != legacy:
        raise ValueError('legacy cycles do not reconstruct from bound raw events')
    if type(samples) is not int or samples <= 0:
        raise ValueError('invalid measured sample count')
    weighted = sum(weight * (events['instructions'] - events['mul'] if key == 'nonmul'
                             else events[key]) for key, weight in ENERGY_MICRO.items())
    exact_energy = Decimal(weighted) / 1_000_000
    if abs(exact_energy - Decimal(str(energy))) > Decimal('0.000001'):
        raise ValueError('frozen energy disagrees with raw events')
    return {'group': group, 'identity': identity, 'samples': samples,
            'legacy_cycles': legacy, 'pop_pc': events['pop_pc'],
            'corrected_cycles': cycles, 'cycles_per_output': _decimal_ratio(cycles, samples),
            'energy_nj': format(exact_energy, '.6f'), 'energy_verified_unchanged': True,
            'events': events, 'instruction_subset': mnemonics,
            'directory': directory.relative_to(root.resolve()).as_posix(),
            'bound_sha256': {key: hashes[key] for key in
                             ('firmware.stderr', 'firmware.disasm', 'firmware.bin')}}


def _key(row):
    return row['compiler'], row['block'], row['variant']


def build_report(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    documents = {name: json.loads(bound_read(root / name, digest)) for name, digest in PINNED.items()
                 if name.endswith('.json')}
    historical = documents['research/fir-sharing-probe/results.json']['rows']
    partial = documents['research/fir-sharing-probe/partial-direct/results.json']['rows']
    sources = {_key(r): r for r in historical + partial
               if r['filter'] == 'speech_minphase48' and r['maximum'] == 32768}
    rows = []
    for saved in documents['research/fir-paper/results.json']['rows']:
        source = sources[_key(saved)]
        parent = 'research/fir-sharing-probe/'
        if saved['variant'] == 'partial_direct32x2':
            parent += 'partial-direct/'
        if source['artifacts']['firmware.bin'] != saved['binary_sha256']:
            raise ValueError('original row binary identity mismatch')
        rows.append(_row(root, 'original', {key: saved[key] for key in ('compiler', 'block', 'variant')},
                         parent + source['directory'], source['artifacts'], saved['arm_zero_ws_cycles'],
                         saved['samples'], saved['estimated_cpu_energy_nj'], saved))
    unavailable = []
    for saved in documents['research/fir-upgrades/panel-results.json']['rows']:
        if saved['status'] == 'unavailable':
            unavailable.append(saved)
            continue
        if saved['status'] != 'admitted':
            raise ValueError('unexpected nonadmitted panel identity')
        paths = saved['artifact_paths']
        hashes = {paths[key]: saved['artifact_sha256'][key] for key in ('stderr', 'disassembly', 'binary')}
        rows.append(_row(root, 'panel', saved['identity'], 'research/fir-upgrades/' + saved['directory'],
                         hashes, saved['arm_zero_ws_cycles'], saved['measured_samples'],
                         saved['energy_nj'], saved['events']))
    for saved in documents['research/fir-upgrades/intervention-results.json']['rows']:
        rows.append(_row(root, 'intervention', saved['identity'],
                         'research/fir-upgrades/' + saved['directory'], saved['artifacts'],
                         saved['cost']['arm_zero_ws_cycles'], saved['identity']['samples'],
                         saved['cost']['energy_nj'], saved['events']))
    counts = dict(Counter(r['group'] for r in rows), panel_unavailable=len(unavailable))
    if counts != {'original': 20, 'panel': 280, 'intervention': 4, 'panel_unavailable': 8}:
        raise ValueError('incomplete timing correction inventory')
    originals = {_key(r['identity']): r for r in rows if r['group'] == 'original'}
    contrasts = []
    for compiler in ('gcc10', 'gcc15'):
        for block in (1, 64):
            for left, right in (('partial_direct32x2', 'spec_direct'),
                                ('trans_hcub_demand', 'trans_const'),
                                ('trans_hcub_demand', 'partial_direct32x2')):
                a, b = originals[compiler, block, left], originals[compiler, block, right]
                contrasts.append({'compiler': compiler, 'block': block, 'left': left, 'right': right,
                                  'legacy_delta': a['legacy_cycles'] - b['legacy_cycles'],
                                  'corrected_delta': a['corrected_cycles'] - b['corrected_cycles']})
    cells = defaultdict(list)
    for row in rows:
        if row['group'] == 'panel':
            cells[tuple((k, v) for k, v in row['identity'].items() if k != 'variant')].append(row)
    changes = []
    for cell in cells.values():
        for a, b in combinations(cell, 2):
            old = a['legacy_cycles'] - b['legacy_cycles']
            new = a['corrected_cycles'] - b['corrected_cycles']
            if (old > 0) - (old < 0) != (new > 0) - (new < 0):
                changes.append({'left': a['identity'], 'right': b['identity'],
                                'legacy_delta': old, 'corrected_delta': new})
    intervention = {(r['identity']['compiler'], r['identity']['variant']): r
                    for r in rows if r['group'] == 'intervention'}
    return {'schema': 'fir-corrected-timing-v2', 'model': MODEL,
            'formula': 'NI+R+W+F+2B+NBL+N_POP_PC',
            'source': 'https://documentation-service.arm.com/static/5e8e294afd977155116a6a5b',
            'assumptions': ['zero waits', 'single-cycle MUL', 'admitted scalar instruction subset',
                            'no interrupts/peripheral timing', 'not physical timing validation'],
            'source_sha256': PINNED, 'counts': counts, 'rows': rows,
            'panel_unavailable': unavailable, 'original_contrasts': contrasts,
            'panel_pair_cycle_order_changes': changes,
            'explanation': {'compiler_cycle_gap':
                originals['gcc15', 1, 'partial_direct32x2']['corrected_cycles']
                - originals['gcc10', 1, 'partial_direct32x2']['corrected_cycles']},
            'intervention': {'cycle_reductions': {c:
                intervention[c, 'general']['corrected_cycles']
                - intervention[c, 'specialized']['corrected_cycles'] for c in ('gcc10', 'gcc15')}},
            'target_tools_executed': False,
            'supersession': 'Cycle fields only; frozen v1 inventories remain historical records.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path, default=HERE / 'timing')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = build_report(args.repo_root)
    target = args.output_dir / 'corrected-timing.json'
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise ValueError('saved corrected timing differs from raw-evidence reconstruction')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'counts': result['counts'], 'panel_pair_order_changes':
                      len(result['panel_pair_cycle_order_changes']), 'target_tools_executed': False}))


if __name__ == '__main__':
    main()
