"""Bounded Task 5 target runner; frozen Task 4 inputs are consumed, never regenerated."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'fir-baseline'
CMSIS = BASE / 'build' / 'cmsis-dsp'
CORE = BASE / 'build' / 'cmsis-core'
SIM = BASE / 'build' / 'thumbulator' / 'sim_main'
SIM_ROOT = BASE / 'build' / 'thumbulator'
SIM_PIN = 'c55ea1b1926b792d7aabb7e3495b55a7b69ef134'
PROTOCOL_SHA = 'd2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c'
PENDING_FAST_REASON = 'pending unresolved pointer-object aliasing'
COMPILER_SHAS = {
    'gcc10': '702dfc4dd0b34ee43ecd164a6db6ada4b5583d8945b17bbea3ebe223db765480',
    'gcc15': '94f60cfbad1091ad86c2435d8b804e82c0fc7e4c16302183c9a60cddd5318b1a',
}
LIBGCC_SHAS = {
    'gcc10': '7d25476df0fb0cb0133911547da014e94bf610d7a1e975c4c64e76c23fdbe517',
    'gcc15': '69e7b7a94214a895eafc7a50a90c0f1025d8c47d20c21e5469d3cd74f7bdd7a6',
}
BINUTIL_SHAS = {
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
SIM_SHA = 'd1fb48bed5f52e94813372054a086ee003cffb56b98dec3052ef4bfe397d9195'
SIM_PATCH_SHA = '970f73c9644170deddbb57b4a3077a5d8f027a12a3296c403fd04719d54aa0c8'
SOURCES_MANIFEST_SHA = '5a3301883e90db9ac41f7c5bed653c9e156ddc1e548784992d62aac9c3076568'
STARTUP_SHA = '8859527adcb9943e5a648fcea01fdf8a2506ee27173b08fc55d82cac3a5b4054'
LINKER_SHA = '37fd6a919b5887762492571804dc8cdfbc5f87afadae4b31734297d52b55d4ca'
KERNELS_HEADER_SHA = '00c2e621e86ee69d6080dd55d4a2bdaa587f6c5284f33e0ad027c12a57703b0c'
COMPILERS = {'gcc10': Path('/usr/bin/arm-none-eabi-gcc'),
             'gcc15': BASE / 'build/toolchains/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc'}
FLAGS = ['-mcpu=cortex-m0', '-mthumb', '-std=c11', '-ffreestanding', '-fno-builtin',
         '-ffunction-sections', '-fdata-sections', '-g0', '-O2', '-Wall', '-Wextra',
         '-Werror', '-fstack-usage']
CASE_KEYS = ('filter', 'variant', 'compiler', 'block', 'stimulus', 'regime')


def dump(value):
    from decimal import Decimal
    def exact_default(item):
        if isinstance(item, Decimal):
            return str(item)
        raise TypeError(f'unsupported JSON value: {type(item).__name__}')
    return (json.dumps(value, indent=2, sort_keys=True, default=exact_default) + '\n').encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(argv, cwd=None, timeout=120):
    return subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True,
                          text=True, timeout=timeout, check=False)


def frozen(root=HERE):
    root = Path(root).resolve()
    protocol_file = root / 'panel-protocol.json'
    if sha(protocol_file) != PROTOCOL_SHA:
        raise ValueError('Task 4 protocol digest mismatch; refusing build')
    design_file, inputs_file = root / 'panel-design.json', root / 'panel-inputs.json'
    if sha(design_file) != '51f8cfec85687672153d10a26e1ab8ab918a37eb2a540490eea2153035f8b414':
        raise ValueError('Task 4 design digest mismatch')
    if sha(inputs_file) != '200a4317989c4a2c85aa3727f739921038206a758e99fb052114f925e9cf9b9b':
        raise ValueError('Task 4 input digest mismatch')
    protocol = json.loads(protocol_file.read_text())
    if len(protocol.get('cases', [])) != 288:
        raise ValueError('frozen performance identity count changed')
    if sha(root / 'sources-manifest.json') != SOURCES_MANIFEST_SHA:
        raise ValueError('frozen generated source manifest digest changed')
    manifest = json.loads((root / 'sources-manifest.json').read_text())
    if len(manifest.get('sources', [])) != 36:
        raise ValueError('frozen generated source inventory changed')
    for item in manifest['sources']:
        folder = root / 'sources' / item['filter'] / item['variant'] / f"b{item['block']}"
        if sha(folder / 'probe.c') != item['source_sha256'] or sha(folder / 'probe.h') != item['header_sha256']:
            raise ValueError(f'frozen generated source hash mismatch: {item}')
    for name, cert in protocol['certificates'].items():
        for relative, expected_hash in cert['cmsis']['source_hashes'].items():
            path = BASE / 'build' / relative
            if not path.is_file() or sha(path) != expected_hash:
                raise ValueError(f'pinned CMSIS dependency changed: {relative}')
    if sha(BASE / 'startup.s') != STARTUP_SHA or sha(BASE / 'link.ld') != LINKER_SHA or sha(BASE / 'kernels.h') != KERNELS_HEADER_SHA:
        raise ValueError('original startup source changed')
    return root, protocol, json.loads(design_file.read_text()), json.loads(inputs_file.read_text())


def gate_stream(design_row):
    h = design_row['coefficients']
    upper = [32767 if c > 0 else -32768 if c < 0 else 0 for c in h][::-1]
    lower = [-32768 if c > 0 else 32767 if c < 0 else 0 for c in h][::-1]
    return [0] * 48 + upper + lower + [-32768, 32767, -1, 0, 1] * 10


def fixture_source(block, x, warm, total):
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


def gate_cases(protocol, design):
    result = []
    for name in protocol['filters']:
        for variant in protocol['variants_by_filter'][name]:
            for compiler in protocol['compilers']:
                for block in protocol['correctness_gate']['blocks']:
                    row = {'filter': name, 'variant': variant, 'compiler': compiler, 'block': block}
                    if name == 'native_lp1800' and variant == 'cmsis32_unroll' and block == 64:
                        row.update(status='skipped', reason=PENDING_FAST_REASON)
                    else:
                        row.update(status='pending', design_row=design['filters'][name])
                    result.append(row)
    return result


def select_gate_identity(protocol, design, identity):
    if not isinstance(identity, (tuple, list)) or len(identity) != 4:
        raise ValueError('gate identity must be filter/variant/compiler/block')
    filt, variant, compiler, block = identity
    if filt not in protocol['filters'] or variant not in protocol['variants_by_filter'].get(filt, []):
        raise ValueError('gate identity is not in the frozen protocol')
    if compiler not in protocol['compilers'] or block not in protocol['correctness_gate']['blocks']:
        raise ValueError('gate identity is not in the frozen protocol')
    case = next(c for c in gate_cases(protocol, design)
                if (c['filter'], c['variant'], c['compiler'], c['block']) == tuple(identity))
    if case['status'] == 'skipped':
        raise ValueError(f'gate identity is pending: {case["reason"]}')
    return case


def state_allocation_from_header(header):
    found = re.search(r'typedef\s+struct\s*\{(.*?)\}\s*ProbeState\s*;', header, re.S)
    if not found:
        raise ValueError('ProbeState declaration missing')
    body = found.group(1)
    widths = {'uint64_t': 8, 'int64_t': 8, 'uint32_t': 4, 'int32_t': 4,
              'uint16_t': 2, 'int16_t': 2, 'uint8_t': 1, 'int8_t': 1,
              'arm_fir_instance_q15': 12}
    fields = re.findall(r'\b(\w+)\s+(\w+)\s*(?:\[(\d+)\])?\s*;', body)
    if not fields:
        raise ValueError('ProbeState fields not parseable')
    offset = 0
    struct_align = 1
    for type_name, _, count in fields:
        if type_name not in widths:
            raise ValueError(f'unknown ProbeState field type {type_name}')
        size = widths[type_name]
        field_align = 4 if type_name == 'arm_fir_instance_q15' else size
        struct_align = max(struct_align, field_align)
        offset = (offset + field_align - 1) // field_align * field_align
        offset += size * (int(count) if count else 1)
    return (offset + struct_align - 1) // struct_align * struct_align


def compiler_identity(name):
    gcc = COMPILERS[name].resolve()
    if not gcc.is_file():
        raise FileNotFoundError(f'pinned {name} compiler missing: {gcc}')
    version = command([gcc, '--version'])
    first = version.stdout.splitlines()[0] if version.stdout else ''
    expected = '10.3.1' if name == 'gcc10' else '15.2.1'
    if version.returncode or expected not in first:
        raise ValueError(f'pinned {name} compiler version mismatch: {first}')
    compiler_hash = sha(gcc)
    if compiler_hash != COMPILER_SHAS[name]:
        raise ValueError(f'pinned {name} compiler binary hash mismatch')
    tools = {}
    for suffix in ('as', 'ld', 'objcopy', 'objdump', 'readelf', 'nm'):
        path = gcc.with_name('arm-none-eabi-' + suffix)
        if not path.is_file():
            raise FileNotFoundError(f'pinned {name} binutils missing: {path}')
        tool_hash = sha(path)
        if tool_hash != BINUTIL_SHAS[name][suffix]:
            raise ValueError(f'pinned {name} {suffix} hash mismatch')
        tools[suffix] = {'path': str(path.resolve()), 'sha256': tool_hash}
    libgcc = Path(command([gcc, '-mcpu=cortex-m0', '-mthumb', '-print-libgcc-file-name']).stdout.strip()).resolve()
    if not libgcc.is_file():
        raise FileNotFoundError(f'pinned libgcc missing: {libgcc}')
    libgcc_hash = sha(libgcc)
    if libgcc_hash != LIBGCC_SHAS[name] or 'thumb/v6-m/nofp/libgcc.a' not in str(libgcc):
        raise ValueError(f'pinned {name} Cortex-M0 libgcc identity mismatch')
    return {'path': str(gcc), 'sha256': compiler_hash, 'version': first, 'tools': tools,
            'libgcc': {'path': str(libgcc), 'sha256': libgcc_hash,
                       'query_flags': ['-mcpu=cortex-m0', '-mthumb']}}


def simulator_identity():
    if not SIM.is_file():
        raise FileNotFoundError('pinned simulator binary missing')
    if sha(SIM) != SIM_SHA:
        raise ValueError('pinned simulator binary hash mismatch')
    rev = command(['git', '-C', SIM_ROOT, 'rev-parse', 'HEAD'])
    if rev.returncode or rev.stdout.strip() != SIM_PIN:
        raise ValueError('pinned simulator commit mismatch')
    patch = BASE / 'simulator-console.patch'
    actual = command(['git', '-C', SIM_ROOT, 'diff', '--', 'sim_support.h'])
    if actual.returncode or not patch.is_file() or patch.read_bytes() != actual.stdout.encode():
        raise ValueError('simulator console patch mismatch')
    if sha(patch) != SIM_PATCH_SHA:
        raise ValueError('pinned simulator patch hash mismatch')
    return {'commit': SIM_PIN, 'binary_path': str(SIM.resolve()), 'binary_sha256': sha(SIM),
            'patch_path': str(patch.resolve()), 'patch_sha256': sha(patch)}


def elf_sections(path):
    raw = Path(path).read_bytes()
    if raw[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('expected little-endian ELF32')
    head = struct.unpack_from('<16sHHIIIIIHHHHHH', raw)
    if head[2] != 40:
        raise ValueError('expected ARM ELF')
    offset, entsize, count, names_index = head[6], head[11], head[12], head[13]
    if entsize != 40 or offset + count * entsize > len(raw) or names_index >= count:
        raise ValueError('invalid ELF section table')
    sections = [struct.unpack_from('<IIIIIIIIII', raw, offset + i * entsize) for i in range(count)]
    shstr = sections[names_index]
    names = raw[shstr[4]:shstr[4] + shstr[5]]
    result = []
    for s in sections:
        if not s[2] & 2:
            continue
        end = names.find(b'\0', s[0])
        name = names[s[0]:end].decode() if 0 <= s[0] < len(names) and end >= s[0] else ''
        result.append({'name': name, 'type': s[1], 'flags': s[2], 'address': s[3],
                       'size': s[5], 'end': s[3] + s[5], 'file_offset': s[4]})
    return raw, result


def validate_memory_ranges(sections):
    ram_start, ram_end_limit = 0x20000000, 0x20002000
    flash_start, flash_end_limit = 0x08000000, 0x08010000
    ram, flash = [], []
    for section in sections:
        if section['size'] == 0:
            continue
        start, end = section['address'], section['end']
        in_ram = ram_start <= start and end <= ram_end_limit
        in_flash = flash_start <= start and end <= flash_end_limit
        if not (in_ram or in_flash):
            raise ValueError(f'allocated section {section["name"]} outside Flash/SRAM: [0x{start:08x},0x{end:08x})')
        (ram if in_ram else flash).append(section)
    if not ram or not flash:
        raise ValueError('allocated Flash/SRAM sections missing')
    static_end = max(s['end'] for s in ram)
    if static_end > 0x200017f0:
        raise ValueError(f'allocated RAM end 0x{static_end:08x} exceeds 0x200017f0')
    return {'ram': ram, 'flash': flash, 'ram_end': static_end,
            'flash_end': max(s['end'] for s in flash)}


def memory_admission(elf, map_file):
    raw, sections = elf_sections(elf)
    validated = validate_memory_ranges(sections)
    ram, flash = validated['ram'], validated['flash']
    ram_end, flash_end = validated['ram_end'], validated['flash_end']
    if any(s['name'] == '.data' and s['size'] for s in sections):
        raise ValueError('nonempty initialized .data unsupported by original startup')
    vector = next((s for s in flash if s['name'] == '.vectors'), None)
    if vector is None or struct.unpack_from('<I', raw, vector['file_offset'])[0] != 0x20001ff0:
        raise ValueError('ELF vector SP is not 0x20001ff0')
    if not Path(map_file).is_file() or not Path(map_file).read_text(errors='replace').strip():
        raise ValueError('linker map missing or empty')
    return {'allocated_sections': sections, 'ram_sections': ram, 'flash_sections': flash,
            'static_ram_end': ram_end, 'flash_end': flash_end, 'initial_sp': 0x20001ff0,
            'ram_ceiling': 0x200017f0, 'map_sha256': sha(map_file)}


def _record(stage, argv, cwd, proc):
    return {'stage': stage, 'argv': [str(x) for x in argv], 'cwd': str(Path(cwd).resolve()),
            'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


def _copy_inputs(root, case, directory):
    if case['filter'] == 'native_lp1800' and case['variant'] == 'cmsis32_unroll' and case['block'] == 64:
        raise ValueError(PENDING_FAST_REASON)
    src = root / 'sources' / case['filter'] / case['variant'] / f"b{case['block']}"
    for source, target in ((src / 'probe.c', directory / 'probe.c'),
                           (src / 'probe.h', directory / 'probe.h'),
                           (BASE / 'startup.s', directory / 'startup.s'),
                           (BASE / 'link.ld', directory / 'link.ld'),
                           (BASE / 'kernels.h', directory / 'kernels.h')):
        if not source.is_file():
            raise FileNotFoundError(f'frozen input missing: {source}')
        shutil.copyfile(source, target)


def _preprocessor_evidence(gcc, source, directory, macros=None):
    inc = ['-I', directory, '-I', BASE, '-I', CMSIS / 'Include', '-I', CORE]
    common = [gcc, *FLAGS, *inc, *(macros or [])]
    dep = command([*common, '-MM', source], cwd=directory)
    pre = command([*common, '-dM', '-E', source], cwd=directory)
    if dep.returncode or pre.returncode:
        raise RuntimeError(f'preprocessor evidence failed for {source}: {dep.stderr}{pre.stderr}')
    return dep.stdout, pre.stdout


def _dependency_hashes(dependencies):
    found = set()
    for text in dependencies.values():
        found.update(re.findall(r'(?m)(?<!\\)(/[^\s\\]+)', text))
    result = {}
    for item in sorted(found):
        path = Path(item)
        if not path.is_file():
            raise FileNotFoundError(f'preprocessor dependency missing: {path}')
        result[str(path.resolve())] = sha(path)
    return result


def _compile(root, case, directory, x, warm, total, commands):
    gcc = COMPILERS[case['compiler']].resolve()
    _copy_inputs(root, case, directory)
    (directory / 'firmware.c').write_text(fixture_source(case['block'], x, warm, total))
    inc = ['-I', directory, '-I', BASE, '-I', CMSIS / 'Include', '-I', CORE]
    source_files = [directory / 'probe.c', directory / 'firmware.c', directory / 'startup.s']
    dependencies, macros, objects = {}, {}, []
    for source in source_files:
        dep, pre = _preprocessor_evidence(gcc, source, directory)
        dependencies[source.name], macros[source.name] = dep, pre
        obj = directory / f'{source.stem}.o'
        argv = [gcc, *FLAGS, *inc, '-c', source, '-o', obj]
        proc = command(argv, cwd=directory)
        commands.append(_record('compile', argv, directory, proc))
        if proc.returncode:
            raise RuntimeError(f'{source.name} compile failed: {proc.stderr}')
        objects.append(obj)
    if case['variant'].startswith('cmsis'):
        libname = 'arm_fir_fast_q15' if case['variant'].startswith('cmsis32') else 'arm_fir_q15'
        libsrc = CMSIS / 'Source/FilteringFunctions' / f'{libname}.c'
        shutil.copyfile(libsrc, directory / 'library-source.c')
        libmacros = ['-DARM_MATH_LOOPUNROLL']
        dep, pre = _preprocessor_evidence(gcc, libsrc, directory, libmacros)
        dependencies['library.c'], macros['library.c'] = dep, pre
        obj = directory / 'library.o'
        argv = [gcc, *FLAGS, *inc, *libmacros, '-c', libsrc, '-o', obj]
        proc = command(argv, cwd=directory)
        commands.append(_record('compile-library', argv, directory, proc))
        if proc.returncode:
            raise RuntimeError(f'CMSIS compile failed: {proc.stderr}')
        objects.append(obj)
    (directory / 'effective-dependencies.json').write_bytes(dump(dependencies))
    (directory / 'effective-dependency-hashes.json').write_bytes(dump(_dependency_hashes(dependencies)))
    (directory / 'effective-macros.json').write_bytes(dump(macros))
    elf = directory / 'firmware.elf'
    argv = [gcc, *FLAGS[:8], '-nostdlib', '-T', directory / 'link.ld', '-Wl,--gc-sections',
            f'-Wl,-Map={directory / "firmware.map"}', *objects, '-lgcc', '-o', elf]
    proc = command(argv, cwd=directory)
    commands.append(_record('link', argv, directory, proc))
    if proc.returncode:
        raise RuntimeError(f'link failed: {proc.stderr}')
    objcopy = gcc.with_name('arm-none-eabi-objcopy')
    argv = [objcopy, '-O', 'binary', elf, directory / 'firmware.bin']
    proc = command(argv, cwd=directory)
    commands.append(_record('objcopy', argv, directory, proc))
    if proc.returncode:
        raise RuntimeError(f'objcopy failed: {proc.stderr}')
    objdump = gcc.with_name('arm-none-eabi-objdump')
    proc = command([objdump, '-d', elf], cwd=directory)
    commands.append(_record('objdump', [objdump, '-d', elf], directory, proc))
    if proc.returncode:
        raise RuntimeError(f'objdump failed: {proc.stderr}')
    (directory / 'firmware.disasm').write_text(proc.stdout)
    return {'gcc': gcc, 'elf': elf, 'binary': directory / 'firmware.bin',
            'dependencies': dependencies, 'macros': macros}


def _execute(binary, directory, commands):
    proc = command([SIM, '-s', binary], cwd=directory, timeout=180)
    commands.append(_record('execute', [SIM, '-s', binary], directory, proc))
    (directory / 'firmware.stdout').write_text(proc.stdout)
    (directory / 'firmware.stderr').write_text(proc.stderr)
    if proc.returncode:
        raise RuntimeError(f'simulator execution failed: {proc.stderr}')
    return proc.stdout, proc.stderr


def _stack_frame_files(directory):
    return sorted(directory.glob('*.su'))


def stack_admission(su_files, disassembly, symbols=None):
    frame_rows, frames = [], {}
    for filename in su_files:
        for source, line, col, name, amount, kind in re.findall(
                r'(\S+):(\d+):(\d+):(\S+)\t(\d+)\t(\S+)', Path(filename).read_text()):
            frames[name] = int(amount)
            frame_rows.append({'file': str(filename), 'source': source, 'line': int(line),
                               'column': int(col), 'function': name, 'bytes': int(amount), 'kind': kind})
    if 'main' not in frames:
        raise ValueError('main frame absent from .su files')
    if any('dynamic' in f['kind'] for f in frame_rows):
        raise ValueError('dynamic frame is unresolved')
    bodies, current = {}, None
    for line in disassembly.splitlines():
        m = re.match(r'^[0-9a-f]+ <([^>]+)>:', line)
        if m:
            current = m.group(1).split('+')[0]
            bodies.setdefault(current, [])
        elif current:
            bodies[current].append(line)
    if 'main' not in bodies or 'measured' not in bodies:
        raise ValueError('main or measured wrapper missing from linked disassembly')

    def observed_frame(name, body):
        pushes = 0
        allocation = 0
        for line in body:
            push = re.search(r'\bpush\s+\{([^}]+)\}', line)
            if push:
                pushes += len([r for r in push[1].split(',') if r.strip()]) * 4
            stmdb = re.search(r'\bstmdb\s+sp!?,?\s*\{([^}]+)\}', line)
            if stmdb:
                pushes += len([r for r in stmdb[1].split(',') if r.strip()]) * 4
            sub = re.search(r'\bsub\s+sp(?:,\s*sp)?,\s*#(0x[0-9a-f]+|\d+)', line)
            if sub:
                allocation += int(sub[1], 0)
            dynamic = re.search(r'\bsub\s+sp(?:,\s*sp)?,\s*(?!#)(r\d+)', line)
            if dynamic and name not in frames:
                raise ValueError(f'dynamic stack allocation in unreported function {name}')
        return pushes + allocation

    for name, body in bodies.items():
        if name not in frames:
            frames[name] = observed_frame(name, body)
            frame_rows.append({'file': 'firmware.disasm', 'source': 'linked prologue', 'line': 0,
                               'column': 0, 'function': name, 'bytes': frames[name], 'kind': 'static'})
        elif name == 'measured' and frames[name] != observed_frame(name, body):
            raise ValueError('measured wrapper .su/prologue frame mismatch')

    graph = {name: [] for name in bodies}
    intra_edges = []
    for name, body in bodies.items():
        for line in body:
            call = re.search(r'\bbl(?:x)?\s+[0-9a-fx]+\s+<([^>]+)>', line)
            if call:
                target = call[1]
                base = target.split('+')[0]
                if base == name:
                    sym = (symbols or {}).get(name)
                    offset = int(target.split('+', 1)[1], 16) if '+' in target else 0
                    address = int(re.search(r'\bbl(?:x)?\s+([0-9a-fx]+)', line)[1], 16)
                    start = sym['address'] & ~1 if sym else -1
                    valid = bool(sym and offset > 0 and address == start + offset and
                                 start < address < start + sym['size'])
                    if valid:
                        intra_edges.append({'from': name, 'to': target, 'kind': 'outlined-intra-function-call'})
                    else:
                        graph[name].append((name, 'call'))
                else:
                    graph[name].append((base, 'call'))
                continue
            if re.search(r'\bblx\s+r\d+\b', line):
                raise ValueError(f'indirect call has unresolved target in {name}')
            branch = re.search(r'\bb(?:\.[nw])?\s+[0-9a-fx]+\s+<([^>]+)>', line)
            if branch:
                target = branch[1]
                base = target.split('+')[0]
                if base == name:
                    sym = (symbols or {}).get(name)
                    address = int(re.search(r'\bb(?:\.[nw])?\s+([0-9a-fx]+)', line)[1], 16)
                    start = sym['address'] & ~1 if sym else -1
                    valid = bool(sym and start <= address < start + sym['size'])
                    if valid:
                        intra_edges.append({'from': name, 'to': target, 'kind': 'intra-function-branch'})
                    else:
                        graph[name].append((name, 'tail'))
                else:
                    graph[name].append((base, 'tail'))
            bx = re.search(r'\bbx\s+(r\d+)\b', line)
            if bx:
                raise ValueError(f'indirect branch has unresolved target in {name}: {bx[1]}')

    memo, active = {}, set()
    def peak(name):
        if name in memo:
            return memo[name]
        if name in active:
            raise ValueError(f'recursive stack call chain is not bounded: {name}')
        if name not in bodies:
            raise ValueError(f'called function missing from linked disassembly: {name}')
        active.add(name)
        own = frames[name]
        best, best_chain = own, [name]
        for child, edge in graph[name]:
            child_size, child_chain = peak(child)
            candidate = own + child_size if edge == 'call' else max(own, child_size)
            candidate_chain = [name] + child_chain if edge == 'call' or own >= child_size else child_chain
            if candidate > best:
                best, best_chain = candidate, candidate_chain
        active.remove(name)
        memo[name] = best, best_chain
        return memo[name]

    size, chain = peak('main')
    if size > 2048:
        raise ValueError(f'live stack chain {size} exceeds 2048')
    return {'maximum_live_stack_bytes': size, 'maximizing_chain': chain,
            'frames': frame_rows, 'stack_limit_bytes': 2048, 'intra_function_edges': intra_edges}


def _artifacts(directory):
    names = {'firmware_source': 'firmware.c', 'stdout': 'firmware.stdout', 'stderr': 'firmware.stderr',
             'disassembly': 'firmware.disasm', 'binary': 'firmware.bin', 'elf': 'firmware.elf',
             'kernel_source': 'probe.c', 'kernel_header': 'probe.h', 'link_map': 'firmware.map',
             'startup_source': 'startup.s', 'linker_script': 'link.ld',
             'baseline_kernels_header': 'kernels.h', 'dependency_hashes': 'effective-dependency-hashes.json',
             'dependencies': 'effective-dependencies.json', 'macros': 'effective-macros.json',
             'commands': 'commands.json'}
    if (directory / 'library-source.c').is_file():
        names['library_source'] = 'library-source.c'
    names.update({f'stack_{p.stem}': p.name for p in directory.glob('*.su')})
    return {k: v for k, v in names.items() if (directory / v).is_file()}


def serialize_cost_fields(events, measured_samples):
    """Serialize the runner's derived metrics without lossy float conversion."""
    import panel_verify
    costs = panel_verify.derive_cost(events, measured_samples)
    return {'arm_zero_ws_cycles': costs['arm_zero_ws_cycles'],
            'cycles_per_output': str(costs['cycles_per_output']),
            'energy_weighted_integer': str(costs['energy_weighted_integer']),
            'energy_nj': str(costs['energy_nj']),
            'energy_nj_per_output': str(costs['energy_nj_per_output'])}


