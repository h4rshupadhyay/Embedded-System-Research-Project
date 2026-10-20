import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifacts


def _small_paths(repo):
    return sorted(p.relative_to(repo) for p in repo.rglob('*') if p.is_file())


def test_small_archive_is_deterministic_and_round_trips(tmp_path):
    repo = tmp_path / 'repo'
    (repo / 'a').mkdir(parents=True)
    (repo / 'a' / 'data.txt').write_bytes(b'alpha\n')
    (repo / 'z.bin').write_bytes(b'\x00\xff')
    first, second = tmp_path / 'first', tmp_path / 'second'
    result1 = artifacts._write_archive(repo, first, _small_paths(repo))
    result2 = artifacts._write_archive(repo, second, _small_paths(repo))
    assert (first / 'evidence.tar.gz').read_bytes() == (second / 'evidence.tar.gz').read_bytes()
    assert result1['files'] == result2['files']
    destination = tmp_path / 'copy'
    report = artifacts.unpack_verified(first / 'evidence.tar.gz', destination)
    assert (destination / 'a/data.txt').read_bytes() == b'alpha\n'
    assert report['verified_files'] == 2


def test_collect_files_includes_hcub_provenance_and_both_license_notices():
    root = Path(__file__).resolve().parents[2]
    collected = artifacts.collect_files(root)
    assert collected == sorted(collected, key=lambda path: path.as_posix())
    assert all(not path.is_absolute() for path in collected)
    paths = {path.as_posix() for path in collected}
    required = {
        'research/fir-sharing-probe/vendor/BUILD.md',
        'research/fir-sharing-probe/vendor/examples-manifest.json',
        'research/fir-sharing-probe/vendor/speech_minphase48.txt',
        'research/fir-sharing-probe/vendor/speech_minphase48.stderr.txt',
        'research/fir-sharing-probe/vendor/synth-jan-14-2009.tar.gz',
        'research/fir-sharing-probe/vendor/synth-jan-14-2009/COPYRIGHT',
        'research/fir-sharing-probe/vendor/synth-jan-14-2009/COPYING',
    }
    assert required <= paths


def test_unpack_rejects_changed_and_missing_manifest_bytes_without_writing(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'raw.txt').write_text('original')
    output = tmp_path / 'out'
    artifacts._write_archive(repo, output, _small_paths(repo))
    original = (output / 'evidence.tar.gz').read_bytes()
    destination = tmp_path / 'copy'
    destination.mkdir()

    changed = tmp_path / 'changed.tar.gz'
    with tarfile.open(output / 'evidence.tar.gz', 'r:gz') as source:
        members = [(m, source.extractfile(m).read() if m.isfile() else b'') for m in source]
    altered = [(m, b'changed' if m.name == 'raw.txt' else body) for m, body in members]
    with tarfile.open(changed, 'w:gz') as target:
        import io
        for member, body in altered:
            member.size = len(body)
            target.addfile(member, io.BytesIO(body) if member.isfile() else None)
    with pytest.raises(ValueError, match='hash or size mismatch'):
        artifacts.unpack_verified(changed, destination)
    assert list(destination.iterdir()) == []

    missing = tmp_path / 'missing.tar.gz'
    with tarfile.open(missing, 'w:gz') as target:
        import io
        manifest = next((m, body) for m, body in members if m.name == artifacts.MANIFEST_NAME)
        target.addfile(manifest[0], io.BytesIO(manifest[1]))
    with pytest.raises(ValueError, match='members do not match'):
        artifacts.unpack_verified(missing, destination)
    assert list(destination.iterdir()) == []
    assert (output / 'evidence.tar.gz').read_bytes() == original


def test_failed_cli_check_preserves_existing_report(tmp_path):
    output = tmp_path / 'reports'
    output.mkdir()
    report = output / 'artifact-check.json'
    report.write_text('prior report\n')
    with pytest.raises(SystemExit):
        artifacts.main(['check', '--archive', str(tmp_path / 'missing.tar.gz'),
                        '--destination', str(tmp_path / 'copy'), '--output-dir', str(output)])
    assert report.read_text() == 'prior report\n'


