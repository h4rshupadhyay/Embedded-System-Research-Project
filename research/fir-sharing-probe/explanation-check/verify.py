"""Independent admission of a two-compiler FIR explanation accounting report.

Numerical consistency is separate from causal interpretation. Only the older
independent checker's raw transcript decoder and ELF reader are reused; no peer
analyzer or component classification is imported.
"""
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
PROBE = HERE.parent
PARTIAL = PROBE / 'partial-direct'
BASELINE = PROBE.parent / 'fir-baseline'
PEER = PROBE / 'compiler-explanation' / 'accounting.json'
OLD_CHECK = PROBE / 'independent-check' / 'check.py'
HEX = re.compile(r'[0-9a-f]{64}\Z')
SOURCE_SHA = 'eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f'
SHARING_SHA = '57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa'
DESIGN_SHA = 'bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f'
KERNEL_SHA = '5832b52eaf1d5eb76e8087d47307feeccf74809cc0f22b288d111505851501cd'
ARCHIVE_SHA = '8aa24f417ff266a2be2a850750defe06d8cbc46766b03d0ba67639f0a154cb83'
BINARIES = {'gcc10': '07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a',
            'gcc15': '114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470'}
EVENTS = ('instructions', 'mul', 'ram_reads', 'ram_writes', 'flash_reads',
          'flash_writes', 'taken_branches', 'bl')
COMPONENTS = ('stream_wrapper', 'copy_in', 'convolution', 'quantize_store',
              'history_copy', 'function_entry_exit', 'unattributed')
WEIGHTS = {'nonmul': Decimal('0.964258'), 'mul': Decimal('1.652455'),
           'taken_branches': Decimal('2.091986'), 'ram_reads': Decimal('1.109833'),
           'ram_writes': Decimal('0.650563'), 'flash_reads': Decimal('0.633621')}
STATIC_SUFFIXES = ('.disasm', '.elf', '.map', '.su', '.s', '.asm', '.c', '.h', '.bin')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_fields(value, fields, label):
    need(type(value) is dict and set(fields) <= value.keys(), f'{label} missing required fields')


def count(value, label):
    need(type(value) is int and value >= 0, f'{label} must be a nonnegative integer')
    return value


def counter_map(value, label):
    need(type(value) is dict and set(value) == set(EVENTS), f'{label} must have exactly eight counters')
    return {key: count(value[key], f'{label}.{key}') for key in EVENTS}


def strings(value, label):
    need(type(value) is list and all(type(s) is str for s in value), f'{label} must be a string list')
    return value


def safe_file(root, name, label):
    need(type(name) is str and name and not Path(name).is_absolute() and
         all(part not in ('', '.', '..') for part in Path(name).parts) and '\\' not in name,
         f'{label} path must be a contained relative filename')
    root = root.resolve()
    path = (root / name).resolve()
    need(path.is_relative_to(root) and path.is_file(), f'{label} path escapes root or is missing: {name}')
    return path


