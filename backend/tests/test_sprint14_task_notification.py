import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class Sprint14TaskNotificationSourceTests(unittest.TestCase):
    def test_backend_routes_and_services_exist(self):
        for path in [
            'backend/app/models/task.py','backend/app/models/task_activity.py','backend/app/models/notification.py',
            'backend/app/services/task_service.py','backend/app/services/notification_service.py',
            'backend/app/api/v1/tasks.py','backend/app/api/v1/notifications.py',
        ]:
            self.assertTrue((ROOT / path).exists(), path)

    def test_task_service_declares_required_api(self):
        tree = ast.parse((ROOT / 'backend/app/services/task_service.py').read_text())
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({'list_tasks','get_task_detail','create_task','update_task','change_task_status','complete_task','cancel_task','add_task_note','create_auto_task_if_not_exists','get_today_tasks','get_overdue_tasks','list_task_assignees'} <= functions)

    def test_notification_service_declares_required_api(self):
        tree = ast.parse((ROOT / 'backend/app/services/notification_service.py').read_text())
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({'list_notifications','unread_count','mark_read','mark_all_read','create_notification','create_task_notification'} <= functions)

    def test_manual_assignment_guardrails_are_documented_in_source(self):
        content = (ROOT / 'backend/app/services/task_service.py').read_text()
        self.assertIn('assigned_user_id or actor.id', content)
        self.assertIn('Người phụ trách không tồn tại.', content)
        self.assertIn('Bạn không có quyền giao công việc cho người này.', content)

    def test_task_form_uses_assignee_select_not_uuid_textbox(self):
        content = (ROOT / 'frontend/src/features/tasks/TaskFormModal.tsx').read_text()
        self.assertIn('Người phụ trách', content)
        self.assertIn('Mặc định giao cho bạn. Có thể chọn người khác nếu bạn có quyền.', content)
        self.assertIn('list="task-assignee-options"', content)
        self.assertIn('Đang tải người phụ trách...', content)
        self.assertIn('Không kết nối được máy chủ. Kiểm tra VITE_API_URL hoặc backend port 8000.', content)
        self.assertNotIn('Người phụ trách (UUID)', content)
        self.assertNotIn('Tìm theo tên/email', content)
        self.assertNotIn('Bỏ trống để giao cho chính bạn', content)

    def test_task_notification_alembic_migration_exists(self):
        migration = ROOT / 'backend/alembic/versions/20260623_0011_task_notification_engine.py'
        self.assertTrue(migration.exists())
        content = migration.read_text()
        for table in ['"tasks"', '"task_activities"', '"notifications"']:
            self.assertIn(table, content)
        self.assertIn('down_revision = "20260613_0010"', content)
        self.assertIn('ix_tasks_assigned_user_id', content)
        self.assertIn('ix_notifications_recipient_user_id', content)

    def test_frontend_api_base_supports_docker_local(self):
        api_client = (ROOT / 'frontend/src/services/apiClient.ts').read_text()
        compose = (ROOT / 'docker-compose.local.yml').read_text()
        dockerfile = (ROOT / 'frontend/Dockerfile').read_text()
        self.assertIn("http://localhost:8000", api_client)
        self.assertIn("VITE_API_URL: http://localhost:8000", compose)
        self.assertIn("ARG VITE_API_URL=http://localhost:8000", dockerfile)

    def test_permissions_registered(self):
        content = (ROOT / 'backend/app/permissions/constants.py').read_text()
        for code in ['tasks.view','tasks.create','tasks.update','tasks.complete','tasks.cancel','tasks.assign','tasks.view_all','notifications.view','notifications.update']:
            self.assertIn(code, content)

if __name__ == '__main__':
    unittest.main()
