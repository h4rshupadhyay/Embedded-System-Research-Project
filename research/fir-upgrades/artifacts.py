"""Build and check a portable, hash-verified slice of the original FIR evidence."""
from __future__ import annotations

import argparse
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


def collect_files(repo: Path) -> list[Path]:
    """Return the sorted, repository-relative finite raw-evidence slice."""
    repo = Path(repo).resolve()
    return sorted((path.resolve().relative_to(repo) for path in _source_inputs(repo)),
                  key=lambda path: path.as_posix())


def _records(repo: Path, paths: list[Path]) -> list[dict]:
    return [{'path': path.as_posix(), 'size': (repo / path).stat().st_size,
             'sha256': _sha(repo / path)} for path in paths]


def _manifest(records: list[dict]) -> bytes:
    payload = {'schema_version': 1,
               'description': 'SHA-256 consistency manifest; hashes do not prove authenticity.',
               'files': records}
    return (json.dumps(payload, sort_keys=True, indent=2) + '\n').encode()


def _write_archive(repo: Path, output: Path, paths: list[Path]) -> dict:
    records = _records(repo, paths)
    embedded = _manifest(records)
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
        sidecar = {'schema_version': 1, 'archive': ARCHIVE_NAME,
                   'archive_sha256': archive_digest, 'files': records,
                   'hashes_are_consistency_checks_not_authenticity_proofs': True}
        manifest_tmp.write_text(json.dumps(sidecar, sort_keys=True, indent=2) + '\n')
        os.replace(archive_tmp, output / ARCHIVE_NAME)
        os.replace(manifest_tmp, output / MANIFEST_NAME)
    return {'archive': str(output / ARCHIVE_NAME), 'archive_sha256': archive_digest,
            'file_count': len(records), 'files': records}


def pack(repo: Path, output: Path) -> dict:
    """Write deterministic gzip tar and sidecar after full validation succeeds."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    paths = collect_files(repo)
    return _write_archive(repo, output, paths)


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
        if destination.exists() and any(destination.iterdir()):
            raise ValueError('destination became nonempty during extraction')
        destination.mkdir(parents=True, exist_ok=True)
        for name in sorted(members):
            target = destination / _safe_rel(name).as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / name, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return {'verified_files': len(members), 'manifest': manifest,
            'archive_sha256': _sha(archive)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pack_parser = sub.add_parser('pack', help='pack and hash the finite evidence slice')
    pack_parser.add_argument('--repo-root', type=Path, required=True, help='repository root')
    pack_parser.add_argument('--output-dir', type=Path, required=True, help='package output directory')
    check_parser = sub.add_parser('check', help='restore archive and run checks in a fresh copy')
    check_parser.add_argument('--archive', type=Path, required=True, help='evidence.tar.gz')
    check_parser.add_argument('--destination', type=Path, required=True, help='empty restore directory')
    check_parser.add_argument('--output-dir', type=Path, required=True, help='integration report directory')
    args = parser.parse_args(argv)
    try:
        if args.command == 'pack':
            result = pack(args.repo_root, args.output_dir)
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            result = unpack_verified(args.archive, args.destination)
            # The required CLI destination is explicit; execute checks against it.
            build = args.destination / 'research/fir-upgrades/build'
            build.mkdir(parents=True, exist_ok=True)
            result['fresh_copy'] = str(args.destination.resolve())
            result['integration'] = _check_restored(args.destination, args.output_dir)
            (args.output_dir / 'artifact-check.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: result[k] for k in ('archive_sha256', 'file_count') if k in result} |
                         ({'verified_files': result.get('verified_files')} if 'verified_files' in result else {}),
                         sort_keys=True))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(1, f'artifact operation failed: {error}\n')


def _check_restored(copied: Path, output: Path) -> dict:
    import subprocess
    import sys
    copied = copied.resolve()
    build = copied / 'research/fir-upgrades/build'
    commands = _check_commands(copied)
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
    report = {'commands': runs, 'historical_rows': len(raw['rows']),
              'peer_rows': len(raw['peer_rows']), 'explanation_rows': explanation['peer_rows_checked'],
              'evidence_hashes': len(explanation['evidence_files_checked']),
              'export_matches_saved': True, 'skip_count': 0}
    return report


def _check_commands(copied: Path) -> list[list[str]]:
    """Build explicit fresh-tree commands for all three standard-library checks."""
    import sys
    copied = Path(copied).resolve()
    build = copied / 'research/fir-upgrades/build'
    return [
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


if __name__ == '__main__':
    main()
