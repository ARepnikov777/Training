import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'source/H11/input'

class CatalogTest(unittest.TestCase):
    def test_build_and_validate_and_detect_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            import shutil
            copied = tmp / 'input'
            shutil.copytree(INPUT, copied)
            pdf = tmp / 'catalog.pdf'
            def run(script, *args):
                return subprocess.run([sys.executable, str(ROOT / script), *map(str, args)], capture_output=True, text=True)
            build = run('build_catalog.py', '--input', copied, '--output', pdf)
            self.assertEqual(build.returncode, 0, build.stderr)
            valid = run('validate_catalog.py', '--input', INPUT, '--pdf', pdf)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            shutil.copyfile(copied / 'product-2.png', copied / 'product-1.png')
            build = run('build_catalog.py', '--input', copied, '--output', pdf)
            self.assertEqual(build.returncode, 0, build.stderr)
            invalid = run('validate_catalog.py', '--input', INPUT, '--pdf', pdf)
            print(f'Подмена: validator exit {invalid.returncode}; {invalid.stderr.strip()}')
            self.assertNotEqual(invalid.returncode, 0, 'Substituted embedded image accepted')
            shutil.copyfile(INPUT / 'product-1.png', copied / 'product-1.png')
            build = run('build_catalog.py', '--input', copied, '--output', pdf)
            self.assertEqual(build.returncode, 0, build.stderr)
            restored = run('validate_catalog.py', '--input', INPUT, '--pdf', pdf)
            print(f'Восстановление: validator exit {restored.returncode}')
            self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)

if __name__ == '__main__':
    unittest.main()
