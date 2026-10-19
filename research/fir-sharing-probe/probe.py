"""Throwaway exact FIR sharing probe. Run: python3 research/fir-sharing-probe/probe.py

Not a production generator or a new algorithm. See PROTOCOL.md before interpreting.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import re
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'fir-baseline'
sys.path.insert(0, str(BASE))
from simulator import (FLAGS, command, sha, run, arm_zero_ws_cycles,
                       estimated_energy_nj, microchecks, ENERGY_WEIGHTS, PIN)
from experiment import check_instruction_subset, decode_output
from selection_validation import is_admitted, reference_outputs, toolchains

BUILD = HERE / 'build'
FILTERS = ('speech_lp48', 'speech_minphase48', 'vibration_bp192')
GENERATED = ('spec_direct', 'spec_fold', 'trans_const', 'trans_csd',
             'trans_hcub_eager', 'trans_hcub_demand')


def width(bound):
    assert 0 <= bound <= 2**63-1
    return 32 if bound <= 2**31-1 else 64


def graph(name):
    """Independently recover exact linear identities from original Hcub output."""
    raw = (HERE / 'vendor' / f'{name}.txt').read_text()
    outputs = {int(c): t for t, c in re.findall(r'//\s+int (t\d+) = (\d+) \* t0', raw)}
    coeff = {'t0': 1}
    ops = {}
    for line in raw.splitlines():
        m = re.fullmatch(r'(t\d+) = (.*);\s*/\*\s*(-?\d+)\s*\*/', line)
        if not m:
            assert not re.match(r't\d+ =', line), line
            continue
        dst, expr, comment = m.groups()
        call = re.fullmatch(r'(\w+)\((.*)\)', expr)
        op, args = (call[1], call[2].replace(' ', '').split(',')) if call else ('copy', [expr])
        assert op in ('copy', 'add', 'sub', 'shl', 'shr', 'neg'), (op, args)
        a = coeff[args[0]]
        if op == 'copy': v = a
        elif op == 'add': v = a + coeff[args[1]]
        elif op == 'sub': v = a - coeff[args[1]]
        elif op == 'neg': v = -a
        elif op == 'shl': v = a * 2**int(args[1])
        else:
            divisor = 2**int(args[1])
            assert a % divisor == 0, (dst, 'nonexact right shift')
            v = a // divisor
        assert v == int(comment), (dst, v, comment)
        coeff[dst] = v
        ops[dst] = (op, args)
    for c, t in outputs.items():
        assert coeff[t] == c
    return outputs, ops, coeff, raw


def csd(c):
    """Standard nonadjacent signed binary digits; no sharing search."""
    original = c
    sign = -1 if c < 0 else 1
    c = abs(c)
    terms = []
    bit = 0
    while c:
        if c & 1:
            digit = 2 - c % 4
            terms.append(sign * digit * 2**bit)
            c -= digit
        c //= 2
        bit += 1
    assert sum(terms) == original
    return terms[::-1]


def certificates(name, h, maximum):
    outputs, ops, coeff, raw = graph(name)
    odds = {abs(c)//(abs(c) & -abs(c)) for c in h if c}
    assert odds <= set(outputs)
    state = [maximum*sum(abs(c) for c in h[i+1:]) for i in range(len(h)-1)]
    node = {t: {'coefficient': c, 'absolute_bound': abs(c)*maximum,
                'width': width(abs(c)*maximum)} for t, c in coeff.items()}
    # Every primitive has its own certified operand/result. No signed shifts in C.
    for c in h:
        partial = 0
        for term in csd(c):
            assert width(abs(term)*maximum) == 32
            partial += term
            assert width(abs(partial)*maximum) == 32
        assert partial == c
    words = [width(b)//32 for b in state]
    # Source-operation diagnostic only. LDM/STM and register retention can
    # make machine execution cheaper; this estimate MUST NOT reject a kernel.
    graph_ops = len({(op, tuple(args)) for op, args in ops.values() if op != 'copy'})
    transfers = 2*sum(words)+2
    additions = sum(words[:-1]) + width(maximum*sum(abs(c) for c in h))//32
    diagnostic = {'named_graph_operations': len(ops), 'unique_primitive_expressions': graph_ops,
                  'source_state_word_transfers_per_output': 2*sum(words),
                  'single_word_access_cycle_estimate_without_products': 2*transfers+additions,
                  'can_reject_candidate': False,
                  'scope': 'source-operation estimate only; LDM/STM, CSE and register retention can reduce it; excludes product graph, control, quantizer and spills'}
    return {'maximum': maximum, 'coefficient_l1': sum(abs(c) for c in h),
            'sum_width': width(maximum*sum(abs(c) for c in h)),
            'state_bounds': state, 'state_widths': [width(b) for b in state],
            'state_payload_bytes': sum(words)*4,
            'direct_history_bytes': 2*(len(h)-1), 'graph_nodes': node,
            'hcub_output_sha256': hashlib.sha256(raw.encode()).hexdigest(),
            'screen': diagnostic}


QUANT = '''
static int16_t quant(int64_t s) {
    if (s >= 1073741824LL) return 32767;
    if (s <= -1073741824LL) return -32768;
    int32_t q=(int32_t)s;
    return (int16_t)(q>=0 ? q/32768 : -1-(-(q+1))/32768);
}
'''


def generate(name, h, maximum, variant, block, force_state64=False):
    cert = certificates(name, h, maximum)
    n = len(h)
    trans = variant.startswith('trans_')
    if force_state64:
        assert trans
        cert['state_widths']=[64]*(n-1)
        cert['state_payload_bytes']=8*(n-1)
    library = variant.startswith('cmsis')
    fields = ([f'int{w}_t z{i};' for i, w in enumerate(cert['state_widths'])] if trans
              else [f'int16_t history[{n+block}];'])
    if library: fields.append('arm_fir_instance_q15 instance;')
    header = ('#include <stdint.h>\n' + ('#include "dsp/filtering_functions.h"\n' if library else '')
              + '#define TAPS '+str(n)+'\n' + 'typedef struct {\n'+'\n'.join(fields)+'\n} ProbeState;\n'
              + 'void probe_init(ProbeState *);\nvoid probe_process(ProbeState *,const int16_t *,int16_t *,uint32_t);\n'
              + 'int64_t probe_get_state(ProbeState *,uint32_t);\nunsigned probe_state_bytes(void);\n')
    lines = ['#include "probe.h"', '#include "kernels.h"',
             'void probe_init(ProbeState *s) {',
             'for(unsigned i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;']
    if library:
        lines += ['s->instance.numTaps=TAPS; s->instance.pState=s->history;',
                  'static const int16_t reversed[TAPS]={'+','.join(map(str,h[::-1]))+'};',
                  's->instance.pCoeffs=reversed;']
    lines += ['}', 'unsigned probe_state_bytes(void) {return sizeof(ProbeState);}',
              'int64_t probe_get_state(ProbeState *s,uint32_t i) {']
    if trans:
        lines += ['switch(i) {']+[f'case {i}:return s->z{i};' for i in range(n-1)]+['default:return 0;}']
    else: lines += ['return s->history[i];']
    lines += ['}']
    if variant in GENERATED: lines += [QUANT]
    lines += ['void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b) {']
    if library:
        symbol = 'arm_fir_fast_q15' if variant.startswith('cmsis32') else 'arm_fir_q15'
        lines += [f'{symbol}(&s->instance,x,y,b);']
    elif variant in ('direct32','direct64','fold32','fold64'):
        lines += ['static const int16_t h[TAPS]={'+','.join(map(str,h))+'};',
                  f'{variant}(s->history,h,x,y,TAPS,b);']
    elif not trans:
        lines += ['for(uint32_t j=0;j<b;++j) s->history[TAPS-1+j]=x[j];',
                  'for(uint32_t j=0;j<b;++j) {', f'int{cert["sum_width"]}_t sum=0;']
        if variant == 'spec_fold':
            assert h == h[::-1]
            for i in range(n//2):
                if not h[i]: continue
                assert 2*maximum*abs(h[i]) <= 2**31-1
                lines += [f'int32_t pair{i}=(int32_t)s->history[j+{i}]+s->history[j+{n-1-i}];',
                          f'sum+=(int32_t)({h[i]})*pair{i};']
            if n%2 and h[n//2]: lines += [f'sum+=(int32_t)({h[n//2]})*s->history[j+{n//2}];']
        else:
            for i, c in enumerate(h):
                if c: lines += [f'sum+=(int32_t)({c})*s->history[j+{n-1-i}];']
        lines += ['y[j]=quant(sum);}', 'for(uint32_t j=0;j<TAPS-1;++j) s->history[j]=s->history[b+j];']
    else:
        outputs, ops, coeff, raw = graph(name)
        lines += ['for(uint32_t j=0;j<b;++j) {', 'int32_t t0=x[j];']
        emitted = {'t0'}

        def emit(t):
            if t in emitted: return
            op,args = ops[t]
            for arg in args:
                if arg.startswith('t'): emit(arg)
            w = cert['graph_nodes'][t]['width']
            cast = f'(int{w}_t)'
            if op == 'copy': expr = args[0]
            elif op in ('add','sub'): expr = cast+args[0]+('+' if op=='add' else '-')+args[1]
            elif op == 'neg': expr = '-'+cast+args[0]
            else: expr = cast+args[0]+('*' if op=='shl' else '/')+str(2**int(args[1]))
            lines.append(f'int{w}_t {t}={expr};')
            emitted.add(t)

        if variant == 'trans_hcub_eager':
            for t in ops: emit(t)

        def product(c):
            if not c: return '0'
            if variant == 'trans_const': return f'(int32_t)({c})*t0'
            if variant == 'trans_csd':
                terms=csd(c)
                return '('+'+'.join(f'(t0*({v}))' for v in terms)+')'
            odd=abs(c)//(abs(c)&-abs(c))
            t=outputs[odd]
            emit(t)
            return f'({t}*({c//odd}))'

        for i,c in enumerate(h):
            p=product(c)
            if i==0:
                lines += [f'int{cert["sum_width"]}_t out=(int{cert["sum_width"]}_t)({p})+s->z0;',
                          'y[j]=quant(out);']
            else:
                w=cert['state_widths'][i-1]
                tail=f'+s->z{i}' if i<n-1 else ''
                lines += [f's->z{i-1}=(int{w}_t)({p}){tail};']
        lines += ['}']
    lines += ['}']
    if variant.startswith('trans_hcub'):
        # Preserve the authors' original generated-output copyright/license notice.
        lines.insert(0, '\n'.join(line for line in raw.splitlines() if line.startswith('//')))
    return header, '\n'.join(lines)+'\n', cert


def expected_state(h, x, trans):
    if not trans: return ([0]*(len(h)-1)+x)[-(len(h)-1):]
    return [sum(h[k]*x[len(x)-1-(k-i-1)] for k in range(i+1,len(h))
                if len(x)-1-(k-i-1)>=0) for i in range(len(h)-1)]


def variants(h, maximum):
    names=['direct32' if is_admitted('direct32',h,maximum) else 'direct64']
    if h==h[::-1]: names += ['fold32' if is_admitted('fold32',h,maximum) else 'fold64']
    names += [v for v in ('cmsis64','cmsis64_unroll','cmsis32','cmsis32_unroll')
              if is_admitted(v,h,maximum)]
    names += [v for v in GENERATED if v!='spec_fold' or h==h[::-1]]
    return names


def write_case(directory,name,h,maximum,variant,block,x,force_state64=False):
    directory.mkdir(parents=True,exist_ok=True)
    header,source,cert=generate(name,h,maximum,variant,block,force_state64)
    (directory/'probe.h').write_text(header)
    (directory/'probe.c').write_text(source)
    return cert


def host_checks(design):
    count=0
    for name in FILTERS:
        h=design['filters'][name]['coefficients']
        for maximum in (1024,32768):
            rng=random.Random(20261020)
            low=-maximum; high=maximum-1
            signals=[[low,high,0,-1,1]*53,
                     [rng.randint(low,high) for _ in range(265)],
                     [low if c>0 else high for c in h[::-1]]+[0]*73]
            for variant in GENERATED:
                if variant=='spec_fold' and h!=h[::-1]: continue
                directory=BUILD/'host'/f'{name}-{maximum}-{variant}'
                write_case(directory,name,h,maximum,variant,64,[])
                lib=directory/'probe.so'
                command(['gcc','-std=c11','-O2','-shared','-fPIC','-fsanitize=undefined',
                         '-fno-sanitize-recover=undefined','-Wall','-Wextra','-Werror',
                         '-I',BASE,'-I',directory,directory/'probe.c','-o',lib])
                dll=ctypes.CDLL(str(lib))
                dll.probe_state_bytes.restype=ctypes.c_uint
                dll.probe_init.argtypes=[ctypes.c_void_p]
                dll.probe_process.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int16),
                                           ctypes.POINTER(ctypes.c_int16),ctypes.c_uint]
                dll.probe_get_state.argtypes=[ctypes.c_void_p,ctypes.c_uint]
                dll.probe_get_state.restype=ctypes.c_int64
                for x in signals:
                    raw=ctypes.create_string_buffer(dll.probe_state_bytes()+16)
                    addr=ctypes.addressof(raw)+8
                    raw[:8]=b'guard123'; raw[-8:]=b'guard456'
                    dll.probe_init(addr)
                    inp=(ctypes.c_int16*len(x))(*x)
                    out=(ctypes.c_int16*(len(x)+4))(*([23130]*(len(x)+4)))
                    offset=0
                    for b in [1,64,3,16,1,63,2,64,7,44]*10:
                        b=min(b,len(x)-offset)
                        if not b: break
                        dll.probe_process(addr,ctypes.cast(ctypes.byref(inp,2*offset),ctypes.POINTER(ctypes.c_int16)),
                                          ctypes.cast(ctypes.byref(out,2*(offset+2)),ctypes.POINTER(ctypes.c_int16)),b)
                        offset+=b
                    assert offset==len(x)
                    assert list(out)[2:-2]==reference_outputs(h,x),(name,maximum,variant,'output')
                    assert [dll.probe_get_state(addr,i) for i in range(len(h)-1)]==expected_state(h,x,variant.startswith('trans_'))
                    assert raw[:8]==b'guard123' and raw[-8:]==b'guard456'
                    assert list(out)[:2]+list(out)[-2:]==[23130]*4
                    count+=len(x)
    return {'host_output_comparisons':count,'ubsan':True,'mixed_partitions':True,
            'state_and_output_guards':True,'retained_states':True}


def firmware(x,block):
    return '''#include "probe.h"
static struct { uint64_t lo; ProbeState state; uint64_t hi; } storage;
static int16_t source[SAMPLES];
static int16_t destination[SAMPLES+4];
extern void measured(void);
void process_stream(void) {
 for(uint32_t off=0;off<SAMPLES;off+=BLOCK) {
  uint32_t b=SAMPLES-off; if(b>BLOCK)b=BLOCK;
  probe_process(&storage.state,source+off,destination+2+off,b);
 }
}
static void put(char c){*(volatile uint32_t*)0xe0000000=(uint32_t)c;}
static void hex32(uint32_t v){for(int s=28;s>=0;s-=4){unsigned d=(v>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
static void hex16(int16_t v){uint32_t u=(uint16_t)v;for(int s=12;s>=0;s-=4){unsigned d=(u>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
int main(void) {
 for(unsigned i=0;i<SAMPLES;++i)source[i]=input_data[i];
 probe_init(&storage.state); storage.lo=storage.hi=0x5a5a5a5a5a5a5a5aULL;
 destination[0]=destination[1]=destination[SAMPLES+2]=destination[SAMPLES+3]=23130;
 measured(); put('O');put(':');for(unsigned i=0;i<SAMPLES;++i)hex16(destination[i+2]);put('\\n');
 put('H');put(':');for(unsigned i=0;i<TAPS-1;++i){uint64_t v=(uint64_t)probe_get_state(&storage.state,i);hex32((uint32_t)(v>>32));hex32((uint32_t)v);}put('\\n');
 put('G');put(':');hex32((uint32_t)storage.lo);hex32((uint32_t)(storage.lo>>32));hex32((uint32_t)storage.hi);hex32((uint32_t)(storage.hi>>32));
 hex16(destination[0]);hex16(destination[1]);hex16(destination[SAMPLES+2]);hex16(destination[SAMPLES+3]);put('\\n');
 put('M');put(':');hex32(probe_state_bytes());put('\\n');return 0;
}
'''.replace('#include "probe.h"','#include "probe.h"\n'+f'#define BLOCK {block}\n#define SAMPLES {len(x)}\n'
             +'static const int16_t input_data[SAMPLES]={'+','.join(map(str,x))+'};')


def target_case(sim,compiler,directory,name,h,maximum,variant,block,x,force_state64=False):
    cert=write_case(directory,name,h,maximum,variant,block,x,force_state64)
    (directory/'firmware.c').write_text(firmware(x,block))
    common=[compiler,*FLAGS,'-O2','-Wall','-Wextra','-Werror','-fstack-usage',
            '-I',directory,'-I',BASE,'-I',BASE/'build/cmsis-dsp/Include','-I',BASE/'build/cmsis-core']
    objects=[]
    for source in (directory/'probe.c',directory/'firmware.c',BASE/'startup.s'):
        obj=directory/(source.stem+'.o'); command([*common,'-c',source,'-o',obj]); objects.append(obj)
    if variant.startswith('cmsis'):
        symbol='arm_fir_fast_q15' if variant.startswith('cmsis32') else 'arm_fir_q15'
        macros=['-DARM_MATH_LOOPUNROLL'] if variant.endswith('_unroll') else []
        source=BASE/'build/cmsis-dsp/Source/FilteringFunctions'/f'{symbol}.c'
        obj=directory/'library.o'; command([*common,*macros,'-c',source,'-o',obj]); objects.append(obj)
    elif variant not in GENERATED:
        obj=directory/'generic.o';command([*common,'-c',BASE/'kernels.c','-o',obj]);objects.append(obj)
    elf=directory/'firmware.elf'
    command([compiler,*FLAGS,'-nostdlib','-T',BASE/'link.ld','-Wl,--gc-sections',
             f'-Wl,-Map={directory/"firmware.map"}',*objects,'-lgcc','-o',elf])
    command([compiler.with_name('arm-none-eabi-objcopy'),'-O','binary',elf,directory/'firmware.bin'])
    dis=command([compiler.with_name('arm-none-eabi-objdump'),'-d',elf]).stdout
    (directory/'firmware.disasm').write_text(dis)
    mnemonics=check_instruction_subset(dis)
    events,stdout=run(sim,directory/'firmware.bin')
    assert decode_output(stdout,'O').tolist()==reference_outputs(h,x),(directory,'output')
    encoded=re.search(r'^H:([a-f0-9]*)$',stdout,re.M)[1]
    state=[int(encoded[i:i+16],16) for i in range(0,len(encoded),16)]
    state=[v-2**64 if v>=2**63 else v for v in state]
    assert state==expected_state(h,x,variant.startswith('trans_')),(directory,'state')
    assert re.search(r'^G:(.*)$',stdout,re.M)[1]=='5a5a5a5a'*4+'5a5a'*4,(directory,'guards')
    size=int(re.search(r'^M:([a-f0-9]+)$',stdout,re.M)[1],16)
    usage='\n'.join(p.read_text() for p in directory.glob('*.su'))
    stack=[{'function':m[0],'bytes':int(m[1]),'kind':m[2]} for m in
           re.findall(r'\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)',usage)]
    sizes=command([compiler.with_name('arm-none-eabi-size'),elf]).stdout
    (directory/'size.txt').write_text(sizes)
    artifacts={p.name:sha(p) for p in directory.iterdir() if p.is_file()}
    return {'variant':variant,'maximum':maximum,'block':block,'samples':len(x),
            'force_state64':force_state64,
            'state_allocation_bytes':size,'transposed_payload_bytes':cert['state_payload_bytes'] if variant.startswith('trans_') else None,
            'stack_usage':stack,'elf_size':sizes,'mnemonics':mnemonics,**events,
            'arm_zero_ws_cycles':arm_zero_ws_cycles(events),'estimated_cpu_energy_nj':estimated_energy_nj(events),
            'outputs_verified':len(x),'retained_state_verified':True,'guards_verified':True,
            'directory':str(directory.relative_to(HERE)),'artifacts':artifacts}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',action='store_true')
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--ablate',action='store_true')
    args=parser.parse_args()
    design=json.loads((BASE/'selection-design.json').read_text())
    BUILD.mkdir(exist_ok=True)
    if args.verify:
        print(json.dumps(verify_results(design)));return
    if args.ablate:
        data=json.loads((HERE/'results.json').read_text())
        rows=[];name='speech_minphase48';h=design['filters'][name]['coefficients']
        for block in (1,64):
            for variant in ('trans_const','trans_hcub_demand'):
                directory=BUILD/'posthoc-width'/f'gcc15-{name}-b{block}-{variant}-uniform64'
                row=target_case(BASE/'build/thumbulator/sim_main',toolchains()['gcc15'],directory,
                                name,h,32768,variant,block,data['actual_input'],True)
                rows.append({'compiler':'gcc15','filter':name,**row})
        data['posthoc_width_controls']=rows
        data['source_sha256']=sha(__file__)
        (HERE/'results.json').write_text(json.dumps(data,indent=2)+'\n')
        print(json.dumps({'posthoc_width_binaries':len(rows),'outputs_verified':sum(r['outputs_verified'] for r in rows)}));return
    if args.host:
        result=host_checks(design)
        (HERE/'host-checks.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result));return
    command([sys.executable,Path(__file__).resolve(),'--host'])
    sim=BASE/'build/thumbulator/sim_main'
    assert sha(sim)==json.loads((BASE/'results.json').read_text())['simulator_binary_sha256']
    checks=microchecks(sim)
    certs={name:{str(m):certificates(name,design['filters'][name]['coefficients'],m)
                 for m in (1024,32768)} for name in FILTERS}
    (HERE/'certificates.json').write_text(json.dumps(certs,indent=2)+'\n')
    raw=design['inputs']['adc_raw'][:257]
    results=[];smoke=[]
    compilers=toolchains()
    for cname,compiler in compilers.items():
        for name in FILTERS:
            h=design['filters'][name]['coefficients']
            for maximum in (1024,32768):
                for block in (1,64):
                    print(f'{cname} {name} M={maximum} block={block}',flush=True)
                    for variant in variants(h,maximum):
                        directory=BUILD/'cases'/f'{cname}-{name}-{maximum}-b{block}-{variant}'
                        row=target_case(sim,compiler,directory,name,h,maximum,variant,block,raw)
                        results.append({'compiler':cname,'filter':name,**row})
        # Separate target edge checks do not enter the timing comparison.
        for name in FILTERS:
            h=design['filters'][name]['coefficients']
            x=[-32768,32767,0,-1,1]*53
            for variant in GENERATED:
                if variant=='spec_fold' and h!=h[::-1]:continue
                directory=BUILD/'edge'/f'{cname}-{name}-{variant}'
                smoke.append(target_case(sim,compiler,directory,name,h,32768,variant,64,x))
    result={'status':'exploratory established-method probe; no novelty/hardware claim',
            'protocol_sha256':sha(HERE/'PROTOCOL.md'),'source_sha256':sha(__file__),
            'design_sha256':sha(BASE/'selection-design.json'),
            'generator_archive_sha256':sha(HERE/'vendor/synth-jan-14-2009.tar.gz'),
            'generator_examples_sha256':sha(HERE/'vendor/examples-manifest.json'),
            'dependency_sources':dependency_sources(), 'model':model_description(),
            'simulator_sha256':sha(sim),'compilers':{k:{'sha256':sha(v),'version':command([v,'--version']).stdout.splitlines()[0]} for k,v in compilers.items()},
            'microchecks':checks,'host_checks':json.loads((HERE/'host-checks.json').read_text()),
            'filters':{n:design['filters'][n] for n in FILTERS},'actual_input':raw,
            'rows':results,'target_edge_checks':smoke}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'measured_binaries':len(results),'edge_binaries':len(smoke),
                      'target_output_comparisons':sum(r['outputs_verified'] for r in results+smoke)}))


def dependency_sources():
    files=['simulator.py','experiment.py','selection_validation.py','cmsis_baseline.py',
           'kernels.c','kernels.h','startup.s','link.ld',
           'build/cmsis-dsp/Source/FilteringFunctions/arm_fir_q15.c',
           'build/cmsis-dsp/Source/FilteringFunctions/arm_fir_fast_q15.c']
    return {str((BASE/f).relative_to(HERE.parent)):sha(BASE/f) for f in files}


def model_description():
    return {'simulator_commit':PIN,'timing_formula':'NI + SRAM_reads + SRAM_writes + Flash_data_reads + 2*taken_branches + BL',
            'configuration':'single-cycle MUL; zero-wait Arm-table estimate; 20 MHz prefetch OFF zero-wait CPU energy model',
            'energy_weights_nj':ENERGY_WEIGHTS,'energy_source':'https://arxiv.org/html/2301.12806v1',
            'hardware_validated':False,'raw_ticks_are_cycles':False}


def verify_results(design):
    """Reconstruct references and generated C, check every artifact and metric."""
    data=json.loads((HERE/'results.json').read_text())
    assert data['design_sha256']==sha(BASE/'selection-design.json')
    assert data['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    assert data['source_sha256']==sha(__file__)
    assert data['dependency_sources']==dependency_sources()
    assert data['model']==model_description()
    assert data['generator_archive_sha256']==sha(HERE/'vendor/synth-jan-14-2009.tar.gz')
    assert data['generator_examples_sha256']==sha(HERE/'vendor/examples-manifest.json')
    assert data['simulator_sha256']==sha(BASE/'build/thumbulator/sim_main')
    for label,compiler in toolchains().items():
        assert data['compilers'][label]['sha256']==sha(compiler)
    seen=set(); total=0
    edge=[-32768,32767,0,-1,1]*53
    for stage,rows in (('primary',data['rows']),('edge',data['target_edge_checks']),
                       ('posthoc',data.get('posthoc_width_controls',[]))):
        is_edge=stage=='edge'
        for row in rows:
            directory=HERE/row['directory']
            name=row.get('filter')
            if name is None:
                name=next(n for n in FILTERS if f'-{n}-' in directory.name)
            h=design['filters'][name]['coefficients']
            variant=row['variant'];m=row['maximum'];block=row['block']
            x=edge if is_edge else data['actual_input']
            expected_header,expected_source,_=generate(name,h,m,variant,block,row.get('force_state64',False))
            assert (directory/'probe.h').read_text()==expected_header
            assert (directory/'probe.c').read_text()==expected_source
            assert (directory/'firmware.c').read_text()==firmware(x,block)
            for filename,digest in row['artifacts'].items():
                assert sha(directory/filename)==digest,(directory,filename,'hash')
            stdout=(directory/'firmware.stdout').read_text()
            assert decode_output(stdout,'O').tolist()==reference_outputs(h,x)
            encoded=re.search(r'^H:([a-f0-9]*)$',stdout,re.M)[1]
            values=[int(encoded[i:i+16],16) for i in range(0,len(encoded),16)]
            values=[v-2**64 if v>=2**63 else v for v in values]
            assert values==expected_state(h,x,variant.startswith('trans_'))
            assert re.search(r'^G:(.*)$',stdout,re.M)[1]=='5a5a5a5a'*4+'5a5a'*4
            assert row['arm_zero_ws_cycles']==arm_zero_ws_cycles(row)
            assert abs(row['estimated_cpu_energy_nj']-estimated_energy_nj(row))<1e-8
            assert row['mnemonics']==check_instruction_subset((directory/'firmware.disasm').read_text())
            assert row['outputs_verified']==len(x)
            assert row['state_allocation_bytes']==int(re.search(r'^M:([a-f0-9]+)$',stdout,re.M)[1],16)
            stderr=(directory/'firmware.stderr').read_text()
            labels={'Executed insns':'instructions','RAM data reads':'ram_reads','RAM writes':'ram_writes',
                    'Flash data reads':'flash_reads','Flash writes':'flash_writes',
                    'Taken branches':'taken_branches','Flash insn reads':'flash_fetches','BL insns':'bl'}
            found=dict(re.findall(r'^([^:\n]+):\s+([0-9]+)\s*$',stderr,re.M))
            raw_events={key:int(found[label]) for label,key in labels.items()}
            assert sum(int(v) for v in re.findall(r'^\s*\d+:\s*(\d+),',stderr,re.M))==raw_events['instructions']
            raw_events['instructions']-=1;raw_events['flash_fetches']-=1
            raw_events['mul']=int(re.search(r'^16:\s*\d+,\s*\[([^\]]+)\]',stderr,re.M)[1].split(',')[13])
            ticks=list(map(int,re.findall(r'(?:raised|cleared) at cycle (\d+)',stderr)))
            assert len(ticks)==2
            raw_events['raw_tick_delta']=ticks[1]-ticks[0]-2
            assert all(row[k]==v for k,v in raw_events.items()),(directory,'raw event mismatch')
            if stage=='primary':
                key=(row['compiler'],name,m,block,variant)
                assert key not in seen
                seen.add(key)
            total+=len(x)
    expected={(c,n,m,b,v) for c in toolchains() for n in FILTERS for m in (1024,32768)
              for b in (1,64) for v in variants(design['filters'][n]['coefficients'],m)}
    assert seen==expected
    return {'measured_binaries':len(data['rows']),'edge_binaries':len(data['target_edge_checks']),
            'posthoc_width_binaries':len(data.get('posthoc_width_controls',[])),
            'target_output_comparisons':total,'all_artifact_hashes_verified':True,
            'generated_sources_reconstructed':True,'admission_accounting_verified':True,
            'reference_outputs_and_states_reconstructed':True}


if __name__=='__main__':
    main()
