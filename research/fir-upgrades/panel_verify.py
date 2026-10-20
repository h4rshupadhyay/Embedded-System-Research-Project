"""Independent saved-evidence audit for the frozen FIR Task 5 panel.

This module reads protocol and campaign artifacts only. It never imports or calls
the panel runner, generator, quantizer, admission logic, or summary code.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
PROTOCOL_SHA256 = 'd2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c'
DESIGN_SHA256 = '51f8cfec85687672153d10a26e1ab8ab918a37eb2a540490eea2153035f8b414'
INPUTS_SHA256 = '200a4317989c4a2c85aa3727f739921038206a758e99fb052114f925e9cf9b9b'
TEMPLATE_VERSION = 'fir-task5-fixture-template-v1'
TEMPLATE_SHA256 = '36f41fa7b16764bf79012d74ee7d921f9b8b3081758a131c8a37ffdfcb941f35'
ENERGY_MICRO = {'nonmul': 964258, 'mul': 1652455, 'taken_branches': 2091986,
                'ram_reads': 1109833, 'ram_writes': 650563, 'flash_reads': 633621}
LABELS = {'Executed insns': 'instructions', 'RAM data reads': 'ram_reads',
          'RAM writes': 'ram_writes', 'Flash data reads': 'flash_reads',
          'Flash writes': 'flash_writes', 'Taken branches': 'taken_branches',
          'Flash insn reads': 'flash_fetches', 'BL insns': 'bl'}
CASE_FIELDS = ('filter', 'variant', 'compiler', 'block', 'stimulus', 'regime')
PENDING_FAST_REASON = 'pending unresolved pointer-object aliasing'
COMPILER_SHA256 = {'gcc10': '702dfc4dd0b34ee43ecd164a6db6ada4b5583d8945b17bbea3ebe223db765480',
                   'gcc15': '94f60cfbad1091ad86c2435d8b804e82c0fc7e4c16302183c9a60cddd5318b1a'}
LIBGCC_SHA256 = {'gcc10': '7d25476df0fb0cb0133911547da014e94bf610d7a1e975c4c64e76c23fdbe517',
                 'gcc15': '69e7b7a94214a895eafc7a50a90c0f1025d8c47d20c21e5469d3cd74f7bdd7a6'}
BINUTIL_SHA256 = {
    'gcc10': {'as': 'f21f52ab6932e550d9d99d48fa515d7580080b75284ed01f8099700aa01ac4cb',
              'ld': 'fba3179421171001ece6a99f0f75be811bda1211f659a96c0ab8cb337633cd8d',
              'objcopy': '1aa0730c7d30826852356952ab74b9a4391a47f2ace3245eb528f634edaea4a1',
              'objdump': '7c7f72ad6c3d9be7516371ba5f8d3c60e07657f62f27c7920f4d33d553493963',
              'readelf': '29498a88f0195434c7d2fc6d18a2c6acc3b60eb9f1f8bb0020d04d53b1a3e090',
              'nm': 'a4ef81dba869a7d6c104bcf2e2b9b763e84515254537ac15abaaf1f5f6155eb3'},
    'gcc15': {'as': '662ceaeb6ffbb8817b18a59d7fcc30e17049698bf1b53cd240c1ba2823154d7f',
              'ld': '85b0ab8e11edb33f4566eecbae69745eabc2df8963efa8a24a6dff4873eddd67',
              'objcopy': '6b599b2848b40309945ea422972aed139b22bde633a19bcd5ba5162522f47642',
              'objdump': '92a9de1dde1fd0f4d274d55912ab3ec921415b35f02073303357e62bd3b7f2b3',
              'readelf': '9f1a1ae49716e2b58ccc27b7fad1a40cf0df93b2c75c43c062f952ed7fe78654',
              'nm': '532efc24169fa506181bbfcd297a8dc3a7e98352a7e0972ff0cfae429245ad86'},
}
SIMULATOR_SHA256 = 'd1fb48bed5f52e94813372054a086ee003cffb56b98dec3052ef4bfe397d9195'
SIMULATOR_PATCH_SHA256 = '970f73c9644170deddbb57b4a3077a5d8f027a12a3296c403fd04719d54aa0c8'
SOURCES_MANIFEST_SHA256 = '5a3301883e90db9ac41f7c5bed653c9e156ddc1e548784992d62aac9c3076568'
STARTUP_SHA256 = '8859527adcb9943e5a648fcea01fdf8a2506ee27173b08fc55d82cac3a5b4054'
LINKER_SHA256 = '37fd6a919b5887762492571804dc8cdfbc5f87afadae4b31734297d52b55d4ca'
KERNELS_HEADER_SHA256 = '00c2e621e86ee69d6080dd55d4a2bdaa587f6c5284f33e0ad027c12a57703b0c'


def _load_raw_checker():
    path = HERE.parent / 'fir-sharing-probe' / 'independent-check' / 'check.py'
    spec = importlib.util.spec_from_file_location('fir_task5_raw_checker', path)
    if spec is None or spec.loader is None:
        raise ValueError('cannot load frozen independent raw checker')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_RAW = _load_raw_checker()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def rederive_raw_events(stderr: str) -> dict:
    """Use the frozen independent strict decoder and verify its corrected totals."""
    raw = _RAW.raw_events(stderr)
    labels = {}
    for label, key in LABELS.items():
        found = re.findall(rf'^{re.escape(label)}:\s*([0-9]+)\s*$', stderr, re.M)
        _require(len(found) == 1, f'missing/duplicate raw counter {label}')
        labels[key] = int(found[0])
    _require(raw['instructions'] == labels['instructions'] - 1,
             'raw instruction correction is not exactly one closing marker')
    _require(raw['flash_fetches'] == labels['flash_fetches'] - 1,
             'raw fetch correction is not exactly one closing marker')
    _require(raw['flash_writes'] == labels['flash_writes'] == 0,
             'Flash writes are unsupported')
    _require(raw['raw_tick_delta'] >= 0, 'negative marker-adjusted tick delta')
    return raw


def weighted_integer(events: dict) -> int:
    counts = dict(events)
    counts['nonmul'] = events['instructions'] - events['mul']
    _require(counts['nonmul'] >= 0, 'MUL count exceeds corrected instructions')
    return sum(ENERGY_MICRO[k] * counts[k] for k in ENERGY_MICRO)


def derive_cost(events: dict, measured_samples: int) -> dict:
    _require(type(measured_samples) is int and measured_samples > 0,
             'measured sample count must be positive integer')
    cycles = (events['instructions'] + events['ram_reads'] + events['ram_writes'] +
              events['flash_reads'] + 2 * events['taken_branches'] + events['bl'])
    energy = weighted_integer(events)
    energy_decimal = Decimal(energy) / Decimal(1_000_000)
    return {'arm_zero_ws_cycles': cycles, 'cycles_per_output': Decimal(cycles) / measured_samples,
            'energy_weighted_integer': energy, 'energy_nj': energy_decimal,
            'energy_nj_per_output': energy_decimal / measured_samples}


def quantizer_clamp_paths(coefficients: list[int], samples: list[int], begin: int, end: int) -> dict:
    """Count exact source-quantizer threshold paths over an absolute sample range."""
    positive = negative = 0
    for n in range(begin, end):
        total = sum(coefficients[k] * samples[n - k]
                    for k in range(min(n, len(coefficients) - 1) + 1))
        positive += total >= 1073741824
        negative += total <= -1073741824
    return {'positive': positive, 'negative': negative, 'total': positive + negative,
            'predicates': {'positive': 'S>=1073741824', 'negative': 'S<=-1073741824'},
            'range': [begin, end]}


def load_frozen_protocol(root: Path) -> dict:
    path = Path(root) / 'panel-protocol.json'
    raw = path.read_bytes()
    _require(sha256_bytes(raw) == PROTOCOL_SHA256, 'frozen Task 4 protocol digest mismatch')
    return json.loads(raw)


def validate_identity_inventory(rows, protocol: dict) -> dict:
    expected = protocol.get('cases')
    _require(isinstance(expected, list) and len(expected) == 288,
             'frozen protocol case inventory must contain 288 rows')
    actual_keys = [tuple((row.get('identity') or row).get(k) for k in CASE_FIELDS) for row in rows]
    expected_keys = [tuple(row.get(k) for k in CASE_FIELDS) for row in expected]
    duplicates = [key for key, count in Counter(actual_keys).items() if count > 1]
    _require(not duplicates, f'duplicate case identity: {duplicates[0] if duplicates else None}')
    _require(len(actual_keys) == 288 and set(actual_keys) == set(expected_keys),
             'case identity inventory is incomplete or contains an extra identity')
    _require(len(set(expected_keys)) == 288, 'frozen protocol itself has duplicate identities')
    by_key = {tuple((r.get('identity') or r).get(k) for k in CASE_FIELDS): r for r in rows}
    return by_key


def audit_serialized_cost(row: dict, case_dir: Path) -> dict:
    artifacts = row.get('artifacts', {})
    stderr_name = artifacts.get('stderr') or row.get('artifact_paths', {}).get('stderr') or artifacts.get('firmware.stderr')
    _require(isinstance(stderr_name, str), 'raw stderr artifact is missing')
    path = Path(case_dir) / stderr_name
    _require(path.is_file(), 'raw stderr artifact is missing')
    actual_hash = sha256_bytes(path.read_bytes())
    expected_hash = row.get('artifact_sha256', {}).get('stderr') or row.get('artifact_sha256', {}).get('firmware.stderr')
    _require(expected_hash == actual_hash,
             'raw stderr artifact hash mismatch')
    events = rederive_raw_events(path.read_text(errors='strict'))
    derived = derive_cost(events, row.get('measured_samples'))
    serialized_events = row.get('events', {})
    for field, value in events.items():
        observed = row.get(field, serialized_events.get(field))
        _require(type(observed) is int and observed == value,
                 f'raw event mismatch for {field}')
    serialized_cycles = row.get('arm_zero_ws_cycles')
    _require(type(serialized_cycles) is int and serialized_cycles == derived['arm_zero_ws_cycles'],
             'serialized cycles disagree with raw events')
    try:
        serialized_energy = Decimal(str(row.get('energy_nj')))
        serialized_integer = int(row.get('energy_weighted_integer'))
    except (ValueError, TypeError, ArithmeticError):
        raise ValueError('serialized raw-derived energy is invalid')
    _require(serialized_integer == derived['energy_weighted_integer'] and
             serialized_energy == derived['energy_nj'],
             'serialized energy disagrees with raw events')
    _require(Decimal(str(row.get('cycles_per_output'))) == derived['cycles_per_output'] and
             Decimal(str(row.get('energy_nj_per_output'))) == derived['energy_nj_per_output'],
             'serialized normalized cost disagrees with raw events')
    return {'events': events, **derived}


def _words(text: str, prefix: str, bits: int):
    values = re.findall(rf'^{re.escape(prefix)}:([0-9a-f]*)$', text, re.M)
    _require(len(values) == 1, f'exactly one {prefix} trace record required')
    width = bits // 4
    _require(len(values[0]) % width == 0, f'{prefix} trace has truncated word')
    result = [int(values[0][i:i+width], 16) for i in range(0, len(values[0]), width)]
    return [v - 2**bits if v >= 2**(bits-1) else v for v in result]


def _reference(h, x):
    return [max(-32768, min(32767, sum(int(c) * int(x[n-k])
            for k, c in enumerate(h) if k <= n) // 32768)) for n in range(len(x))]


def _retained(h, x, transposed):
    if not transposed:
        return ([0] * (len(h)-1) + list(x))[-(len(h)-1):]
    return [sum(int(h[k]) * int(x[-1-(k-i-1)])
                for k in range(i+1, len(h)) if k-i <= len(x))
            for i in range(len(h)-1)]


def _fixture_template(block: int, x: list[int], warm: int, total: int) -> str:
    """Frozen audited body grammar, independent from the runner's renderer."""
    arr = ','.join(map(str, x[:total]))
    return f'''#include "probe.h"
#define BLOCK {block}
#define WARMUP {warm}
#define TOTAL {total}
static const int16_t input_data[TOTAL]={{{arr}}};
static struct {{ uint64_t lo; ProbeState state; uint64_t hi; }} storage;
static int16_t source[TOTAL];
static int16_t destination[TOTAL+4];
extern void measured(void);
static void process_range(uint32_t begin,uint32_t end) {{
 for(uint32_t off=begin;off<end;off+=BLOCK) {{
  uint32_t b=end-off; if(b>BLOCK)b=BLOCK;
  probe_process(&storage.state,source+off,destination+2+off,b);
 }}
}}
void process_stream(void) {{ process_range(WARMUP,TOTAL); }}
static void warmup(void) {{ process_range(0,WARMUP); }}
static void put(char c){{*(volatile uint32_t*)0xe0000000=(uint32_t)c;}}
static void hex32(uint32_t v){{for(int s=28;s>=0;s-=4){{unsigned d=(v>>s)&15;put(d<10?'0'+d:'a'+d-10);}}}}
static void hex16(int16_t v){{uint32_t u=(uint16_t)v;for(int s=12;s>=0;s-=4){{unsigned d=(u>>s)&15;put(d<10?'0'+d:'a'+d-10);}}}}
int main(void) {{
 for(unsigned i=0;i<TOTAL;++i)source[i]=input_data[i];
 probe_init(&storage.state); storage.lo=storage.hi=0x5a5a5a5a5a5a5a5aULL;
 destination[0]=destination[1]=destination[TOTAL+2]=destination[TOTAL+3]=23130;
 warmup(); measured(); put('O');put(':');for(unsigned i=0;i<TOTAL;++i)hex16(destination[i+2]);put('\\n');
 put('H');put(':');for(unsigned i=0;i<TAPS-1;++i){{uint64_t v=(uint64_t)probe_get_state(&storage.state,i);hex32((uint32_t)(v>>32));hex32((uint32_t)v);}}put('\\n');
 put('G');put(':');hex32((uint32_t)storage.lo);hex32((uint32_t)(storage.lo>>32));hex32((uint32_t)storage.hi);hex32((uint32_t)(storage.hi>>32));
 hex16(destination[0]);hex16(destination[1]);hex16(destination[TOTAL+2]);hex16(destination[TOTAL+3]);put('\\n');
 put('M');put(':');hex32(probe_state_bytes());put('\\n');return 0;
}}
'''


