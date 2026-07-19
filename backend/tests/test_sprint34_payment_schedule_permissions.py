import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

class Sprint34PaymentSchedulePermissionSourceTest(unittest.TestCase):
    def test_contract_payment_schedules_call_has_consistent_date_args(self):
        api = read('backend/app/api/v1/payments.py')
        service = read('backend/app/services/payment_service.py')
        self.assertIn('date_from:date|None=None', api)
        self.assertIn('date_to:date|None=None', api)
        self.assertIn('def list_schedules(db,actor,page=1,page_size=20,q=None,status=None,contract_id=None,deal_id=None,customer_id=None,overdue=None,date_from=None,date_to=None):', service)
        self.assertIn('list_schedules(db,actor,page=1,page_size=100,contract_id=contract_id)', api)
        self.assertIn('PaymentSchedule.due_date >= date_from', service)
        self.assertIn('PaymentSchedule.due_date <= date_to', service)
        self.assertIn('def list_invoices(db,actor,page=1,page_size=20,q=None,status=None,date_from=None,date_to=None):', service)
        self.assertIn('PaymentInvoice.created_at >= datetime.combine(date_from', service)

    def test_create_schedule_respects_business_role_scope(self):
        service = read('backend/app/services/payment_service.py')
        self.assertIn("roles & {'admin', 'director'}: return 'all'", service)
        self.assertIn("if 'sales_manager' in roles: return 'department'", service)
        self.assertIn("if 'leader' in roles: return 'team'", service)
        self.assertIn("if 'sale' in roles: return 'own'", service)
        self.assertIn('get_accessible_user_ids_for_lead_scope(db, actor, scope)', service)
        self.assertIn('contract.deal.owner_id', service)
        self.assertIn('contract.booking.assigned_user_id', service)
        self.assertIn('_require_schedule_write_access(db, actor, c, \'payments.create\')', service)
        self.assertNotIn("if not _can_write(actor,'payments.create'): raise HTTPException(403,'Bạn không có quyền tạo lịch thanh toán')", service)

    def test_frontend_no_permission_state_hides_enabled_create_controls(self):
        form = read('frontend/src/features/payments/PaymentForms.tsx')
        self.assertIn('createDenied', form)
        self.assertIn("error.includes('không có quyền tạo lịch thanh toán')", form)
        self.assertIn('createDenied ? <div className="form-warning">Bạn không có quyền tạo lịch thanh toán cho hợp đồng này.</div>', form)
        self.assertIn('disabled={!form.contract_id}', form)

if __name__ == '__main__':
    unittest.main()
