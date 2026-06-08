import unittest
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.customer import CustomerCreate


class Sprint7CustomerValidationTests(unittest.TestCase):
    def test_only_name_and_phone_is_valid(self):
        customer = CustomerCreate(full_name="Khách hàng A", primary_phone="0987332499")
        self.assertEqual("0987332499", customer.primary_phone)
        self.assertIsNone(customer.email)

    def test_empty_email_is_optional(self):
        for email in ("", "   "):
            with self.subTest(email=email):
                customer = CustomerCreate(full_name="Khách hàng A", primary_phone="0987 332 499", email=email)
                self.assertEqual("0987332499", customer.primary_phone)
                self.assertIsNone(customer.email)

    def test_valid_email_is_accepted(self):
        customer = CustomerCreate(full_name="Khách hàng A", primary_phone="0987332499", email="test@gmail.com")
        self.assertEqual("test@gmail.com", customer.email)

    def test_invalid_email_has_clear_message(self):
        for email in ("xada@g,ail.com", "abc", "test@", "@gmail.com", "test@gmail"):
            with self.subTest(email=email), self.assertRaisesRegex(ValidationError, "Email không hợp lệ"):
                CustomerCreate(full_name="Khách hàng A", primary_phone="0987332499", email=email)

    def test_phone_formats_and_invalid_values(self):
        accepted = ("0987332499", "0987 332 499", "0987-332-499", "+84987332499", "84 987332499")
        for phone in accepted:
            with self.subTest(phone=phone):
                self.assertEqual("0987332499", CustomerCreate(full_name="Khách hàng A", primary_phone=phone).primary_phone)
        for phone in ("098733249999", "0987", "abc123"):
            with self.subTest(phone=phone), self.assertRaisesRegex(ValidationError, "Số điện thoại không hợp lệ"):
                CustomerCreate(full_name="Khách hàng A", primary_phone=phone)

    def test_all_fields_filled_is_valid(self):
        customer = CustomerCreate(
            full_name="Khách hàng A",
            primary_phone="+84987332499",
            secondary_phone="0987-332-498",
            email="test@gmail.com",
            customer_type="individual",
            status="active",
            source="facebook_ads",
            interested_project="Vinhomes Ocean Park",
            interested_area="Gia Lâm",
            budget_min="1000000000",
            budget_max="2000000000",
            bedroom_count="2",
            area_min="55.5",
            area_max="75.5",
            purpose="buy_to_live",
            next_follow_up_at="2026-06-10T09:00:00Z",
            note="Đã xác nhận nhu cầu",
        )
        self.assertEqual("0987332499", customer.primary_phone)
        self.assertEqual("0987332498", customer.secondary_phone)
        self.assertEqual("test@gmail.com", customer.email)
        self.assertEqual(Decimal("1000000000"), customer.budget_min)
        self.assertEqual(2, customer.bedroom_count)

    def test_all_optional_empty_strings_are_valid(self):
        customer = CustomerCreate(
            full_name="Khách hàng A",
            primary_phone="0987332499",
            secondary_phone="",
            email="",
            source="",
            interested_project="",
            interested_area="",
            budget_min="",
            budget_max="",
            bedroom_count="",
            area_min="",
            area_max="",
            purpose="",
            next_follow_up_at="",
            note="",
        )
        self.assertIsNone(customer.email)
        self.assertIsNone(customer.secondary_phone)
        self.assertIsNone(customer.budget_min)
        self.assertIsNone(customer.bedroom_count)
        self.assertIsNone(customer.purpose)


if __name__ == "__main__":
    unittest.main()
