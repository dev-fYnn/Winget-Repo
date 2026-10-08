import ast
import unittest
from pathlib import Path

# Keep tests runnable without Flask/server dependencies.
source = Path(__file__).resolve().parents[1] / 'Modules/Store/Functions.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
names = {'inherit_store_correlation', 'extract_store_correlation'}
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
assert len(nodes) == len(names), 'Missing Store correlation helpers'
ns = {}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
inherit = ns['inherit_store_correlation']
extract = ns['extract_store_correlation']


class StoreCorrelationTests(unittest.TestCase):
    def test_root_product_and_upgrade(self):
        root = {'ProductCode': '{VC-X64}', 'AppsAndFeaturesEntries': [{'UpgradeCode': '{VC-UPGRADE}'}]}
        installer = inherit(root, {'Architecture': 'x64'})
        self.assertEqual(extract(installer), ('{VC-X64}', '{VC-UPGRADE}'))

    def test_root_x86_independent(self):
        root = {'ProductCode': '{VC-X86}', 'AppsAndFeaturesEntries': [{'UpgradeCode': '{X86-UPGRADE}'}]}
        installer = inherit(root, {'Architecture': 'x86'})
        self.assertEqual(extract(installer), ('{VC-X86}', '{X86-UPGRADE}'))

    def test_installer_overrides_root(self):
        result = inherit({'ProductCode': 'ROOT'}, {'ProductCode': 'LOCAL'})
        self.assertEqual(extract(result)[0], 'LOCAL')

    def test_apps_and_features_overrides_product(self):
        data = {'ProductCode': 'ROOT', 'AppsAndFeaturesEntries': [{'ProductCode': 'ARP', 'UpgradeCode': 'UPGRADE'}]}
        self.assertEqual(extract(data), ('ARP', 'UPGRADE'))

    def test_package_family_name_inheritance(self):
        result = inherit({'PackageFamilyName': 'Microsoft.Terminal_8wekyb3d8bbwe'}, {})
        self.assertEqual(result['PackageFamilyName'], 'Microsoft.Terminal_8wekyb3d8bbwe')

    def test_installer_aaf_overrides_root(self):
        root = {'AppsAndFeaturesEntries': [{'UpgradeCode': 'ROOT'}]}
        data = {'AppsAndFeaturesEntries': [{'UpgradeCode': 'LOCAL'}]}
        self.assertEqual(extract(inherit(root, data))[1], 'LOCAL')

    def test_missing_fields_preserve_default(self):
        self.assertEqual(extract(inherit({}, {})), ('', ''))

    def test_does_not_mutate_root_aaf(self):
        root = {'AppsAndFeaturesEntries': [{'UpgradeCode': 'ROOT'}]}
        result = inherit(root, {})
        result['AppsAndFeaturesEntries'][0]['UpgradeCode'] = 'MODIFIED'
        self.assertEqual(root['AppsAndFeaturesEntries'][0]['UpgradeCode'], 'ROOT')


if __name__ == '__main__':
    unittest.main()
