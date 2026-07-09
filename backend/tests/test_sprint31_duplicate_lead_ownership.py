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

    def test_duplicate_check_endpoint_contract(self):
        api = self.b("app/api/v1/leads.py")
        service = self.b("app/services/lead_service.py")
        duplicate_service = self.b("app/services/duplicate_lead_service.py")
        self.assertIn('@router.get("/duplicate-check")', api)
        self.assertIn("check_lead_duplicate", api + service)
        self.assertIn("is_duplicate", service)
        self.assertIn("matched_phone", service)
        self.assertIn("match_reason", service)
        self.assertIn("open_url", service)
        self.assertIn("can_view_other_journeys", service)
        self.assertIn("normalize_phone(phone_primary)", duplicate_service)
        self.assertIn("normalize_phone(phone_secondary)", duplicate_service)

    def test_create_lead_duplicate_reengages_existing_customer_without_new_lead(self):
        service = self.b("app/services/lead_service.py")
        api = self.b("app/api/v1/leads.py")
        for snippet in ("detect_duplicate_customer", "record_duplicate_reengagement", "existing_customer_reengaged", "leads.duplicate_reengaged", "duplicate_info", "Tiếp cận lại khách trùng"):
            self.assertIn(snippet, service + api)
        self.assertIn("if duplicate.is_duplicate:\n        return record_duplicate_reengagement", service)
        self.assertLess(service.index("if duplicate.is_duplicate:"), service.index("lead = Lead(**payload"))
        self.assertIn("CustomerActivity", service)
        self.assertIn("last_contact_at = now", service)
        self.assertIn("updated_at = now", service)
        self.assertNotIn("leads.duplicate_detected", service)
        audit = self.b("app/services/audit_service.py")
        self.assertIn("json_safe", audit)
        self.assertIn("before_data=json_safe(before_data)", audit)
        self.assertIn("after_data=json_safe(after_data)", audit)

    def test_customer_profile_visibility_and_team_scoped_journey_privacy(self):
        service = self.b("app/services/customer_service.py")
        for snippet in ("Lead.customer_id == customer.id", "_visible_journey_leads", "can_view_lead(db, actor, lead)", "can_view_all_journeys", "duplicate_visibility", "journey_leads"):
            self.assertIn(snippet, service)
        for common_field in ("primary_phone", "secondary_phone", "email", "zalo", "facebook", "address", "interested_project", "expected_budget", "related_people", "score_total", "first_upload_note"):
            self.assertIn(common_field, service)
        self.assertIn("Bạn chỉ thấy chi tiết hành trình thuộc phạm vi quyền của mình", service)
        self.assertIn("Bạn đang xem toàn bộ hành trình", service)

    def test_frontend_duplicate_modal_no_browser_alert_and_blur_check(self):
        form = self.f("features/leads/LeadFormModal.tsx")
        page = self.f("features/leads/LeadsPage.tsx")
        api = self.f("features/leads/api.ts")
        detail = self.f("features/customers/CustomerDetailPage.tsx")
        customer_types = self.f("features/customers/types.ts")
        lead_types = self.f("features/leads/types.ts")
        for snippet in ("Số điện thoại đã tồn tại", "Mở thông tin", "Đóng", "Đóng, không lưu", "checkDuplicateOnBlur", "checkLeadDuplicate(phone)", "existing_customer_reengaged", "duplicateInfo?.is_duplicate", "duplicateModalOpen"):
            self.assertIn(snippet, form + api + lead_types)
        for label in ("Số điện thoại chính trùng với số điện thoại chính đã có", "Số điện thoại chính trùng với số điện thoại phụ đã có", "Số điện thoại phụ trùng với số điện thoại chính đã có", "Số điện thoại phụ trùng với số điện thoại phụ đã có", "Đã ghi nhận lượt tiếp cận lại khách hàng hiện có", "Tiếp cận lại khách hàng trùng"):
            self.assertIn(label, form)
        self.assertIn("Không thể lưu lead mới vì số điện thoại đã tồn tại trong hệ thống", form)
        self.assertIn("setDuplicateModalOpen(false)", form)
        self.assertNotIn("onClose={()=>setDuplicateInfo(null)}", form)
        self.assertNotIn("window.alert", form + page)
        self.assertNotIn("alert(", form + page)
        self.assertIn("if ((response.data as any).duplicate_info?.is_duplicate) return response", page)
        for snippet in ("duplicate_visibility", "Khách trùng / Có nhiều hành trình", "Ghi chú upload ban đầu", "Khách có hành trình khác ngoài phạm vi quyền của bạn"):
            self.assertIn(snippet, detail + customer_types)
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
