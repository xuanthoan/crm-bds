import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = runpy.run_path(ROOT / "backend/app/permissions/constants.py")
MODULES = CONSTANTS["PERMISSION_CODES_BY_MODULE"]
ROLES = CONSTANTS["ROLE_PERMISSION_MAP"]


class Sprint7PermissionTests(unittest.TestCase):
    def test_customer_permissions_are_explicit(self):
        expected = {
            "customers.view.own", "customers.view.team", "customers.view.department", "customers.view.all",
            "customers.create", "customers.update.own", "customers.update.team", "customers.update.department", "customers.update.all",
            "customers.delete", "customers.assign.own", "customers.assign.team", "customers.assign.department", "customers.assign.all",
            "customers.add_activity.own", "customers.add_activity.team", "customers.add_activity.department", "customers.add_activity.all",
        }
        self.assertEqual(expected, set(MODULES["customers"]))

    def test_conversion_permissions_and_role_scopes(self):
        for scope in ("own", "team", "department", "all"):
            self.assertIn(f"leads.convert.{scope}", MODULES["leads"])
        self.assertIn("leads.convert.all", ROLES["director"])
        self.assertIn("leads.convert.department", ROLES["sales_manager"])
        self.assertIn("leads.convert.team", ROLES["leader"])
        self.assertIn("leads.convert.own", ROLES["sale"])
        self.assertNotIn("leads.convert.own", ROLES["viewer"])

    def test_admin_receives_every_permission(self):
        expected = {code for codes in MODULES.values() for code in codes}
        self.assertEqual(expected, set(ROLES["admin"]))


if __name__ == "__main__":
    unittest.main()