def test_fresh_export_uses_only_dependencies_in_the_copy(tmp_path):
    copied = tmp_path / 'copy'
    script = copied / 'research/fir-paper/build_results.py'
    script.parent.mkdir(parents=True)
    source_script = Path(__file__).resolve().parents[1] / 'fir-paper/build_results.py'
    shutil.copyfile(source_script, script)
    command = artifacts._check_commands(copied)[0]
    import os
    import subprocess
    env = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
    result = subprocess.run(command, cwd=copied, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'missing frozen input:' in result.stderr
    assert (source_script.parents[0] / 'source-manifest.json').is_file()


def test_fresh_copy_check_runs_subprocess_and_reports_failure(tmp_path):
    copied = tmp_path / 'copy'
    script = copied / 'research/fir-paper/build_results.py'
    script.parent.mkdir(parents=True)
    script.write_text('raise SystemExit(17)\n')
    with pytest.raises(RuntimeError, match='fresh-copy integration failed'):
        artifacts._check_restored(copied, tmp_path / 'reports')


def test_public_pack_preserves_prior_outputs_when_a_copied_source_is_changed_or_missing(tmp_path):
    source_root = Path(__file__).resolve().parents[2]
    paths = artifacts.collect_files(source_root)
    repo = tmp_path / 'repo'
    for relative in paths:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, target)
    output = tmp_path / 'package'
    artifacts.pack(repo, output)
    prior = {name: (output / name).read_bytes()
             for name in (artifacts.ARCHIVE_NAME, artifacts.MANIFEST_NAME)}

    affected = next(path for path in paths if path.name == 'firmware.bin')
    (repo / affected).write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='artifact missing or hash mismatch'):
        artifacts.pack(repo, output)
    assert {name: (output / name).read_bytes() for name in prior} == prior

    (repo / affected).unlink()
    with pytest.raises(ValueError, match='artifact missing or hash mismatch'):
        artifacts.pack(repo, output)
    assert {name: (output / name).read_bytes() for name in prior} == prior


def _archive_with(tmp_path, members):
    archive = tmp_path / 'bad.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for info, body in members:
            import io
            tar.addfile(info, io.BytesIO(body) if info.isfile() else None)
    return archive


@pytest.mark.parametrize('name,kind', [
    ('../escape', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
    ('./escape', tarfile.REGTYPE), ('nested//escape', tarfile.REGTYPE),
    ('duplicate.txt', tarfile.REGTYPE), ('link', tarfile.SYMTYPE),
    ('hardlink', tarfile.LNKTYPE),
    ('fifo', tarfile.FIFOTYPE),
])
def test_unpack_rejects_unsafe_duplicate_or_special_members_without_writing_outside(tmp_path, name, kind):
    import io
    good = tarfile.TarInfo('evidence-manifest.json')
    body = b'x' if kind == tarfile.REGTYPE else b''
    files = ([{'path': name, 'size': len(body), 'sha256': hashlib.sha256(body).hexdigest()}]
             if kind == tarfile.REGTYPE and name != 'duplicate.txt' else [])
    manifest_body = json.dumps({'schema_version': 1, 'files': files}).encode()
    good.size = len(manifest_body)
    members = [(good, manifest_body)]
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = len(body)
    members.append((info, body))
    if name == 'duplicate.txt':
        info2 = tarfile.TarInfo(name)
        info2.size = 1
        members.append((info2, b'y'))
    archive = _archive_with(tmp_path, members)
    destination = tmp_path / 'empty'
    destination.mkdir()
    outside = tmp_path / 'escape'
    expected_error = 'unsafe relative path' if name in ('./escape', 'nested//escape') else None
    with pytest.raises((ValueError, OSError, tarfile.TarError), match=expected_error):
        artifacts.unpack_verified(archive, destination)
    assert list(destination.iterdir()) == []
    assert not outside.exists()
