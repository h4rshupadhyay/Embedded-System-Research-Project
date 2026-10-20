"""Frozen Task 4 FIR panel preparation and generated safe kernel sources."""
from __future__ import annotations
import ctypes, hashlib, importlib.util, json, subprocess, shutil, numbers
from pathlib import Path
import numpy as np
import scipy
from scipy import signal

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'fir-baseline'
LEGACY=ROOT.parent/'fir-sharing-probe'/'probe.py'
TAPS=48; MAXIMUM=32768
SPECS=(('native_lp1800',1800,'hamming',50000,'4cc95f66dcae4fa848d8b5870ecca26a5be6101c91fc7e28bd52e404419c4118'),('wide_lp2800',2800,'hamming',100000,'6293e26668672b816f2a5f22d4f0ce09ef7af8bc5d01cb0d433cff432615f573'),('wide_lp4600',4600,'blackman',110000,'900cf584be9d2b3597a63e5acd42e14594bd768607ac05e5c705a71f405b310b'))
FULL_SHA='45f756624d8bb824a19352860fff89648c26971c961433f5ee1bcc8dab6fefc8'; ADC_SHA='4ee975455373f3b8c4af42282b82d542e8e2810b4f46cf253a0f13ce4a78095e'
CMSIS_PIN='3a04f817a4380c00ff51f9bcdc6c4e4bb7a18b80'; VARIANTS=('wide_direct64','cert_direct_first','trans_const','trans_hcub_demand','cmsis64_unroll'); COMPILERS=('gcc10','gcc15'); _MODULES={}

def _dump(x): return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def coefficient_bytes(x): return np.asarray(x,dtype='<i2').tobytes()
def _hash(x): return hashlib.sha256(coefficient_bytes(x)).hexdigest()
def _interval(h):
    low=sum(min(-32768*c,32767*c) for c in h); high=sum(max(-32768*c,32767*c) for c in h); return [low,high]
def _prefix_intervals(h,a,b):
    rows=[]; lo=hi=0
    for c in h[a:b]:
        lo+=min(-32768*c,32767*c); hi+=max(-32768*c,32767*c); rows.append([lo,hi])
    return rows
def _cuts(h):
    legal=[k for k in range(1,len(h)) if 32768*sum(map(abs,h[:k]))<=2**31-1 and 32768*sum(map(abs,h[k:]))<=2**31-1]
    if 32768*sum(map(abs,h))<=2**31-1: return []
    if not legal: raise ValueError('no safe two-group cut')
    first=legal[0]; balanced=min(legal,key=lambda k:(max(sum(map(abs,h[:k])),sum(map(abs,h[k:]))),k)); return list(dict.fromkeys((first,balanced)))
def make_design():
    if (np.__version__,scipy.__version__)!=('1.26.4','1.15.3'): raise RuntimeError('Pinned NumPy/SciPy versions required')
    filters={}
    for name,cutoff,window,target,expected in SPECS:
        p=signal.firwin(95,cutoff,fs=16000,window=window,scale=True); t=signal.minimum_phase(p,method='homomorphic',half=True,n_fft=32768)
        h=np.rint(t*(target/np.abs(t).sum())).astype(np.int64).tolist()
        if _hash(h)!=expected: raise ValueError(name+' coefficient hash mismatch')
        if len(h)!=TAPS or h==h[::-1] or any(not -32768<=c<=32767 for c in h): raise ValueError(name+' frozen coefficient domain failure')
        cuts=_cuts(h); interval=_interval(h)
        upper=[32767 if c>0 else -32768 if c<0 else 0 for c in h]; lower=[-32768 if c>0 else 32767 if c<0 else 0 for c in h]
        us=sum(a*b for a,b in zip(h,upper)); ls=sum(a*b for a,b in zip(h,lower))
        if [ls,us]!=interval: raise AssertionError('extremal witness mismatch')
        groups={'whole':[[0,TAPS]]}
        for key,k in zip(('first','balanced'),cuts): groups[key]=[[0,k],[k,TAPS]]
        group_prefixes={policy:[{'group':[a,b],'prefix_intervals':_prefix_intervals(h,a,b)} for a,b in parts] for policy,parts in groups.items()}
        reduction_prefixes={}
        for policy,parts in groups.items():
            lo=hi=0; rows=[]
            for a,b in parts:
                iv=_interval(h[a:b]); lo+=iv[0]; hi+=iv[1]; rows.append([lo,hi])
            reduction_prefixes[policy]=rows
        filters[name]={'design':{'numtaps':95,'cutoff_hz':cutoff,'fs_hz':16000,'window':window,'scale':True,'minimum_phase_method':'homomorphic','half':True,'n_fft':32768,'target_l1':target,'numpy':np.__version__,'scipy':scipy.__version__},'coefficients':h,'coefficient_sha256_le_i16':expected,'coefficient_l1':sum(map(abs,h)),'full_sum_interval':interval,'full_prefix_intervals':_prefix_intervals(h,0,TAPS),'cuts':cuts,'cut_groups':groups,'group_prefix_intervals':group_prefixes,'group_reduction_prefix_intervals':reduction_prefixes,'group_abs_bounds':{str(k):[32768*sum(map(abs,h[:k])),32768*sum(map(abs,h[k:]))] for k in cuts},'upper_witness_taps':upper[::-1],'lower_witness_taps':lower[::-1],'upper_witness_sum':us,'lower_witness_sum':ls}
    return {'schema':'fir-task4-design-v1','scope':'three controlled gain-normalized synthetic nonsymmetric 48-tap filters','domain':[-32768,32767],'filters':filters}