def audited_template_hash() -> str:
    # SHA is bound to the source string above; changing the grammar needs review.
    sample = _fixture_template(1, [0], 0, 1).replace('0x5a5a5a5a5a5a5a5aULL', 'GUARD')
    return sha256_bytes(sample.encode())


def audit_fixture_source(source: str, case: dict, input_values: list[int]) -> dict:
    _require(audited_template_hash() == TEMPLATE_SHA256, 'audited fixture template digest changed')
    expected = _fixture_template(case['block'], input_values, case['warmup_samples'], case['total_samples'])
    _require(source == expected,
             'firmware body differs from audited initialization/range/ROI/state/guard/output template')
    return {'template_version': TEMPLATE_VERSION, 'template_sha256': audited_template_hash(),
            'input_samples': len(input_values), 'warmup_samples': case['warmup_samples'],
            'measured_offsets': [case['warmup_samples'], case['total_samples']]}


def audit_trace(row: dict, case_dir: Path, design: dict, inputs: dict) -> dict:
    h = design['filters'][row['filter']]['coefficients']
    x = inputs[row['stimulus']][:row['total_samples']]
    stdout_path = Path(case_dir) / row['artifacts']['stdout']
    _require(stdout_path.is_file(), 'raw stdout trace is missing')
    _require(row.get('artifact_sha256', {}).get('stdout') == sha256_bytes(stdout_path.read_bytes()),
             'raw stdout trace hash mismatch')
    stdout = stdout_path.read_text(errors='strict')
    _require(_words(stdout, 'O', 16) == _reference(h, x), 'full output trace mismatch')
    _require(_words(stdout, 'H', 64) == _retained(h, x, row['variant'].startswith('trans_')),
             'terminal state trace mismatch')
    guard = re.findall(r'^G:([0-9a-f]*)$', stdout, re.M)
    _require(len(guard) == 1 and guard[0] == '5a5a5a5a'*4 + '5a5a'*4,
             'state or output guard trace mismatch')
    memory = re.findall(r'^M:([0-9a-f]+)$', stdout, re.M)
    _require(len(memory) == 1 and int(memory[0], 16) == row.get('state_allocation_bytes'),
             'reported state allocation mismatch')
    _require(row.get('outputs_verified') == row['total_samples'],
             'outputs_verified must equal total processed samples')
    _require(row.get('guards_verified') is True and row.get('state_verified') is True,
             'guard/state evidence flags are absent')
    return {'outputs_verified': len(x), 'measured_outputs': row['measured_samples'],
            'terminal_state_words': 47, 'guards_verified': True}


def _state_size_from_header(header: str) -> int:
    found = re.search(r'typedef\s+struct\s*\{(.*?)\}\s*ProbeState\s*;', header, re.S)
    _require(found is not None, 'independent ProbeState layout cannot parse header')
    widths = {'uint64_t': 8, 'int64_t': 8, 'uint32_t': 4, 'int32_t': 4,
              'uint16_t': 2, 'int16_t': 2, 'uint8_t': 1, 'int8_t': 1,
              'arm_fir_instance_q15': 12}
    offset, maximum_alignment = 0, 1
    fields = re.findall(r'\b(\w+)\s+(\w+)\s*(?:\[(\d+)\])?\s*;', found[1])
    _require(fields, 'independent ProbeState has no parseable fields')
    for type_name, _, count in fields:
        _require(type_name in widths, f'unsupported ProbeState field type {type_name}')
        width = widths[type_name]
        alignment = 4 if type_name == 'arm_fir_instance_q15' else width
        maximum_alignment = max(maximum_alignment, alignment)
        offset = (offset + alignment - 1) // alignment * alignment
        offset += width * (int(count) if count else 1)
    return (offset + maximum_alignment - 1) // maximum_alignment * maximum_alignment


