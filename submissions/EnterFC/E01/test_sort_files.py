"""Behavior checks derived from input/rules.md, without checks/expected.json."""
from pathlib import Path
import tempfile
import unittest

from sort_files import copy_files

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'kit/E01/input/files'
EXPECTED = {
    'documents/manual.pdf', 'documents/notes.md', 'documents/readme.txt',
    'documents/record.json', 'images/picture-1.png', 'images/picture-2.png',
    'images/picture-3.png', 'images/picture-4.png', 'tables/table-1.csv',
    'tables/table-2.csv', 'tables/table-3.csv', 'tables/table-4.csv',
}


def contents(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in folder.rglob('*') if p.is_file()}


class CopyFilesTests(unittest.TestCase):
    def setUp(self):
        # Keep all temporary writes inside the submission.
        self.temp = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'result'

    def test_all_twelve_files_have_required_categories(self):
        # Catches missing files or a wrong category.
        copy_files(SOURCE, self.output)
        self.assertEqual(set(contents(self.output)), EXPECTED)

    def test_copies_preserve_every_byte(self):
        # Catches text decoding, truncation, or replacing binary content.
        copy_files(SOURCE, self.output)
        self.assertEqual(len(contents(self.output)), 12)
        for relative in EXPECTED:
            with self.subTest(file=relative):
                self.assertEqual((self.output / relative).read_bytes(),
                                 (SOURCE / Path(relative).name).read_bytes())

    def test_source_names_and_bytes_remain_unchanged(self):
        # Catches moving, deleting, or rewriting a source file.
        before = contents(SOURCE.parent)
        copy_files(SOURCE, self.output)
        self.assertEqual(contents(SOURCE.parent), before)

    def test_repeat_on_fresh_copy_matches_first_run(self):
        # Catches state retained between runs or incomplete fresh output.
        fresh_source = self.root / 'fresh-input'
        fresh_source.mkdir()
        for source in SOURCE.iterdir():
            (fresh_source / source.name).write_bytes(source.read_bytes())
        copy_files(SOURCE, self.output)
        repeat = self.root / 'repeat'
        copy_files(fresh_source, repeat)
        self.assertEqual(set(contents(repeat)), EXPECTED)
        self.assertEqual(contents(repeat), contents(self.output))

    def test_output_cannot_be_created_inside_source(self):
        # Catches accidental modification of the input directory tree.
        source = self.root / 'input'
        source.mkdir()
        (source / 'note.txt').write_bytes(b'keep original\r\n')
        before = contents(source)
        with self.assertRaises(ValueError):
            copy_files(source, source / 'result')
        self.assertEqual(contents(source), before)
        self.assertFalse((source / 'result').exists())


if __name__ == '__main__':
    unittest.main()
