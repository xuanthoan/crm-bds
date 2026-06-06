import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.leads.constants import SALES_ROLE_CODES
from app.services.organization_service import list_eligible_lead_assignees
from app.services.user_service import user_role_code_set, user_role_codes


class FakeScalarResult:
    def __init__(self, users):
        self.users = users

    def unique(self):
        return self

    def __iter__(self):
        return iter(self.users)


class FakeSession:
    def __init__(self, users):
        self.users = users

    def scalars(self, _query):
        return FakeScalarResult(self.users)


def make_user(*role_codes, is_superuser=False):
    return SimpleNamespace(
        id=uuid4(),
        status="active",
        deleted_at=None,
        is_superuser=is_superuser,
        roles=[SimpleNamespace(code=code) for code in role_codes],
    )


class RoleCodeSetTests(unittest.TestCase):
    def test_role_helper_keeps_list_contract_and_exposes_safe_set(self):
        user = make_user("sale", "leader", "sale")

        self.assertEqual(user_role_codes(user), ["leader", "sale"])
        self.assertEqual(user_role_code_set(user), {"leader", "sale"})
        self.assertTrue(user_role_code_set(user) & SALES_ROLE_CODES)

    @patch("app.permissions.dependencies.get_user_permissions", return_value=["leads.assign.all"])
    @patch("app.services.organization_service.get_accessible_user_ids_for_lead_scope")
    def test_assign_all_returns_active_eligible_users_without_list_set_error(
        self, accessible_ids, _permissions
    ):
        actor = make_user("admin")
        sale = make_user("sale")
        non_sales = make_user("accountant")
        accessible_ids.return_value = {sale.id, non_sales.id}

        result = list_eligible_lead_assignees(FakeSession([sale, non_sales]), actor)

        self.assertEqual(result, [sale])
        accessible_ids.assert_called_once_with(unittest.mock.ANY, actor, "all")

    @patch("app.permissions.dependencies.get_user_permissions", return_value=["leads.assign.team"])
    @patch("app.services.organization_service.get_accessible_user_ids_for_lead_scope")
    def test_team_assignment_uses_team_scope_and_filters_sales_roles(
        self, accessible_ids, _permissions
    ):
        actor = make_user("leader")
        team_sale = make_user("sale")
        accessible_ids.return_value = {actor.id, team_sale.id}

        result = list_eligible_lead_assignees(FakeSession([actor, team_sale]), actor)

        self.assertEqual(result, [actor, team_sale])
        accessible_ids.assert_called_once_with(unittest.mock.ANY, actor, "team")

    @patch("app.permissions.dependencies.get_user_permissions", return_value=["leads.view.own"])
    def test_user_without_assign_permission_is_forbidden(self, _permissions):
        actor = make_user("sale")

        with self.assertRaises(HTTPException) as context:
            list_eligible_lead_assignees(FakeSession([]), actor)

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