def _elf_layout(path: Path) -> dict:
    data = Path(path).read_bytes()
    _require(data[:7] == b'\x7fELF\x01\x01\x01', 'expected little-endian ELF32')
    head = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    _require(head[2] == 40, 'ELF target is not ARM')
    shoff, shentsize, shnum, shstrndx = head[6], head[11], head[12], head[13]
    _require(shentsize == 40 and shstrndx < shnum and shoff + shnum * 40 <= len(data),
             'invalid ELF section table')
    raw_sections = [struct.unpack_from('<IIIIIIIIII', data, shoff + i * 40) for i in range(shnum)]
    shstr = raw_sections[shstrndx]
    names = data[shstr[4]:shstr[4] + shstr[5]]
    sections = []
    for section in raw_sections:
        name_start = section[0]
        name_end = names.find(b'\0', name_start)
        name = names[name_start:name_end].decode() if name_start < len(names) and name_end >= name_start else ''
        sections.append({'name': name, 'type': section[1], 'flags': section[2],
                         'address': section[3], 'offset': section[4], 'size': section[5],
                         'end': section[3] + section[5], 'link': section[6]})
    allocated = [s for s in sections if s['flags'] & 2 and s['size']]
    ram, flash = [], []
    for section in allocated:
        start, end = section['address'], section['end']
        in_ram = 0x20000000 <= start and end <= 0x20002000
        in_flash = 0x08000000 <= start and end <= 0x08010000
        _require(in_ram or in_flash,
                 f'allocated section outside original memory map: {section["name"]}')
        (ram if in_ram else flash).append(section)
    _require(ram and flash, 'allocated SRAM or Flash sections are missing')
    ram_end = max(s['end'] for s in ram)
    _require(ram_end <= 0x200017f0, 'allocated SRAM exceeds 0x200017f0 static ceiling')
    _require(not any(s['name'] == '.data' and s['size'] for s in sections),
             'nonempty initialized .data is unsupported by original startup')
    phoff, phentsize, phnum = head[5], head[9], head[10]
    _require(phentsize == 32 and phoff + phentsize * phnum <= len(data), 'invalid ELF program headers')
    segments = []
    for i in range(phnum):
        p_type, p_offset, vaddr, paddr, filesz, memsz, flags, align = struct.unpack_from(
            '<IIIIIIII', data, phoff + i * phentsize)
        if p_type != 1 or memsz == 0:
            continue
        in_ram = 0x20000000 <= vaddr and vaddr + memsz <= 0x20002000
        in_flash = 0x08000000 <= vaddr and vaddr + memsz <= 0x08010000
        _require(in_ram or in_flash, 'PT_LOAD segment outside original Flash/SRAM map')
        if in_ram:
            _require(vaddr + memsz <= 0x200017f0,
                     'PT_LOAD SRAM segment exceeds 0x200017f0 static ceiling')
        _require(filesz <= memsz and p_offset + filesz <= len(data), 'invalid PT_LOAD file/memory size')
        segments.append({'vaddr': vaddr, 'paddr': paddr, 'file_size': filesz,
                         'memory_size': memsz, 'flags': flags, 'align': align,
                         'file_offset': p_offset})
    symbols = {}
    for section in sections:
        if section['type'] != 2:
            continue
        table = raw_sections[next(i for i, s in enumerate(sections) if s is section)]
        _require(table[9] == 16 and table[6] < len(raw_sections), 'invalid ELF symbol table')
        strings = raw_sections[table[6]]
        string_data = data[strings[4]:strings[4] + strings[5]]
        for off in range(table[4], table[4] + table[5], 16):
            st_name, st_value, st_size, _info, _other, st_shndx = struct.unpack_from('<IIIBBH', data, off)
            if st_name and st_shndx and st_name < len(string_data):
                end = string_data.find(b'\0', st_name)
                if end >= st_name:
                    symbols[string_data[st_name:end].decode()] = {'address': st_value, 'size': st_size}
    vector = next((s for s in sections if s['name'] == '.vectors'), None)
    _require(vector is not None and struct.unpack_from('<I', data, vector['offset'])[0] == 0x20001ff0,
             'vector initial SP is not 0x20001ff0')
    return {'allocated_sections': allocated, 'ram_sections': ram, 'flash_sections': flash,
            'ram_end': ram_end, 'flash_end': max(s['end'] for s in flash),
            'segments': segments, 'symbols': symbols, 'initial_sp': 0x20001ff0,
            'elf_bytes': data}


def _read_loaded(layout, address, size):
    for segment in layout['segments']:
        start, end = segment['vaddr'], segment['vaddr'] + segment['file_size']
        if start <= address and address + size <= end:
            offset = segment['file_offset'] + address - start
            return layout['elf_bytes'][offset:offset + size]
    raise ValueError(f'address range 0x{address:08x}+{size} is not file-backed by a PT_LOAD segment')


def _audit_binary_binding(elf_path, binary_path, disassembly, layout, samples):
    symbols = layout['symbols']
    symbol = symbols.get('input_data')
    _require(symbol is not None and symbol['size'] == len(samples) * 2,
             'ELF input_data symbol size differs from frozen gate stream')
    expected_input = struct.pack('<' + 'h' * len(samples), *samples)
    _require(_read_loaded(layout, symbol['address'], symbol['size']) == expected_input,
             'ELF input_data bytes differ from exact frozen gate stream')
    elf_bytes = layout['elf_bytes']
    flash_segments = sorted((s for s in layout['segments'] if 0x08000000 <= s['paddr'] < 0x08010000),
                            key=lambda s: s['paddr'])
    _require(flash_segments, 'ELF has no Flash load segments')
    low = flash_segments[0]['paddr']
    high = max(s['paddr'] + s['file_size'] for s in flash_segments)
    expected_binary = bytearray(high - low)
    for segment in flash_segments:
        begin = segment['paddr'] - low
        src = segment['file_offset']
        expected_binary[begin:begin + segment['file_size']] = elf_bytes[src:src + segment['file_size']]
    _require(Path(binary_path).read_bytes() == expected_binary,
             'objcopy binary bytes differ from ELF Flash load image')
    checked = 0
    pattern = re.compile(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4}\s+)+)', re.I)
    for line in disassembly.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        address = int(match[1], 16)
        encoded = bytes.fromhex(''.join(bytes.fromhex(word)[::-1].hex()
                                        for word in match[2].split()))
        _require(_read_loaded(layout, address, len(encoded)) == encoded,
                 f'disassembly machine bytes differ from ELF at 0x{address:08x}')
        checked += len(encoded)
    _require(checked > 0, 'no disassembly machine bytes were bound to the ELF')
    return {'input_bytes': len(expected_input), 'flash_binary_bytes': len(expected_binary),
            'disassembly_bytes_bound': checked}


def _independent_stack_chain(su_paths, disassembly: str, symbols=None) -> dict:
    frames, frame_evidence = {}, []
    for path in su_paths:
        raw = Path(path).read_text()
        rows = re.findall(r'(\S+):(\d+):(\d+):(\S+)\t(\d+)\t(\S+)', raw)
        _require(rows, f'stack diagnostics are empty: {path}')
        for source, line, column, name, amount, kind in rows:
            _require('dynamic' not in kind, f'dynamic stack usage for {name}')
            frames[name] = int(amount)
            frame_evidence.append({'file': str(path), 'source': source, 'line': int(line),
                                   'column': int(column), 'function': name,
                                   'bytes': int(amount), 'kind': kind})
    bodies, current = {}, None
    for line in disassembly.splitlines():
        label = re.match(r'^[0-9a-f]+ <([^>]+)>:', line)
        if label:
            current = label[1].split('+')[0]
            bodies.setdefault(current, [])
        elif current:
            bodies[current].append(line)
    _require('main' in bodies and 'measured' in bodies, 'main/measured absent from linked disassembly')
    def asm_frame(body):
        size = 0
        for line in body:
            p = re.search(r'\bpush\s+\{([^}]+)\}', line)
            if p:
                size += 4 * len(p[1].split(','))
            p = re.search(r'\bsub\s+sp(?:,\s*sp)?,\s*#(0x[0-9a-f]+|\d+)', line)
            if p:
                size += int(p[1], 0)
        return size
    for name, body in bodies.items():
        if name not in frames:
            frames[name] = asm_frame(body)
            frame_evidence.append({'file': 'linked disassembly', 'source': 'prologue',
                                   'line': 0, 'column': 0, 'function': name,
                                   'bytes': frames[name], 'kind': 'static'})
    calls, tails = {name: [] for name in bodies}, {name: [] for name in bodies}
    intra_edges = []
    for name, body in bodies.items():
        for line in body:
            branch = re.search(r'\bbl(?:x)?\s+[0-9a-fx]+\s+<([^>]+)>', line)
            if branch:
                target_text = branch[1]
                target = target_text.split('+')[0]
                if target == name:
                    sym = (symbols or {}).get(name)
                    offset = int(target_text.split('+', 1)[1], 16) if '+' in target_text else 0
                    address = int(re.search(r'\bbl(?:x)?\s+([0-9a-fx]+)', line)[1], 16)
                    start = sym['address'] & ~1 if sym else -1
                    valid = bool(sym and offset > 0 and address == start + offset and
                                 start < address < start + sym['size'])
                    if valid:
                        intra_edges.append({'from': name, 'to': target_text,
                                            'kind': 'outlined-intra-function-call'})
                    else:
                        calls[name].append(name)
                else:
                    calls[name].append(target)
            elif re.search(r'\bblx\s+r\d+\b', line):
                raise ValueError(f'indirect stack call in {name}')
            branch = re.search(r'\bb(?:\.[nw])?\s+[0-9a-fx]+\s+<([^>]+)>', line)
            if branch:
                target_text = branch[1]
                target = target_text.split('+')[0]
                if target == name:
                    sym = (symbols or {}).get(name)
                    address = int(re.search(r'\bb(?:\.[nw])?\s+([0-9a-fx]+)', line)[1], 16)
                    start = sym['address'] & ~1 if sym else -1
                    valid = bool(sym and start <= address < start + sym['size'])
                    if valid:
                        intra_edges.append({'from': name, 'to': target_text, 'kind': 'intra-function-branch'})
                    else:
                        tails[name].append(name)
                else:
                    tails[name].append(target)
            if re.search(r'\bbx\s+r\d+\b', line):
                raise ValueError(f'indirect stack branch in {name}')
    active, memo = set(), {}
    def peak(name):
        _require(name in bodies, f'called function missing from disassembly: {name}')
        if name in memo:
            return memo[name]
        _require(name not in active, f'recursive stack path is unresolved: {name}')
        active.add(name)
        own = frames[name]
        best, path = own, [name]
        for child in calls[name]:
            child_size, child_path = peak(child)
            if own + child_size > best:
                best, path = own + child_size, [name] + child_path
        for child in tails[name]:
            child_size, child_path = peak(child)
            if child_size > best:
                best, path = child_size, child_path
        active.remove(name)
        memo[name] = best, path
        return memo[name]
    maximum, chain = peak('main')
    _require(maximum <= 2048, 'live stack chain exceeds 2048 bytes')
    measured_frame = asm_frame(bodies['measured'])
    _require(measured_frame == 16, 'measured wrapper does not save exactly 16 bytes')
    return {'maximum_live_stack_bytes': maximum, 'maximizing_chain': chain,
            'frames': frame_evidence, 'stack_limit_bytes': 2048,
            'intra_function_edges': intra_edges}


def _gate_input(h):
    upper = [32767 if c > 0 else -32768 if c < 0 else 0 for c in h][::-1]
    lower = [-32768 if c > 0 else 32767 if c < 0 else 0 for c in h][::-1]
    return [0] * 48 + upper + lower + [-32768, 32767, -1, 0, 1] * 10


