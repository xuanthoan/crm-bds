import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def normalize_search_text(value: str) -> str:
    import unicodedata
    text = ''.join(ch for ch in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(ch))
    return text.replace('đ', 'd')


class Sprint261SalesPlaybookRealEstateHelpSourceTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding='utf-8')

    def test_help_sales_playbook_sections_exist(self):
        content = self.read('frontend/src/features/help/helpContent.ts')
        for text in [
            'Cẩm nang sale BĐS',
            'Checklist tư vấn khách hàng',
            'Cách phân loại khách hàng',
            'Nguyên tắc follow-up khách hàng',
            'Mẫu ghi chú sale chuẩn',
            'Lý do mất khách thường gặp',
            'Lỗi thường gặp của sale',
            'Quy trình từ lead đến hợp đồng',
            'Bộ hướng dẫn nhanh giúp sale chăm sóc khách hàng bất động sản bài bản hơn.',
            'Bao gồm: checklist tư vấn khách, phân loại khách nóng/ấm/lạnh, nguyên tắc follow-up, mẫu ghi chú sale, lý do mất khách và các lỗi sale cần tránh.',
            'Lưu ý: Nội dung này là hướng dẫn nghiệp vụ phổ thông trong CRM, không phải tư vấn pháp lý chính thức.',
        ]:
            self.assertIn(text, content)

    def test_glossary_real_estate_groups_and_terms_exist(self):
        content = self.read('frontend/src/features/help/helpContent.ts')
        for group in ['Bất động sản', 'Chăm sóc khách hàng', 'Marketing & nguồn lead']:
            self.assertIn(group, content)
        for term in [
            'Chủ đầu tư', 'Sổ đỏ', 'Sổ hồng', 'Pháp lý dự án', 'Tiến độ thanh toán',
            'Diện tích thông thủy', 'Diện tích tim tường', 'Khách nóng', 'Khách ấm',
            'Khách lạnh', 'Follow-up', 'Lead quá hạn', 'Trùng khách',
            'Người quyết định chính', 'CPL', 'ROI quảng cáo',
        ]:
            self.assertIn(term, content)

    def test_glossary_new_terms_preserve_accent_insensitive_search_targets(self):
        content = self.read('frontend/src/features/help/helpContent.ts')
        terms = re.findall(r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"', content)
        normalized_terms = {normalize_search_text(term): term for term, _group, _description in terms}
        expected = {
            'so do': 'Sổ đỏ',
            'so hong': 'Sổ hồng',
            'phap ly du an': 'Pháp lý dự án',
            'dien tich thong thuy': 'Diện tích thông thủy',
            'khach nong': 'Khách nóng',
            'trung khach': 'Trùng khách',
            'nguoi quyet dinh chinh': 'Người quyết định chính',
        }
        for query, term in expected.items():
            self.assertEqual(normalized_terms[query], term)

    def test_sale_guide_boxes_added_to_lead_pages(self):
        leads = self.read('frontend/src/features/leads/LeadsPage.tsx')
        overdue = self.read('frontend/src/features/leads/OverdueLeadsPage.tsx')
        self.assertIn('Cách chăm sóc lead hiệu quả', leads)
        self.assertIn('Cách xử lý lead quá hạn', overdue)
        self.assertIn('GuideBox', leads)
        self.assertIn('GuideBox', overdue)


if __name__ == '__main__':
    unittest.main()
