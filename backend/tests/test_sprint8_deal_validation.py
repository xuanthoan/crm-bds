import unittest
from pydantic import ValidationError
from app.schemas.deal import DealCreate, DealStageUpdate, DealStatusUpdate

IDS={'customer_id':'11111111-1111-1111-1111-111111111111','owner_id':'22222222-2222-2222-2222-222222222222'}
class Sprint8DealValidationTests(unittest.TestCase):
    def make(self,**kwargs): return DealCreate(**IDS,title='Căn hộ A',**kwargs)
    def test_defaults_and_blank_normalization(self):
        deal=self.make(description='',expected_value=''); self.assertEqual('new',deal.pipeline_stage); self.assertEqual('open',deal.status); self.assertIsNone(deal.description); self.assertIsNone(deal.expected_value)
    def test_non_negative_money(self):
        for value in ('abc','-1','NaN'):
            with self.subTest(value=value),self.assertRaisesRegex(ValidationError,'Giá trị tiền không hợp lệ'): self.make(expected_value=value)
    def test_contract_not_less_than_deposit(self):
        with self.assertRaisesRegex(ValidationError,'Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc'): self.make(deposit_amount=100,contract_value=99)
    def test_enums(self):
        with self.assertRaisesRegex(ValidationError,'Giai đoạn giao dịch không hợp lệ'): self.make(pipeline_stage='bad')
        with self.assertRaisesRegex(ValidationError,'Trạng thái giao dịch không hợp lệ'): self.make(status='bad')
        with self.assertRaisesRegex(ValidationError,'Ưu tiên không hợp lệ'): self.make(priority='bad')
    def test_lost_requires_reason(self):
        with self.assertRaisesRegex(ValidationError,'Vui lòng nhập lý do thất bại/hủy giao dịch'): DealStatusUpdate(status='lost')
        with self.assertRaisesRegex(ValidationError,'Vui lòng nhập lý do thất bại/hủy giao dịch'): DealStageUpdate(pipeline_stage='lost')
if __name__=='__main__': unittest.main()
