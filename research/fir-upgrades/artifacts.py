"""Build and check a portable, hash-verified slice of the original FIR evidence."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


MANIFEST_NAME = 'evidence-manifest.json'
ARCHIVE_NAME = 'evidence.tar.gz'
EXCLUDED = {'build', '__pycache__'}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path):
    return json.loads(path.read_text())


def _safe_rel(value: str) -> PurePosixPath:
    if (not isinstance(value, str) or not value or value.startswith('/') or
            '\\' in value or '\x00' in value or ':' in value or
            any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError(f'unsafe relative path: {value!r}')
    return PurePosixPath(value)


def _source_inputs(repo: Path) -> set[Path]:
    """Resolve frozen manifests and exact admitted rows into repo-root paths."""
    research = repo / 'research'
    probe = research / 'fir-sharing-probe'
    baseline = research / 'fir-baseline'
    paper = research / 'fir-paper'
    manifest = _json(paper / 'source-manifest.json')
    for name, expected in manifest['files'].items():
        path = repo / _safe_rel(name).as_posix()
        if not path.is_file() or path.is_symlink() or _sha(path) != expected:
            raise ValueError(f'numerical export input missing or hash mismatch: {path}')
    selected: set[Path] = {repo / name for name in manifest['files']}
    selected.update({paper / name for name in ('source-manifest.json', 'results.json', 'tables.md',
                                                'build_results.py', 'README.md')})
    selected.update({baseline / name for name in ('selection-design.json', 'README.md', 'PROTOCOL.md')
                     if (baseline / name).is_file()})

    historical = _json(probe / 'results.json')
    controls = {'direct64', 'cmsis64', 'cmsis64_unroll', 'spec_direct',
                'trans_const', 'trans_hcub_demand'}
    rows = [row for row in historical['rows']
            if row.get('filter') == 'speech_minphase48' and row.get('maximum') == 32768
            and row.get('variant') in controls]
    if len(rows) != 24:
        raise ValueError(f'expected 24 historical control rows, found {len(rows)}')
    for row in rows:
        directory = probe / _safe_rel(row['directory']).as_posix()
        for name, expected in row['artifacts'].items():
            path = directory / _safe_rel(name).as_posix()
            if not path.is_file() or path.is_symlink() or _sha(path) != expected:
                raise ValueError(f'historical artifact missing or hash mismatch: {path}')
            selected.add(path)
    for name, expected in historical['dependency_sources'].items():
        path = research / _safe_rel(name).as_posix()
        if not path.is_file() or path.is_symlink() or _sha(path) != expected:
            raise ValueError(f'historical dependency source missing or hash mismatch: {path}')
        selected.add(path)
    selected.update({probe / name for name in ('results.json', 'probe.py', 'PROTOCOL.md',
                                                'certificates.json', 'README.md', 'analysis.json',
                                                'independent-check/check.py',
                                                'independent-check/reference-cases.json',
                                                'independent-check/verification.json',
                                                'independent-check/join-review.md',
                                                'independent-check/positioning.md')})
    vendor = probe / 'vendor'
    selected.update({vendor / name for name in ('BUILD.md', 'examples-manifest.json',
                                                 'speech_minphase48.txt',
                                                 'speech_minphase48.stderr.txt',
                                                 'synth-jan-14-2009.tar.gz',
                                                 'synth-jan-14-2009/COPYRIGHT',
                                                 'synth-jan-14-2009/COPYING')})

    partial_dir = probe / 'partial-direct'
    partial = _json(partial_dir / 'results.json')
    peer_rows = [row for row in partial['rows'] if row.get('filter') == 'speech_minphase48'
                 and row.get('maximum') == 32768]
    if len(peer_rows) != 4:
        raise ValueError(f'expected four partial-direct rows, found {len(peer_rows)}')
    for row in peer_rows:
        directory = partial_dir / _safe_rel(row['directory']).as_posix()
        for name, expected in row['artifacts'].items():
            path = directory / _safe_rel(name).as_posix()
            if not path.is_file() or path.is_symlink() or _sha(path) != expected:
                raise ValueError(f'partial artifact missing or hash mismatch: {path}')
            selected.add(path)
    selected.update({partial_dir / name for name in ('results.json', 'kernel.c', 'kernel.h',
                                                       'run.py', 'host_harness.c', 'notes.md',
                                                       'host-tests.txt')})
    selected.update({probe / name for name in ('independent-check/partial-direct-target-evidence.tar.gz',
                                                'independent-check/partial-direct-target-evidence.sha256')})

    explanation = probe / 'compiler-explanation'
    accounting_path = explanation / 'accounting.json'
    accounting = _json(accounting_path)
    if len(accounting.get('evidence', {})) != 29:
        raise ValueError('explanation evidence manifest must contain exactly 29 paths')
    for name, expected in accounting['evidence'].items():
        path = explanation / _safe_rel(name).as_posix()
        if not path.is_file() or path.is_symlink() or _sha(path) != expected:
            raise ValueError(f'explanation evidence missing or hash mismatch: {path}')
        selected.add(path)
    selected.update({accounting_path, explanation / 'analyze.py', explanation / 'findings.md',
                     explanation / 'assembly-notes.md', explanation / 'review.md',
                     probe / 'explanation-check/verify.py',
                     probe / 'independent-check/check.py'})

    for path in selected:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'missing or non-regular evidence source: {path}')
        try:
            path.resolve().relative_to(repo)
        except ValueError as error:
            raise ValueError(f'evidence source escapes repository: {path}') from error
    return selected


def _upgrade_root_paths(repo: Path, *, require_paper_build: bool = False) -> set[Path]:
    """Return the exact, finite source and admitted-raw slice for Task 2/5/6/7."""
    stage = repo / 'research/fir-upgrades'
    selected: set[Path] = set()

    def add(relative: str) -> Path:
        path = repo / _safe_rel(relative).as_posix()
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'upgraded evidence source missing or non-regular: {relative}')
        try:
            path.resolve().relative_to(repo)
        except ValueError as error:
            raise ValueError(f'upgraded evidence source escapes repository: {path}') from error
        selected.add(path)
        return path

    # Saved numeric reports, frozen specifications, verifiers and their independent audits.
    files = (
        'research/fir-upgrades/README.md', 'research/fir-upgrades/PROGRESS.md',
        'research/fir-upgrades/artifacts.py', 'research/fir-upgrades/test_artifacts.py',
        'research/fir-upgrades/analyze.py', 'research/fir-upgrades/test_analyze.py',
        'research/fir-upgrades/analysis/analysis.json', 'research/fir-upgrades/analysis/analysis.md',
        'research/fir-upgrades/panel.py', 'research/fir-upgrades/panel_run.py',
        'research/fir-upgrades/panel_verify.py', 'research/fir-upgrades/test_panel.py',
        'research/fir-upgrades/test_panel_run.py', 'research/fir-upgrades/test_panel_verify.py',
        'research/fir-upgrades/panel-design.json', 'research/fir-upgrades/panel-inputs.json',
        'research/fir-upgrades/panel-protocol.json', 'research/fir-upgrades/panel-protocol.sha256',
        'research/fir-upgrades/panel-certificates.json', 'research/fir-upgrades/panel-results.json',
        'research/fir-upgrades/panel-summary.json', 'research/fir-upgrades/panel-summary.md',
        'research/fir-upgrades/build/panel/correctness/correctness-gates.json',
        'research/fir-upgrades/sources-manifest.json', 'research/fir-upgrades/vendor/graphs-manifest.json',
        'research/fir-upgrades/verification/independent-audit.json',
        'research/fir-upgrades/verification/scientific-evidence-manifest.json',
        'research/fir-upgrades/verification/correctness-audit.json',
        'research/fir-upgrades/verification/task5-tdd-verification.md',
        'research/fir-upgrades/panel-tdd-log.md', 'research/fir-upgrades/tdd-log.md',
        'research/fir-upgrades/intervention.py', 'research/fir-upgrades/test_intervention.py',
        'research/fir-upgrades/intervention-results.json', 'research/fir-upgrades/intervention.md',
        'research/fir-upgrades/intervention-tdd-log.md', 'research/fir-upgrades/intervention-review.md',
        'research/fir-upgrade-gates.md',
        'research/fir-baseline/build/cmsis-dsp/Source/FilteringFunctions/arm_fir_q15.c',
        'research/fir-baseline/build/cmsis-dsp/Source/FilteringFunctions/arm_fir_fast_q15.c',
        'research/fir-baseline/build/cmsis-dsp/LICENSE.txt',
    )
    for relative in files:
        add(relative)

    # Generated FIR source/graph evidence is finite and covered by its manifests.
    for relative in (
            'research/fir-upgrades/sources/native_lp1800/cert_direct_first/b1/probe.c',
            'research/fir-upgrades/sources/native_lp1800/cert_direct_first/b1/probe.h',
            'research/fir-upgrades/sources/native_lp1800/cert_direct_first/b64/probe.c',
            'research/fir-upgrades/sources/native_lp1800/cert_direct_first/b64/probe.h'):
        add(relative)
    for directory in (stage / 'sources', stage / 'vendor'):
        if directory.exists():
            for path in directory.rglob('*'):
                if path.is_symlink():
                    raise ValueError(f'upgraded evidence contains a symlink: {path}')
                if path.is_file() and (directory.name != 'vendor' or path.name != 'README.md'):
                    try:
                        path.resolve().relative_to(repo)
                    except ValueError as error:
                        raise ValueError(f'upgraded evidence source escapes repository: {path}') from error
                    selected.add(path)

    # Pin only the CMSIS headers that the admitted effective-dependency records name.
    cmsis = (
        'research/fir-baseline/build/cmsis-core/cmsis_compiler.h',
        'research/fir-baseline/build/cmsis-core/cmsis_gcc.h',
        'research/fir-baseline/build/cmsis-dsp/Include/arm_math_memory.h',
        'research/fir-baseline/build/cmsis-dsp/Include/arm_math_types.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/filtering_functions.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/none.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/utils.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/support_functions.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/fast_math_functions.h',
        'research/fir-baseline/build/cmsis-dsp/Include/dsp/basic_math_functions.h',
    )
    for relative in cmsis:
        add(relative)

    panel = _json(stage / 'panel-results.json')
    protocol = _json(stage / 'panel-protocol.json')
    protocol_hash = _sha(stage / 'panel-protocol.json')
    if stage.joinpath('panel-protocol.sha256').read_text().split()[0] != protocol_hash or \
            panel.get('protocol_sha256') != protocol_hash:
        raise ValueError('upgraded panel protocol binding is incomplete')
    expected_perf = {tuple(case[k] for k in ('filter', 'variant', 'compiler', 'block', 'stimulus', 'regime'))
                     for case in protocol.get('cases', [])}
    actual_perf = {tuple(row.get('identity', {}).get(k) for k in
                         ('filter', 'variant', 'compiler', 'block', 'stimulus', 'regime'))
                   for row in panel.get('rows', [])}
    if panel.get('identity_count') != 288 or len(panel.get('rows', [])) != 288 or \
            len(actual_perf) != 288 or actual_perf != expected_perf:
        raise ValueError('upgraded performance inventory is incomplete')
    statuses = [row.get('status') for row in panel['rows']]
    if set(statuses) - {'admitted', 'unavailable'} or statuses.count('admitted') != 280 or \
            statuses.count('unavailable') != 8:
        raise ValueError('upgraded performance inventory must admit 280, mark 8 unavailable, and have 0 failures')
    expected_unavailable = {(f, 'cmsis32_unroll', c, 64, s, r)
                            for f in ('native_lp1800',) for c in ('gcc10', 'gcc15')
                            for s in ('adc', 'full') for r in ('startup', 'post_startup')}
    actual_unavailable = {tuple(row['identity'][k] for k in
                                ('filter', 'variant', 'compiler', 'block', 'stimulus', 'regime'))
                          for row in panel['rows'] if row.get('status') == 'unavailable'}
    if actual_unavailable != expected_unavailable:
        raise ValueError('upgraded performance unavailable identities differ from the frozen rule')
    _add_hashed_row_files(repo, stage, panel['rows'], 'panel performance', selected)

    gates = _json(stage / 'build/panel/correctness/correctness-gates.json')
    if gates.get('protocol_sha256') != protocol_hash or gates.get('condition_count') != 72 or \
            gates.get('condition_limit') != 72 or len(gates.get('rows', [])) != 72:
        raise ValueError('upgraded correctness inventory is incomplete')
    gate_statuses = [row.get('status') for row in gates['rows']]
    if set(gate_statuses) - {'passed', 'skipped'} or gate_statuses.count('passed') != 70 or \
            gate_statuses.count('skipped') != 2:
        raise ValueError('upgraded correctness inventory must admit 70, mark 2 unavailable, and have 0 failures')
    expected_correct = {(f, v, c, b) for f, variants in protocol['variants_by_filter'].items()
                        for v in variants for c in protocol['compilers']
                        for b in protocol['correctness_gate']['blocks']}
    actual_correct = {tuple(row.get('identity', row).get(k) for k in ('filter', 'variant', 'compiler', 'block'))
                      for row in gates['rows']}
    expected_skipped = {('native_lp1800', 'cmsis32_unroll', c, 64) for c in ('gcc10', 'gcc15')}
    actual_skipped = {tuple(row.get('identity', row)[k] for k in ('filter', 'variant', 'compiler', 'block'))
                      for row in gates['rows'] if row.get('status') == 'skipped'}
    if len(actual_correct) != 72 or actual_correct != expected_correct or actual_skipped != expected_skipped:
        raise ValueError('upgraded correctness identities differ from the frozen inventory')
    _add_hashed_row_files(repo, stage, gates['rows'], 'panel correctness', selected)

    intervention = _json(stage / 'intervention-results.json')
    if intervention.get('comparability') != 'admitted' or len(intervention.get('rows', [])) != 4 or \
            len(intervention.get('correctness_only', [])) != 4:
        raise ValueError('upgraded intervention inventory must contain four performance and four correctness rows')
    for row in intervention['rows'] + intervention['correctness_only']:
        if not isinstance(row.get('artifacts'), dict) or not row['artifacts']:
            raise ValueError('upgraded intervention row has no recorded artifact map')
        directory = stage / _safe_rel(row['directory']).as_posix()
        for name, expected in row['artifacts'].items():
            relative_name = _safe_rel(name).as_posix()
            path = directory / relative_name
            if not path.is_file() or path.is_symlink() or _sha(path) != expected:
                raise ValueError(f'upgraded intervention artifact missing or hash mismatch: {path}')
            selected.add(path)

    # Portable paper sources and outputs are part of the final, reviewable package.
    paper_files = (
        'research/fir-upgrades/paper/manuscript.md',
        'research/fir-upgrades/paper/make_figures.py',
        'research/fir-upgrades/paper/ieee-template.tex',
        'research/fir-upgrades/paper/ieee-filter.lua',
        'research/fir-upgrades/paper/requirements-paper.txt',
        'research/fir-upgrades/paper/render_paper.py',
        'research/fir-upgrades/paper/README.md',
        'research/fir-upgrades/paper/render-log.md',
    )
    for relative in paper_files:
        add(relative)
    for relative in ('research/fir-upgrades/paper/manuscript.tex',
                     'research/fir-upgrades/paper/manuscript.pdf'):
        path = repo / relative
        if require_paper_build or path.exists():
            add(relative)
    for name in ('representation-lifetime.png', 'representation-lifetime.svg',
                 'ram-sensitivity.png', 'ram-sensitivity.svg',
                 'panel-boundaries.png', 'panel-boundaries.svg'):
        add(f'research/fir-upgrades/paper/figures/{name}')

    # Preserve selected canonical JSON outcomes and source archive notices, not tool binaries.
    return selected


def _add_hashed_row_files(repo: Path, stage: Path, rows: list[dict], label: str,
                          selected: set[Path]) -> None:
    for row in rows:
        if row.get('status') not in {'admitted', 'passed'}:
            continue
        if not isinstance(row.get('artifact_paths'), dict) or \
                set(row['artifact_paths']) != set(row.get('artifact_sha256', {})):
            raise ValueError(f'{label} row has an incomplete artifact inventory')
        directory = stage / _safe_rel(row['directory']).as_posix()
        for key, name in row['artifact_paths'].items():
            path = directory / _safe_rel(name).as_posix()
            expected = row['artifact_sha256'][key]
            if not path.is_file() or path.is_symlink() or _sha(path) != expected:
                raise ValueError(f'{label} artifact missing or hash mismatch: {path}')
            try:
                path.resolve().relative_to(repo)
            except ValueError as error:
                raise ValueError(f'{label} artifact escapes repository: {path}') from error
            selected.add(path)


def _validate_upgraded_tree(root: Path) -> dict:
    """Validate a restored upgrade archive's declared inventories and all raw hashes."""
    root = Path(root).resolve()
    stage = root / 'research/fir-upgrades'
    try:
        selected = _upgrade_root_paths(root, require_paper_build=True)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f'upgraded package inventory is incomplete: {error}') from error
    return {'files_referenced_by_admitted_rows': len(selected), 'scope': 'upgraded'}


