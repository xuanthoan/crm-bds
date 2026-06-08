import unittest
from datetime import date, timedelta

from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerRelatedPersonCreate


class Sprint9CustomerProfileValidationTests(unittest.TestCase):
    def base(self, **values):
        return CustomerCreate(full_name="Nguyễn Văn A", primary_phone="0901234567", **values)

    def assert_invalid(self, message, **values):
        with self.assertRaises(ValidationError) as context:
            self.base(**values)
        self.assertIn(message, str(context.exception))

    def test_empty_optional_values_become_none(self):
        customer = self.base(email="", expected_budget="", buying_purpose="")
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.expected_budget)
        self.assertIsNone(customer.buying_purpose)

    def test_financial_and_enum_validation(self):
        self.assert_invalid("Giá trị tài chính không hợp lệ", available_cash=-1)
        self.assert_invalid("Tỷ lệ vay phải từ 0 đến 100", loan_ratio=101)
        self.assert_invalid("Xếp hạng tài chính không hợp lệ", financial_rating="E")
        self.assert_invalid("Mục đích mua không hợp lệ", buying_purpose="holiday")
        self.assert_invalid("Loại hình quan tâm không hợp lệ", interested_property_type="office")
        self.assert_invalid("Timeline mua không hợp lệ", buying_timeline="tomorrow")

    def test_birth_date_phone_email_and_relationship_validation(self):
        self.assert_invalid("Ngày sinh không hợp lệ", date_of_birth=date.today() + timedelta(days=1))
        self.assert_invalid("Số điện thoại không hợp lệ", secondary_phone="123")
        self.assert_invalid("Email không hợp lệ", email="invalid")
        with self.assertRaises(ValidationError) as context:
            CustomerRelatedPersonCreate(full_name="B", relationship="boss", phone="0901234567")
        self.assertIn("Mối quan hệ không hợp lệ", str(context.exception))


if __name__ == "__main__":
    unittest.main()
