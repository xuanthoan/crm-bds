from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src"
DOCS = ROOT / "docs"


class Sprint31DuplicateLeadOwnershipSourceTests(unittest.TestCase):
    def b(self, rel): return (BACKEND / rel).read_text(encoding="utf-8")
    def f(self, rel): return (FRONTEND / rel).read_text(encoding="utf-8")
    def d(self, rel): return (DOCS / rel).read_text(encoding="utf-8")

    def test_phone_normalization(self):
        from app.services.phone_service import normalize_phone
        self.assertEqual(normalize_phone("0912345678"), normalize_phone("0912 345 678"))
        self.assertEqual(normalize_phone("0912345678"), normalize_phone("0912.345.678"))
        self.assertEqual(normalize_phone("0912345678"), normalize_phone("0912-345-678"))
        self.assertEqual(normalize_phone("0912345678"), normalize_phone("+84912345678"))
        self.assertEqual(normalize_phone("0912345678"), normalize_phone("84912345678"))
        self.assertIsNone(normalize_phone(None))
        self.assertIsNone(normalize_phone("  "))

    def test_models_and_migration_support_shared_customer_journeys(self):
        lead = self.b("app/models/lead.py")
        customer = self.b("app/models/customer.py")
        migration = self.b("alembic/versions/20260708_0022_duplicate_lead_ownership.py")
        for source in (lead, customer, migration):
            for name in ("phone_primary_normalized", "phone_secondary_normalized"):
                self.assertIn(name, source)
        for name in ("customer_id", "duplicate_of_customer_id", "duplicate_detected", "duplicate_match_reason"):
            self.assertIn(name, lead + migration)
        for name in ("first_lead_id", "first_touch_user_id", "first_uploaded_at", "first_upload_note", "is_duplicate_profile"):
            self.assertIn(name, customer + migration)
        self.assertNotIn("unique=True", migration.lower())

    def test_duplicate_detection_rules_only_use_primary_secondary_phone(self):
        service = self.b("app/services/duplicate_lead_service.py")
        for reason in ("phone_primary_to_phone_primary", "phone_primary_to_phone_secondary", "phone_secondary_to_phone_primary", "phone_secondary_to_phone_secondary"):
            self.assertIn(reason.split("_to_")[0], service)
            self.assertIn(reason.split("_to_")[1], service)
        self.assertIn("detect_duplicate_customer", service)
        self.assertIn("normalize_phone", service)
        self.assertIn("Email/Zalo/Facebook không dùng", service)
        self.assertNotIn("email ==", service.lower())
        self.assertNotIn("zalo ==", service.lower())
        self.assertNotIn("facebook ==", service.lower())

    def test_create_lead_duplicate_links_to_common_customer_and_audits(self):
        service = self.b("app/services/lead_service.py")
        for snippet in ("detect_duplicate_customer", "customer_id=customer.id", "duplicate_detected=duplicate.is_duplicate", "duplicate_of_customer_id", "duplicate_match_reason", "leads.duplicate_detected", "Phát hiện khách hàng trùng"):
            self.assertIn(snippet, service)
        self.assertIn("customers.create", service)
        self.assertIn("first_upload_note", service)
        self.assertNotIn("_ensure_phone_unique(db, primary, secondary)\n    owner_id", service)
        self.assertIn("duplicate_info", service)
        audit = self.b("app/services/audit_service.py")
        self.assertIn("json_safe", audit)
        self.assertIn("before_data=json_safe(before_data)", audit)
        self.assertIn("after_data=json_safe(after_data)", audit)
        self.assertIn("Lead mới đã được liên kết vào hồ sơ khách hàng chung", service)

    def test_customer_profile_visibility_and_team_scoped_journey_privacy(self):
        service = self.b("app/services/customer_service.py")
        for snippet in ("Lead.customer_id == customer.id", "_visible_journey_leads", "can_view_lead(db, actor, lead)", "can_view_all_journeys", "duplicate_visibility", "journey_leads"):
            self.assertIn(snippet, service)
        for common_field in ("primary_phone", "secondary_phone", "email", "zalo", "facebook", "address", "interested_project", "expected_budget", "related_people", "score_total", "first_upload_note"):
            self.assertIn(common_field, service)
        self.assertIn("Bạn chỉ thấy chi tiết hành trình thuộc phạm vi quyền của mình", service)
        self.assertIn("Bạn đang xem toàn bộ hành trình", service)

    def test_frontend_duplicate_warning_and_customer_banner(self):
        form = self.f("features/leads/LeadFormModal.tsx")
        page = self.f("features/leads/LeadsPage.tsx")
        detail = self.f("features/customers/CustomerDetailPage.tsx")
        types = self.f("features/customers/types.ts")
        for snippet in ("Số điện thoại này đã tồn tại", "hồ sơ khách hàng chung"):
            self.assertIn(snippet, form + page)
        for snippet in ("duplicate_visibility", "Khách trùng / Có nhiều hành trình", "Ghi chú upload ban đầu", "Khách có hành trình khác ngoài phạm vi quyền của bạn"):
            self.assertIn(snippet, detail + types)
        self.assertNotIn("team khác được xem toàn bộ journey", detail.lower())


    def test_audit_json_safe_for_nested_uuid_datetime_decimal(self):
        audit = self.b("app/services/audit_service.py")
        for snippet in ("def json_safe", "isinstance(value, UUID)", "isinstance(value, (datetime, date))", "isinstance(value, Decimal)", "if isinstance(value, dict)", "if isinstance(value, (list, tuple, set))"):
            self.assertIn(snippet, audit)
        self.assertIn("before_data=json_safe(before_data)", audit)
        self.assertIn("after_data=json_safe(after_data)", audit)

    def test_task_lead_id_filter_contract(self):
        api = self.b("app/api/v1/tasks.py")
        service = self.b("app/services/task_service.py")
        frontend_api = self.f("features/tasks/api.ts")
        lead_detail = self.f("features/leads/LeadDetailPage.tsx")
        self.assertIn('lead_id:UUID|None=Query(None,alias="lead_id")', api)
        self.assertIn("related_lead_id=lead_filter", api)
        self.assertIn('("lead_id",Task.related_lead_id)', service)
        self.assertIn('("related_lead_id",Task.related_lead_id)', service)
        self.assertIn("lead_id?:string", frontend_api)
        self.assertIn("listTasks({lead_id:leadId,page_size:10})", lead_detail)
        self.assertIn("Chưa có công việc nào cho lead này.", lead_detail)

    def test_api_client_distinguishes_http_500_from_network_error(self):
        api_client = self.f("services/apiClient.ts")
        self.assertIn("SERVER_ERROR_MESSAGE", api_client)
        self.assertIn("response.status >= 500", api_client)
        self.assertIn("Không kết nối được máy chủ", api_client)
        self.assertIn("Có lỗi máy chủ khi xử lý yêu cầu", api_client)

    def test_revenue_rule_documented_and_not_first_touch_commission(self):
        docs = self.d("BUSINESS_RULES.md")
        self.assertIn("Doanh số và hoa hồng tính cho sale/team/phòng chốt hợp đồng", docs)
        self.assertIn("First uploader không mặc định", docs)
        self.assertIn("contract/deal winning owner", docs)
        self.assertIn("không tách database", docs.lower())


if __name__ == "__main__":
    unittest.main()
