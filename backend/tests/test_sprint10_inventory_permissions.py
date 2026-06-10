import unittest
from app.permissions.constants import PERMISSION_CODES_BY_MODULE, ROLE_PERMISSION_MAP
class Sprint10InventoryPermissionTests(unittest.TestCase):
    def test_inventory_permission_matrix(self):
        codes=set(PERMISSION_CODES_BY_MODULE['inventory'])
        self.assertEqual(29,len(codes))
        for code in ('inventory.projects.view.all','inventory.projects.create','inventory.projects.update','inventory.projects.delete','inventory.properties.create'):self.assertIn(code,codes)
        for action in ('view','update','status','delete','price.view','price.update'):
            for scope in ('own','team','department','all'):self.assertIn(f'inventory.properties.{action}.{scope}',codes)
    def test_default_role_scopes(self):
        codes=set(PERMISSION_CODES_BY_MODULE['inventory']);self.assertTrue(codes.issubset(ROLE_PERMISSION_MAP['admin']));self.assertTrue(codes.issubset(ROLE_PERMISSION_MAP['inventory_manager']))
        self.assertIn('inventory.properties.view.all',ROLE_PERMISSION_MAP['director']);self.assertNotIn('inventory.properties.delete.all',ROLE_PERMISSION_MAP['director'])
        self.assertIn('inventory.properties.view.department',ROLE_PERMISSION_MAP['sales_manager']);self.assertIn('inventory.properties.view.team',ROLE_PERMISSION_MAP['leader'])
        self.assertIn('inventory.properties.view.own',ROLE_PERMISSION_MAP['sale']);self.assertNotIn('inventory.properties.delete.own',ROLE_PERMISSION_MAP['sale'])
        self.assertIn('inventory.projects.view.all',ROLE_PERMISSION_MAP['viewer']);self.assertNotIn('inventory.properties.update.own',ROLE_PERMISSION_MAP['viewer'])
if __name__=='__main__':unittest.main()
