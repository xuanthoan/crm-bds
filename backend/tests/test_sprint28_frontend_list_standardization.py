from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


class Sprint28FrontendListStandardizationTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (FRONTEND / relative).read_text(encoding="utf-8")

    def test_shared_pagination_component_contains_smart_page_logic(self):
        source = self.read("components/common/Pagination.tsx")
        self.assertIn("export function Pagination", source)
        self.assertIn("export function getPaginationItems", source)
        self.assertRegex(source, r"safeTotal\s*<=\s*7")
        self.assertIn("'ellipsis'", source)
        self.assertIn("new Set<number>([1, safeTotal])", source)
        self.assertIn("aria-current", source)
        self.assertIn("disabled={loading || safeCurrent <= 1}", source)
        self.assertIn("disabled={loading || safeCurrent >= safeTotal}", source)
        self.assertIn("Trang {safeCurrent} / {safeTotal}", source)

    def test_priority_list_pages_use_shared_pagination_or_equivalent_audit_adapter(self):
        pages = [
            "features/leads/LeadsPage.tsx",
            "features/customers/CustomersPage.tsx",
            "features/deals/DealsPage.tsx",
            "features/bookings/BookingsPage.tsx",
            "features/contracts/ContractsPage.tsx",
            "features/companyCommissions/CompanyCommissionsPage.tsx",
            "features/commissions/CommissionsPage.tsx",
            "features/commissionPaymentVouchers/CommissionPaymentVouchersPage.tsx",
            "features/commissionReconciliationReport/CommissionReconciliationReportPage.tsx",
            "features/auditLogs/AuditLogsPage.tsx",
        ]
        for page in pages:
            with self.subTest(page=page):
                source = self.read(page)
                self.assertIn("Pagination", source)
                self.assertNotRegex(source, r"undefined\.map")

    def test_filter_actions_reset_to_first_page_and_empty_state_exists(self):
        checked_pages = [
            "features/commissionPaymentVouchers/CommissionPaymentVouchersPage.tsx",
            "features/commissionReconciliationReport/CommissionReconciliationReportPage.tsx",
            "features/commissions/CommissionsPage.tsx",
            "features/companyCommissions/CompanyCommissionsPage.tsx",
            "features/auditLogs/AuditLogsPage.tsx",
        ]
        for page in checked_pages:
            with self.subTest(page=page):
                source = self.read(page)
                self.assertIn("page:'1'", source.replace(" ", ""))
                self.assertIn("Xóa lọc", source)
                self.assertRegex(source, r"Không có dữ liệu phù hợp|Chưa có dữ liệu")

    def test_pagination_css_wraps_on_small_screens(self):
        css = self.read("../styles.css") if False else (FRONTEND / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".pagination", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn("@media (max-width: 600px)", css)


if __name__ == "__main__":
    unittest.main()
