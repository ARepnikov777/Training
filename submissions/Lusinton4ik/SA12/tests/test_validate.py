import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'validate.py'


def rows():
    return [dict(id=i, name=f'item {i}', category='test', price=123.45,
                 currency='USD', supplier='synthetic', availability='yes',
                 ram_GB=16, ssd_GB=512, screen_inches=15.6) for i in range(1, 51)]


class ValidatorTests(unittest.TestCase):
    def run_cli(self, data, *, csv_data=False, expected=None, catalog=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = rows() if catalog is None else catalog
            expected = [r['id'] for r in rows()] if expected is None else expected
            (root / 'ids.json').write_text(json.dumps(expected), encoding='utf-8')
            (root / 'catalog.json').write_text(json.dumps(catalog), encoding='utf-8')
            path = root / ('data.csv' if csv_data else 'data.json')
            if csv_data:
                with path.open('w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=list(data[0]))
                    writer.writeheader()
                    writer.writerows(data)
            else:
                path.write_text(json.dumps(data), encoding='utf-8')
            result = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), '--data', str(path),
                                     '--expected-ids', str(root / 'ids.json'), '--catalog', str(root / 'catalog.json')],
                                    capture_output=True, text=True, encoding='utf-8')
            return result.returncode, json.loads(result.stdout)

    def valid(self):
        return [dict(row, source_url=f'http://localhost:8000/product?id={row["id"]}') for row in rows()]

    def test_valid_json_and_object_ids(self):
        code, report = self.run_cli(self.valid(), expected={'ids': list(range(1, 51))})
        self.assertEqual((code, report['ok'], report['count'], report['unique_count'], report['errors']),
                         (0, True, 50, 50, []))

    def test_valid_csv(self):
        code, report = self.run_cli(self.valid(), csv_data=True)
        self.assertEqual((code, report['ok']), (0, True), report)

    def test_missing_record(self):
        code, report = self.run_cli(self.valid()[:-1])
        self.assertEqual(code, 1)
        self.assertFalse(report['ok'])
        self.assertTrue(any('missing' in e.lower() for e in report['errors']))

    def test_duplicate_and_unexpected(self):
        data = self.valid()
        data[0] = data[1].copy()
        code, report = self.run_cli(data)
        self.assertEqual(code, 1)
        self.assertTrue(any('duplicate' in e.lower() for e in report['errors']))
        data = self.valid()
        data[0]['id'] = 999
        code, report = self.run_cli(data)
        self.assertEqual(code, 1)
        self.assertTrue(any('unexpected' in e.lower() for e in report['errors']))

    def test_wrong_fields_and_missing_field(self):
        for field, value in [('price', 999), ('currency', 'EUR'), ('name', None)]:
            with self.subTest(field=field):
                data = self.valid()
                if value is None:
                    del data[0][field]
                else:
                    data[0][field] = value
                code, report = self.run_cli(data)
                self.assertEqual(code, 1)
                self.assertTrue(any(field in e for e in report['errors']))

    def test_bad_or_missing_url(self):
        for url in ['http://localhost/product?id=2', 'https://example.com/product?id=1',
                    'http://localhost/other?id=1', 'http://localhost/product?id=1&id=1', None]:
            with self.subTest(url=url):
                data = self.valid()
                if url is None:
                    del data[0]['source_url']
                else:
                    data[0]['source_url'] = url
                code, report = self.run_cli(data)
                self.assertEqual(code, 1)
                self.assertTrue(any('source_url' in e for e in report['errors']))

    def test_csv_does_not_round_numeric_values(self):
        data = self.valid()
        data[0]['price'] = '123.45001'
        code, report = self.run_cli(data, csv_data=True)
        self.assertEqual(code, 1)
        self.assertTrue(any('price' in e for e in report['errors']))

    def test_nullable_fields_match_json_and_csv(self):
        for field in ('availability', 'ram_GB', 'ssd_GB', 'screen_inches'):
            with self.subTest(field=field):
                catalog = rows()
                catalog[0][field] = None
                data = self.valid()
                data[0][field] = None
                for is_csv in (False, True):
                    code, report = self.run_cli(data, catalog=catalog, csv_data=is_csv)
                    self.assertEqual((code, report['ok']), (0, True), report)

    def test_nullable_fields_reject_missing_and_substitution(self):
        for field in ('availability', 'ram_GB', 'ssd_GB', 'screen_inches'):
            catalog = rows()
            catalog[0][field] = None
            for value in ('None', 42):
                for is_csv in (False, True):
                    with self.subTest(field=field, value=value, csv=is_csv):
                        data = self.valid()
                        data[0][field] = value
                        code, report = self.run_cli(data, catalog=catalog, csv_data=is_csv)
                        self.assertEqual(code, 1)
                        self.assertTrue(any(field in e for e in report['errors']), report)
            data = self.valid()
            del data[0][field]
            code, report = self.run_cli(data, catalog=catalog)
            self.assertEqual(code, 1)
            self.assertTrue(any(field in e for e in report['errors']), report)

    def test_null_rejected_when_reference_is_not_null(self):
        for field in ('availability', 'ram_GB', 'ssd_GB', 'screen_inches'):
            data = self.valid()
            data[0][field] = None
            for is_csv in (False, True):
                with self.subTest(field=field, csv=is_csv):
                    code, report = self.run_cli(data, csv_data=is_csv)
                    self.assertEqual(code, 1)
                    self.assertTrue(any(field in e for e in report['errors']), report)

    def test_catalog_missing_or_null_required_field_is_rejected(self):
        for field, value in (('ram_GB', 'missing'), ('name', None)):
            with self.subTest(field=field, value=value):
                catalog = rows()
                if value == 'missing':
                    del catalog[0][field]
                else:
                    catalog[0][field] = value
                code, report = self.run_cli(self.valid(), catalog=catalog)
                self.assertEqual(code, 1)
                self.assertTrue(report['errors'])

    def test_read_error_is_json(self):
        result = subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPT), '--data', 'absent.json',
                                 '--expected-ids', 'absent-ids.json', '--catalog', 'absent-catalog.json'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report['ok'])
        self.assertTrue(report['errors'])


if __name__ == '__main__':
    unittest.main()