def _attempt(root, case, attempt_dir, x, warm, total):
    attempt_dir.mkdir(parents=True, exist_ok=False)
    start = time.time()
    commands = []
    record = {'identity': {k: case[k] for k in CASE_KEYS if k in case},
              'directory': str(attempt_dir.relative_to(root)), 'status': 'failed', 'commands': commands,
              'warmup_samples': warm, 'measured_samples': total - warm, 'total_samples': total}
    try:
        built = _compile(root, case, attempt_dir, x, warm, total, commands)
        stdout, stderr = _execute(built['binary'], attempt_dir, commands)
        import panel_verify
        events = panel_verify.rederive_raw_events(stderr)
        h = json.loads((root / 'panel-design.json').read_text())['filters'][case['filter']]['coefficients']
        if panel_verify._words(stdout, 'O', 16) != panel_verify._reference(h, x[:total]):
            raise ValueError('target output/reference mismatch')
        if panel_verify._words(stdout, 'H', 64) != panel_verify._retained(h, x[:total], case['variant'].startswith('trans_')):
            raise ValueError('target final state mismatch')
        if re.findall(r'^G:([0-9a-f]*)$', stdout, re.M) != ['5a5a5a5a'*4 + '5a5a'*4]:
            raise ValueError('target state/output guards changed')
        allocation = re.findall(r'^M:([0-9a-f]+)$', stdout, re.M)
        expected_state = state_allocation_from_header((attempt_dir / 'probe.h').read_text())
        if len(allocation) != 1 or int(allocation[0], 16) != expected_state:
            raise ValueError('target M state size differs from independent header ABI calculation')
        memory = memory_admission(built['elf'], attempt_dir / 'firmware.map')
        symbols = panel_verify._elf_layout(built['elf'])['symbols']
        stack = stack_admission(_stack_frame_files(attempt_dir),
                                (attempt_dir / 'firmware.disasm').read_text(), symbols)
        artifacts = _artifacts(attempt_dir)
        record.update({'status': 'passed', 'events': events, 'state_allocation_bytes': expected_state,
                       'memory': memory, 'stack': stack, 'compiler_identity': compiler_identity(case['compiler']),
                       'simulator_identity': simulator_identity(), 'artifact_paths': artifacts,
                       'artifact_sha256': {k: sha(attempt_dir / v) for k, v in artifacts.items()},
                       'measured_samples': total - warm, 'total_samples': total, 'warmup_samples': warm,
                       'outputs_verified': total, 'state_verified': True, 'guards_verified': True,
                       'mnemonics': panel_verify.instruction_subset((attempt_dir / 'firmware.disasm').read_text()),
                       'duration_seconds': time.time() - start})
        if 'stimulus' in case:
            record.update(serialize_cost_fields(events, total - warm))
            record['quantizer_clamp_paths'] = panel_verify.quantizer_clamp_paths(
                h, x, warm, total)
    except Exception as exc:
        record.update({'status': 'failed', 'reason': f'{type(exc).__name__}: {exc}',
                       'duration_seconds': time.time() - start})
        (attempt_dir / 'failure.json').write_bytes(dump(record))
    (attempt_dir / 'commands.json').write_bytes(dump(commands))
    # Include command log itself in the final hash list, avoiding self-referential bytes.
    record['artifact_paths'] = _artifacts(attempt_dir)
    record['artifact_sha256'] = {k: sha(attempt_dir / v) for k, v in record['artifact_paths'].items()}
    (attempt_dir / 'attempt.json').write_bytes(dump(record))
    return record


