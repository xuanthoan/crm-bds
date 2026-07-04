import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Sprint26UserGuideBusinessGlossarySourceTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_routes_and_menu_exist(self):
        routes = self.read("frontend/src/routes/AppRoutes.tsx")
        layout = self.read("frontend/src/layouts/AppLayout.tsx")
        self.assertIn("'/help'", routes)
        self.assertIn("<HelpPage />", routes)
        self.assertIn("'/glossary'", routes)
        self.assertIn("<GlossaryPage />", routes)
        self.assertIn("Hướng dẫn", layout)
        self.assertIn("Từ điển nghiệp vụ", layout)
        self.assertIn("Trợ giúp", layout)

    def test_required_glossary_terms_exist(self):
        content = self.read("frontend/src/features/help/helpContent.ts")
        for term in [
            "Hoa hồng công ty",
            "Hoa hồng sale",
            "Phiếu chi hoa hồng",
            "Đối soát hoa hồng",
            "Bị chặn theo chính sách",
            "Có phiếu nháp",
            "Hạn mức còn có thể chi",
        ]:
            self.assertIn(term, content)
        self.assertGreaterEqual(content.count("description"), 0)
        self.assertGreaterEqual(content.count("['"), 30)

    def test_tooltips_and_guide_boxes_added_to_commission_modules(self):
        expected_files = [
            "frontend/src/features/commissions/CommissionsPage.tsx",
            "frontend/src/features/companyCommissions/CompanyCommissionsPage.tsx",
            "frontend/src/features/commissionPaymentVouchers/CommissionPaymentVouchersPage.tsx",
            "frontend/src/features/commissionReconciliationReport/CommissionReconciliationReportPage.tsx",
        ]
        for relative_path in expected_files:
            source = self.read(relative_path)
            self.assertIn("GuideBox", source, relative_path)
            self.assertIn("tooltipTexts", source, relative_path)
            self.assertTrue("HelpLabel" in source or "HelpTooltip" in source, relative_path)


if __name__ == "__main__":
    unittest.main()
