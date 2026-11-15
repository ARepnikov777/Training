"""Recheck saved output and repeat from a clean copy; no external packages."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
KIT = HERE / 'kit/E01'


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    expected = json.loads((KIT / 'checks/expected.json').read_text(encoding='utf-8'))
    expected_paths = {f'{category}/{name}' for category, names in expected.items() for name in names}
    output = HERE / 'result'
    output_hashes = snapshot(output)
    assert set(output_hashes) == expected_paths and len(output_hashes) == 12
    pairs = []
    for relative in sorted(expected_paths):
        source = KIT / 'input/files' / Path(relative).name
        target = output / relative
        assert source.read_bytes() == target.read_bytes(), relative
        pairs.append({'source': source.relative_to(HERE).as_posix(), 'output': relative,
                      'sha256': output_hashes[relative], 'bytes_equal': True})
    before = json.loads((HERE / 'evidence/input-before.json').read_text(encoding='utf-8'))
    after = snapshot(KIT / 'input')
    assert after == before, 'Input names or bytes changed'
    checksums = json.loads((KIT / 'checksums.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((KIT / relative).read_bytes()).hexdigest() == digest
               for relative, digest in checksums.items()), 'Kit checksum mismatch'
    with tempfile.TemporaryDirectory(dir=HERE) as temporary:
        fresh = Path(temporary)
        shutil.copytree(KIT / 'input', fresh / 'input')
        shutil.copyfile(HERE / 'sort_files.py', fresh / 'sort_files.py')
        fresh_before = snapshot(fresh / 'input')
        command = [sys.executable, '-B', 'sort_files.py', 'input/files', 'result']
        run = subprocess.run(command, cwd=fresh, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        assert snapshot(fresh / 'result') == output_hashes
        assert snapshot(fresh / 'input') == fresh_before
        for relative in expected_paths:
            assert (fresh / 'result' / relative).read_bytes() == (fresh / 'input/files' / Path(relative).name).read_bytes()
        repeat_log = run.stdout + run.stderr
    assert snapshot(KIT / 'input') == before
    report = {'files_copied': 12, 'categories': {key: len(value) for key, value in expected.items()},
              'matches_expected_json': True, 'input_unchanged': True,
              'input_files_including_rules': len(after),
              'kit_checksums_verified': len(checksums),
              'fresh_copy_repeat_matches': True, 'fresh_input_unchanged': True,
              'repeat_command': 'python -B sort_files.py input/files result',
              'repeat_log': repeat_log, 'pairs': pairs}
    (HERE / 'evidence/input-after.json').write_text(json.dumps(after, indent=2) + '\n', encoding='utf-8')
    (HERE / 'evidence/verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: 12/12 copies byte-identical; 4 documents, 4 images, 4 tables.')
    print(f'PASS: {len(after)} input files unchanged; {len(checksums)} kit checksums verified.')
    print('PASS: clean copy, fresh working directory, CLI repeat byte-identical.')


if __name__ == '__main__':
    main()
