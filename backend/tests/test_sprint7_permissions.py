import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = runpy.run_path(ROOT / "backend/app/permissions/constants.py")
MODULES = CONSTANTS["PERMISSION_CODES_BY_MODULE"]
ROLES = CONSTANTS["ROLE_PERMISSION_MAP"]
CUSTOMER_SERVICE = (ROOT / "backend/app/services/customer_service.py").read_text()
CUSTOMER_MODEL = (ROOT / "backend/app/models/customer.py").read_text()
CUSTOMER_MIGRATION = (ROOT / "backend/alembic/versions/20260608_0005_customer_360_conversion.py").read_text()
LEAD_CONSTANTS = runpy.run_path(ROOT / "backend/app/leads/constants.py")
FRONTEND_LEAD_CONSTANTS = (ROOT / "frontend/src/features/leads/constants.ts").read_text()


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

    def test_converted_status_has_vietnamese_label_everywhere(self):
        self.assertEqual("Đã chuyển đổi", LEAD_CONSTANTS["LEAD_STATUS_LABELS"]["converted"])
        self.assertIn("converted: 'Đã chuyển đổi'", FRONTEND_LEAD_CONSTANTS)

    def test_customer_code_is_unique_and_sequence_todo_is_documented(self):
        self.assertIn('customer_code: Mapped[str] = mapped_column(String(30), unique=True', CUSTOMER_MODEL)
        self.assertIn('sa.Column("customer_code", sa.String(30), nullable=False, unique=True)', CUSTOMER_MIGRATION)
        self.assertIn('return f"CUS-{max(numbers, default=0) + 1:06d}"', CUSTOMER_SERVICE)
        self.assertIn("TODO: Replace with database sequence for high-concurrency production.", CUSTOMER_SERVICE)

    def test_duplicate_phone_check_covers_both_columns_and_ignores_deleted_rows(self):
        self.assertIn("Customer.deleted_at.is_(None)", CUSTOMER_SERVICE)
        self.assertIn("Customer.primary_phone.in_(phones)", CUSTOMER_SERVICE)
        self.assertIn("Customer.secondary_phone.in_(phones)", CUSTOMER_SERVICE)
        self.assertIn("Số điện thoại khách hàng đã tồn tại", CUSTOMER_SERVICE)

    def test_soft_delete_and_owner_history_are_preserved(self):
        self.assertIn("customer.deleted_at = datetime.now(timezone.utc)", CUSTOMER_SERVICE)
        self.assertIn("customer.deleted_by_id = actor.id", CUSTOMER_SERVICE)
        self.assertNotIn("db.delete(customer)", CUSTOMER_SERVICE)
        self.assertIn('"owner_change",', CUSTOMER_SERVICE)
        self.assertIn('"Đổi người phụ trách",', CUSTOMER_SERVICE)
        self.assertIn("old_owner_name", CUSTOMER_SERVICE)
        self.assertIn("new_owner.full_name", CUSTOMER_SERVICE)

    def test_conversion_preserves_bidirectional_links_and_both_timelines(self):
        self.assertIn("source_lead_id=lead.id", CUSTOMER_SERVICE)
        self.assertIn("lead.converted_customer_id = customer.id", CUSTOMER_SERVICE)
        self.assertIn('"conversion", "Chuyển đổi từ lead"', CUSTOMER_SERVICE)
        self.assertIn('title="Chuyển đổi khách hàng"', CUSTOMER_SERVICE)


if __name__ == "__main__":
    unittest.main()