def old_decoder():
    spec = importlib.util.spec_from_file_location('existing_independent_check', OLD_CHECK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modeled_cost(events):
    cycles = (events['instructions'] + events['ram_reads'] + events['ram_writes'] +
              events['flash_reads'] + 2*events['taken_branches'] + events['bl'])
    counts = dict(events, nonmul=events['instructions']-events['mul'])
    energy = sum(weight*counts[key] for key, weight in WEIGHTS.items())
    return cycles, energy


def static_diagnostics(directory, decoder):
    symbols = decoder.elf_symbols(directory / 'firmware.elf')
    reports = (directory / 'kernel.su').read_text() + (directory / 'firmware.su').read_text()
    frames = re.findall(r'\S+:\d+:\d+:probe_process\t(\d+)\tstatic', reports)
    need(len(frames) == 1, 'source stack report lacks one probe_process frame')
    listing = (directory / 'probe_process.disasm').read_text()
    sites = sum(bool(re.search(r'\[sp(?:,|\])', line)) for line in listing.splitlines())
    return {'probe_process_symbol_bytes': symbols['probe_process'],
            'compiler_frame_bytes': int(frames[0]),
            'sp_relative_instruction_sites': sites}


def frozen_inputs():
    fixed = [(BASELINE / 'selection-design.json', DESIGN_SHA),
             (PROBE / 'results.json', SHARING_SHA),
             (PARTIAL / 'results.json', SOURCE_SHA),
             (PARTIAL / 'kernel.c', KERNEL_SHA),
             (PROBE / 'independent-check' / 'partial-direct-target-evidence.tar.gz', ARCHIVE_SHA)]
    for path, expected in fixed:
        need(path.is_file() and digest(path) == expected, f'frozen source hash mismatch: {path}')
    result = json.loads((PARTIAL / 'results.json').read_text(), parse_float=Decimal)
    need(result.get('variant') == 'partial_direct32x2' and result.get('filter') == 'speech_minphase48'
         and result.get('maximum') == 32768 and result.get('samples') == 257,
         'frozen source metadata mismatch')
    groups = result.get('fixed_groups')
    need(type(groups) is list and [(g.get('first'), g.get('past_last')) for g in groups] ==
         [(0, 2), (2, 48)], 'frozen source groups mismatch')
    need(result.get('design_sha256') == DESIGN_SHA and
         result.get('sharing_results_sha256') == SHARING_SHA, 'frozen source lineage mismatch')
    need(result.get('model', {}).get('hardware_validated') is False and
         result.get('model', {}).get('raw_ticks_are_cycles') is False, 'frozen source model scope mismatch')
    need({k: Decimal(str(v)) for k, v in result['model']['energy_weights_nj'].items()} == WEIGHTS,
         'frozen source energy model mismatch')
    source_rows = [r for r in result['rows'] if r.get('block') == 1]
    need(len(source_rows) == 2 and {r.get('compiler') for r in source_rows} == set(BINARIES),
         'frozen source block1 rows mismatch')
    decoder = old_decoder()
    rows, checked = {}, [str(path) for path, _ in fixed]
    for row in source_rows:
        compiler = row['compiler']
        directory = PARTIAL / 'build' / 'target' / f'{compiler}-b1'
        need(row.get('directory') == f'build/target/{compiler}-b1' and
             row.get('variant') == 'partial_direct32x2' and row.get('samples') == 257 and
             row.get('maximum') == 32768 and row.get('filter') == 'speech_minphase48',
             f'frozen source row identity mismatch: {compiler}')
        artifacts = row.get('artifacts')
        need(type(artifacts) is dict and {'firmware.bin', 'firmware.stderr', 'firmware.elf',
             'probe_process.disasm', 'kernel.su', 'firmware.su'} <= artifacts.keys(),
             f'frozen source artifact manifest incomplete: {compiler}')
        for filename, expected in artifacts.items():
            need(type(expected) is str and HEX.fullmatch(expected), f'source artifact hash malformed: {filename}')
            path = safe_file(directory, filename, 'source artifact')
            need(digest(path) == expected, f'source artifact hash mismatch: {compiler}/{filename}')
            checked.append(str(path))
        need(row['artifacts']['firmware.bin'] == BINARIES[compiler], f'frozen binary identity mismatch: {compiler}')
        events = decoder.raw_events((directory / 'firmware.stderr').read_text())
        totals = {key: events[key] for key in EVENTS}
        need(all(type(row.get(k)) is int and row[k] == totals[k] for k in EVENTS),
             f'frozen source raw counter mismatch: {compiler}')
        cycles, energy = modeled_cost(totals)
        need(row.get('arm_zero_ws_cycles') == cycles and
             Decimal(str(row.get('estimated_cpu_energy_nj'))) == energy,
             f'frozen source modeled cost mismatch: {compiler}')
        rows[compiler] = {'compiler': compiler, 'block': 1, 'binary_sha256': BINARIES[compiler],
                          'totals': totals, 'reconstructed_totals': totals,
                          'estimated_cycles': cycles,
                          'modeled_cpu_energy_nj': str(energy),
                          'static_diagnostics': static_diagnostics(directory, decoder)}
    return rows, checked


def admit_peer(report, root, frozen):
    object_fields(report, ('schema_version', 'stage', 'source_results_sha256', 'evidence', 'rows'), 'peer report')
    need(type(report['schema_version']) is int and report['schema_version'] == 1, 'peer schema_version mismatch')
    need(report['stage'] == 'post-join compiler explanation', 'peer stage mismatch')
    need(report['source_results_sha256'] == SOURCE_SHA, 'peer source_results_sha256 mismatch')
    manifest = report['evidence']
    need(type(manifest) is dict, 'peer evidence manifest must be an object')
    checked = []
    for name, expected in manifest.items():
        need(type(expected) is str and HEX.fullmatch(expected), f'evidence hash malformed: {name}')
        path = safe_file(root, name, 'evidence')
        need(digest(path) == expected, f'evidence hash mismatch: {name}')
        checked.append({'path': name, 'sha256': expected})
    rows = report['rows']
    need(type(rows) is list and len(rows) == 2 and
         all(type(r) is dict for r in rows) and
         {r.get('compiler') for r in rows} == set(BINARIES),
         'peer compiler rows must contain exactly one gcc10 and one gcc15')
    accepted = {}
    for row in rows:
        compiler = row['compiler']
        object_fields(row, ('block', 'binary_sha256', 'method', 'totals', 'components',
                            'static_diagnostics', 'causal_status', 'limitations'), f'{compiler} row')
        need(type(row['block']) is int and row['block'] == 1, f'{compiler} block mismatch')
        need(row['binary_sha256'] == BINARIES[compiler], f'{compiler} binary identity mismatch')
        need(row['method'] in ('saved-evidence', 'trace-reconciled'), f'{compiler} method invalid')
        need(row['causal_status'] in ('supported', 'partial', 'unresolved'), f'{compiler} causal_status invalid')
        strings(row['limitations'], f'{compiler} limitations')
        totals = counter_map(row['totals'], f'{compiler} totals')
        need(totals == frozen[compiler]['totals'], f'{compiler} total mismatch versus frozen raw events')
        diagnostics = row['static_diagnostics']
        object_fields(diagnostics, ('probe_process_symbol_bytes', 'compiler_frame_bytes',
                                    'sp_relative_instruction_sites'), f'{compiler} static_diagnostics')
        for key, expected in frozen[compiler]['static_diagnostics'].items():
            actual = count(diagnostics[key], f'{compiler} static_diagnostics.{key}')
            need(actual == expected, f'{compiler} static_diagnostics.{key} mismatch versus raw artifact')
        components = row['components']
        need(type(components) is list and len(components) == len(COMPONENTS) and
             all(type(c) is dict for c in components) and
             {c.get('name') for c in components} == set(COMPONENTS),
             f'{compiler} component names must occur exactly once')
        summed = {key: 0 for key in EVENTS}
        for component in components:
            name = component['name']
            object_fields(component, ('events', 'basis', 'evidence_refs'), f'{compiler} component {name}')
            basis = component['basis']
            need(basis in ('dynamic-trace', 'exact-control-flow', 'residual'),
                 f'{compiler} component {name} basis invalid')
            need((name == 'unattributed') == (basis == 'residual'),
                 f'{compiler} component {name} basis/residual mismatch')
            events = counter_map(component['events'], f'{compiler} component {name} events')
            need(events['mul'] <= events['instructions'],
                 f'{compiler} component {name} mul exceeds instructions')
            need(events['instructions'] > 0 or not any(events.values()),
                 f'{compiler} component {name} has events with zero instructions')
            for event in ('taken_branches', 'bl'):
                need(events[event] <= events['instructions'],
                     f'{compiler} component {name} {event} exceeds instructions')
            refs = strings(component['evidence_refs'], f'{compiler} component {name} evidence_refs')
            need(len(set(refs)) == len(refs) and all(ref in manifest for ref in refs),
                 f'{compiler} component {name} evidence_refs missing from manifest')
            if name != 'unattributed' and any(events.values()):
                need(refs, f'{compiler} component {name} nonzero events require evidence_refs')
                need(not all(Path(ref).suffix.lower() in STATIC_SUFFIXES for ref in refs),
                     f'{compiler} component {name} static-only evidence cannot support dynamic event counts')
            for key in EVENTS:
                summed[key] += events[key]
        need(summed == totals, f'{compiler} component sum mismatch versus frozen total')
        accepted[compiler] = {'compiler': compiler, 'block': 1, 'totals': totals,
                              'reconstructed_totals': summed,
                              'components': {c['name']: c['events'] for c in components},
                              'static_diagnostics': diagnostics,
                              'method': row['method'], 'reported_causal_status': row['causal_status'],
                              'limitations': row['limitations']}
    return accepted, checked


def candidate_context():
    """Recompute old candidate winners and two distinct comparison denominators."""
    historical = json.loads((PROBE / 'results.json').read_text(), parse_float=Decimal)['rows']
    partial = json.loads((PARTIAL / 'results.json').read_text(), parse_float=Decimal)['rows']
    comparisons = []
    lookup = {}
    for compiler in ('gcc10', 'gcc15'):
        for block in (1, 64):
            options = {}
            for variant in ('trans_const', 'trans_hcub_demand'):
                found = [r for r in historical if r.get('compiler') == compiler and
                         r.get('block') == block and r.get('filter') == 'speech_minphase48' and
                         r.get('maximum') == 32768 and r.get('variant') == variant]
                need(len(found) == 1, f'historical candidate missing/duplicate: {compiler}/b{block}/{variant}')
                options[variant] = Decimal(str(found[0]['estimated_cpu_energy_nj']))
            found = [r for r in partial if r.get('compiler') == compiler and r.get('block') == block]
            need(len(found) == 1, f'partial-direct candidate missing/duplicate: {compiler}/b{block}')
            options['partial_direct32x2'] = Decimal(str(found[0]['estimated_cpu_energy_nj']))
            comparisons.append({'compiler': compiler, 'block': block,
                                'winner': min(options, key=options.get),
                                'modeled_cpu_energy_nj': {k: str(v) for k, v in options.items()}})
            lookup[(compiler, block)] = options
    pct = lambda a, b: str(((1-a/b)*100).quantize(Decimal('0.01')))
    within = pct(lookup[('gcc15', 1)]['trans_hcub_demand'],
                 lookup[('gcc15', 1)]['partial_direct32x2'])
    selectable = {f'block{block}': pct(lookup[('gcc15', block)]['trans_hcub_demand'],
                                      lookup[('gcc10', block)]['partial_direct32x2'])
                  for block in (1, 64)}
    return comparisons, within, selectable


def comparison(result):
    rows = result['source_rows']
    delta = result['delta']
    costs = result['cost_delta']
    lines = ['# GCC10/GCC15 block1 explanation check', '',
             'Frozen `partial_direct32x2`, `speech_minphase48`, 257 samples, full-int16, '
             '`-O2`, no LTO. Values below are reconstructed from the original raw simulator logs '
             'and frozen result, with the closing marker instruction excluded.', '',
             f"Peer accounting status: **{result['status']}**; {result['peer_rows_checked']} peer rows checked. "
             'Manual causal review: **pending**. The checker tests arithmetic and file identity, '
             'not whether PC labels establish a cause.', '',
             '| Counter | GCC10 | GCC15 | GCC15 − GCC10 |', '|---|---:|---:|---:|']
    for key in EVENTS:
        lines.append(f"| {key} | {rows['gcc10']['totals'][key]} | {rows['gcc15']['totals'][key]} | {delta[key]} |")
    lines += ['', f"Estimated zero-wait cycles: {rows['gcc10']['estimated_cycles']} / "
              f"{rows['gcc15']['estimated_cycles']}; delta **{costs['estimated_cycles']}**.",
              f"Modeled CPU nJ: {rows['gcc10']['modeled_cpu_energy_nj']} / "
              f"{rows['gcc15']['modeled_cpu_energy_nj']}; delta **{costs['modeled_cpu_energy_nj']} nJ**.",
              '', 'These are simulator/model aggregates, not measured wall time or board energy. '
              'Static frame, symbol and stack-address sites are diagnostics, not dynamic event counts.', '']
    lines += ['| Compiler | Block | Lowest modeled CPU-energy candidate |',
              '|---|---:|---|']
    for candidate in result['candidate_comparisons']:
        lines.append(f"| {candidate['compiler']} | {candidate['block']} | {candidate['winner']} |")
    lines += ['', 'Within GCC15/block1, demand Hcub uses '
              f"{result['within_gcc15_block1_hcub_saving_percent']}% less modeled energy than "
              'GCC15 partial direct. When selecting the lower-cost compiler for each variant, '
              'GCC15 demand Hcub saves '
              f"{result['selectable_compiler_hcub_saving_percent']['block1']}% at block1 and "
              f"{result['selectable_compiler_hcub_saving_percent']['block64']}% at block64 "
              'relative to GCC10 partial direct. These denominators describe different comparisons.', '']
    if result['status'] == 'pending':
        lines += ['The real peer `accounting.json` has not been delivered. Fixture tests are illustrative '
                  'and do not verify a generated-code explanation.', '']
    else:
        lines += ['The peer rows reconcile numerically. Source-value flow, PC boundaries, '
                  'and any spill or causal claim still need manual review.', '']
    return '\n'.join(lines)


def verify(peer_path):
    frozen, source_files = frozen_inputs()
    candidates, within, selectable = candidate_context()
    delta = {key: frozen['gcc15']['totals'][key]-frozen['gcc10']['totals'][key] for key in EVENTS}
    cost_delta = {'estimated_cycles': frozen['gcc15']['estimated_cycles']-frozen['gcc10']['estimated_cycles'],
                  'modeled_cpu_energy_nj': str(Decimal(frozen['gcc15']['modeled_cpu_energy_nj'])-
                                                Decimal(frozen['gcc10']['modeled_cpu_energy_nj']))}
    result = {'schema_version': 1, 'status': 'pending', 'source_results_sha256': SOURCE_SHA,
              'peer_report_sha256': None, 'peer_rows_checked': 0,
              'peer_component_deltas': None,
              'source_rows': frozen, 'delta': delta, 'cost_delta': cost_delta,
              'candidate_comparisons': candidates,
              'within_gcc15_block1_hcub_saving_percent': within,
              'selectable_compiler_hcub_saving_percent': selectable,
              'source_files_checked': source_files, 'evidence_files_checked': [],
              'manual_causal_review': 'pending',
              'limitations': ['Aggregate event logs do not supply per-PC execution history.',
                              'Numerical reconciliation cannot certify component labels or causal truth.',
                              'Static opcode sites and stack access alone do not establish dynamic counts or spills.']}
    if peer_path.is_file():
        peer = json.loads(peer_path.read_text())
        accepted, evidence = admit_peer(peer, peer_path.parent, frozen)
        component_deltas = {name: {key: accepted['gcc15']['components'][name][key] -
                                          accepted['gcc10']['components'][name][key] for key in EVENTS}
                            for name in COMPONENTS}
        result.update(status='consistent', peer_report_sha256=digest(peer_path),
                      peer_rows_checked=2, peer_rows=accepted, evidence_files_checked=evidence,
                      peer_component_deltas=component_deltas)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--peer-report', type=Path, default=PEER)
    parser.add_argument('--output-dir', type=Path, default=HERE)
    args = parser.parse_args()
    try:
        need(not args.peer_report.exists() or args.peer_report.is_file(), 'peer report path is not a file')
        result = verify(args.peer_report)
        rendered_json = json.dumps(result, indent=2) + '\n'
        rendered_md = comparison(result)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / 'verification.json').write_text(rendered_json)
        (args.output_dir / 'comparison.md').write_text(rendered_md)
        print(json.dumps({'status': result['status'], 'peer_rows_checked': result['peer_rows_checked']}))
    except (ValueError, TypeError, KeyError, OSError, IndexError, json.JSONDecodeError) as error:
        parser.exit(1, f'verification failed: {error}\n')


if __name__ == '__main__':
    main()