def _run_correctness(root, protocol, design):
    out = root / 'build/panel/correctness'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in gate_cases(protocol, design):
        if case['status'] == 'skipped':
            rows.append(case)
            continue
        identity = [case[k] for k in ('filter', 'variant', 'compiler', 'block')]
        attempt = _run_one_gate(root, protocol, design, identity)
        result = dict(attempt)
        if attempt.get('status') == 'passed':
            try:
                spec = importlib.util.spec_from_file_location('fir_panel_verify', HERE / 'panel_verify.py')
                verifier = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(verifier)
                result['independent_audit'] = verifier.audit_gate_attempt(attempt, root)
                result['admission_status'] = 'admitted'
            except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
                result.update(admission_status='failed', admission_reason=f'{type(exc).__name__}: {exc}')
        else:
            result.update(admission_status='failed', admission_reason=attempt.get('reason', 'runner gate failed'))
        rows.append(result)
    result = {'schema': 'fir-task5-correctness-gates-v1', 'protocol_sha256': PROTOCOL_SHA,
              'condition_limit': 72, 'condition_count': len(rows),
              'executed_conditions': sum(r.get('admission_status') == 'admitted' for r in rows),
              'skipped_conditions': sum(r.get('status') == 'skipped' for r in rows),
              'failed_conditions': sum(r.get('admission_status') == 'failed' for r in rows), 'rows': rows}
    path = out / 'correctness-gates.json'
    tmp = out / '.correctness-gates.json.tmp'
    tmp.write_bytes(dump(result)); os.replace(tmp, path)
    return result