def _command_admission(row, case_dir, identity, protocol):
    commands_path = Path(case_dir) / row['artifact_paths']['commands']
    commands = json.loads(commands_path.read_text())
    _require(commands == row['commands'], 'commands.json differs from serialized command log')
    compiler = protocol['toolchain_identities'][identity['compiler']]['path']
    root_parts = Path(protocol['toolchain_identities']['gcc15']['path']).parts
    _require('research' in root_parts, 'pinned project root cannot be derived')
    project_root = Path(*root_parts[:root_parts.index('research')])
    recorded_case = project_root / 'research/fir-upgrades' / row['directory']
    cwd = str(recorded_case)
    _require(all(item.get('cwd') == cwd for item in commands),
             'command cwd differs from frozen historical case location')
    gcc = Path(compiler)
    bin_dir = gcc.parent
    flags = ['-mcpu=cortex-m0', '-mthumb', '-std=c11', '-ffreestanding', '-fno-builtin',
             '-ffunction-sections', '-fdata-sections', '-g0', '-O2', '-Wall', '-Wextra',
             '-Werror', '-fstack-usage']
    includes = ['-I', str(recorded_case), '-I', str(project_root / 'research/fir-baseline'),
                '-I', str(project_root / 'research/fir-baseline/build/cmsis-dsp/Include'),
                '-I', str(project_root / 'research/fir-baseline/build/cmsis-core')]
    sources = ['probe.c', 'firmware.c', 'startup.s']
    expected = []
    for source in sources:
        expected.append(('compile', [compiler, *flags, *includes, '-c', str(recorded_case / source),
                                     '-o', str(recorded_case / f'{Path(source).stem}.o')]))
    objects = ['probe.o', 'firmware.o', 'startup.o']
    if identity['variant'].startswith('cmsis'):
        cmsis_source = ('arm_fir_fast_q15.c' if identity['variant'].startswith('cmsis32')
                        else 'arm_fir_q15.c')
        library = project_root / 'research/fir-baseline/build/cmsis-dsp/Source/FilteringFunctions' / cmsis_source
        expected.append(('compile-library', [compiler, *flags, *includes, '-DARM_MATH_LOOPUNROLL',
                                             '-c', str(library), '-o', str(recorded_case / 'library.o')]))
        objects.append('library.o')
    elf, binary = recorded_case / 'firmware.elf', recorded_case / 'firmware.bin'
    expected.extend([
        ('link', [compiler, *flags[:8], '-nostdlib', '-T', str(recorded_case / 'link.ld'),
                  '-Wl,--gc-sections', f'-Wl,-Map={recorded_case / "firmware.map"}',
                  *[str(recorded_case / obj) for obj in objects], '-lgcc', '-o', str(elf)]),
        ('objcopy', [str(bin_dir / 'arm-none-eabi-objcopy'), '-O', 'binary', str(elf), str(binary)]),
        ('objdump', [str(bin_dir / 'arm-none-eabi-objdump'), '-d', str(elf)]),
        ('execute', [str(project_root / 'research/fir-baseline/build/thumbulator/sim_main'), '-s', str(binary)]),
    ])
    _require([(item.get('stage'), item.get('argv')) for item in commands] == expected,
             'build/execution argv differs from exact frozen command grammar')
    _require(all(item.get('returncode') == 0 for item in commands), 'a recorded build/execution command failed')
    return commands


def _project_root_from_protocol(protocol):
    parts = Path(protocol['toolchain_identities']['gcc15']['path']).parts
    _require('research' in parts, 'pinned project root cannot be derived')
    return Path(*parts[:parts.index('research')])


def _verify_frozen_sources(root, directory, ident, artifact_paths, protocol):
    manifest_path = Path(root) / 'sources-manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    _require(sha256_bytes(manifest_bytes) == SOURCES_MANIFEST_SHA256,
             'Task 4 source manifest differs from frozen digest')
    manifest = json.loads(manifest_bytes)
    source_item = next((s for s in manifest['sources'] if
                 (s['filter'], s['variant'], s['block']) ==
                 (ident['filter'], ident['variant'], ident['block'])), None)
    _require(source_item is not None, 'gate source identity is absent from Task 4 source manifest')
    expected = {'kernel_source': source_item['source_sha256'], 'kernel_header': source_item['header_sha256'],
                'startup_source': STARTUP_SHA256, 'linker_script': LINKER_SHA256,
                'baseline_kernels_header': KERNELS_HEADER_SHA256}
    for name, digest in expected.items():
        _require(name in artifact_paths, f'frozen source artifact missing: {name}')
        _require(sha256_bytes((Path(directory) / artifact_paths[name]).read_bytes()) == digest,
                 f'frozen source bytes differ: {name}')
    if ident['variant'].startswith('cmsis'):
        _require('library_source' in artifact_paths, 'CMSIS source copy missing')
        filename = 'arm_fir_fast_q15.c' if ident['variant'].startswith('cmsis32') else 'arm_fir_q15.c'
        pinned = protocol['certificates'][ident['filter']]['cmsis']['source_hashes']
        key = next((k for k in pinned if k.endswith('/' + filename)), None)
        _require(key is not None and sha256_bytes((Path(directory) / artifact_paths['library_source']).read_bytes()) == pinned[key],
                 'CMSIS library source differs from frozen Task 4 source hash')
    dep_path = Path(directory) / artifact_paths['dependencies']
    dependencies = json.loads(dep_path.read_text())
    hash_path = Path(directory) / artifact_paths['dependency_hashes']
    dep_hashes = json.loads(hash_path.read_text())
    macro_data = json.loads((Path(directory) / artifact_paths['macros']).read_text())
    expected_tus = {'probe.c', 'firmware.c', 'startup.s'}
    is_cmsis = ident['variant'].startswith('cmsis')
    if is_cmsis:
        expected_tus.add('library.c')
    _require(set(dependencies) == expected_tus and set(macro_data) == expected_tus,
             'effective macro/dependency translation-unit inventory differs from build')
    for tu in expected_tus - {'startup.s'}:
        _require(isinstance(dependencies[tu], str) and dependencies[tu].strip() and
                 isinstance(macro_data[tu], str) and macro_data[tu].strip(),
                 f'empty effective C provenance for {tu}')
    _require(dependencies['startup.s'] == '' and macro_data['startup.s'] == '',
             'startup.s must have empty assembler dependency and macro records')
    dependency_paths = set()
    for text in dependencies.values():
        dependency_paths.update(re.findall(r'(?m)(?<!\\)(/[^\s\\]+)', text))
    _require(dependency_paths == set(dep_hashes),
             'transitive dependency inventory differs from hashed dependency evidence')
    for item_path, digest in dep_hashes.items():
        _require(re.fullmatch(r'[0-9a-f]{64}', digest) is not None,
                 f'invalid transitive dependency hash for {item_path}')
    expected_local = {
        'firmware.c': {'firmware.c', 'probe.h'},
        'probe.c': {'probe.c', 'probe.h'},
    }
    if is_cmsis:
        expected_local['probe.c'].add('kernels.h')
        expected_local['library.c'] = set()
    copied_root = Path(root).resolve()
    case_relative = Path(directory).resolve().relative_to(copied_root)
    pinned = protocol['certificates'][ident['filter']]['cmsis']['source_hashes'] if is_cmsis else {}
    required_cmsis = {
        'cmsis-core/cmsis_compiler.h', 'cmsis-core/cmsis_gcc.h',
        'cmsis-dsp/Include/arm_math_memory.h', 'cmsis-dsp/Include/arm_math_types.h',
        'cmsis-dsp/Include/dsp/filtering_functions.h', 'cmsis-dsp/Include/dsp/none.h',
        'cmsis-dsp/Include/dsp/utils.h', 'cmsis-dsp/Include/dsp/support_functions.h',
        'cmsis-dsp/Include/dsp/fast_math_functions.h', 'cmsis-dsp/Include/dsp/basic_math_functions.h',
    }
    for tu in expected_tus - {'startup.s'}:
        paths = set(re.findall(r'(?m)(?<!\\)(/[^\s\\]+)', dependencies[tu]))
        for filename in expected_local.get(tu, set()):
            matching = [dep for dep in paths if Path(dep).name == filename and
                        f'/research/fir-upgrades/{case_relative.as_posix()}/' in dep]
            _require(len(matching) == 1, f'{tu} dependency missing required copied {filename}')
        if is_cmsis:
            for relative in required_cmsis:
                matching = [dep for dep in paths if dep.replace('/build/', '/').endswith('/' + relative)]
                _require(len(matching) == 1, f'{tu} dependency missing pinned CMSIS/core header {relative}')
            if tu == 'library.c':
                filename = 'arm_fir_fast_q15.c' if ident['variant'].startswith('cmsis32') else 'arm_fir_q15.c'
                _require(any(Path(dep).name == filename for dep in paths),
                         f'library.c dependency missing pinned {filename}')
        for item in paths:
            normalized = item.replace('/build/', '/')
            local_marker = '/research/fir-upgrades/'
            if local_marker in item:
                relative = item.split(local_marker, 1)[1]
                _require(relative.startswith(case_relative.as_posix() + '/'),
                         f'copied dependency path escapes case directory: {item}')
                copied = copied_root / relative
                _require(copied.is_file(), f'copied dependency source/header missing: {relative}')
                _require(dep_hashes[item] == sha256_bytes(copied.read_bytes()),
                         f'copied dependency hash differs from actual bytes: {relative}')
            elif is_cmsis:
                match = next((v for k, v in pinned.items() if normalized.endswith('/' + k)), None)
                _require(match is not None, f'unrecognized external CMSIS dependency: {item}')
                _require(dep_hashes[item] == match,
                         f'pinned CMSIS/core dependency hash mismatch: {item}')
            else:
                _require(False, f'unrecognized external dependency: {item}')
    return {'generated_source': source_item['source_sha256'], 'generated_header': source_item['header_sha256'],
            'dependency_count': len(dependency_paths), 'cmsis_source_checked': is_cmsis}


