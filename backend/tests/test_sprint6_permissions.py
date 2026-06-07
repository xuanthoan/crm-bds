import unittest
from app.permissions.constants import ALL_PERMISSION_CODES, ROLE_PERMISSION_MAP

class Sprint6PermissionTests(unittest.TestCase):
    def test_admin_receives_all_sprint6_permissions(self):
        expected={"lead_tasks.create","lead_appointments.create","dashboard.view.all"}
        self.assertTrue(expected <= set(ROLE_PERMISSION_MAP["admin"]))
        self.assertTrue(expected <= set(ALL_PERMISSION_CODES))
    def test_sale_and_leader_scopes(self):
        self.assertIn("dashboard.view.own",ROLE_PERMISSION_MAP["sale"])
        self.assertIn("lead_tasks.complete.own",ROLE_PERMISSION_MAP["sale"])
        self.assertIn("dashboard.view.team",ROLE_PERMISSION_MAP["leader"])
        self.assertIn("lead_appointments.complete.team",ROLE_PERMISSION_MAP["leader"])
if __name__=='__main__':unittest.main()