def _run_one_gate(root, protocol, design, identity):
    case = select_gate_identity(protocol, design, identity)
    key = '__'.join(str(case[k]) for k in ('filter', 'variant', 'compiler', 'block'))
    parent = root / 'build/panel/correctness' / key
    parent.mkdir(parents=True, exist_ok=True)
    existing = sorted(parent.glob('attempt-*'))
    for prior in existing:
        manifest = prior / 'attempt.json'
        if not manifest.is_file():
            continue
        prior_row = json.loads(manifest.read_text())
        if prior_row.get('status') != 'passed':
            continue
        try:
            spec = importlib.util.spec_from_file_location('fir_panel_verify', HERE / 'panel_verify.py')
            verifier = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(verifier)
            verifier.audit_gate_attempt(prior_row, root)
        except (ValueError, OSError, KeyError, json.JSONDecodeError):
            # Preserve a runner-passed but independently rejected attempt, then
            # mechanically repair the same scientific identity in a new folder.
            continue
        return prior_row
    attempt_number = len(existing) + 1
    attempt = parent / f'attempt-{attempt_number:03d}'
    samples = gate_stream(case['design_row'])
    return _attempt(root, case, attempt, samples, 0, len(samples))


def select_performance_case(protocol, identity):
    if not isinstance(identity, (tuple, list)) or len(identity) != len(CASE_KEYS):
        raise ValueError('performance identity must be filter/variant/compiler/block/stimulus/regime')
    selected = tuple(identity)
    cases = protocol['cases']
    expected = next((case for case in cases if tuple(case[k] for k in CASE_KEYS) == selected), None)
    if expected is None:
        raise ValueError('performance identity is absent from frozen protocol')
    if (expected['filter'] == 'native_lp1800' and expected['variant'] == 'cmsis32_unroll'
            and expected['block'] == 64):
        raise ValueError('performance identity is unavailable: ' + PENDING_FAST_REASON)
    return expected