def audit_execution_attempt(row: dict, root: Path, protocol=None, design=None, case=None, samples=None) -> dict:
    root = Path(root).resolve()
    _require(row.get('status') in ('passed', 'admitted'), 'execution attempt did not pass runner admission')
    ident = row.get('identity', {})
    _require(set(ident) >= {'filter', 'variant', 'compiler', 'block'}, 'gate identity fields missing')
    protocol = protocol or load_frozen_protocol(root)
    _require(ident['filter'] in protocol['filters'] and
             ident['variant'] in protocol['variants_by_filter'][ident['filter']] and
             ident['compiler'] in protocol['compilers'],
             'execution identity is outside frozen protocol')
    _require(not (ident['filter'] == 'native_lp1800' and ident['variant'] == 'cmsis32_unroll'
                  and ident['block'] == 64), 'pending fast block64 identity must remain skipped')
    if design is None:
        design_raw = (root / 'panel-design.json').read_bytes()
        _require(sha256_bytes(design_raw) == DESIGN_SHA256, 'frozen design identity mismatch')
        design = json.loads(design_raw)
    h = design['filters'][ident['filter']]['coefficients']
    if case is None:
        x = _gate_input(h)
        case = {**ident, 'warmup_samples': 0, 'measured_samples': len(x), 'total_samples': len(x)}
    else:
        x = samples
        _require(isinstance(x, list) and len(x) == case['total_samples'],
                 'explicit performance input prefix differs from frozen case length')
        frozen_case = next((c for c in protocol['cases'] if
                            tuple(c[k] for k in CASE_FIELDS) == tuple(case[k] for k in CASE_FIELDS)), None)
        _require(frozen_case is not None and all(case[k] == frozen_case[k]
                 for k in ('warmup_samples', 'measured_samples', 'total_samples')),
                 'performance fixture ranges differ from frozen case identity')
    directory = contained(root, row.get('directory', ''))
    artifact_paths = row.get('artifact_paths', {})
    required = {'firmware_source', 'stdout', 'stderr', 'disassembly', 'binary', 'elf',
                'kernel_source', 'kernel_header', 'link_map', 'commands', 'dependencies', 'macros',
                'startup_source', 'linker_script', 'baseline_kernels_header', 'dependency_hashes'}
    if ident['variant'].startswith('cmsis'):
        required.add('library_source')
    _require(required <= set(artifact_paths), f'gate attempt lacks raw artifacts: {sorted(required-set(artifact_paths))}')
    for name, relative in artifact_paths.items():
        path = contained(directory, relative)
        _require(path.is_file(), f'missing gate artifact {relative}')
        _require(row.get('artifact_sha256', {}).get(name) == sha256_bytes(path.read_bytes()),
                 f'gate artifact hash mismatch: {name}')
    source_identity = _verify_frozen_sources(root, directory, ident, artifact_paths, protocol)
    source = (directory / artifact_paths['firmware_source']).read_text(errors='strict')
    fixture = audit_fixture_source(source, case, x)
    output_row = {**row, 'artifacts': artifact_paths,
                  'artifact_sha256': row['artifact_sha256'], 'total_samples': len(x),
                  'measured_samples': len(x), 'outputs_verified': row.get('outputs_verified'),
                  'state_allocation_bytes': row.get('state_allocation_bytes')}
    stdout_path = directory / artifact_paths['stdout']
    stdout = stdout_path.read_text(errors='strict')
    _require(_words(stdout, 'O', 16) == _reference(h, x), 'gate output trace disagrees with independent FIR')
    _require(_words(stdout, 'H', 64) == _retained(h, x, ident['variant'].startswith('trans_')),
             'gate terminal state trace disagrees with independent state oracle')
    guards = re.findall(r'^G:([0-9a-f]*)$', stdout, re.M)
    _require(guards == ['5a5a5a5a'*4 + '5a5a'*4], 'gate state/output guards changed')
    m = re.findall(r'^M:([0-9a-f]+)$', stdout, re.M)
    header = (directory / artifact_paths['kernel_header']).read_text(errors='strict')
    state_bytes = _state_size_from_header(header)
    _require(m == [f'{state_bytes:08x}'], 'M trace does not match independently derived ProbeState layout')
    _require(row.get('state_allocation_bytes') == state_bytes, 'serialized state bytes disagree with header')
    _require(row.get('outputs_verified') == len(x) and row.get('state_verified') is True
             and row.get('guards_verified') is True, 'gate output/state/guard completeness flag missing')
    stderr_path = directory / artifact_paths['stderr']
    events = rederive_raw_events(stderr_path.read_text(errors='strict'))
    _require(row.get('events') == events, 'serialized execution events disagree with raw counters')
    clamp_paths = quantizer_clamp_paths(h, x, case['warmup_samples'], case['total_samples'])
    if row.get('quantizer_clamp_paths') is not None:
        _require(row.get('quantizer_clamp_paths') == clamp_paths,
                 'serialized quantizer clamp paths disagree with exact measured-region sums')
    disasm = (directory / artifact_paths['disassembly']).read_text(errors='strict')
    mnemonics = instruction_subset(disasm)
    _require(row.get('mnemonics') == mnemonics, 'serialized instruction subset differs from disassembly')
    memory = _elf_layout(directory / artifact_paths['elf'])
    binary_binding = _audit_binary_binding(directory / artifact_paths['elf'],
        directory / artifact_paths['binary'], disasm, memory, x)
    symbols = memory['symbols']
    required_symbols = {'storage': 120, 'source': len(x) * 2, 'destination': (len(x) + 4) * 2,
                        'input_data': len(x) * 2}
    # storage has 8-byte guards with AAPCS alignment around ProbeState.
    state_offset = (8 + state_bytes + 7) // 8 * 8
    required_symbols['storage'] = state_offset + 8
    for name, size in required_symbols.items():
        _require(name in symbols and symbols[name]['size'] == size,
                 f'ELF symbol {name} size does not match fixture arrays/guards')
    _require(0x20000000 <= symbols['storage']['address'] < 0x20002000 and
             0x20000000 <= symbols['source']['address'] < 0x20002000 and
             0x20000000 <= symbols['destination']['address'] < 0x20002000,
             'source/destination/state arrays are not in SRAM')
    _require(0x08000000 <= symbols['input_data']['address'] < 0x08010000,
             'constant input array is not in Flash')
    state_function = re.search(r'<probe_state_bytes>:\n((?:[^\n]*\n){1,8})', disasm)
    _require(state_function is not None, 'linked probe_state_bytes function is missing')
    immediate = re.search(r'\bmovs?\s+r0,\s*#(0x[0-9a-f]+|\d+)', state_function[1])
    _require(immediate is not None and int(immediate[1], 0) == state_bytes,
             'linked probe_state_bytes return constant disagrees with independent ABI layout')
    stack_files = [directory / relative for name, relative in artifact_paths.items()
                   if name.startswith('stack_')]
    stack = _independent_stack_chain(stack_files, disasm, symbols)
    _require(row.get('stack', {}).get('maximum_live_stack_bytes') == stack['maximum_live_stack_bytes'] and
             row.get('stack', {}).get('maximizing_chain') == stack['maximizing_chain'] and
             row.get('stack', {}).get('intra_function_edges') == stack['intra_function_edges'],
             'serialized stack admission differs from independent call-chain reconstruction')
    _require(row.get('memory', {}).get('initial_sp') == memory['initial_sp'] and
             row.get('memory', {}).get('static_ram_end') == memory['ram_end'],
             'serialized memory admission differs from ELF')
    commands = _command_admission(row, directory, ident, protocol)
    compiler = row.get('compiler_identity', {})
    _require(compiler.get('sha256') == COMPILER_SHA256[ident['compiler']], 'compiler binary hash mismatch')
    project_root = _project_root_from_protocol(protocol)
    compiler_expected = protocol['toolchain_identities'][ident['compiler']]
    _require(compiler.get('path') == compiler_expected['path'] and
             compiler.get('version', '').find('10.3.1' if ident['compiler'] == 'gcc10' else '15.2.1') >= 0,
             'compiler path/version differs from frozen identity')
    _require(set(compiler.get('tools', {})) == set(BINUTIL_SHA256[ident['compiler']]),
             'pinned binutils inventory is incomplete')
    for tool, expected_hash in BINUTIL_SHA256[ident['compiler']].items():
        observed = compiler['tools'][tool]
        expected_path = str(Path(compiler_expected['path']).with_name('arm-none-eabi-' + tool))
        _require(observed.get('path') == expected_path and observed.get('sha256') == expected_hash,
                 f'pinned binutils identity mismatch: {tool}')
    _require(compiler.get('libgcc', {}).get('sha256') == LIBGCC_SHA256[ident['compiler']] and
             compiler.get('libgcc', {}).get('query_flags') == ['-mcpu=cortex-m0', '-mthumb'],
             'libgcc multilib identity mismatch')
    sim = row.get('simulator_identity', {})
    _require(sim.get('binary_sha256') == SIMULATOR_SHA256 and
             sim.get('patch_sha256') == SIMULATOR_PATCH_SHA256,
             'simulator or console patch identity mismatch')
    _require(sim.get('binary_path') == str(project_root / 'research/fir-baseline/build/thumbulator/sim_main') and
             sim.get('patch_path') == str(project_root / 'research/fir-baseline/simulator-console.patch') and
             sim.get('commit') == 'c55ea1b1926b792d7aabb7e3495b55a7b69ef134',
             'simulator binary/source/patch location or commit differs from frozen identity')
    macro_data = json.loads((directory / artifact_paths['macros']).read_text())
    for name, macros in macro_data.items():
        if name == 'startup.s':
            _require(not macros.strip(), 'startup assembler unexpectedly produced C feature macros')
            continue
        _require(re.search(r'^#define __ARM_ARCH\s+6$', macros, re.M) and
                 re.search(r'^#define __ARMEL__\s+1$', macros, re.M) and
                 re.search(r'^#define __ARM_EABI__\s+1$', macros, re.M),
                 f'wrong ARM architecture/endianness macros in {name}')
        for forbidden in ('__ARM_FEATURE_DSP', '__ARM_FEATURE_MVE', '__ARM_NEON', '__ARM_FEATURE_HELIUM'):
            _require(not re.search(rf'^#define {forbidden}\b', macros, re.M),
                     f'unsupported target macro present: {forbidden}')
    _require(commands, 'command provenance missing')
    return {'status': 'admitted', 'identity': ident, 'outputs_verified': len(x),
            'measured_samples': case['measured_samples'], 'warmup_samples': case['warmup_samples'],
            'state_allocation_bytes': state_bytes, 'raw_events': events,
            'quantizer_clamp_paths': clamp_paths,
            'memory': {'initial_sp': memory['initial_sp'], 'ram_end': memory['ram_end'],
                       'flash_end': memory['flash_end'], 'segments': memory['segments']},
            'stack': stack, 'fixture': fixture, 'mnemonics': mnemonics,
            'source_identity': source_identity, 'binary_binding': binary_binding,
            'artifacts_verified': len(artifact_paths)}


