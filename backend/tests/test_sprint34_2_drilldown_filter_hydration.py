from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Sprint342DrilldownFilterHydrationTests(unittest.TestCase):
    def test_shared_query_hydration_helper_exists(self):
        source = read("frontend/src/utils/queryHydration.ts")
        self.assertIn("hydrateFiltersFromQuery", source)
        self.assertIn("useQueryHydratedFilters", source)
        self.assertIn("URLSearchParams", source)
        self.assertIn("popstate", source)
        self.assertIn("boolean", source)
        self.assertIn("array", source)

    def test_drilldown_list_pages_hydrate_scope_and_filters(self):
        pages = {
            "frontend/src/features/leads/LeadsPage.tsx": ["scope", "care_status", "activity_status", "stale", "created_from", "created_to"],
            "frontend/src/features/appointments/AppointmentsPage.tsx": ["scope", "status", "today"],
            "frontend/src/features/customers/CustomersPage.tsx": ["scope"],
            "frontend/src/features/bookings/BookingsPage.tsx": ["scope", "date_from", "date_to"],
            "frontend/src/features/deals/DealsPage.tsx": ["scope", "stage", "date_from", "date_to"],
            "frontend/src/features/contracts/ContractsPage.tsx": ["scope", "status", "date_from", "date_to"],
            "frontend/src/features/receipts/ReceiptsPage.tsx": ["scope", "date_from", "date_to"],
            "frontend/src/features/commissions/CommissionsPage.tsx": ["scope", "date_from", "date_to"],
        }
        for path, expected in pages.items():
            with self.subTest(path=path):
                source = read(path)
                self.assertIn("useQueryHydratedFilters", source)
                for token in expected:
                    self.assertIn(token, source)

    def test_frontend_filter_types_accept_dashboard_query_params(self):
        self.assertIn("scope?: string", read("frontend/src/features/leads/api.ts"))
        self.assertIn("care_status?: string", read("frontend/src/features/leads/api.ts"))
        self.assertIn("activity_status?: string", read("frontend/src/features/leads/api.ts"))
        self.assertIn("stale?: boolean | string", read("frontend/src/features/leads/api.ts"))
        self.assertIn("scope?:string", read("frontend/src/features/appointments/api.ts"))
        self.assertIn("scope?:string", read("frontend/src/features/tasks/api.ts"))
        self.assertIn("date_from?:string", read("frontend/src/features/bookings/types.ts"))
        self.assertIn("stage?:string", read("frontend/src/features/deals/api.ts"))

    def test_backend_scope_mine_resolves_to_current_user_not_url_ids(self):
        expectations = {
            "backend/app/api/v1/leads.py": ["scope == \"mine\"", "owner_id = current_user.id"],
            "backend/app/api/v1/tasks.py": ["scope==\"mine\"", "assigned_user_id=actor.id"],
            "backend/app/api/v1/lead_appointments.py": ["scope==\"mine\"", "assigned_to_id=user.id"],
            "backend/app/api/v1/customers.py": ["scope == \"mine\"", "owner_id = current_user.id"],
            "backend/app/api/v1/bookings.py": ["scope==\"mine\"", "assigned_user_id=actor.id"],
            "backend/app/api/v1/deals.py": ["scope==\"mine\"", "owner_id=actor.id"],
            "backend/app/services/contract_service.py": ["query_scope == \"mine\"", "Deal.owner_id==actor.id"],
            "backend/app/services/payment_service.py": ["scope == \"mine\"", "Deal.owner_id==actor.id"],
            "backend/app/services/commission_service.py": ["f.get('scope') == 'mine'", "SalesCommission.sale_id==actor.id"],
        }
        for path, tokens in expectations.items():
            with self.subTest(path=path):
                source = read(path)
                for token in tokens:
                    self.assertIn(token, source)

    def test_backend_supports_dashboard_filter_semantics(self):
        lead_service = read("backend/app/services/lead_service.py")
        self.assertIn('lead_status in {"active", "open"}', lead_service)
        self.assertIn('care_status == "overdue"', lead_service)
        self.assertIn('activity_status == "none"', lead_service)
        self.assertIn('stale is True', lead_service)
        appointment_service = read("backend/app/services/lead_appointment_service.py")
        self.assertIn('status_filter == "overdue"', appointment_service)
        contract_service = read("backend/app/services/contract_service.py")
        self.assertIn('status == "valid"', contract_service)

    def test_sale_dashboard_links_still_do_not_expose_raw_scope_ids(self):
        source = read("frontend/src/features/dashboard/SaleDashboard.tsx")
        self.assertIn("scope", source)
        self.assertNotIn("user_id=", source)
        self.assertNotIn("sale_id=", source)
        self.assertNotIn("team_id=", source)
        self.assertNotIn("department_id=", source)


if __name__ == "__main__":
    unittest.main()
