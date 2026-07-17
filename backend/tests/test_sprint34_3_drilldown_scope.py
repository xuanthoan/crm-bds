import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path: str) -> str:
    return (ROOT / path).read_text()

class Sprint343DrilldownScopeEnforcementTests(unittest.TestCase):
    def test_routes_accept_scope_without_dashboard_special_case(self):
        for path in [
            'backend/app/api/v1/leads.py',
            'backend/app/api/v1/lead_appointments.py',
            'backend/app/api/v1/tasks.py',
            'backend/app/api/v1/customers.py',
            'backend/app/api/v1/bookings.py',
            'backend/app/api/v1/deals.py',
            'backend/app/api/v1/contracts.py',
            'backend/app/api/v1/payments.py',
            'backend/app/api/v1/commissions.py',
        ]:
            text = read(path)
            self.assertIn('scope:', text, path)
            self.assertNotIn('if dashboard', text.lower(), path)

    def test_backend_scope_mine_is_sql_level_current_user_filter(self):
        expectations = {
            'backend/app/services/lead_service.py': ['mine_only(request_scope)', 'Lead.owner_id == user.id'],
            'backend/app/services/lead_appointment_service.py': ['mine_only(filters.get("scope"))', 'LeadAppointment.assigned_to_id==user.id'],
            'backend/app/services/task_service.py': ['mine_only(f.get("scope"))', 'Task.assigned_user_id==actor.id'],
            'backend/app/services/customer_service.py': ['mine_only(request_scope)', 'Customer.owner_id == actor.id'],
            'backend/app/services/booking_service.py': ['mine_only(request_scope)', 'Booking.assigned_user_id == actor.id'],
            'backend/app/services/deal_service.py': ['mine_only(request_scope)', 'Deal.owner_id == actor.id'],
            'backend/app/services/contract_service.py': ['mine_only(request_scope)', 'Contract.deal.has(Deal.owner_id==actor.id)'],
            'backend/app/services/payment_service.py': ['mine_only(scope)', 'PaymentReceipt.deal.has(Deal.owner_id==actor.id)'],
            'backend/app/services/commission_service.py': ['mine_only(f.get("scope"))', 'SalesCommission.sale_id==actor.id'],
        }
        for path, snippets in expectations.items():
            text = read(path)
            for snippet in snippets:
                self.assertIn(snippet, text, f'{path} missing {snippet}')
            self.assertNotIn('.all()\n    for', text, f'{path} must not Python-filter after loading all rows')

    def test_drilldown_filters_are_enforced_in_query_builders(self):
        lead = read('backend/app/services/lead_service.py')
        self.assertIn('lead_status == "active"', lead)
        self.assertIn('care_status == "overdue"', lead)
        self.assertIn('Lead.next_follow_up_at < datetime.now(timezone.utc)', lead)
        self.assertIn('stale is True', lead)
        self.assertIn('Lead.created_at >= datetime.combine(created_from', lead)
        appt = read('backend/app/services/lead_appointment_service.py')
        self.assertIn('LeadAppointment.status.in_({"scheduled","rescheduled"})', appt)
        self.assertIn('LeadAppointment.start_at < now()', appt)
        task = read('backend/app/services/task_service.py')
        self.assertIn('Task.due_at>=start', task)
        self.assertIn('Task.due_at<f["due_before"]', task)
        commission = read('backend/app/services/commission_service.py')
        self.assertIn("f.get('status') == 'paid'", commission)
        self.assertIn("f.get('status') == 'approved'", commission)
        self.assertIn("f.get('status') == 'remaining'", commission)

if __name__ == '__main__':
    unittest.main()