def audit_gate_attempt(row: dict, root: Path) -> dict:
    return audit_execution_attempt(row, root)


def instruction_subset(disassembly: str) -> list[str]:
    return _RAW.instruction_subset(disassembly)


def contained(root: Path, relative: str) -> Path:
    path = (Path(root).resolve() / relative).resolve()
    _require(path.is_relative_to(Path(root).resolve()), f'artifact path escapes campaign root: {relative}')
    return path


def audit_case(row: dict, root: Path, protocol: dict, design: dict, inputs: dict) -> dict:
    identity = row.get('identity', row)
    key = tuple(identity[k] for k in CASE_FIELDS)
    expected = next((c for c in protocol['cases'] if tuple(c[k] for k in CASE_FIELDS) == key), None)
    _require(expected is not None, 'case identity is absent from frozen protocol')
    for key_name in ('warmup_samples', 'measured_samples', 'total_samples'):
        _require(row.get(key_name, expected[key_name]) == expected[key_name],
                 f'case {key_name} differs from frozen protocol')
    _require(row.get('outputs_verified') == expected['total_samples'], 'outputs_verified must equal total_samples')
    case_dir = contained(root, row.get('directory', ''))
    raw_artifacts = row.get('artifacts', row.get('artifact_paths', {}))
    aliases = {'firmware.c': 'firmware_source', 'firmware.stdout': 'stdout',
               'firmware.stderr': 'stderr', 'firmware.disasm': 'disassembly',
               'firmware.bin': 'binary', 'firmware.elf': 'elf', 'kernel.c': 'kernel_source',
               'kernel.h': 'kernel_header', 'firmware.map': 'link_map',
               'effective-dependencies.json': 'dependencies', 'effective-macros.json': 'macros',
               'effective-dependency-hashes.json': 'dependency_hashes', 'startup.s': 'startup_source',
               'link.ld': 'linker_script', 'kernels.h': 'baseline_kernels_header',
               'library-source.c': 'library_source'}
    artifact_paths = {aliases.get(k, k): v for k, v in raw_artifacts.items()}
    required = {'firmware_source', 'stdout', 'stderr', 'disassembly', 'binary', 'elf',
                'kernel_source', 'kernel_header', 'link_map', 'commands', 'dependencies', 'macros',
                'dependency_hashes', 'startup_source', 'linker_script', 'baseline_kernels_header'}
    if identity['variant'].startswith('cmsis'):
        required.add('library_source')
    _require(required <= set(artifact_paths), f'missing raw evidence artifacts: {sorted(required-set(artifact_paths))}')
    hashes_in = row.get('artifact_sha256', {})
    artifact_hashes = {aliases.get(k, k): v for k, v in hashes_in.items()}
    for name, relative in artifact_paths.items():
        path = contained(case_dir, relative)
        _require(path.is_file(), f'missing artifact {name}: {relative}')
        _require(artifact_hashes.get(name) == sha256_bytes(path.read_bytes()),
                 f'artifact hash mismatch: {name}')
    x = inputs[identity['stimulus']][:expected['total_samples']]
    commands = row.get('commands')
    if commands is None:
        commands = json.loads((case_dir / artifact_paths['commands']).read_text())
    events = row.get('events', {k: row.get(k) for k in
        ('instructions', 'ram_reads', 'ram_writes', 'flash_reads', 'flash_writes',
         'taken_branches', 'flash_fetches', 'bl', 'mul', 'raw_tick_delta')})
    clamp_paths = quantizer_clamp_paths(
        design['filters'][identity['filter']]['coefficients'],
        inputs[identity['stimulus']][:expected['total_samples']],
        expected['warmup_samples'], expected['total_samples'])
    if row.get('quantizer_clamp_paths') is not None:
        _require(row['quantizer_clamp_paths'] == clamp_paths,
                 'serialized quantizer clamp paths disagree with exact measured-region sums')
    attempt = dict(row)
    attempt.update(identity=identity, status='admitted', artifact_paths=artifact_paths,
                   artifact_sha256=artifact_hashes, commands=commands, events=events,
                   quantizer_clamp_paths=clamp_paths)
    execution = audit_execution_attempt(attempt, root, protocol, design, expected, x)
    cost_row = dict(row)
    cost_row.update(artifacts={'stderr': artifact_paths['stderr']}, artifact_sha256={
        'stderr': artifact_hashes['stderr']})
    if 'events' not in cost_row:
        cost_row['events'] = events
    costs = audit_serialized_cost(cost_row, case_dir)
    disasm = (case_dir / artifact_paths['disassembly']).read_text(errors='strict')
    mnemonics = instruction_subset(disasm)
    _require(row.get('mnemonics') == mnemonics, 'instruction subset differs from raw disassembly')
    return {'identity': list(key), 'execution': execution, 'cost': costs,
            'mnemonics': mnemonics}


def audit_campaign(root: Path) -> dict:
    root = Path(root).resolve()
    protocol = load_frozen_protocol(root)
    design_bytes = (root / 'panel-design.json').read_bytes()
    inputs_bytes = (root / 'panel-inputs.json').read_bytes()
    _require(sha256_bytes(design_bytes) == DESIGN_SHA256, 'frozen design identity mismatch')
    _require(sha256_bytes(inputs_bytes) == INPUTS_SHA256, 'frozen input identity mismatch')
    design, inputs = json.loads(design_bytes), json.loads(inputs_bytes)
    result = json.loads((root / 'panel-results.json').read_text())
    _require(result.get('schema') == 'fir-task5-performance-results-v1' and
             result.get('protocol_sha256') == PROTOCOL_SHA256 and
             result.get('identity_count') == 288, 'performance results header differs from frozen protocol')
    rows = result.get('rows')
    _require(isinstance(rows, list), 'panel results lack performance rows')
    by_key = validate_identity_inventory(rows, protocol)
    audited, unavailable, failed = [], [], []
    for key, row in by_key.items():
        if row.get('status') == 'unavailable':
            identity = row.get('identity', row)
            _require(row.get('reason') == PENDING_FAST_REASON and identity.get('variant') == 'cmsis32_unroll'
                     and identity.get('filter') == 'native_lp1800' and identity.get('block') == 64,
                     'only pending fast-CMSIS block64 cases may be unavailable')
            unavailable.append(row)
            continue
        _require(row.get('status') == 'admitted', 'failed rows must block summary admission')
        audited.append(audit_case(row, root, protocol, design, inputs))
    _require(len(unavailable) == 8, 'native fast block64 must retain exactly eight unavailable identities')
    _require(not failed and len(audited) == 280,
             'performance audit requires all 280 executable identities admitted')
    return {'schema': 'fir-task5-independent-audit-v1', 'protocol_sha256': PROTOCOL_SHA256,
            'template_sha256': audited_template_hash(), 'identity_count': len(rows),
            'admitted_count': len(audited), 'unavailable_count': len(unavailable),
            'failed_count': len(failed), 'audited': audited,
            'unavailable': [{'identity': [(r.get('identity') or r)[k] for k in CASE_FIELDS],
                             'reason': r['reason']} for r in unavailable]}


def _decimal_text(value):
    return str(value) if isinstance(value, Decimal) else value


def _minimum(rows, variants):
    present = {r['identity'][1]: r for r in rows}
    missing = [variant for variant in variants if variant not in present]
    if missing:
        return {'status': 'unknown', 'missing_forms': missing}
    costs = [(present[variant]['cost']['energy_nj_per_output'], variant) for variant in variants]
    best = min(cost for cost, _ in costs)
    return {'status': 'known', 'energy_nj_per_output': str(best),
            'minimizers': [variant for cost, variant in costs if cost == best]}


def _percent(numerator, denominator):
    if denominator == 0:
        return None
    return str((numerator / denominator - 1) * 100)


