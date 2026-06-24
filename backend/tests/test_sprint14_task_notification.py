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
        self.assertTrue({'list_tasks','get_task_detail','create_task','update_task','change_task_status','complete_task','cancel_task','add_task_note','create_auto_task_if_not_exists','get_today_tasks','get_overdue_tasks','list_task_assignees','auto_reassign_booking_tasks'} <= functions)

    def test_notification_service_declares_required_api(self):
        tree = ast.parse((ROOT / 'backend/app/services/notification_service.py').read_text())
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({'list_notifications','unread_count','mark_read','mark_all_read','create_notification','create_task_notification'} <= functions)

    def test_manual_assignment_guardrails_are_documented_in_source(self):
        content = (ROOT / 'backend/app/services/task_service.py').read_text()
        self.assertIn('assigned_user_id or actor.id', content)
        self.assertIn('Người phụ trách không tồn tại.', content)
        self.assertIn('Bạn không có quyền giao công việc cho người này.', content)
        self.assertIn('role.code == "admin"', content)

    def test_task_form_uses_assignee_select_not_uuid_textbox(self):
        content = (ROOT / 'frontend/src/features/tasks/TaskFormModal.tsx').read_text()
        self.assertIn('Người phụ trách', content)
        self.assertIn('Mặc định giao cho bạn. Có thể chọn người khác nếu bạn có quyền.', content)
        self.assertIn('searchable-combobox', content)
        self.assertIn('Đang tải người phụ trách...', content)
        self.assertIn('Không kết nối được máy chủ. Kiểm tra VITE_API_URL hoặc backend port 8000.', content)
        self.assertNotIn('Người phụ trách (UUID)', content)
        self.assertNotIn('Tìm theo tên/email', content)
        self.assertNotIn('Bỏ trống để giao cho chính bạn', content)
        self.assertIn('selectedAssigneeId', content)
        self.assertIn('chooseAssignee', content)

    def test_task_search_links_and_booking_reassign_sources_exist(self):
        task_service = (ROOT / 'backend/app/services/task_service.py').read_text()
        task_model = (ROOT / 'backend/app/models/task.py').read_text()
        booking_service = (ROOT / 'backend/app/services/booking_service.py').read_text()
        task_table = (ROOT / 'frontend/src/features/tasks/components/TaskTable.tsx').read_text()
        task_filters = (ROOT / 'frontend/src/features/tasks/components/TaskFilters.tsx').read_text()
        for needle in ['Booking.booking_code', 'Deal.deal_code', 'Contract.contract_code', 'Customer.full_name', 'Customer.primary_phone', 'PropertyUnit.property_code']:
            self.assertIn(needle, task_service)
        self.assertIn('selectinload(Task.related_booking).load_only(Booking.id, Booking.booking_code).lazyload("*")', task_service)
        self.assertNotIn('lazy="joined"', task_model)
        self.assertIn('Booking đổi người phụ trách nên công việc được chuyển', task_service)
        self.assertIn('create_task_notification(db,t,"Bạn được giao công việc")', task_service)
        self.assertIn('auto_reassign_booking_tasks(db, booking, old_assignee_id, actor)', booking_service)
        self.assertIn('primaryLink', task_table)
        self.assertIn('/bookings/', task_table)
        self.assertIn('/contracts/', task_table)
        self.assertIn('/deals/', task_table)
        self.assertIn('related_booking?.booking_code', task_table)
        self.assertNotIn('link-stack', task_table)
        self.assertIn("value={value.q??''}", task_filters)

    def test_task_notification_alembic_migration_exists(self):
        migration = ROOT / 'backend/alembic/versions/20260623_0011_task_notification_engine.py'
        self.assertTrue(migration.exists())
        content = migration.read_text()
        for table in ['"tasks"', '"task_activities"', '"notifications"']:
            self.assertIn(table, content)
        self.assertIn('down_revision = "20260613_0010"', content)
        self.assertIn('ix_tasks_assigned_user_id', content)
        self.assertIn('ix_notifications_recipient_user_id', content)

    def test_local_demo_users_are_seeded_when_enabled(self):
        init_db = (ROOT / 'backend/app/db/init_db.py').read_text()
        compose = (ROOT / 'docker-compose.local.yml').read_text()
        for email in ['sale04@gmail.com', 'sale05@gmail.com', 'sale7@gmail.com', 'sale06@gmail.com', 'sale01@test.com']:
            self.assertIn(email, init_db)
        self.assertIn('SEED_DEMO_USERS: "true"', compose)
        self.assertIn('crm_bds_all_in_one_postgres_data', compose)
        self.assertIn('seed_demo_users(db)', init_db)
        self.assertIn('if user:', init_db)
        self.assertIn('continue', init_db)

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
