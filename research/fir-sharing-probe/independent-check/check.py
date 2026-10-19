"""Independent FIR reference and saved-evidence checker (Python standard library).

No imports from the generator, peer runner or their reference functions. Never
executes target firmware or writes outside the explicitly requested report files.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
DESIGN_SHA = 'bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f'
RESULTS_SHA = '57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa'
FILTER = 'speech_minphase48'
CONFIGS = {(c, b) for c in ('gcc10', 'gcc15') for b in (1, 64)}
NONTRANS = {'direct64', 'cmsis64', 'cmsis64_unroll', 'spec_direct'}
CONTROLS = NONTRANS | {'trans_const', 'trans_hcub_demand'}
ENERGY = {'nonmul': '0.964258', 'mul': '1.652455', 'taken_branches': '2.091986',
          'ram_reads': '1.109833', 'ram_writes': '0.650563', 'flash_reads': '0.633621'}
LABELS = {'Executed insns': 'instructions', 'RAM data reads': 'ram_reads',
          'RAM writes': 'ram_writes', 'Flash data reads': 'flash_reads',
          'Flash writes': 'flash_writes', 'Taken branches': 'taken_branches',
          'Flash insn reads': 'flash_fetches', 'BL insns': 'bl'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(h, x):
    """Literal lag-order integer convolution, floor and one final saturation."""
    return [max(-32768, min(32767, sum(int(c) * int(x[n-k])
            for k, c in enumerate(h) if k <= n) // 32768)) for n in range(len(x))]


def retained_state(h, x, transposed=False):
    if not transposed:
        return ([0] * (len(h)-1) + list(x))[-(len(h)-1):] if len(h) > 1 else []
    # State i holds the unquantized delayed contribution to future output i+1.
    return [sum(int(h[k]) * int(x[-1-(k-i-1)])
                for k in range(i+1, len(h)) if k-i <= len(x))
            for i in range(len(h)-1)]


def partition_reference(h, x, partitions):
    require(partitions and all(type(n) is int and n > 0 for n in partitions),
            'partitions must contain positive sizes')
    require(sum(partitions) == len(x), 'partitions must consume the complete stream')
    outputs, histories, off = [], [], 0
    for size in partitions:
        end = off + size
        outputs.extend(reference(h, x[:end])[off:end])
        histories.append(retained_state(h, x[:end]))
        off = end
    return outputs, histories


def arithmetic_certificate(h):
    require(len(h) == 48, 'fixed certificate requires 48 taps')
    groups = [h[:2], h[2:]]
    bounds = [32768 * sum(abs(c) for c in group) for group in groups]
    require(all(bound <= 2**31-1 for bound in bounds), 'unsafe int32 partial bound')
    require(all(abs(c) * 32768 <= 2**31-1 for c in h), 'unsafe int32 product')
    # A positive endpoint uses +32767 for positive coefficients and -32768 for
    # negative coefficients. Reverse lag order to construct chronological input.
    positive = [32767 if c >= 0 else -32768 for c in reversed(h)]
    negative = [-32768 if c >= 0 else 32767 for c in reversed(h)]
    return {'groups_zero_based_half_open': [[0, 2], [2, 48]],
            'partial_l1': [sum(abs(c) for c in group) for group in groups],
            'partial_absolute_bounds': bounds, 'full_absolute_bound': sum(bounds),
            'every_partial_prefix_safe_by_triangle_inequality': True,
            'positive_window': positive, 'negative_window': negative,
            'positive_aligned_sum': sum(c*x for c, x in zip(h, reversed(positive))),
            'negative_aligned_sum': sum(c*x for c, x in zip(h, reversed(negative))),
            'final_addition': 'widen each partial to int64 before addition; quantize once'}


def record(text, prefix):
    lines = re.findall(rf'^{re.escape(prefix)}:([0-9a-f]*)$', text, re.M)
    require(len(lines) == 1, f'exactly one {prefix} record required')
    return lines[0]


def decode_words(text, prefix, bits):
    encoded = record(text, prefix)
    digits = bits // 4
    require(len(encoded) % digits == 0, f'{prefix} record has truncated word')
    values = [int(encoded[i:i+digits], 16) for i in range(0, len(encoded), digits)]
    return [v - 2**bits if v >= 2**(bits-1) else v for v in values]


def raw_events(stderr):
    values = {}
    for label, key in LABELS.items():
        matches = re.findall(rf'^{re.escape(label)}:\s*([0-9]+)\s*$', stderr, re.M)
        require(len(matches) == 1, f'missing/duplicate raw counter {label}')
        values[key] = int(matches[0])
    opcode_rows = re.findall(r'^\s*(\d+):\s*(\d+),\s*\[([^\]]+)\]\s*$', stderr, re.M)
    require(len(opcode_rows) == 64 and {int(i) for i, _, _ in opcode_rows} == set(range(64)),
            'opcode histogram must contain 64 unique rows')
    require(sum(int(total) for _, total, _ in opcode_rows) == values['instructions'],
            'opcode totals disagree with instruction counter')
    histogram = {}
    # The pinned simulator's exmemwb.c increments secondary bins only in
    # these dispatchers. Other primary opcodes legitimately have zero bins.
    secondary_rows = {6, 7, 16, 17, 20, 21, 22, 23, 44, 46, 47}
    for index, total, encoded in opcode_rows:
        parts = [part.strip() for part in encoded.split(',')]
        require(len(parts) == 16 and all(re.fullmatch(r'[0-9]+', part) for part in parts),
                f'malformed opcode bins in row {index}')
        bins = list(map(int, parts))
        expected = int(total) if int(index) in secondary_rows else 0
        require(sum(bins) == expected, f'opcode bins disagree with row {index} total')
        histogram[int(index)] = bins
    values['mul'] = histogram[16][13]
    markers = re.findall(r'GPIOC\[0\] (raised|cleared) at cycle (\d+)', stderr)
    require([kind for kind, _ in markers] == ['raised', 'cleared'], 'bad measurement markers')
    values['raw_tick_delta'] = int(markers[1][1]) - int(markers[0][1]) - 2
    # Closing STR is counted in NI and fetches, but not in transfer counters.
    values['instructions'] -= 1
    values['flash_fetches'] -= 1
    require(all(v >= 0 for v in values.values()), 'negative corrected raw event')
    require(values['mul'] <= values['instructions'], 'MUL count exceeds instructions')
    require(values['flash_writes'] == 0, 'Flash writes are outside the cost model')
    return values


def costs(events):
    cycles = (events['instructions'] + events['ram_reads'] + events['ram_writes'] +
              events['flash_reads'] + 2*events['taken_branches'] + events['bl'])
    counts = dict(events, nonmul=events['instructions']-events['mul'])
    energy = sum(Decimal(weight) * counts[name] for name, weight in ENERGY.items())
    return cycles, float(energy)


def contained(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root), f'artifact path escapes root: {relative}')
    return path


def elf_symbols(path):
    """Read sizes from an ARM ELF32 little-endian symbol table, without binutils."""
    data = Path(path).read_bytes()
    require(data[:7] == b'\x7fELF\x01\x01\x01', 'expected little-endian ELF32')
    head = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    require(head[2] == 40, 'expected ARM ELF machine')
    offset, entry_size, count = head[6], head[11], head[12]
    require(entry_size == 40 and offset + count*40 <= len(data), 'invalid ELF sections')
    sections = [struct.unpack_from('<IIIIIIIIII', data, offset+i*40) for i in range(count)]
    result = {}
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        require(section[9] == 16 and section[6] < len(sections), 'invalid ELF symbol table')
        strings = sections[section[6]]
        names = data[strings[4]:strings[4]+strings[5]]
        for off in range(section[4], section[4]+section[5], 16):
            name, _, size, _, _, index = struct.unpack_from('<IIIBBH', data, off)
            if name and size and index:
                result[names[name:names.index(b'\0', name)].decode()] = size
    require('probe_process' in result, 'ELF lacks probe_process symbol')
    return result


def instruction_subset(disassembly):
    """Screen the documented scalar integer subset, not literal-pool data."""
    allowed = set(('adc adcs add adds adr and ands asr asrs bic bics bl blx bx cmn cmp '
        'eor eors ldm ldmia ldr ldrb ldrh ldrsb ldrsh lsl lsls lsr lsrs mov movs '
        'mul muls mvn mvns neg negs nop orr orrs pop push rev rev16 revsh ror rors '
        'rsb rsbs sbc sbcs stm stmia str strb strh sub subs sxtb sxth tst uxtb uxth').split())
    function, seen = '', set()
    for line in disassembly.splitlines():
        label = re.match(r'^[0-9a-f]+ <([^>]+)>:', line)
        if label:
            function = label[1]
        fields = line.split('\t')
        if len(fields) < 3 or not re.fullmatch(r'[0-9a-f]{4}(?: [0-9a-f]{4})?', fields[1].strip()):
            continue
        mnemonic = fields[2].split()[0].split('.')[0]
        if not mnemonic or (mnemonic == 'svc' and function == 'Reset_Handler'):
            continue
        require(mnemonic in allowed or re.fullmatch(r'b(eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?', mnemonic),
                f'unsupported instruction in {function}: {mnemonic}')
        seen.add(mnemonic)
    require(seen, 'no instructions in disassembly')
    return sorted(seen)


def resource_diagnostics(row, directory):
    parsed = []
    for filename in row['artifacts']:
        if filename.endswith('.su'):
            parsed.extend({'function': name, 'bytes': int(size), 'kind': kind}
                          for name, size, kind in re.findall(
                              r'\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)',
                              (directory / filename).read_text()))
    identity = lambda s: (s['function'], s['bytes'], s['kind'])
    require(Counter(map(identity, parsed)) == Counter(map(identity, row['stack_usage'])),
            'stack diagnostics disagree with raw .su files')
    frames = {item['function']: item['bytes'] for item in parsed}
    require('probe_process' in frames, 'missing probe_process frame diagnostic')
    symbols = elf_symbols(directory / 'firmware.elf')
    selected = {'probe_process', 'quant', 'h.0', 'reversed.0'}
    variant = row['variant']
    if variant in {'direct64', 'direct32', 'fold64', 'fold32'}:
        selected.add(variant)
    if variant.startswith('cmsis'):
        selected.add('arm_fir_fast_q15' if variant.startswith('cmsis32') else 'arm_fir_q15')
    included = {k: v for k, v in symbols.items() if k in selected or k.startswith('quant.')}
    return {'kernel_and_coefficient_symbol_bytes': sum(included.values()),
            'included_symbols': included, 'probe_process_stack_bytes': frames['probe_process'],
            'kernel_function_frames': {k: v for k, v in frames.items()
                                       if k in selected or k.startswith('quant.')},
            'state_allocation_bytes': row['state_allocation_bytes']}


def verify_row(row, root, h, x):
    require((row['compiler'], row['block']) in CONFIGS, 'unsupported compiler/block')
    require(row['filter'] == FILTER and row['maximum'] == 32768 and row['samples'] == 257,
            'numeric domain/filter/sample metadata mismatch')
    require(row['variant'] in CONTROLS | {'partial_direct32x2'}, 'unexpected variant')
    directory = contained(root, row['directory'])
    artifacts = row['artifacts']
    required = {'firmware.bin', 'firmware.elf', 'firmware.disasm', 'firmware.stdout',
                'firmware.stderr', 'firmware.c'}
    require(required <= artifacts.keys(), f'missing required artifact: {required-artifacts.keys()}')
    require(any(k.endswith('.su') for k in artifacts), 'missing stack artifact')
    require(any(k.endswith('.c') and k != 'firmware.c' for k in artifacts), 'missing kernel source artifact')
    for filename, digest in artifacts.items():
        path = contained(directory, filename)
        require(path.is_file() and sha(path) == digest, f'artifact hash mismatch: {filename}')
    firmware = (directory / 'firmware.c').read_text()
    arrays = re.findall(r'\binput_data\s*\[[^\]]*\]\s*=\s*\{([^}]+)\}', firmware)
    require(len(arrays) == 1, 'missing/duplicate firmware input array')
    inputs = [int(v.strip()) for v in arrays[0].split(',') if v.strip()]
    require(inputs == x, 'firmware input identity mismatch')
    for macro, expected in [('BLOCK', row['block']), ('SAMPLES', len(x))]:
        require(re.findall(rf'^#define\s+{macro}\s+(\d+)\s*$', firmware, re.M) == [str(expected)],
                f'firmware {macro} mismatch')
    stdout = (directory / 'firmware.stdout').read_text()
    require(decode_words(stdout, 'O', 16) == reference(h, x), 'output mismatch')
    require(decode_words(stdout, 'H', 64) == retained_state(h, x, row['variant'].startswith('trans_')),
            'retained state/history mismatch')
    require(record(stdout, 'G') == '5a5a5a5a'*4 + '5a5a'*4, 'state/output guard mismatch')
    allocation = record(stdout, 'M')
    require(len(allocation) == 8 and int(allocation, 16) == row['state_allocation_bytes'],
            'state allocation mismatch')
    if row['variant'] in {'spec_direct', 'partial_direct32x2'}:
        require(int(allocation, 16) == 2*(48+row['block']), 'direct state layout mismatch')
    require(type(row['outputs_verified']) is int and row['outputs_verified'] == len(x) and
            row['retained_state_verified'] is True and row['guards_verified'] is True,
            'verification metadata mismatch')
    events = raw_events((directory / 'firmware.stderr').read_text())
    mnemonics = instruction_subset((directory / 'firmware.disasm').read_text())
    if 'mnemonics' in row:
        require(row['mnemonics'] == mnemonics, 'instruction-subset metadata mismatch')
    for name, value in events.items():
        # Older result format always includes fetches/ticks. Peer schema may omit
        # those diagnostic fields; all cost-driving counters remain mandatory.
        if name in {'flash_fetches', 'raw_tick_delta'} and name not in row:
            continue
        require(type(row.get(name)) is int and row[name] == value, f'raw counter mismatch: {name}')
    cycles, energy = costs(events)
    require(row['arm_zero_ws_cycles'] == cycles, 'cycle cost disagrees with raw counters')
    require(isinstance(row['estimated_cpu_energy_nj'], (float, int)) and
            math.isfinite(row['estimated_cpu_energy_nj']) and
            abs(row['estimated_cpu_energy_nj'] - energy) < 1e-7,
            'energy cost disagrees with raw counters')
    return {'compiler': row['compiler'], 'block': row['block'], 'variant': row['variant'],
            'directory': row['directory'], 'samples': len(x),
            'arm_zero_ws_cycles': cycles, 'cycles_per_output': cycles/len(x),
            'estimated_cpu_energy_nj': energy, 'energy_nj_per_output': energy/len(x),
            'artifacts_verified': len(artifacts), 'mnemonics': mnemonics,
            **resource_diagnostics(row, directory)}


def verify_existing(probe_root):
    root = Path(probe_root)
    design_file = root.parent / 'fir-baseline/selection-design.json'
    require(sha(design_file) == DESIGN_SHA, 'frozen design hash mismatch')
    require(sha(root / 'results.json') == RESULTS_SHA, 'frozen sharing results hash mismatch')
    data = json.loads((root / 'results.json').read_text())
    design = json.loads(design_file.read_text())
    h, x = design['filters'][FILTER]['coefficients'], design['inputs']['adc_raw'][:257]
    require(data['design_sha256'] == DESIGN_SHA and data['actual_input'] == x, 'input metadata mismatch')
    require(data['model']['energy_weights_nj'] == {k: float(v) for k, v in ENERGY.items()},
            'energy-model parameter mismatch')
    require(data['model']['hardware_validated'] is False and data['model']['raw_ticks_are_cycles'] is False,
            'model scope mismatch')
    require(sha(root / 'probe.py') == data['source_sha256'], 'frozen generator source mismatch')
    require(sha(root / 'PROTOCOL.md') == data['protocol_sha256'], 'frozen protocol mismatch')
    for filename, digest in data['dependency_sources'].items():
        require(sha(contained(root.parent, filename)) == digest,
                f'frozen dependency source mismatch: {filename}')
    selected = [r for r in data['rows'] if r['filter'] == FILTER and r['maximum'] == 32768
                and r['variant'] in CONTROLS]
    identities = [(r['compiler'], r['block'], r['variant']) for r in selected]
    expected = {(c, b, v) for c, b in CONFIGS for v in CONTROLS}
    require(len(identities) == len(expected) and set(identities) == expected,
            'missing/duplicate historical control configurations')
    rows = [verify_row(row, root, h, x) for row in selected]
    return {'design_sha256': DESIGN_SHA, 'sharing_results_sha256': RESULTS_SHA,
            'verification_source_sha256': sha(__file__),
            'filter': FILTER, 'maximum': 32768, 'samples': len(x),
            'arithmetic_certificate': arithmetic_certificate(h), 'rows': rows,
            'verified_output_comparisons': sum(r['samples'] for r in rows),
            'compilers': data['compilers'], 'model': data['model'],
            'peer_status': 'pending; no peer measurements checked'}


def verify_peer(data, peer_root, baseline, h, x):
    require(data.get('stage') == 'post-audit missing-control', 'peer stage mismatch')
    for aliases, expected in [(['design_sha256'], DESIGN_SHA),
                              (['sharing_results_sha256', 'baseline_results_sha256',
                                'results_sha256'], RESULTS_SHA)]:
        found = [data[k] for k in aliases if k in data]
        require(found and all(v == expected for v in found), f'peer frozen hash mismatch: {aliases[0]}')
    for compiler in ('gcc10', 'gcc15'):
        identity = data.get('compilers', {}).get(compiler, {})
        for key in ('sha256', 'version'):
            require(identity.get(key) == baseline['compilers'][compiler][key],
                    f'peer compiler {compiler} {key} mismatch; use the pinned environment')
        flags = identity.get('flags', data.get('flags'))
        require(isinstance(flags, list) and all(isinstance(f, str) for f in flags),
                f'peer compiler {compiler} needs an explicit flags list')
        needed = {'-mcpu=cortex-m0', '-mthumb', '-std=c11', '-ffreestanding', '-fno-builtin',
                  '-ffunction-sections', '-fdata-sections', '-g0', '-O2'}
        require(needed <= set(flags), f'peer compiler {compiler} flags mismatch')
        require(all(not f.startswith('-flto') and (not f.startswith('-O') or f == '-O2') and
                    (not f.startswith('-mcpu=') or f == '-mcpu=cortex-m0') and
                    not f.startswith(('-march=', '-mtune=', '-marm')) for f in flags),
                f'peer compiler {compiler} incompatible flags')
    model = data.get('model', {})
    for key in ('simulator_commit', 'energy_weights_nj', 'hardware_validated', 'raw_ticks_are_cycles',
                'configuration', 'timing_formula'):
        require(model.get(key) == baseline['model'][key], f'peer model mismatch: {key}')
    if 'simulator_sha256' in data:
        require(data['simulator_sha256'] == baseline['simulator_sha256'], 'peer simulator binary mismatch')
    rows = data.get('rows', [])
    keys = [(r.get('compiler'), r.get('block')) for r in rows]
    require(len(keys) == 4 and set(keys) == CONFIGS, 'peer requires four distinct configurations')
    require(all(r.get('variant') == 'partial_direct32x2' for r in rows), 'peer variant mismatch')
    return [verify_row(row, peer_root, h, x) for row in rows]


def comparison_markdown(result):
    lines = ['# Missing-direct-baseline comparison', '',
        'Filter `speech_minphase48`; full-int16 guarantee; 257 frozen ADC samples; '
        '`-O2`, Cortex-M0 Thumb, no LTO. Costs include recurring state, stream, call '
        'and final short-block work. All costs below are estimates, not physical measurements.', '',
        'Each historical row was independently checked against raw output/history/guards, '
        'event counters, artifact hashes, ELF symbols and compiler stack reports. '
        + ('Four peer evidence rows passed those checks; manual arithmetic and assembly review remains required.'
           if result.get('peer_rows') else
           'The peer result remains pending until four complete rows pass the same checks.'), '',
        '| Compiler | Block | Variant | Status | Cycles/output | Modeled nJ/output | '
        'Kernel+coefficient symbol bytes | State bytes | Wrapper frame bytes |',
        '|---|---:|---|---|---:|---:|---:|---:|---:|']
    comparisons = []
    for compiler, block in sorted(CONFIGS):
        rows = [r for r in result['rows'] if (r['compiler'], r['block']) == (compiler, block)]
        controls = [r for r in rows if r['variant'] in NONTRANS]
        energy_best = min(controls, key=lambda r: r['estimated_cpu_energy_nj'])
        cycle_best = min(controls, key=lambda r: r['arm_zero_ws_cycles'])
        names = list(dict.fromkeys([energy_best['variant'], cycle_best['variant'], 'spec_direct',
                                   'trans_const', 'trans_hcub_demand']))
        for name in names:
            r = next(row for row in rows if row['variant'] == name)
            lines.append(f'| {compiler} | {block} | {name} | verified historical | '
                         f'{r["cycles_per_output"]:.2f} | {r["energy_nj_per_output"]:.2f} | '
                         f'{r["kernel_and_coefficient_symbol_bytes"]} | {r["state_allocation_bytes"]} | '
                         f'{r["probe_process_stack_bytes"]} |')
        peer = next((r for r in result.get('peer_rows', [])
                     if (r['compiler'], r['block']) == (compiler, block)), None)
        if peer is None:
            lines.append(f'| {compiler} | {block} | partial_direct32x2 | pending | — | — | — | — | — |')
        else:
            lines.append(f'| {compiler} | {block} | partial_direct32x2 | verified peer evidence | '
                         f'{peer["cycles_per_output"]:.2f} | {peer["energy_nj_per_output"]:.2f} | '
                         f'{peer["kernel_and_coefficient_symbol_bytes"]} | {peer["state_allocation_bytes"]} | '
                         f'{peer["probe_process_stack_bytes"]} |')
        desc = (f'{compiler}, block {block}: strongest historical nontransposed energy control '
                f'`{energy_best["variant"]}`; cycle control `{cycle_best["variant"]}`.')
        if peer:
            hcub = next(r for r in rows if r['variant'] == 'trans_hcub_demand')
            desc += (f' Hcub cost relative to new direct: '
                     f'{100*(hcub["estimated_cpu_energy_nj"]/peer["estimated_cpu_energy_nj"]-1):+.2f}% '
                     f'modeled energy; {100*(hcub["arm_zero_ws_cycles"]/peer["arm_zero_ws_cycles"]-1):+.2f}% '
                     'estimated cycles. Negative means Hcub costs less.')
        comparisons.append(desc)
    lines += ['', *comparisons, '',
        'Code-size metric matches the historical selected-symbol diagnostic: '
        '`probe_process`, named kernel/library functions, `quant*`, and `h.0`/`reversed.0` '
        'coefficient symbols when present. It excludes fixture code and can exclude '
        'other compiler-generated helpers; it is not total image size. The full included '
        'symbol map is in `verification.json`.', '',
        'Wrapper frame is `probe_process` alone, not peak stack. Callee frames (including '
        'library/kernel frames) are recorded separately in `kernel_function_frames` in '
        '`verification.json`. Static compiler reports do not establish maximum live '
        'stack or physical SRAM high-water usage.', '',
        'Decision remains conditional. These already-inspected cases are a missing-control '
        'check, not fresh held-out validation. A surviving benefit/tradeoff still needs '
        'an emitted-code explanation and the prior-art distinctions in [positioning.md](positioning.md). '
        'An erased benefit requires revising the headline; no peer values are inferred.', '']
    return '\n'.join(lines)


def reference_cases(h):
    proof = arithmetic_certificate(h)
    signals = {'zeros': [0]*87, 'signed_edges': [-32768, 32767, 0, -1, 1]*53,
               'positive_aligned': proof['positive_window']+[0]*73,
               'negative_aligned': proof['negative_window']+[0]*73}
    cases = []
    for name, x in signals.items():
        sizes, offset, index = [], 0, 0
        while offset < len(x):
            n = min([1, 64, 3, 16][index % 4], len(x)-offset)
            sizes.append(n)
            offset += n
            index += 1
        outputs, histories = partition_reference(h, x, sizes)
        cases.append({'name': name, 'input': x, 'partitions': sizes, 'outputs': outputs,
                      'history_after_each_call': histories,
                      'final_transposed_state': retained_state(h, x, True)})
    return {'design_sha256': DESIGN_SHA, 'filter': FILTER,
            'meaning': 'independent integer specifications, not executed target tests', 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-root', type=Path, default=HERE.parent,
                        help='sharing-probe directory containing frozen results and raw build/')
    parser.add_argument('--peer-results', type=Path, help='optional peer results.json; requires four rows')
    parser.add_argument('--output-dir', type=Path, default=HERE)
    args = parser.parse_args()
    try:
        result = verify_existing(args.probe_root)
        design = json.loads((args.probe_root.parent/'fir-baseline/selection-design.json').read_text())
        h, x = design['filters'][FILTER]['coefficients'], design['inputs']['adc_raw'][:257]
        if args.peer_results:
            baseline = json.loads((args.probe_root/'results.json').read_text())
            peer = json.loads(args.peer_results.read_text())
            result['peer_rows'] = verify_peer(peer, args.peer_results.parent, baseline, h, x)
            result['peer_results_sha256'] = sha(args.peer_results)
            result['peer_status'] = 'four performance rows independently checked; manual arithmetic/assembly review still required'
        # Check everything before writing: a failed run never overwrites a good report.
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for filename, obj in [('verification.json', result), ('reference-cases.json', reference_cases(h))]:
            (args.output_dir/filename).write_text(json.dumps(obj, indent=2)+'\n')
        (args.output_dir/'comparison.md').write_text(comparison_markdown(result))
        print(json.dumps({'historical_rows_verified': len(result['rows']),
                          'output_comparisons': result['verified_output_comparisons'],
                          'peer_rows_verified': len(result.get('peer_rows', [])),
                          'peer_status': result['peer_status']}))
    except (ValueError, KeyError, OSError, TypeError, struct.error, IndexError) as error:
        parser.exit(1, f'check failed: {error}\n')


if __name__ == '__main__':
    main()
