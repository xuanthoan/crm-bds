import unittest
from app.permissions.constants import CONTRACT_PERMISSIONS,PERMISSION_CODES_BY_MODULE,ROLE_PERMISSION_MAP
class Sprint12ContractPermissionsTest(unittest.TestCase):
 def test_vocabulary(self):
  self.assertEqual(PERMISSION_CODES_BY_MODULE["contracts"],CONTRACT_PERMISSIONS)
  for action in ("view","update","status","delete"):
   for scope in ("own","team","department","all"):self.assertIn(f"contracts.{action}.{scope}",CONTRACT_PERMISSIONS)
  for action in ("view","update","confirm"):
   for scope in ("own","team","department","all"):self.assertIn(f"contracts.payment.{action}.{scope}",CONTRACT_PERMISSIONS)
 def test_role_mapping(self):
  self.assertTrue(set(CONTRACT_PERMISSIONS)<=set(ROLE_PERMISSION_MAP["admin"]))
  self.assertIn("contracts.view.all",ROLE_PERMISSION_MAP["director"]);self.assertNotIn("contracts.delete.all",ROLE_PERMISSION_MAP["director"])
  self.assertIn("contracts.status.department",ROLE_PERMISSION_MAP["sales_manager"]);self.assertIn("contracts.payment.confirm.team",ROLE_PERMISSION_MAP["leader"])
  self.assertIn("contracts.update.own",ROLE_PERMISSION_MAP["sale"]);self.assertNotIn("contracts.payment.confirm.own",ROLE_PERMISSION_MAP["sale"])
  self.assertIn("contracts.view.own",ROLE_PERMISSION_MAP["viewer"])
if __name__=="__main__":unittest.main()