def summarize_campaign(audit: dict, protocol: dict) -> dict:
    """Derive all cell estimands and paired contrasts from independently audited rows."""
    rows = audit['audited']
    clamp_buckets = {}
    for row in rows:
        ident = row['identity']
        key = (ident[0], ident[4], ident[5])
        paths = row['execution']['quantizer_clamp_paths']
        clamp_buckets.setdefault(key, set()).add((paths['positive'], paths['negative'], paths['total']))
    _require(all(len(values) == 1 for values in clamp_buckets.values()),
             'quantizer clamp counts differ across implementations of one input/regime')
    clamps = [{'filter': key[0], 'stimulus': key[1], 'regime': key[2],
               'positive': next(iter(values))[0], 'negative': next(iter(values))[1],
               'total': next(iter(values))[2],
               'range': next(row['execution']['quantizer_clamp_paths']['range'] for row in rows
                             if tuple((row['identity'][0], row['identity'][4], row['identity'][5])) == key)}
              for key, values in sorted(clamp_buckets.items())]
    fixed_cells = {}
    for row in rows:
        ident = row['identity']
        key = (ident[0], ident[2], ident[3], ident[4], ident[5])
        fixed_cells.setdefault(key, []).append(row)
    fixed = []
    all_wide_witnesses = []
    for key in sorted(fixed_cells):
        filt, compiler, block, stimulus, regime = key
        cell_rows = fixed_cells[key]
        forms = {r['identity'][1]: r for r in cell_rows}
        expected_forms = protocol['variants_by_filter'][filt]
        complete = all(form in forms for form in expected_forms)
        winners = _minimum(cell_rows, expected_forms)
        old_forms = ['wide_direct64', 'cmsis64_unroll']
        if filt == 'native_lp1800':
            old_forms.append('cmsis32_unroll')
        new_forms = old_forms + ['cert_direct_first']
        if filt != 'native_lp1800':
            new_forms.append('cert_direct_balanced')
        d_old = _minimum(cell_rows, old_forms)
        d_new = _minimum(cell_rows, new_forms)
        derived = {'filter': filt, 'compiler': compiler, 'block': block,
                   'stimulus': stimulus, 'regime': regime,
                   'complete_all_forms': complete, 'all_form_winner': winners,
                   'D_old': d_old, 'D_new': d_new}
        if 'trans_hcub_demand' in forms and 'trans_const' in forms:
            hcub = forms['trans_hcub_demand']['cost']['energy_nj_per_output']
            ordinary = forms['trans_const']['cost']['energy_nj_per_output']
            derived['hcub_vs_ordinary_percent'] = _percent(hcub, ordinary)
        for cert in ('cert_direct_first', 'cert_direct_balanced'):
            if cert in forms and 'wide_direct64' in forms:
                derived[f'{cert}_correction_vs_wide_percent'] = _percent(
                    forms[cert]['cost']['energy_nj_per_output'],
                    forms['wide_direct64']['cost']['energy_nj_per_output'])
        if filt in ('wide_lp2800', 'wide_lp4600'):
            if d_old['status'] == 'known' and d_new['status'] == 'known' and 'trans_hcub_demand' in forms:
                h = forms['trans_hcub_demand']['cost']['energy_nj_per_output']
                old = Decimal(d_old['energy_nj_per_output'])
                new = Decimal(d_new['energy_nj_per_output'])
                witness = h < old and h >= new
                derived['primary_reversal_witness'] = witness
                if witness:
                    all_wide_witnesses.append({'cell': list(key), 'E_Hcub': str(h),
                                               'D_old': str(old), 'D_new': str(new)})
            else:
                derived['primary_reversal_witness'] = None
        fixed.append(derived)

    selectable = []
    filter_forms = protocol['variants_by_filter']
    selectable_buckets = {}
    for row in rows:
        filt, variant, _compiler, block, stimulus, regime = row['identity']
        key = (filt, block, stimulus, regime)
        selectable_buckets.setdefault(key, {}).setdefault(variant, []).append(row)
    for key in sorted(selectable_buckets):
        filt, block, stimulus, regime = key
        forms = selectable_buckets[key]
        per_form = {}
        for variant in filter_forms[filt]:
            variants_rows = forms.get(variant, [])
            compilers = {r['identity'][2]: r for r in variants_rows}
            if set(compilers) != set(protocol['compilers']):
                per_form[variant] = {'status': 'unknown', 'missing_compilers':
                                     sorted(set(protocol['compilers']) - set(compilers))}
            else:
                costs = [(r['cost']['energy_nj_per_output'], c) for c, r in compilers.items()]
                best = min(cost for cost, _ in costs)
                per_form[variant] = {'status': 'known', 'energy_nj_per_output': str(best),
                                     'minimizing_compilers': [c for cost, c in costs if cost == best]}
        old_forms = ['wide_direct64', 'cmsis64_unroll']
        if filt == 'native_lp1800':
            old_forms.append('cmsis32_unroll')
        new_forms = old_forms + ['cert_direct_first']
        if filt != 'native_lp1800':
            new_forms.append('cert_direct_balanced')
        pseudo_rows = [{'identity': [filt, variant, 'selectable', block, stimulus, regime],
                        'cost': {'energy_nj_per_output': Decimal(value['energy_nj_per_output'])}}
                       for variant, value in per_form.items() if value['status'] == 'known']
        d_old = _minimum(pseudo_rows, old_forms)
        d_new = _minimum(pseudo_rows, new_forms)
        if per_form.get('trans_const', {}).get('status') == 'known' and per_form.get('trans_hcub_demand', {}).get('status') == 'known':
            hcub = Decimal(per_form['trans_hcub_demand']['energy_nj_per_output'])
            ordinary = Decimal(per_form['trans_const']['energy_nj_per_output'])
            hcub_increment = _percent(hcub, ordinary)
        else:
            hcub_increment = None
        direct_corrections = {}
        if per_form.get('wide_direct64', {}).get('status') == 'known':
            wide = Decimal(per_form['wide_direct64']['energy_nj_per_output'])
            for cert in ('cert_direct_first', 'cert_direct_balanced'):
                if per_form.get(cert, {}).get('status') == 'known':
                    direct_corrections[cert] = _percent(
                        Decimal(per_form[cert]['energy_nj_per_output']), wide)
        selectable.append({'filter': filt, 'block': block, 'stimulus': stimulus,
                           'regime': regime, 'per_form': per_form,
                           'all_forms_complete': all(v['status'] == 'known' for v in per_form.values()),
                           'D_old': d_old, 'D_new': d_new,
                           'hcub_vs_ordinary_percent': hcub_increment,
                           'direct_correction_vs_wide_percent': direct_corrections,
                           'all_form_winner': _minimum([
                               {'identity': [filt, variant, 'selectable', block, stimulus, regime],
                                'cost': {'energy_nj_per_output': Decimal(v['energy_nj_per_output'])}}
                               for variant, v in per_form.items() if v['status'] == 'known'],
                               filter_forms[filt])})

    by_identity = {tuple(row['identity']): row for row in rows}
    unavailable_keys = {tuple(item['identity']) for item in audit['unavailable']}
    contrasts = {}
    dimensions = {
        'block_size': (3, [1, 64], 'block64_vs_block1'),
        'amplitude': (4, ['adc', 'full'], 'full_vs_adc'),
        'regime': (5, ['startup', 'post_startup'], 'post_startup_vs_startup')}
    for name, (position, values, label) in dimensions.items():
        output = []
        for case in protocol['cases']:
            ident = [case[k] for k in CASE_FIELDS]
            if ident[position] != values[0]:
                continue
            left_key = tuple(ident)
            other = list(ident); other[position] = values[1]; other = tuple(other)
            if left_key in unavailable_keys or other in unavailable_keys:
                output.append({'identity': list(ident), 'paired_identity': list(other),
                               'status': 'unknown', 'reason': PENDING_FAST_REASON})
                continue
            if left_key not in by_identity or other not in by_identity:
                output.append({'identity': list(ident), 'paired_identity': list(other),
                               'status': 'unknown', 'reason': 'comparison identity failed or is absent'})
                continue
            left = by_identity[left_key]['cost']['energy_nj_per_output']
            right = by_identity[other]['cost']['energy_nj_per_output']
            if name == 'width':
                base, changed = left, right
            elif name == 'amplitude':
                base, changed = left, right
            else:
                base, changed = left, right
            output.append({'identity': list(ident), 'paired_identity': list(other),
                           'status': 'known', 'base_energy_nj_per_output': str(base),
                           'changed_energy_nj_per_output': str(changed),
                           'percent_change': _percent(changed, base)})
        contrasts[name] = {'meaning': label, 'pairs': output,
                           'known_count': sum(p['status'] == 'known' for p in output),
                           'unknown_count': sum(p['status'] == 'unknown' for p in output)}

    witnesses_by_compiler = Counter(item['cell'][1] for item in all_wide_witnesses)
    witnesses_by_filter_compiler = Counter((item['cell'][0], item['cell'][1])
                                           for item in all_wide_witnesses)
    stack_max = max((row['execution']['stack']['maximum_live_stack_bytes'] for row in rows), default=0)
    ram_max = max((row['execution']['memory']['ram_end'] for row in rows), default=0)
    flash_max = max((row['execution']['memory']['flash_end'] for row in rows), default=0)
    mnemonics = sorted({mnemonic for row in rows for mnemonic in row['mnemonics']})
    return {'schema': 'fir-task5-panel-summary-v1', 'protocol_sha256': PROTOCOL_SHA256,
            'identity_count': audit['identity_count'], 'admitted_count': audit['admitted_count'],
            'unavailable_count': audit['unavailable_count'], 'failed_count': audit['failed_count'],
            'assessment': 'incomplete' if audit['unavailable_count'] else 'complete',
            'unavailability_reason': PENDING_FAST_REASON,
            'primary_extension': {'wide_required_fixed_compiler_witnesses': all_wide_witnesses,
                                  'falsified': not bool(all_wide_witnesses) and not audit['unavailable_count'],
                                  'incomplete': bool(audit['unavailable_count'])},
            'compiler_pattern': {'fixed_cell_witnesses_by_compiler': dict(witnesses_by_compiler),
                                 'wide_fixed_cell_count_by_compiler': {
                                     compiler: sum(1 for row in fixed if row['filter'] in ('wide_lp2800', 'wide_lp4600')
                                                   and row['compiler'] == compiler)
                                     for compiler in ('gcc10', 'gcc15')},
                                 'fixed_cell_witnesses_by_filter_compiler': {
                                     f'{filt}/{compiler}': count for (filt, compiler), count in
                                     sorted(witnesses_by_filter_compiler.items())}},
            'quantizer_clamp_paths_by_input_regime': clamps,
            'resource_admission': {'maximum_static_ram_end': ram_max,
                                   'static_ram_ceiling': 0x200017F0,
                                   'maximum_live_stack_bytes': stack_max,
                                   'stack_reservation_bytes': 2048,
                                   'maximum_flash_end': flash_max,
                                   'instruction_subset_union': mnemonics},
            'fixed_compiler_cells': fixed, 'compiler_selectable_cells': selectable,
            'paired_contrasts': contrasts}


