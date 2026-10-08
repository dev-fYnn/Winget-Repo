"""Standard-library regression tests for REST package correlation searches.

Loads only the functions under test, avoiding Flask/database application startup.
"""
import ast
from pathlib import Path
import re
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_search_class():
    tree = ast.parse((ROOT / 'Modules/Database/Database.py').read_text())
    source_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SQLiteDatabase')
    method = next(n for n in source_class.body if isinstance(n, ast.FunctionDef) and n.name == 'search_packages')
    class_node = ast.ClassDef(name='SearchDatabase', bases=[], keywords=[], body=[method], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[class_node], type_ignores=[]))
    def all_to_dict(rows, description):
        return [dict(zip([c[0] for c in description], row)) for row in rows]
    namespace = {'re': re, 'all_to_dict': all_to_dict}
    exec(compile(module, '<upstream search_packages>', 'exec'), namespace)
    return namespace['SearchDatabase']


def load_filter():
    tree = ast.parse((ROOT / 'Modules/Winget/Functions.py').read_text())
    method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'filter_entries_by_package_match_field')
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), '<upstream filter>', 'exec'), namespace)
    return namespace['filter_entries_by_package_match_field']


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        self.connection.execute('CREATE TABLE tbl_PACKAGES (PACKAGE_ID TEXT, PACKAGE_NAME TEXT, PACKAGE_PUBLISHER TEXT, PACKAGE_ACTIVE INTEGER)')
        self.connection.execute('CREATE TABLE tbl_PACKAGES_VERSIONS (PACKAGE_ID TEXT, PRODUCTCODE TEXT, PACKAGE_FAMILY_NAME TEXT)')
        self.connection.executemany('INSERT INTO tbl_PACKAGES VALUES (?,?,?,?)', [
            ('Microsoft.AzureCLI', 'Microsoft Azure CLI', 'Microsoft Corporation', 1),
            ('Microsoft.msodbcsql.18', 'Microsoft ODBC Driver 18 for SQL Server', 'Microsoft Corporation', 1),
            ('Microsoft.WindowsTerminal', 'Windows Terminal', 'Microsoft Corporation', 1),
            ('Devolutions.RemoteDesktopManager', 'Remote Desktop Manager', 'Devolutions', 1),
            ('Devolutions.Launcher', 'Devolutions Launcher', 'Devolutions', 1),
            ('OpenJS.NodeJS', 'Node.js', 'OpenJS Foundation', 1),
            ('Disabled.Package', 'Disabled Package', 'Test', 0),
        ])
        self.connection.executemany('INSERT INTO tbl_PACKAGES_VERSIONS VALUES (?,?,?)', [
            ('Microsoft.AzureCLI', '{CB3186C1-BF23-488F-A4D4-8A1BFE220427}', ''),
            ('Microsoft.AzureCLI', '{CB3186C1-BF23-488F-A4D4-8A1BFE220427}', ''),
            ('Microsoft.msodbcsql.18', '{820A3DEC-9783-42AE-B12D-750FCCF07E10}', ''),
            ('Microsoft.WindowsTerminal', '', 'Microsoft.WindowsTerminal_8wekyb3d8bbwe'),
            ('Disabled.Package', '{ABC}', ''),
        ])
        self.db = load_search_class()()  # Class dynamically assembled from upstream method AST.
        self.db._SearchDatabase__cursor = self.connection.cursor()

    def tearDown(self):
        self.connection.close()

    def query(self, text, field, typ='Exact'):
        return [row['PACKAGE_ID'] for row in self.db.search_packages(text, typ, field)]

    def test_product_code_case_insensitive_and_distinct(self):
        self.assertEqual(['Microsoft.AzureCLI'], self.query('{cb3186c1-bf23-488f-a4d4-8a1bfe220427}', 'ProductCode'))

    def test_package_family_name(self):
        self.assertEqual(['Microsoft.WindowsTerminal'], self.query('microsoft.windowsterminal_8wekyb3d8bbwe', 'PackageFamilyName'))

    def test_normalized_name_exact_not_substring(self):
        self.assertEqual(['Devolutions.RemoteDesktopManager'], self.query('remotedesktopmanager', 'NormalizedPackageNameAndPublisher'))
        self.assertEqual(['OpenJS.NodeJS'], self.query('nodejs', 'NormalizedPackageNameAndPublisher'))
        self.assertEqual([], self.query('desktop', 'NormalizedPackageNameAndPublisher'))

    def test_package_identifier_and_name_regression(self):
        self.assertEqual(['Microsoft.AzureCLI'], self.query('microsoft.azurecli', 'PackageIdentifier'))
        self.assertIn('Microsoft.AzureCLI', self.query('Azure', 'PackageName', 'Substring'))
        self.assertEqual(['Microsoft.AzureCLI'], self.query('Microsoft.Az', 'PackageIdentifier', 'StartsWith'))

    def test_inactive_and_unsupported_are_filtered(self):
        self.assertEqual([], self.query('{abc}', 'ProductCode'))
        self.assertEqual([], self.query('anything', 'UnknownField'))
        self.assertEqual([], self.query('  ', 'PackageName'))

    def test_supported_rest_filters(self):
        fn = load_filter()
        fields = ['ProductCode', 'PackageFamilyName', 'NormalizedPackageNameAndPublisher', 'PackageIdentifier', 'PackageName']
        payload = [{'PackageMatchField': f, 'RequestMatch': {'KeyWord': 'value'}} for f in fields]
        payload += [{'PackageMatchField': 'BadField', 'RequestMatch': {}}, {'PackageMatchField': 'ProductCode'}, None]
        self.assertEqual(fields, [x['PackageMatchField'] for x in fn(payload)])


if __name__ == '__main__':
    unittest.main()
