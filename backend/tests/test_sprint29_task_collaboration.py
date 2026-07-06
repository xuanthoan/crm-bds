from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src"


class Sprint29TaskCollaborationSourceTests(unittest.TestCase):
    def read_backend(self, relative: str) -> str:
        return (BACKEND / relative).read_text(encoding="utf-8")

    def read_frontend(self, relative: str) -> str:
        return (FRONTEND / relative).read_text(encoding="utf-8")

    def test_models_and_migration_define_collaboration_tables(self):
        model = self.read_backend("app/models/task.py")
        migration = self.read_backend("alembic/versions/20260706_0020_task_collaboration.py")
        for source in (model, migration):
            self.assertIn("task_assignees", source)
            self.assertIn("task_watchers", source)
            self.assertIn("task_id", source)
            self.assertIn("user_id", source)
        self.assertIn("uq_task_assignees_task_user", migration)
        self.assertIn("uq_task_watchers_task_user", migration)
        self.assertIn("ondelete=\"CASCADE\"", model)
        self.assertIn("ON CONFLICT (task_id, user_id) DO NOTHING", migration)
        self.assertIn("assigned_user_id", migration)

    def test_backend_payload_and_response_contract(self):
        schema = self.read_backend("app/schemas/task.py")
        service = self.read_backend("app/services/task_service.py")
        for field in ("primary_assignee_id", "assigned_to_id", "assignee_ids", "watcher_ids"):
            self.assertIn(field, schema)
            self.assertIn(field, service)
        for field in ("primary_assignee", "assignees", "watchers", "assigned_to", "creator"):
            self.assertIn(f'"{field}"', service)
        self.assertIn("task_assignees.any", service)
        self.assertIn("task_watchers.any", service)
        self.assertIn("Người phụ trách chính phải nằm trong danh sách người cùng thực hiện", service)
        self.assertIn("actor.id not in current_assignee_ids", service)

    def test_frontend_form_and_table_show_collaboration_roles(self):
        form = self.read_frontend("features/tasks/TaskFormModal.tsx")
        table = self.read_frontend("features/tasks/components/TaskTable.tsx")
        types = self.read_frontend("features/tasks/types.ts")
        for label in ("Người phụ trách chính", "Người cùng thực hiện", "Người quan sát"):
            self.assertIn(label, form)
            self.assertIn(label, table)
        for field in ("primary_assignee_id", "assignee_ids", "watcher_ids"):
            self.assertIn(field, form)
            self.assertIn(field, types)
        self.assertIn("Array.isArray", table)
        self.assertNotRegex(table, r"undefined\.map")
        self.assertIn("Pagination", self.read_frontend("features/tasks/TasksPage.tsx"))
        self.assertIn("today:true", self.read_frontend("features/tasks/TodayTasksPage.tsx"))
        self.assertIn("overdue:true", self.read_frontend("features/tasks/OverdueTasksPage.tsx"))


if __name__ == "__main__":
    unittest.main()