def _summary_markdown(summary: dict) -> str:
    witnesses = summary['primary_extension']['wide_required_fixed_compiler_witnesses']
    lines = ['# Frozen FIR Task 5 panel results', '',
             f"Protocol digest: `{summary['protocol_sha256']}`", '',
             f"Inventory: {summary['identity_count']} identities; {summary['admitted_count']} admitted; "
             f"{summary['unavailable_count']} unavailable; {summary['failed_count']} failed.", '',
             f"Assessment: **{summary['assessment']}**. The native fast-CMSIS block64 identities remain "
             f"unavailable because {summary['unavailability_reason']}.", '',
             'The fixed panel is purposive and synthetic. Normalized costs are per measured output; '
             'post-startup is not an isolated steady-state estimate.', '',
             '## Primary extension check', '']
    if witnesses:
        lines.append('At least one wide-required fixed-compiler cell meets the frozen reversal condition:')
        lines.append('')
        lines.append('| Filter / compiler / block / stimulus / regime | Hcub nJ/output | D_old | D_new |')
        lines.append('|---|---:|---:|---:|')
        for row in witnesses:
            filt, compiler, block, stimulus, regime = row['cell']
            lines.append(f"| {filt} / {compiler} / {block} / {stimulus} / {regime} | "
                         f"{row['E_Hcub']} | {row['D_old']} | {row['D_new']} |")
    elif summary['primary_extension']['incomplete']:
        lines.append('No conclusion is assigned: unavailable required cells leave the full-panel check incomplete.')
    else:
        lines.append('No frozen reversal witness was observed; the claim is falsified for this complete bounded panel.')
    pattern = summary['compiler_pattern']
    lines.extend(['', '## Complete-case outcome counts', '',
                  f"The reversal condition holds in {sum(pattern['fixed_cell_witnesses_by_compiler'].values())} of "
                  f"32 complete wide-required fixed-compiler cells: GCC10 "
                  f"{pattern['fixed_cell_witnesses_by_compiler'].get('gcc10', 0)}/16, GCC15 "
                  f"{pattern['fixed_cell_witnesses_by_compiler'].get('gcc15', 0)}/16. This reports each compiler "
                  'separately; it does not pool compiler minima into a fixed-compiler denominator.', '',
                  f"D_old and D_new are known in {sum(c['D_old']['status'] == 'known' for c in summary['fixed_compiler_cells'])}/48 "
                  f"fixed cells and {sum(c['D_old']['status'] == 'known' for c in summary['compiler_selectable_cells'])}/24 "
                  'compiler-selectable cells. The remaining native block64 cells are unknown because the fast-CMSIS '
                  'candidate is unavailable.', '',
                  'Complete-cell all-form winners (ties retained in JSON): ' + ', '.join(
                      f"{form} {count}" for form, count in sorted(summary['all_form_winner_counts'].items())), '',
                  '## Exact source quantizer thresholds', '',
                  'Counts below use exact source sums for measured samples only; they are not inferred from target branches.', '',
                  '| Filter | Stimulus | Regime | Positive | Negative | Total | Range |',
                  '|---|---|---|---:|---:|---:|---|'])
    for row in summary['quantizer_clamp_paths_by_input_regime']:
        lines.append(f"| {row['filter']} | {row['stimulus']} | {row['regime']} | {row['positive']} | "
                     f"{row['negative']} | {row['total']} | {row['range']} |")
    resources = summary['resource_admission']
    lines.extend(['', f"Maximum admitted static RAM end: `0x{resources['maximum_static_ram_end']:08x}` "
                  f"(ceiling `0x{resources['static_ram_ceiling']:08x}`); maximum conservative live stack: "
                  f"{resources['maximum_live_stack_bytes']} / {resources['stack_reservation_bytes']} bytes; "
                  f"maximum Flash end: `0x{resources['maximum_flash_end']:08x}`.", '',
                  f"Unique admitted firmware binaries by SHA256: {summary['binary_identity']['unique_binary_count']} "
                  f"across {summary['admitted_count']} logical identities; "
                  f"{summary['binary_identity']['duplicate_binary_group_count']} duplicate groups."])
    lines.extend(['', '## Derived result files', '',
                  '`panel-summary.json` contains every fixed-compiler cell, tied minimizer, '
                  'D_old/D_new result, direct correction, Hcub increment, compiler-selectable result, '
                  'and paired width/amplitude/regime contrast. `panel-results.json` preserves the '
                  'complete identity inventory and raw-evidence references. '
                  '`verification/independent-audit.json` records the independent raw-evidence audit.', ''])
    return '\n'.join(lines)


def _write_atomic(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.tmp')
    temporary.write_text(data)
    os.replace(temporary, path)


def write_campaign_reports(root: Path, audit: dict, summary: dict):
    root = Path(root).resolve()
    results = json.loads((root / 'panel-results.json').read_text())
    evidence = {'schema': 'fir-task5-scientific-evidence-v1',
                'protocol_sha256': PROTOCOL_SHA256,
                'identity_count': results['identity_count'],
                'rows': [{'identity': (row.get('identity') or row),
                          'status': row.get('status'), 'reason': row.get('reason'),
                          'directory': row.get('directory'),
                          'artifact_paths': row.get('artifact_paths', {}),
                          'artifact_sha256': row.get('artifact_sha256', {}),
                          'commands': row.get('commands', []),
                          'compiler_identity': row.get('compiler_identity'),
                          'simulator_identity': row.get('simulator_identity'),
                          'memory': row.get('memory'), 'stack': row.get('stack')}
                         for row in results['rows']]}
    binary_groups = {}
    for row in results['rows']:
        if row.get('status') != 'admitted':
            continue
        digest = row.get('artifact_sha256', {}).get('binary')
        if digest:
            binary_groups.setdefault(digest, []).append(row['identity'])
    summary['binary_identity'] = {
        'unique_binary_count': len(binary_groups),
        'duplicate_binary_group_count': sum(len(group) > 1 for group in binary_groups.values()),
        'duplicate_groups': [{'sha256': digest, 'identities': ids}
                             for digest, ids in binary_groups.items() if len(ids) > 1]}
    summary['all_form_winner_counts'] = dict(Counter(
        variant for cell in summary['fixed_compiler_cells']
        for variant in cell['all_form_winner'].get('minimizers', [])))
    audit_text = json.dumps(audit, indent=2, sort_keys=True, default=_decimal_text) + '\n'
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + '\n'
    evidence_text = json.dumps(evidence, indent=2, sort_keys=True) + '\n'
    # Validate every document is serializable before replacing any previous report.
    json.loads(audit_text); json.loads(summary_text); json.loads(evidence_text)
    _write_atomic(root / 'verification/independent-audit.json', audit_text)
    _write_atomic(root / 'panel-summary.json', summary_text)
    _write_atomic(root / 'panel-summary.md', _summary_markdown(summary))
    _write_atomic(root / 'verification/scientific-evidence-manifest.json', evidence_text)


def audit_correctness_campaign(root: Path) -> dict:
    root = Path(root).resolve()
    protocol = load_frozen_protocol(root)
    design_bytes = (root / 'panel-design.json').read_bytes()
    _require(sha256_bytes(design_bytes) == DESIGN_SHA256, 'frozen design identity mismatch')
    design = json.loads(design_bytes)
    source = json.loads((root / 'build/panel/correctness/correctness-gates.json').read_text())
    _require(source.get('schema') == 'fir-task5-correctness-gates-v1' and
             source.get('protocol_sha256') == PROTOCOL_SHA256 and
             source.get('condition_limit') == 72 and source.get('condition_count') == 72,
             'correctness gate inventory header differs from frozen protocol')
    expected, unavailable = set(), set()
    for filt in protocol['filters']:
        for variant in protocol['variants_by_filter'][filt]:
            for compiler in protocol['compilers']:
                for block in protocol['correctness_gate']['blocks']:
                    key = (filt, variant, compiler, block)
                    expected.add(key)
                    if filt == 'native_lp1800' and variant == 'cmsis32_unroll' and block == 64:
                        unavailable.add(key)
    rows = source.get('rows')
    identities = [r.get('identity', r) for r in rows]
    keys = [tuple(identity.get(k) for k in ('filter', 'variant', 'compiler', 'block'))
            for identity in identities]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    _require(not duplicates, f'duplicate correctness gate identity: {duplicates[0] if duplicates else None}')
    _require(len(keys) == 72 and set(keys) == expected,
             'correctness gate identity inventory is missing or contains extras')
    audited, skipped = [], []
    for key, row in zip(keys, rows):
        identity = row.get('identity', row)
        if key in unavailable:
            _require(row.get('status') == 'skipped' and row.get('reason') == PENDING_FAST_REASON,
                     'only the pending native fast block64 gates may be skipped')
            skipped.append({'identity': list(key), 'reason': row['reason']})
            continue
        _require(row.get('status') == 'passed' and row.get('admission_status') == 'admitted',
                 f'executable correctness gate is not admitted: {key}')
        result = audit_gate_attempt(row, root)
        audited.append({'identity': list(key), 'directory': row['directory'],
                        'outputs_verified': result['outputs_verified'],
                        'state_allocation_bytes': result['state_allocation_bytes'],
                        'raw_events': result['raw_events'], 'memory': result['memory'],
                        'stack': result['stack'], 'source_identity': result['source_identity'],
                        'binary_binding': result['binary_binding']})
    _require(len(audited) == 70 and len(skipped) == 2,
             'correctness gate admitted/skipped counts differ from frozen exclusions')
    return {'schema': 'fir-task5-correctness-independent-audit-v1',
            'protocol_sha256': PROTOCOL_SHA256, 'identity_count': 72,
            'admitted_count': 70, 'skipped_count': 2, 'failed_count': 0,
            'audited': audited, 'skipped': skipped}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=HERE)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--correctness-only', action='store_true')
    args = parser.parse_args(argv)
    if args.correctness_only:
        audit = audit_correctness_campaign(args.root)
    else:
        audit = audit_campaign(args.root)
        protocol = load_frozen_protocol(args.root)
        summary = summarize_campaign(audit, protocol)
        write_campaign_reports(args.root, audit, summary)
    payload = json.dumps(audit, indent=2, sort_keys=True, default=_decimal_text) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name('.' + args.output.name + '.tmp')
        temporary.write_text(payload)
        os.replace(temporary, args.output)
    else:
        print(payload, end='')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f'panel_verify: {exc}')
