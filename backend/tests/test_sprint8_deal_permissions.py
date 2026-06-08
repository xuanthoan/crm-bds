import unittest
from app.permissions.constants import PERMISSION_CODES_BY_MODULE, ROLE_PERMISSION_MAP

class Sprint8DealPermissionTests(unittest.TestCase):
    def test_complete_permission_matrix(self):
        codes=set(PERMISSION_CODES_BY_MODULE['deals'])
        self.assertEqual(29,len(codes))
        for action in ('view','update','assign','stage','status','add_activity','delete'):
            for scope in ('own','team','department','all'): self.assertIn(f'deals.{action}.{scope}',codes)
        self.assertIn('deals.create',codes)
    def test_default_roles_follow_scope(self):
        self.assertTrue(set(PERMISSION_CODES_BY_MODULE['deals']).issubset(ROLE_PERMISSION_MAP['admin']))
        self.assertIn('deals.view.all',ROLE_PERMISSION_MAP['director']); self.assertNotIn('deals.delete.all',ROLE_PERMISSION_MAP['director'])
        self.assertIn('deals.assign.department',ROLE_PERMISSION_MAP['sales_manager'])
        self.assertIn('deals.assign.team',ROLE_PERMISSION_MAP['leader'])
        self.assertIn('deals.update.own',ROLE_PERMISSION_MAP['sale']); self.assertNotIn('deals.assign.own',ROLE_PERMISSION_MAP['sale'])
        self.assertEqual(['deals.view.own'],[x for x in ROLE_PERMISSION_MAP['viewer'] if x.startswith('deals.')])
if __name__=='__main__': unittest.main()