def _canonicalize_panel_audit_paths(audit: dict) -> dict:
    """Normalize only absolute roots in stack-frame diagnostic paths."""
    normalized = copy.deepcopy(audit)
    marker = '/research/fir-upgrades/'
    for row in normalized.get('audited', []):
        frames = row.get('execution', {}).get('stack', {}).get('frames', [])
        for frame in frames:
            for field in ('file', 'source'):
                value = frame.get(field)
                if isinstance(value, str) and value.startswith('/') and marker in value:
                    suffix = value.split(marker, 1)[1]
                    frame[field] = '<repo>' + marker + suffix
    return normalized


def _upgraded_source_inputs(repo: Path) -> set[Path]:
    return _upgrade_root_paths(Path(repo).resolve())


def collect_files(repo: Path, *, include_upgrades: bool = False) -> list[Path]:
    """Return the sorted, repository-relative finite raw-evidence slice."""
    repo = Path(repo).resolve()
    selected = _source_inputs(repo)
    if include_upgrades:
        selected.update(_upgraded_source_inputs(repo))
    return sorted((path.resolve().relative_to(repo) for path in selected),
                  key=lambda path: path.as_posix())


def _records(repo: Path, paths: list[Path]) -> list[dict]:
    return [{'path': path.as_posix(), 'size': (repo / path).stat().st_size,
             'sha256': _sha(repo / path)} for path in paths]


