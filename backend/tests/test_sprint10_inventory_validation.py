import ast
import unittest
from pathlib import Path
from pydantic import ValidationError
from app.schemas.project import ProjectCreate
from app.schemas.property_unit import PropertyPriceUpdate,PropertyUnitCreate
class Sprint10InventoryValidationTests(unittest.TestCase):
    def base(self,**values):
        payload={'title':'Căn A01','property_type':'apartment'};payload.update(values);return PropertyUnitCreate(**payload)
    def invalid(self,message,**values):
        with self.assertRaises(ValidationError) as context:self.base(**values)
        self.assertIn(message,str(context.exception))
    def test_required_and_enum_validation(self):
        with self.assertRaises(ValidationError) as context:PropertyUnitCreate(title='',property_type='apartment')
        self.assertIn('Tên bất động sản là bắt buộc',str(context.exception))
        self.invalid('Loại bất động sản không hợp lệ',property_type='castle');self.invalid('Trạng thái kho hàng không hợp lệ',inventory_status='hidden');self.invalid('Trạng thái pháp lý không hợp lệ',legal_status='pending')
        with self.assertRaises(ValidationError) as context:ProjectCreate(name=' ',project_type='urban_area')
        self.assertIn('Tên dự án là bắt buộc',str(context.exception))
    def test_numeric_contact_and_price_validation(self):
        self.invalid('Giá trị không hợp lệ',listed_price=-1);self.invalid('Diện tích không hợp lệ',area_net=-1);self.invalid('Tỷ lệ hoa hồng phải từ 0 đến 100',commission_rate=101)
        self.invalid('Số điện thoại không hợp lệ',owner_phone='123');self.invalid('Email không hợp lệ',owner_email='bad')
        self.invalid('Giá tối thiểu không được lớn hơn giá niêm yết',listed_price=100,minimum_price=101)
    def test_optional_blanks_and_price_payload(self):
        item=self.base(owner_email='',owner_phone='',project_id='');self.assertIsNone(item.owner_email);self.assertIsNone(item.owner_phone);self.assertIsNone(item.project_id)
        with self.assertRaises(ValidationError) as context:PropertyPriceUpdate(listed_price=-1)
        self.assertIn('Giá trị không hợp lệ',str(context.exception))
    def test_models_do_not_shadow_relationship(self):
        for filename in ('property_price_history.py','property_status_history.py'):
            tree=ast.parse(Path('backend/app/models',filename).read_text());names={n.target.id for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)};self.assertNotIn('relationship',names)
if __name__=='__main__':unittest.main()
