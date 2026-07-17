import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def read(path): return (ROOT / path).read_text(encoding='utf-8')
class Sprint343DrilldownScopeSourceTest(unittest.TestCase):
    def test_frontend_pages_hydrate_scope_from_url(self):
        helper = read('frontend/src/utils/urlFilters.ts')
        self.assertIn('new URLSearchParams(search)', helper)
        self.assertIn('BOOLEAN_KEYS', helper)
        pages = {
            'frontend/src/features/tasks/TasksPage.tsx': ['queryFilters<Filters>', 'scope'],
            'frontend/src/features/appointments/AppointmentsPage.tsx': ['queryFilters<Filters>'],
            'frontend/src/features/leads/LeadsPage.tsx': ['queryFilters<Filters>'],
            'frontend/src/features/leads/OverdueLeadsPage.tsx': ['queryFilters', 'scope'],
            'frontend/src/features/customers/CustomersPage.tsx': ['queryFilters'],
            'frontend/src/features/bookings/BookingsPage.tsx': ['queryFilters<Filters>'],
            'frontend/src/features/deals/DealsPage.tsx': ['queryFilters<Filters>'],
            'frontend/src/features/contracts/ContractsPage.tsx': ['queryFilters<Record<string,string>>'],
            'frontend/src/features/receipts/ReceiptsPage.tsx': ['queryFilters<Record<string,string>>'],
            'frontend/src/features/commissions/CommissionsPage.tsx': ['queryFilters<Record<string,string>>'],
        }
        for path, needles in pages.items():
            src = read(path)
            for needle in needles:
                self.assertIn(needle, src, path)
    def test_backend_routes_accept_scope(self):
        for path in ['backend/app/api/v1/tasks.py','backend/app/api/v1/lead_appointments.py','backend/app/api/v1/leads.py','backend/app/api/v1/customers.py','backend/app/api/v1/bookings.py','backend/app/api/v1/deals.py','backend/app/api/v1/contracts.py','backend/app/api/v1/payments.py','backend/app/api/v1/commissions.py']:
            self.assertIn('scope', read(path), path)
    def test_services_enforce_scope_mine_with_actor_in_sql_conditions(self):
        checks = {
            'backend/app/services/task_service.py': ['f.get("scope") == "mine"', 'Task.assigned_user_id==actor.id', 'Task.task_assignees.any(TaskAssignee.user_id==actor.id)', 'active_only'],
            'backend/app/services/lead_appointment_service.py': ['filters.get("scope") == "mine"', 'LeadAppointment.assigned_to_id==user.id', 'filters.get("status") == "overdue"'],
            'backend/app/services/lead_service.py': ['scope == "mine"', 'Lead.owner_id == user.id', 'activity_status == "none"', 'has_activity is False', 'care_status == "overdue"', 'timedelta(days=7)'],
            'backend/app/services/customer_service.py': ['request_scope == "mine"', 'Customer.owner_id == actor.id', 'Lead.owner_id == actor.id'],
            'backend/app/services/booking_service.py': ['request_scope == "mine"', 'Booking.assigned_user_id == actor.id'],
            'backend/app/services/deal_service.py': ['request_scope == "mine"', 'Deal.owner_id == actor.id'],
            'backend/app/services/contract_service.py': ['request_scope == "mine"', 'Contract.deal.has(Deal.owner_id == actor.id)', 'status == "valid"'],
            'backend/app/services/payment_service.py': ['scope == "mine"', 'Deal.owner_id == actor.id'],
            'backend/app/services/commission_service.py': ["f.get('scope') == 'mine'", 'SalesCommission.sale_id==actor.id'],
        }
        for path, needles in checks.items():
            src = read(path)
            for needle in needles:
                self.assertIn(needle, src, path)
    def test_drilldown_urls_are_forwarded_to_backend(self):
        task_api = read('frontend/src/features/tasks/api.ts')
        appt_api = read('frontend/src/features/appointments/api.ts')
        lead_api = read('frontend/src/features/leads/api.ts')
        dashboard = read('frontend/src/features/dashboard/SaleDashboard.tsx')
        self.assertIn("q('/tasks/overdue',mine)", dashboard)
        self.assertIn("q('/appointments',{...mine,status:'overdue'})", dashboard)
        self.assertIn("q('/leads',{...mine,activity_status:'none',has_activity:'false'})", dashboard)
        self.assertIn('scope?:string', task_api)
        self.assertIn('scope?:string', appt_api)
        self.assertIn('activity_status?: string', lead_api)
        self.assertIn('has_activity?: boolean | string', lead_api)
        self.assertIn("status:'remaining',date_from:resolvedStart,date_to:resolvedEnd", dashboard)
        self.assertIn('Funnel Lead → Customer', dashboard)
        self.assertIn('Funnel Booking → Cọc → Deal → Hợp đồng', dashboard)
if __name__ == '__main__': unittest.main()
