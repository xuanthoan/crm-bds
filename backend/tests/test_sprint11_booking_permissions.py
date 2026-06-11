import unittest
from app.permissions.constants import PERMISSION_CODES_BY_MODULE, ROLE_PERMISSION_MAP

class Sprint11BookingPermissionTests(unittest.TestCase):
    def test_permission_vocabulary(self):
        codes=set(PERMISSION_CODES_BY_MODULE["bookings"])
        self.assertEqual(21,len(codes)); self.assertIn("bookings.create",codes)
        for action in ("view","update","status","delete","refund"):
            for scope in ("own","team","department","all"): self.assertIn(f"bookings.{action}.{scope}",codes)
    def test_default_role_assignment(self):
        codes=set(PERMISSION_CODES_BY_MODULE["bookings"]); self.assertTrue(codes.issubset(ROLE_PERMISSION_MAP["admin"]))
        for code in ("bookings.view.all","bookings.update.all","bookings.status.all","bookings.refund.all"): self.assertIn(code,ROLE_PERMISSION_MAP["director"])
        self.assertNotIn("bookings.delete.all",ROLE_PERMISSION_MAP["director"])
        self.assertIn("bookings.refund.department",ROLE_PERMISSION_MAP["sales_manager"]); self.assertIn("bookings.refund.team",ROLE_PERMISSION_MAP["leader"])
        self.assertIn("bookings.status.own",ROLE_PERMISSION_MAP["sale"]); self.assertNotIn("bookings.refund.own",ROLE_PERMISSION_MAP["sale"]); self.assertEqual(["bookings.view.own"], [p for p in ROLE_PERMISSION_MAP["viewer"] if p.startswith("bookings.")])
if __name__=="__main__": unittest.main()