def _manifest(records: list[dict], package_scope: str = 'central') -> bytes:
    payload = {'schema_version': 1, 'package_scope': package_scope,
               'description': 'SHA-256 consistency manifest; hashes do not prove authenticity.',
               'files': records}
    return (json.dumps(payload, sort_keys=True, indent=2) + '\n').encode()


def _write_archive(repo: Path, output: Path, paths: list[Path],
                   package_scope: str = 'central') -> dict:
    records = _records(repo, paths)
    if package_scope not in {'central', 'upgraded'}:
        raise ValueError(f'unsupported package scope: {package_scope}')
    embedded = _manifest(records, package_scope)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        temp = Path(temporary)
        archive_tmp, manifest_tmp = temp / ARCHIVE_NAME, temp / MANIFEST_NAME
        manifest_tmp.write_bytes(embedded)
        with archive_tmp.open('wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
                with tarfile.open(fileobj=zipped, mode='w|') as tar:
                    for record in records:
                        source = repo / record['path']
                        info = tarfile.TarInfo(record['path'])
                        info.size = record['size']
                        info.mode = 0o644
                        info.mtime = 0
                        info.uid = info.gid = 0
                        info.uname = info.gname = ''
                        with source.open('rb') as stream:
                            tar.addfile(info, stream)
                    info = tarfile.TarInfo(MANIFEST_NAME)
                    info.size = len(embedded)
                    info.mode = 0o644
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ''
                    tar.addfile(info, io.BytesIO(embedded))
        archive_digest = _sha(archive_tmp)
        sidecar = {'schema_version': 1, 'package_scope': package_scope, 'archive': ARCHIVE_NAME,
                   'archive_sha256': archive_digest, 'files': records,
                   'hashes_are_consistency_checks_not_authenticity_proofs': True}
        manifest_tmp.write_text(json.dumps(sidecar, sort_keys=True, indent=2) + '\n')
        os.replace(archive_tmp, output / ARCHIVE_NAME)
        os.replace(manifest_tmp, output / MANIFEST_NAME)
    return {'archive': str(output / ARCHIVE_NAME), 'archive_sha256': archive_digest,
            'file_count': len(records), 'files': records}


def pack(repo: Path, output: Path, *, include_upgrades: bool = False) -> dict:
    """Write deterministic gzip tar and sidecar after full validation succeeds."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    if include_upgrades:
        paths = _source_inputs(repo) | _upgrade_root_paths(repo, require_paper_build=True)
    else:
        paths = _source_inputs(repo)
    paths = sorted((path.resolve().relative_to(repo) for path in paths), key=lambda p: p.as_posix())
    return _write_archive(repo, output, paths, 'upgraded' if include_upgrades else 'central')


def unpack_verified(archive: Path, destination: Path) -> dict:
    """Validate every archive member and embedded digest before writing files."""
    archive, destination = Path(archive).resolve(), Path(destination).resolve()
    if not archive.is_file():
        raise ValueError(f'archive does not exist: {archive}')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('destination must be an empty directory')
    members: dict[str, bytes] = {}
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            name = member.name
            relative = _safe_rel(name)
            if name in members:
                raise ValueError(f'duplicate archive member: {name}')
            if not member.isfile():
                raise ValueError(f'non-regular archive member: {name}')
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError(f'unreadable archive member: {name}')
            members[name] = stream.read()
    if MANIFEST_NAME not in members:
        raise ValueError('archive has no embedded evidence manifest')
    try:
        manifest = json.loads(members.pop(MANIFEST_NAME))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid embedded manifest') from error
    records = manifest.get('files')
    if manifest.get('schema_version') != 1 or not isinstance(records, list):
        raise ValueError('unsupported or malformed embedded manifest')
    package_scope = manifest.get('package_scope', 'central')
    if package_scope not in {'central', 'upgraded'}:
        raise ValueError('unsupported evidence package scope')
    if package_scope == 'central' and any(
            path in members for path in ('research/fir-upgrades/panel-results.json',
                                         'research/fir-upgrades/intervention-results.json')):
        raise ValueError('upgrade result files require an explicitly upgraded package scope')
    sidecar_path = archive.parent / MANIFEST_NAME
    if sidecar_path.is_file():
        sidecar = _json(sidecar_path)
        if sidecar.get('archive_sha256') != _sha(archive) or \
                sidecar.get('package_scope', 'central') != package_scope or \
                sidecar.get('files') != records:
            raise ValueError('sidecar manifest does not bind the archive bytes and declared scope')
    expected = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {'path', 'size', 'sha256'}:
            raise ValueError('malformed manifest record')
        name = _safe_rel(record['path']).as_posix()
        if name == MANIFEST_NAME or name in expected:
            raise ValueError(f'duplicate or reserved manifest path: {name}')
        if type(record['size']) is not int or record['size'] < 0:
            raise ValueError(f'invalid size for {name}')
        if not isinstance(record['sha256'], str) or len(record['sha256']) != 64:
            raise ValueError(f'invalid digest for {name}')
        expected[name] = record
    if set(members) != set(expected):
        raise ValueError('archive members do not match manifest')
    for name, data in members.items():
        record = expected[name]
        if len(data) != record['size'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError(f'archive content hash or size mismatch: {name}')
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.evidence-stage-', dir=destination.parent))
    try:
        for name, data in members.items():
            path = staging / _safe_rel(name).as_posix()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if package_scope == 'upgraded':
            _validate_upgraded_tree(staging)
        if destination.exists() and any(destination.iterdir()):
            raise ValueError('destination became nonempty during extraction')
        destination.mkdir(parents=True, exist_ok=True)
        for name in sorted(members):
            target = destination / _safe_rel(name).as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / name, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return {'verified_files': len(members), 'manifest': manifest, 'package_scope': package_scope,
            'archive_sha256': _sha(archive)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pack_parser = sub.add_parser('pack', help='pack and hash the finite evidence slice')
    pack_parser.add_argument('--repo-root', type=Path, required=True, help='repository root')
    pack_parser.add_argument('--output-dir', type=Path, required=True, help='package output directory')
    pack_parser.add_argument('--include-upgrades', action='store_true',
                             help='include the admitted prospective panel and intervention evidence')
    check_parser = sub.add_parser('check', help='restore archive and run checks in a fresh copy')
    check_parser.add_argument('--archive', type=Path, required=True, help='evidence.tar.gz')
    check_parser.add_argument('--destination', type=Path, required=True, help='empty restore directory')
    check_parser.add_argument('--output-dir', type=Path, required=True, help='integration report directory')
    args = parser.parse_args(argv)
    try:
        if args.command == 'pack':
            result = pack(args.repo_root, args.output_dir, include_upgrades=args.include_upgrades)
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            result = unpack_verified(args.archive, args.destination)
            # The required CLI destination is explicit; execute checks against it.
            build = args.destination / 'research/fir-upgrades/build'
            build.mkdir(parents=True, exist_ok=True)
            result['fresh_copy'] = str(args.destination.resolve())
            result['integration'] = _check_restored(args.destination, args.output_dir,
                                                    result['package_scope'])
            (args.output_dir / 'artifact-check.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: result[k] for k in ('archive_sha256', 'file_count') if k in result} |
                         ({'verified_files': result.get('verified_files')} if 'verified_files' in result else {}),
                         sort_keys=True))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'artifact operation failed: {error}\n')


def _check_restored(copied: Path, output: Path, package_scope: str = 'central') -> dict:
    import subprocess
    import sys
    copied = copied.resolve()
    build = copied / 'research/fir-upgrades/build'
    stage = copied / 'research/fir-upgrades'
    if package_scope not in {'central', 'upgraded'}:
        raise ValueError('unsupported copied-tree package scope')
    if package_scope == 'upgraded':
        _validate_upgraded_tree(copied)
        saved_analysis = _json(stage / 'analysis/analysis.json')
        saved_panel = _json(stage / 'panel-summary.json')
        saved_audit = _json(stage / 'verification/independent-audit.json')
    commands = _check_commands(copied, include_upgrades=package_scope == 'upgraded')
    env = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
    runs = []
    for command in commands:
        completed = subprocess.run(command, cwd=copied, env=env, capture_output=True, text=True)
        runs.append({'command': command, 'returncode': completed.returncode,
                     'stdout': completed.stdout, 'stderr': completed.stderr})
        if completed.returncode:
            raise RuntimeError(f'fresh-copy integration failed: {command}: {completed.stderr}')
    saved = _json(copied / 'research/fir-paper/results.json')
    exported = _json(build / 'paper-export/results.json')
    if saved != exported:
        raise ValueError('fresh-copy numerical export differs from saved paper results')
    raw = _json(build / 'raw-check/verification.json')
    explanation = _json(build / 'explanation-check/verification.json')
    expected = (24, 4, 2, 29)
    observed = (len(raw['rows']), len(raw['peer_rows']), explanation['peer_rows_checked'],
                len(explanation['evidence_files_checked']))
    if observed != expected:
        raise ValueError(f'fresh-copy checker admission mismatch: expected {expected}, got {observed}')
    if package_scope == 'upgraded':
        _validate_upgraded_tree(copied)
    upgrade_report = None
    if package_scope == 'upgraded':
        generated_analysis = _json(build / 'artifact-check/analysis/analysis.json')
        if generated_analysis != saved_analysis:
            raise ValueError('fresh-copy U2 analysis differs from the admitted analysis')
        generated_panel = _json(stage / 'panel-summary.json')
        # panel_verify writes its fresh audit to the explicit build output; the
        # saved verification/independent-audit.json is regenerated as a side
        # effect too, so comparing that path would compare the source to itself.
        generated_audit = _json(build / 'artifact-check/panel-audit.json')
        if generated_panel != saved_panel:
            raise ValueError('fresh-copy panel summary differs from independently derived raw results')
        if _canonicalize_panel_audit_paths(generated_audit) != _canonicalize_panel_audit_paths(saved_audit):
            raise ValueError('fresh-copy panel audit differs from saved independent audit')
        panel_audit = _json(build / 'artifact-check/panel-audit.json')
        correctness_audit = _json(build / 'artifact-check/correctness-audit.json')
        intervention = json.loads(runs[-1]['stdout'])
        counts = (panel_audit.get('admitted_count'), panel_audit.get('unavailable_count'),
                  panel_audit.get('failed_count'), correctness_audit.get('admitted_count'),
                  correctness_audit.get('skipped_count'), correctness_audit.get('failed_count'),
                  intervention.get('performance_rows'), intervention.get('correctness_only_rows'))
        if counts != (280, 8, 0, 70, 2, 0, 4, 4):
            raise ValueError(f'fresh-copy upgrade admission mismatch: expected (280, 8, 0, 70, 2, 0, 4, 4), got {counts}')
        upgrade_report = {'panel_performance': {'admitted': counts[0], 'unavailable': counts[1], 'failed': counts[2]},
                          'panel_correctness': {'admitted': counts[3], 'unavailable': counts[4], 'failed': counts[5]},
                          'intervention': {'performance': counts[6], 'correctness': counts[7]},
                          'analysis_matches_saved': True, 'panel_summary_matches_saved': True,
                          'panel_audit_matches_saved': True}
    report = {'commands': runs, 'historical_rows': len(raw['rows']),
              'peer_rows': len(raw['peer_rows']), 'explanation_rows': explanation['peer_rows_checked'],
              'evidence_hashes': len(explanation['evidence_files_checked']),
              'export_matches_saved': True,
              'package_scope': package_scope, 'upgrades': upgrade_report,
              'skip_count': 0, 'integration_skip_count': 0,
              'toolchain_executions': 0}
    return report


def _check_commands(copied: Path, *, include_upgrades: bool = False) -> list[list[str]]:
    """Build explicit fresh-tree commands for all three standard-library checks."""
    import sys
    copied = Path(copied).resolve()
    build = copied / 'research/fir-upgrades/build'
    commands = [
        [sys.executable, str(copied / 'research/fir-paper/build_results.py'), '--repo-root', str(copied),
         '--output-dir', str(build / 'paper-export')],
        [sys.executable, str(copied / 'research/fir-sharing-probe/independent-check/check.py'),
         '--probe-root', str(copied / 'research/fir-sharing-probe'),
         '--peer-results', str(copied / 'research/fir-sharing-probe/partial-direct/results.json'),
         '--output-dir', str(build / 'raw-check')],
        [sys.executable, str(copied / 'research/fir-sharing-probe/explanation-check/verify.py'),
         '--peer-report', str(copied / 'research/fir-sharing-probe/compiler-explanation/accounting.json'),
         '--output-dir', str(build / 'explanation-check')],
    ]
    if include_upgrades:
        upgrades = copied / 'research/fir-upgrades'
        upgraded_build = build / 'artifact-check'
        commands.extend([
            [sys.executable, str(upgrades / 'analyze.py'), '--repo-root', str(copied),
             '--output-dir', str(upgraded_build / 'analysis')],
            [sys.executable, str(upgrades / 'panel_verify.py'), '--root', str(upgrades),
             '--output', str(upgraded_build / 'panel-audit.json')],
            [sys.executable, str(upgrades / 'panel_verify.py'), '--root', str(upgrades),
             '--correctness-only', '--output', str(upgraded_build / 'correctness-audit.json')],
            [sys.executable, str(upgrades / 'intervention.py'), '--verify'],
        ])
    return commands


if __name__ == '__main__':
    main()
