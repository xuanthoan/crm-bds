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
        self.assertTrue({'list_tasks','get_task_detail','create_task','update_task','change_task_status','complete_task','cancel_task','add_task_note','create_auto_task_if_not_exists','get_today_tasks','get_overdue_tasks'} <= functions)

    def test_notification_service_declares_required_api(self):
        tree = ast.parse((ROOT / 'backend/app/services/notification_service.py').read_text())
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({'list_notifications','unread_count','mark_read','mark_all_read','create_notification','create_task_notification'} <= functions)

    def test_permissions_registered(self):
        content = (ROOT / 'backend/app/permissions/constants.py').read_text()
        for code in ['tasks.view','tasks.create','tasks.update','tasks.complete','tasks.cancel','tasks.assign','tasks.view_all','notifications.view','notifications.update']:
            self.assertIn(code, content)

if __name__ == '__main__':
    unittest.main()