def _latest_attempt(directory):
    attempts = sorted(directory.glob('attempt-*'))
    for attempt in reversed(attempts):
        manifest = attempt / 'attempt.json'
        if manifest.is_file():
            yield attempt, json.loads(manifest.read_text())


def _run_one_performance(root, protocol, design, inputs, identity):
    case = select_performance_case(protocol, identity)
    # Every performance identity must already have its exact correctness gate.
    gate_file = root / 'build/panel/correctness/correctness-gates.json'
    gate_result = json.loads(gate_file.read_text())
    gate = next((r for r in gate_result['rows']
                 if tuple((r.get('identity') or r).get(k) for k in ('filter', 'variant', 'compiler', 'block')) ==
                 tuple(case[k] for k in ('filter', 'variant', 'compiler', 'block'))), None)
    if gate is None or gate.get('admission_status') != 'admitted':
        raise ValueError('matching correctness gate is not independently admitted')
    key = '__'.join(str(case[k]) for k in CASE_KEYS)
    parent = root / 'build/panel/performance' / key
    parent.mkdir(parents=True, exist_ok=True)
    x = inputs[case['stimulus']][:case['total_samples']]
    for prior_dir, prior in _latest_attempt(parent):
        if prior.get('status') != 'passed':
            continue
        try:
            spec = importlib.util.spec_from_file_location('fir_panel_verify', HERE / 'panel_verify.py')
            verifier = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(verifier)
            audit = verifier.audit_execution_attempt(prior, root, protocol, design, case, x)
            cost = verifier.audit_serialized_cost(prior, prior_dir)
        except (ValueError, OSError, KeyError, json.JSONDecodeError):
            continue
        if audit['status'] == 'admitted':
            return prior, cost
    attempt_number = 1 + max((int(p.name.split('-')[1]) for p in parent.glob('attempt-*')
                              if p.name.split('-')[-1].isdigit()), default=0)
    attempt_dir = parent / f'attempt-{attempt_number:03d}'
    row = _attempt(root, case, attempt_dir, x, case['warmup_samples'], case['total_samples'])
    if row.get('status') != 'passed':
        return row, None
    spec = importlib.util.spec_from_file_location('fir_panel_verify', HERE / 'panel_verify.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    audit = verifier.audit_execution_attempt(row, root, protocol, design, case, x)
    cost = verifier.audit_serialized_cost(row, attempt_dir)
    row['independent_audit'] = audit
    (attempt_dir / 'attempt.json').write_bytes(dump(row))
    return row, cost


def _save_performance_checkpoint(root, protocol, design, inputs, current_row):
    path = root / 'build/panel/performance/checkpoint-results.json'
    existing = []
    if path.is_file():
        previous = json.loads(path.read_text())
        existing = previous.get('rows', [])
    rows_by_identity = {tuple(r.get('identity', {}).get(k) for k in CASE_KEYS): r for r in existing}
    key = tuple(current_row['identity'][k] for k in CASE_KEYS)
    result_row = dict(current_row)
    result_row['status'] = 'admitted' if current_row.get('status') == 'passed' else 'failed'
    rows_by_identity[key] = result_row
    rows = [rows_by_identity[k] for k in sorted(rows_by_identity)]
    audit_rows = []
    for row in rows:
        if row.get('status') != 'admitted':
            raise ValueError('cannot write checkpoint with a non-admitted performance row')
        audit = panel_verify_case(row, root, protocol, design, inputs)
        row['quantizer_clamp_paths'] = audit['execution']['quantizer_clamp_paths']
        audit_rows.append({'identity': row['identity'], 'audit': audit})
    payload = {'schema': 'fir-task5-performance-checkpoint-v1',
               'protocol_sha256': PROTOCOL_SHA, 'condition_count': len(rows),
               'rows': rows, 'audited': audit_rows}
    tmp = path.with_name('.checkpoint-results.json.tmp')
    tmp.write_bytes(dump(payload)); os.replace(tmp, path)


def panel_verify_case(row, root, protocol, design, inputs):
    import importlib.util
    spec = importlib.util.spec_from_file_location('fir_panel_verify', HERE / 'panel_verify.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    return verifier.audit_case(row, root, protocol, design, inputs)


def _run_one_performance_and_save(root, protocol, design, inputs, identity):
    row, _cost = _run_one_performance(root, protocol, design, inputs, identity)
    if row.get('status') != 'passed':
        return row
    _save_performance_checkpoint(root, protocol, design, inputs, row)
    return row


def _write_json_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.tmp')
    tmp.write_bytes(dump(payload))
    os.replace(tmp, path)


def _run_performance_campaign(root, protocol, design, inputs):
    progress_path = root / 'build/panel/performance/campaign-progress.json'
    checkpoint_path = root / 'build/panel/performance/checkpoint-results.json'
    known = {}
    if checkpoint_path.is_file():
        checkpoint = json.loads(checkpoint_path.read_text())
        if checkpoint.get('protocol_sha256') != PROTOCOL_SHA:
            raise ValueError('performance checkpoint protocol digest mismatch')
        for row in checkpoint.get('rows', []):
            ident = row.get('identity', {})
            key = tuple(ident.get(k) for k in CASE_KEYS)
            if key in known:
                raise ValueError(f'duplicate checkpoint identity: {key}')
            known[key] = row
    rows = []
    for index, case in enumerate(protocol['cases'], 1):
        key = tuple(case[k] for k in CASE_KEYS)
        if case['filter'] == 'native_lp1800' and case['variant'] == 'cmsis32_unroll' and case['block'] == 64:
            row = {'identity': {k: case[k] for k in CASE_KEYS}, 'status': 'unavailable',
                   'reason': PENDING_FAST_REASON}
        elif key in known and known[key].get('status') == 'admitted':
            row = dict(known[key])
            try:
                panel_verify_case(row, root, protocol, design, inputs)
            except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
                raise ValueError(f'previously admitted checkpoint row failed fresh audit: {key}: {exc}')
        else:
            try:
                attempt, _cost = _run_one_performance(root, protocol, design, inputs, key)
                if attempt.get('status') != 'passed':
                    row = dict(attempt); row['status'] = 'failed'
                    row.setdefault('reason', 'runner failed')
                else:
                    row = dict(attempt)
                    row['status'] = 'admitted'
                    audit = panel_verify_case(row, root, protocol, design, inputs)
                    row['quantizer_clamp_paths'] = audit['execution']['quantizer_clamp_paths']
            except (ValueError, OSError, KeyError, RuntimeError, json.JSONDecodeError) as exc:
                row = {'identity': {k: case[k] for k in CASE_KEYS}, 'status': 'failed',
                       'reason': f'{type(exc).__name__}: {exc}'}
        rows.append(row)
        progress = {'schema': 'fir-task5-performance-progress-v1', 'protocol_sha256': PROTOCOL_SHA,
                    'completed_case_count': index, 'condition_count': len(rows),
                    'rows': rows}
        _write_json_atomic(progress_path, progress)
        if index % 10 == 0 or index == 288:
            print(f'completed {index}/288 identities; admitted={sum(r["status"] == "admitted" for r in rows)}; '
                  f'unavailable={sum(r["status"] == "unavailable" for r in rows)}; '
                  f'failed={sum(r["status"] == "failed" for r in rows)}', flush=True)
    results = {'schema': 'fir-task5-performance-results-v1', 'protocol_sha256': PROTOCOL_SHA,
               'identity_count': 288, 'rows': rows}
    results_path = root / 'panel-results.json'
    _write_json_atomic(results_path, results)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run fixed FIR Task 5 gates')
    parser.add_argument('stage', choices=('correctness', 'performance'))
    parser.add_argument('--root', type=Path, default=HERE)
    parser.add_argument('--identity', help='single declared gate identity FILTER/VARIANT/COMPILER/BLOCK')
    args = parser.parse_args(argv)
    root, protocol, design, _inputs = frozen(args.root)
    if args.stage == 'correctness':
        if args.identity:
            parts = args.identity.split('/')
            if len(parts) != 4:
                raise SystemExit('--identity must be FILTER/VARIANT/COMPILER/BLOCK')
            parts[3] = int(parts[3])
            row = _run_one_gate(root, protocol, design, parts)
            print(json.dumps({k: row.get(k) for k in ('identity', 'status', 'reason', 'directory')}, indent=2))
            return
        result = _run_correctness(root, protocol, design)
        print(json.dumps({k: result[k] for k in ('executed_conditions', 'skipped_conditions', 'failed_conditions')}, indent=2))
        return
    if not args.identity:
        result = _run_performance_campaign(root, protocol, design, _inputs)
        print(json.dumps({'identity_count': result['identity_count'],
                          'admitted': sum(r['status'] == 'admitted' for r in result['rows']),
                          'unavailable': sum(r['status'] == 'unavailable' for r in result['rows']),
                          'failed': sum(r['status'] == 'failed' for r in result['rows'])}, indent=2))
        return
    parts = args.identity.split('/')
    if len(parts) != 6:
        raise SystemExit('--identity must be FILTER/VARIANT/COMPILER/BLOCK/STIMULUS/REGIME')
    parts[3] = int(parts[3])
    row = _run_one_performance_and_save(root, protocol, design, _inputs, parts)
    print(json.dumps({'identity': row.get('identity'), 'status': row.get('status'),
                      'reason': row.get('reason'), 'directory': row.get('directory')}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f'panel_run: {exc}')