def make_inputs():
    x=[-32768,32767,0,-1,1,-32767,32766,0]; s=20261021
    while len(x)<1089: s=(1664525*s+1013904223)&0xffffffff; x.append((s>>16)-32768)
    adc=[v//32 for v in x]
    if x[:16]!=[-32768,32767,0,-1,1,-32767,32766,0,-3675,-21672,280,-30481,-17793,-19545,13532,-30280] or _hash(x)!=FULL_SHA or _hash(adc)!=ADC_SHA: raise AssertionError('input identity mismatch')
    return {'full':x,'adc':adc,'full_sha256_le_i16':FULL_SHA,'adc_sha256_le_i16':ADC_SHA,'description':'synthetic amplitude regimes; not acquired application traces'}

def case_rows():
    out=[]
    for name in make_design()['filters']:
        variants=list(VARIANTS)+(['cmsis32_unroll'] if name=='native_lp1800' else ['cert_direct_balanced'])
        for v in variants:
          for compiler in COMPILERS:
           for block in (1,64):
            for stimulus in ('adc','full'):
             for regime,warm,measured,total in (('startup',0,257,257),('post_startup',64,1025,1089)):
              out.append({'filter':name,'variant':v,'compiler':compiler,'block':block,'stimulus':stimulus,'regime':regime,'warmup_samples':warm,'measured_samples':measured,'total_samples':total})
    return out

def _legacy(root):
    root=Path(root).resolve(); key=str(root)
    if key not in _MODULES:
        spec=importlib.util.spec_from_file_location('fir_task4_'+hashlib.sha1(key.encode()).hexdigest()[:12],LEGACY); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.HERE=root; m.BUILD=root/'build'; m.BASE=BASE.resolve(); _MODULES[key]=m
    return _MODULES[key]
def _name(h,root):
    design=json.loads((Path(root)/'panel-design.json').read_text()) if (Path(root)/'panel-design.json').exists() else make_design()
    matches=[n for n,r in design['filters'].items() if r['coefficient_sha256_le_i16']==_hash(h)]
    if len(matches)!=1: raise ValueError('coefficients do not identify exactly one frozen filter')
    return matches[0]
def _groups(h,variant,block,groups):
    if len(h)!=TAPS or any(isinstance(c,bool) or not isinstance(c,numbers.Integral) or not -32768<=c<=32767 for c in h): raise ValueError('expected 48 signed-int16 integer coefficients')
    if isinstance(block,bool) or not isinstance(block,numbers.Integral) or block not in (1,64): raise ValueError('block capacity must be integer 1 or 64')
    groups=list(groups)
    if any(len(pair)!=2 or any(isinstance(v,bool) or not isinstance(v,numbers.Integral) for v in pair) for pair in groups): raise ValueError('group boundaries must be exact integers')
    groups=[(a,b) for a,b in groups]
    if not groups or groups[0][0]!=0 or groups[-1][1]!=TAPS: raise ValueError('groups must cover all taps')
    cursor=0
    for a,b in groups:
        if a!=cursor or b<=a or b>TAPS: raise ValueError('groups must be nonempty, ordered, disjoint and contiguous')
        cursor=b
    if variant.startswith('cert_direct'):
        for a,b in groups:
            p=0
            for c in h[a:b]:
                p+=32768*abs(int(c))
                if p>2**31-1: raise ValueError('int32 group prefix unsafe')
    return groups

def _direct(h,variant,block,groups):
    groups=_groups(h,variant,block,groups); wide=variant=='wide_direct64'; n=len(h)
    header=f'''#include <stdint.h>\n#define TAPS 48\ntypedef struct {{ int16_t history[{n+block}]; }} ProbeState;\nvoid probe_init(ProbeState *);\nvoid probe_process(ProbeState * restrict,const int16_t * restrict,int16_t * restrict,uint32_t);\nint64_t probe_get_state(ProbeState *,uint32_t);\nunsigned probe_state_bytes(void);\n'''
    src=['#include "probe.h"','void probe_init(ProbeState *s){for(unsigned i=0;i<sizeof(*s);++i)((unsigned char*)s)[i]=0;}','unsigned probe_state_bytes(void){return sizeof(ProbeState);}','int64_t probe_get_state(ProbeState*s,uint32_t i){return s->history[i];}', '''static int16_t quant(int64_t s){if(s>=1073741824LL)return 32767;if(s<=-1073741824LL)return -32768;int32_t q=(int32_t)s;return (int16_t)(q>=0?q/32768:-1-(-(q+1))/32768);}''',f'void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b){{',f'for(uint32_t j=0;j<b;++j)s->history[47+j]=x[j];','for(uint32_t j=0;j<b;++j){']
    if wide:
        src.append('int64_t sum=0;')
        for k,c in enumerate(h):
            if c: src.append(f'sum+=(int32_t)({c})*s->history[j+{47-k}];')
    else:
        for i,(a,b) in enumerate(groups):
            src.append(f'int32_t partial{i}=0;')
            for k in range(a,b):
                if h[k]: src.append(f'partial{i}+=(int32_t)({h[k]})*s->history[j+{47-k}];')
        src.append('int64_t sum='+ '+'.join(f'(int64_t)partial{i}' for i in range(len(groups)))+';')
    src += ['y[j]=quant(sum);}','for(uint32_t j=0;j<47;++j)s->history[j]=s->history[b+j];','}']
    return header,'\n'.join(src)+'\n'
def generate_kernel(h:list[int],variant:str,block:int,groups:list[tuple[int,int]])->tuple[str,str]: return _generate(h,variant,block,groups,ROOT)
def _generate(h,variant,block,groups,root):
    groups=_groups(h,variant,block,groups)
    if variant in ('wide_direct64','cert_direct_first','cert_direct_balanced'): return _direct(h,variant,block,groups)
    name=_name(h,root); m=_legacy(root)
    if variant not in ('trans_const','trans_hcub_demand','cmsis64_unroll','cmsis32_unroll'): raise ValueError('unknown panel variant')
    header,source,_=m.generate(name,h,MAXIMUM,variant,block)
    return header,source

def _graphs(root,design):
    vendor=Path(root)/'vendor'; vendor.mkdir(parents=True,exist_ok=True); srcdir=LEGACY.parent/'vendor'/'synth-jan-14-2009'; acm=srcdir/'acm'; manifest_path=vendor/'graphs-manifest.json'
    provenance={'executable':str(acm.resolve()),'executable_sha256':hashlib.sha256(acm.read_bytes()).hexdigest(),'source_archive_sha256':'24b3fd41181f2e5443f0324a4138096dfce91fa2514b0f96b25b5a1da6c33bc2','algorithm':'Hcub','flags':['-b','15','-seed','1','-nofs','-gc']}
    if Path(root).resolve()!=ROOT.resolve():
        frozen=ROOT/'vendor'; frozen_manifest=frozen/'graphs-manifest.json'
        if not frozen_manifest.exists(): raise RuntimeError('production graph prepare is required first')
        present=manifest_path.exists() or any((vendor/(n+'.txt')).exists() for n in design['filters'])
        if present:
            if not manifest_path.exists(): raise ValueError('partial temporary graph set has no manifest')
        else:
            for name in design['filters']:
                for suffix in ('.txt','.stderr.txt'): shutil.copyfile(frozen/(name+suffix),vendor/(name+suffix))
            shutil.copyfile(frozen_manifest,manifest_path)
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if manifest and manifest.get('provenance')!=provenance:
        if Path(root).resolve()==ROOT.resolve() and 'provenance' not in manifest: manifest['provenance']=provenance
        else: raise ValueError('Hcub executable/source provenance changed')
    for name,row in design['filters'].items():
        path=vendor/f'{name}.txt'; err=vendor/f'{name}.stderr.txt'; odds=sorted({abs(c)//(abs(c)&-abs(c)) for c in row['coefficients'] if c}); cmd=[str(acm),*map(str,odds),'-b','15','-seed','1','-nofs','-gc']
        if path.exists():
            record=manifest.get(name)
            if not record or not err.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=record.get('stdout_sha256') or hashlib.sha256(err.read_bytes()).hexdigest()!=record.get('stderr_sha256') or record.get('command')!=cmd or record.get('fundamentals')!=odds: raise ValueError(f'{name} saved Hcub outputs/command fail identity validation')
            continue
        p=subprocess.run(cmd,cwd=srcdir,capture_output=True)
        if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace'))
        path.write_bytes(p.stdout); err.write_bytes(p.stderr)
        manifest[name]={'command':cmd,'returncode':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'stderr_notices':p.stderr.decode(errors='replace'),'fundamentals':odds}
        manifest['provenance']=provenance; manifest_path.write_bytes(_dump(manifest))
    manifest['provenance']=provenance; manifest_path.write_bytes(_dump(manifest)); return manifest

def _graph_cert(name,h,root):
    m=_legacy(root); outputs,ops,coeff,raw=m.graph(name); odds={abs(c)//(abs(c)&-abs(c)) for c in h if c}
    if not odds<=set(outputs): raise ValueError('Hcub graph missing fundamentals')
    i32=(-2**31,2**31-1); i64=(-2**63,2**63-1); nodes={'t0':{'coefficient':1,'bound':MAXIMUM,'width':32}}; checks=[]
    for dst,(op,args) in ops.items():
        a=coeff[args[0]]; second=args[1] if len(args)>1 else None
        b=coeff[second] if second is not None and second.startswith('t') else None; r=coeff[dst]
        w=32 if abs(r)*MAXIMUM<=i32[1] else 64; dest=i32 if w==32 else i64
        al,ah=-abs(a)*MAXIMUM,abs(a)*MAXIMUM
        if b is not None:
            bl,bh=-abs(b)*MAXIMUM,abs(b)*MAXIMUM; bw=32 if abs(b)*MAXIMUM<=i32[1] else 64
        elif second is not None and op in ('add','sub'):
            bl=bh=int(second); bw=32 if abs(int(second))<=i32[1] else 64
        else:
            bl=bh=0; bw=32
        ew=max(w,bw); ev=i32 if ew==32 else i64
        if al<dest[0] or ah>dest[1] or bl<ev[0] or bh>ev[1]: raise ValueError(f'{name}:{dst} operand cast/evaluation overflow')
        if op=='copy': rl,rh=al,ah
        elif op=='add': rl,rh=al+bl,ah+bh
        elif op=='sub': rl,rh=al-bh,ah-bl
        elif op=='neg': rl,rh=-ah,-al
        elif op in ('shl','shr'):
            shift=int(args[1]); divisor=2**shift
            if not 0<=shift<=30 or op=='shr' and a%divisor: raise ValueError('invalid or nonexact shift')
            rl,rh=(al*divisor,ah*divisor) if op=='shl' else (al//divisor,ah//divisor)
        else: raise ValueError('unrecognized graph primitive')
        if rl<ev[0] or rh>ev[1] or rl<dest[0] or rh>dest[1]: raise ValueError(f'{dst} result overflow')
        nodes[dst]={'coefficient':r,'bound':abs(r)*MAXIMUM,'width':w}; checks.append({'node':dst,'op':op,'evaluation_width':ew,'result_width':w,'operand_bounds':[[al,ah],[bl,bh]],'result_interval':[rl,rh],'exact_division':op=='shr'})
    restored=[]
    for c in h:
        if not c: continue
        odd=abs(c)//(abs(c)&-abs(c)); t=outputs[odd]; w=nodes[t]['width']; bound=abs(c)*MAXIMUM; lim=2**(w-1)-1; ratio=c//odd
        if bound>lim or abs(ratio)>lim: raise ValueError('restored output product overflows evaluation type')
        restored.append({'coefficient':c,'node':t,'ratio':ratio,'evaluation_width':w,'product_interval':[-bound,bound]})
    suffix=[MAXIMUM*sum(map(abs,h[i+1:])) for i in range(TAPS-1)]
    suffix_intervals=[_interval(h[i+1:]) for i in range(TAPS-1)]
    return {'graph_sha256':hashlib.sha256(raw.encode()).hexdigest(),'required_odds':sorted(odds),'outputs':outputs,'nodes':nodes,'primitive_checks':checks,'restored_products':restored,'state_suffix_bounds':suffix,'state_suffix_intervals':suffix_intervals,'state_widths':[32 if b<=i32[1] else 64 for b in suffix],'graph_arithmetic_certified':True}

def _cmsis_cert(h):
    pair=[32768*(abs(h[i])+abs(h[i+1])) for i in range(0,TAPS,2)]; interval=_interval(h)
    cmsis=BASE/'build'/'cmsis-dsp'; inc=cmsis/'Include'; core=BASE/'build'/'cmsis-core'
    files=[cmsis/'Source/FilteringFunctions/arm_fir_q15.c',cmsis/'Source/FilteringFunctions/arm_fir_fast_q15.c']+sorted(inc.rglob('*.h'))+sorted(core.rglob('*.h'))
    hashes={str(f.relative_to(BASE/'build')):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    tree=hashlib.sha256(_dump(hashes)).hexdigest()
    fast=(cmsis/'Source/FilteringFunctions/arm_fir_fast_q15.c').read_text(); standard=(cmsis/'Source/FilteringFunctions/arm_fir_q15.c').read_text()
    none=(inc/'dsp/none.h').read_text(); memory=(inc/'arm_math_memory.h').read_text()
    revision=subprocess.run(['git','-C',str(cmsis),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    source_checks={'pinned_revision':revision==CMSIS_PIN,'fast_pb_const_decl':bool(__import__('re').search(r'const\s+q15_t\s*\*\s*pb',fast)),'fast_casted_incremental_read':'read_q15x2_ia ((q15_t **) &pb)' in fast,'standard_typed_incremental_read':'read_q15x2_ia (&pb)' in standard,'fast_four_output_gate':'blkCnt = blockSize >> 2U;' in fast,'packed_fallback_helpers':all(k in none for k in ('__PKHBT','__SMLAD','__SMLALD','__SMLALDX')),'q15_pair_reader':bool(__import__('re').search(r'read_q15x2\s*\(\s*q15_t const',memory)),'q15_pair_writer':'write_q15x2_ia' in memory}
    if not all(source_checks.values()): raise ValueError('pinned CMSIS source no longer matches audited helper paths')
    return {'source_pin':CMSIS_PIN,'source_hashes':hashes,'transitive_header_tree_sha256':tree,'source_checks':source_checks,'pair_bounds':pair,'maximum_pair_bound':max(pair),'full_sum_interval':interval,'floored_interval':[interval[0]//32768,interval[1]//32768],'reversed_coefficients':h[::-1],'state_storage_samples_by_block':{'1':TAPS+1,'64':TAPS+64},'full_domain_accumulator_abs_bound':32768*sum(map(abs,h)),'standard_postshift_int32_safe':max(abs(interval[0]//32768),abs(interval[1]//32768))<=2**31-1,'gcc_contract':'GCC 10.3/Arm GCC 15.2 implementation semantics; portable ISO-C packed-helper proof not claimed','helper_obligations':['packed halfword extraction/packing signed shifts follow pinned GCC implementation semantics','__PKHBT and write_q15x2 narrowing/right-shift semantics follow GCC contract','unsigned packed helper returns converted to signed accumulator types per GCC contract','ordinary signed pair multiplication/addition intermediates fit certified widths','reversed coefficient pair bounds and every accumulation prefix certified','standard acc>>15 conversion to int32 is inside certified range'],'ARM_MATH_LOOPUNROLL':True,'DSP_MVE_NEON_HELIUM':False,'ARM_FEATURE_UNALIGNED':'record effective compiler macro at Task 5','fast_full_domain_arithmetic_eligible':32768*sum(map(abs,h))<=2**31-1,'fast_cmsis_block64_admission':'pending unresolved pointer-object aliasing','fast_cmsis_block1_alias_path':'source sets blkCnt=blockSize>>2; b=1 bypasses four-output cast path and uses scalar remainder; verify target source identity at Task 5'}
def _protocol(design,inputs,certs):
    return {'schema':'fir-task4-protocol-v1','case_identity':['filter','variant','compiler','block','stimulus','regime'],'filters':list(design['filters']),'variants_by_filter':{n:list(VARIANTS)+(['cmsis32_unroll'] if n=='native_lp1800' else ['cert_direct_balanced']) for n in design['filters']},'compilers':COMPILERS,'toolchain_identities':{'gcc10':{'path':'/usr/bin/arm-none-eabi-gcc','version':'GNU Arm Embedded 10.3.1'},'gcc15':{'path':str((BASE/'build/toolchains/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc').resolve()),'version':'Arm GNU Toolchain 15.2.rel1'},'target':'Cortex-M0 Thumb, little-endian','optimization':'-O2','LTO':False,'flags':['-mcpu=cortex-m0','-mthumb','-std=c11','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-g0']},'legacy_helper_sha256':hashlib.sha256(LEGACY.read_bytes()).hexdigest(),'blocks':[1,64],'stimuli':['adc','full'],'regimes':[{'name':'startup','warmup_samples':0,'measured_samples':257,'total_samples':257},{'name':'post_startup','warmup_samples':64,'measured_samples':1025,'total_samples':1089}],'case_count':288,'cases':case_rows(),'inputs':inputs,'reference':{'causal':True,'initial_history':0,'single_saturating_floor_quantizer':True,'append_tail':False,'full_domain_for_both_stimuli':[-32768,32767]},'measurement':{'retained_warm_history':True,'measured_offsets':[64,1089],'performance_runs_task4':0,'flash_limit_bytes':65536,'ram_limit_bytes':8192,'initial_sp':'0x20001ff0','stack_reservation_bytes':2048,'static_ram_ceiling':'0x200017f0','markers_include':['wrapper','calls','copies','quantizer','retained-state movement'],'markers_exclude':['initialization','printing']},'cmsis':{n:_cmsis_cert(r['coefficients']) for n,r in design['filters'].items()},'certificates':certs,'correctness_gate':{'maximum_conditions':72,'stream_definition':'48 zeros, 48-sample upper extremal window, 48-sample lower extremal window, then ten repetitions of [-32768,32767,-1,0,1] (194 samples)','target_compilers':COMPILERS,'blocks':[1,64],'one_fixed_stream_per_condition':True,'host_mixed_call_partitions':[1,64,3,16]},'performance_gate':{'maximum_conditions':288,'compile_or_run_each_logical_condition_once':True,'binary_deduplication':'document identical binaries; no repeated sampling to invent variance','target_performance_runs_task4':0,'flags':'-O2 Cortex-M0 Thumb, no LTO'},'response_metrics':['integer events','cycles and energy','per measured-output normalization','state/frame/symbol diagnostics','reference quantizer clamp-path count'], 'clamp_path_predicates':{'positive':'prequantized S >= 1073741824','negative':'prequantized S <= -1073741824'},'comparison':{'D_old':'min(wide_direct64,cmsis64_unroll[,cmsis32_unroll when eligible])','D_new':'min(D_old,cert_direct_first[,cert_direct_balanced])','primary_claim':'at least one wide-required fixed-compiler cell with E_Hcub < D_old and E_Hcub >= D_new','unavailable_required_cell':'full-panel assessment incomplete'},'unavailability_rule':'Pending native fast block64 remains unavailable unless aliasing source-semantic item is discharged; do not change denominator.'}

def prepare_panel(output:Path)->dict:
    output=Path(output).resolve(); output.mkdir(parents=True,exist_ok=True); design=make_design(); (output/'panel-design.json').write_bytes(_dump(design)); inputs=make_inputs(); (output/'panel-inputs.json').write_bytes(_dump(inputs)); graphs=_graphs(output,design)
    certs={n:{'graph':_graph_cert(n,r['coefficients'],output),'cmsis':_cmsis_cert(r['coefficients'])} for n,r in design['filters'].items()}; (output/'panel-certificates.json').write_bytes(_dump(certs))
    protocol=_dump(_protocol(design,inputs,certs)); (output/'panel-protocol.json').write_bytes(protocol); ph=hashlib.sha256(protocol).hexdigest(); (output/'panel-protocol.sha256').write_text(ph+'  panel-protocol.json\n')
    sources=[]
    for name,row in design['filters'].items():
      variants=list(VARIANTS)+(['cmsis32_unroll'] if name=='native_lp1800' else ['cert_direct_balanced'])
      for variant in variants:
       if variant in ('wide_direct64','trans_const','trans_hcub_demand','cmsis64_unroll','cmsis32_unroll'): groups=[(0,48)]
       elif variant=='cert_direct_first':
        k=row['cuts'][0] if row['cuts'] else 48; groups=[(0,k),(k,48)] if k<48 else [(0,48)]
       else: k=row['cuts'][1]; groups=[(0,k),(k,48)]
       for block in (1,64):
        header,source=_generate(row['coefficients'],variant,block,groups,output); d=hashlib.sha256((header+source).encode()).hexdigest(); dest=output/'sources'/name/variant/f'b{block}'; dest.mkdir(parents=True,exist_ok=True)
        for fn,content in (('probe.h',header),('probe.c',source)):
         path=dest/fn
         path.write_text(content)
        sources.append({'filter':name,'variant':variant,'block':block,'header_sha256':hashlib.sha256(header.encode()).hexdigest(),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'combined_sha256':d})
    (output/'sources-manifest.json').write_bytes(_dump({'schema':'fir-task4-sources-v1','sources':sources}))
    return {'design_sha256':hashlib.sha256((output/'panel-design.json').read_bytes()).hexdigest(),'input_sha256':hashlib.sha256((output/'panel-inputs.json').read_bytes()).hexdigest(),'protocol_sha256':ph,'graphs':graphs,'source_count':len(sources),'performance_runs':0,'fast_cmsis_block64_admission':'pending unresolved pointer-object aliasing'}

def _quantize(s):
    if s>=1073741824:return 32767
    if s<=-1073741824:return -32768
    return s//32768
def _reference(h,x):
    return [_quantize(sum(int(h[k])*int(x[n-k]) for k in range(min(len(h),n+1)))) for n in range(len(x))]
def _aligned_state_buffer(size):
    raw=ctypes.create_string_buffer(size+31); base=ctypes.addressof(raw); addr=(base+23)&~15
    if addr-8<base or addr+size+8>base+ctypes.sizeof(raw): raise AssertionError('state guard allocation outside backing buffer')
    ctypes.memset(addr-8,0xA5,size+16); return raw,addr
def _state(h,x,trans):
    if not trans:return ([0]*(len(h)-1)+list(x))[-(len(h)-1):]
    n=len(x);return [sum(h[k]*x[n-1-(k-i-1)] for k in range(i+1,len(h)) if n-1-(k-i-1)>=0) for i in range(len(h)-1)]
def host_ubsan_checks(root):
    root=Path(root); design=json.loads((root/'panel-design.json').read_text()); inputs=json.loads((root/'panel-inputs.json').read_text()); reports=[]
    forms=('wide_direct64','cert_direct_first','cert_direct_balanced','trans_const','trans_hcub_demand')
    for name,row in design['filters'].items():
      h=row['coefficients']; upper=[32767 if c>0 else -32768 if c<0 else 0 for c in h][::-1]; lower=[-32768 if c>0 else 32767 if c<0 else 0 for c in h][::-1]; streams=[([0]*48+upper+lower+[-32768,32767,-1,0,1]*10,False,'extrema'),(inputs['full'],False,'full-mixed'),(inputs['full'],True,'post-startup-boundary'),(inputs['adc'],False,'adc-mixed'),([-1]+[0]*128,False,'negative-floor')]
      for block in (1,64):
       for variant in forms:
        if variant=='cert_direct_balanced' and len(row['cuts'])<2: continue
        cut=(row['cuts'][0] if variant=='cert_direct_first' and row['cuts'] else row['cuts'][1] if variant=='cert_direct_balanced' else 48)
        groups=[(0,cut),(cut,48)] if cut<48 else [(0,48)]
        header,source=_generate(h,variant,block,groups,root); identity=hashlib.sha256((header+source).encode()).hexdigest(); work=root/'build'/'host'/name/f'{variant}-b{block}-{identity[:16]}'; work.mkdir(parents=True,exist_ok=True); (work/'probe.h').write_text(header);(work/'probe.c').write_text(source); lib=work/f'probe-{identity}.so'
        subprocess.run(['gcc','-std=c11','-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=undefined','-Wall','-Wextra','-Werror','-I',str(BASE),'-I',str(work),str(work/'probe.c'),'-o',str(lib)],check=True,capture_output=True,text=True)
        dll=ctypes.CDLL(str(lib));dll.probe_state_bytes.restype=ctypes.c_uint;dll.probe_init.argtypes=[ctypes.c_void_p];dll.probe_process.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int16),ctypes.POINTER(ctypes.c_int16),ctypes.c_uint];dll.probe_get_state.argtypes=[ctypes.c_void_p,ctypes.c_uint];dll.probe_get_state.restype=ctypes.c_int64
        for x,split64,label in streams:
         x=list(x); raw,addr=_aligned_state_buffer(dll.probe_state_bytes());dll.probe_init(addr);expected=_reference(h,x);
         if label=='negative-floor' and expected[0]!=-1: raise AssertionError('negative-floor probe must quantize first output to -1')
         src=(ctypes.c_int16*len(x))(*x);out=(ctypes.c_int16*(len(x)+4))(*([23130]*(len(x)+4)));off=0;parts=(1,) if block==1 else (1,64,3,16);pi=0
         while off<len(x):
          b=1 if block==1 else min((64-off) if split64 and off<64 else parts[pi%4],len(x)-off);pi+=1; ip=ctypes.cast(ctypes.byref(src,2*off),ctypes.POINTER(ctypes.c_int16));op=ctypes.cast(ctypes.byref(out,2*(off+2)),ctypes.POINTER(ctypes.c_int16));dll.probe_process(addr,ip,op,b);off+=b;prefix=x[:off]
          if list(out)[2+off-b:2+off]!=expected[off-b:off]:raise AssertionError((name,variant,block,'output'))
          if [dll.probe_get_state(addr,i) for i in range(47)]!=_state(h,prefix,variant.startswith('trans_')):raise AssertionError((name,variant,block,'state'))
          if ctypes.string_at(addr-8,8)!=b'\xA5'*8 or ctypes.string_at(addr+dll.probe_state_bytes(),8)!=b'\xA5'*8 or list(out)[:2]+list(out)[-2:]!=[23130]*4:raise AssertionError((name,variant,block,'guard'))
         reports.append({'filter':name,'variant':variant,'block':block,'stream':label,'stream_length':len(x),'status':'pass'})
    return {'runs':reports,'compiled_libraries':len({(r['filter'],r['variant'],r['block']) for r in reports}),'reference_quantizer_boundary_sums':[-1073741825,-1073741824,-1073741823,-32769,-32768,-32767,-1,0,1,32767,32768,1073741823,1073741824,1073741825],'ubsan':'host GCC; generated direct/transposed C only','cmsis_host_ubsan':'not run; unmodified pinned library is separately admitted','state_output_guards':True,'mixed_partitions':[1,64,3,16]}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','host-checks'));p.add_argument('--output',type=Path,default=ROOT);a=p.parse_args(argv)
    print(json.dumps(prepare_panel(a.output) if a.command=='prepare' else host_ubsan_checks(a.output),indent=2))
if __name__=='__main__':main()
