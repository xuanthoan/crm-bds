import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app.services.lead_task_service import is_overdue
from app.services.user_service import user_role_code_set

class Sprint6WorkflowTests(unittest.TestCase):
    def test_pending_past_task_is_overdue(self):
        task=SimpleNamespace(status="pending",due_at=datetime.now(timezone.utc)-timedelta(hours=2))
        self.assertTrue(is_overdue(task))
    def test_completed_past_task_is_not_overdue(self):
        task=SimpleNamespace(status="completed",due_at=datetime.now(timezone.utc)-timedelta(days=1))
        self.assertFalse(is_overdue(task))
    def test_role_code_helper_remains_set_safe(self):
        user=SimpleNamespace(roles=[SimpleNamespace(code="sale")])
        self.assertEqual(user_role_code_set(user),{"sale"})
if __name__=="__main__": unittest.main()
