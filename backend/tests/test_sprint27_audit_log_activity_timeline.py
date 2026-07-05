import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Sprint27AuditLogActivityTimelineSourceTest(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding='utf-8')

    def test_migration_model_service_and_sanitization(self):
        migration = ''.join(p.read_text(encoding='utf-8') for p in (ROOT/'backend/alembic/versions').glob('*audit_logs.py'))
        model = self.read('backend/app/models/audit_log.py')
        service = self.read('backend/app/services/audit_log_service.py')
        self.assertIn('audit_logs', migration)
        self.assertIn('inspect(op.get_bind())', migration)
        self.assertIn('if not _table_exists()', migration)
        self.assertIn('_create_missing_columns()', migration)
        self.assertIn('_create_missing_indexes()', migration)
        self.assertIn('def _add_column_safely', migration)
        self.assertIn('column_to_add.nullable = True', migration)
        self.assertIn('op.alter_column(TABLE_NAME, name, nullable=False)', migration)
        for backfill_sql in [
            "UPDATE audit_logs SET action = 'unknown' WHERE action IS NULL",
            "UPDATE audit_logs SET module = 'audit_log' WHERE module IS NULL",
            "UPDATE audit_logs SET entity_type = 'audit_log' WHERE entity_type IS NULL",
            "UPDATE audit_logs SET entity_id = COALESCE(id::text, 'unknown') WHERE entity_id IS NULL",
            "UPDATE audit_logs SET created_at = now() WHERE created_at IS NULL",
        ]:
            self.assertIn(backfill_sql, migration)
        self.assertNotIn('drop_table(TABLE_NAME)\n    else', migration)
        for index_name in ['ix_audit_logs_created_at', 'ix_audit_logs_actor_id', 'ix_audit_logs_module_entity']:
            self.assertIn(index_name, migration)
        for field in ['actor_id','actor_name','actor_email','module','entity_label','changed_fields','request_id']:
            self.assertIn(field, model)
        self.assertIn('def create_audit_log', service)
        self.assertIn('SENSITIVE_KEYS', service)
        self.assertIn('password', service)
        self.assertIn('token', service)
        self.assertIn('def diff_dict', service)
        self.assertIn("'before'", service)
        self.assertIn("'after'", service)

    def test_api_routes_and_permissions_exist(self):
        api = self.read('backend/app/api/v1/audit_logs.py')
        router = self.read('backend/app/api/v1/__init__.py')
        perms = self.read('backend/app/permissions/constants.py')
        self.assertIn("prefix='/audit-logs'", api)
        self.assertIn("/entity/{entity_type}/{entity_id}", api)
        self.assertIn('audit_logs.view', api)
        self.assertIn('api_router.include_router(settings.router)', router)
        self.assertIn('api_router.include_router(audit_logs.router)', router)
        for line in router.splitlines():
            if line.strip().startswith('api_router.include_router('):
                self.assertNotIn(', audit_logs.router', line)
        self.assertIn('audit_logs.view', perms)

    def test_labels_and_sensitive_fields(self):
        constants = self.read('backend/app/audit_constants.py')
        service = self.read('backend/app/services/audit_log_service.py')
        self.assertIn("'approve': 'Duyệt'", constants)
        self.assertIn("'company_commission': 'Hoa hồng công ty'", constants)
        self.assertIn('sanitize_audit_data', service)
        self.assertIn('SENSITIVE_KEYS', service)

    def test_risk_modules_call_audit_service(self):
        expectations = {
            'backend/app/services/commission_service.py': ['sales_commission', 'approve', 'hold', 'cancel'],
            'backend/app/services/company_commission_service.py': ['company_commission', 'record_received', 'hold', 'cancel'],
            'backend/app/services/commission_payment_voucher_service.py': ['commission_payment_voucher', 'create_voucher', 'mark_paid', 'cancel_voucher'],
            'backend/app/services/settings_service.py': ['commission_payout_policy', 'update_policy'],
        }
        for path, needles in expectations.items():
            source = self.read(path)
            self.assertIn('create_audit_log', source)
            for needle in needles:
                self.assertIn(needle, source)

    def test_frontend_route_page_timeline_and_labels(self):
        for path in ['frontend/src/features/auditLogs/AuditLogsPage.tsx','frontend/src/components/audit/ActivityTimeline.tsx','frontend/src/features/auditLogs/api.ts']:
            self.assertTrue((ROOT/path).exists(), path)
        route = self.read('frontend/src/routes/AppRoutes.tsx')
        layout = self.read('frontend/src/layouts/AppLayout.tsx')
        page = self.read('frontend/src/features/auditLogs/AuditLogsPage.tsx')
        self.assertIn('/audit-logs', route)
        self.assertIn('Lịch sử thao tác', layout)
        for text in ['Thời gian','Người thao tác','Module','Hành động','Đối tượng','Mô tả','Lý do','Xem chi tiết','Dữ liệu trước','Dữ liệu sau']:
            self.assertIn(text, page)
        for path in ['frontend/src/features/commissions/CommissionDetailPage.tsx','frontend/src/features/companyCommissions/CompanyCommissionDetailPage.tsx','frontend/src/features/commissionPaymentVouchers/CommissionPaymentVoucherDetailPage.tsx']:
            self.assertIn('ActivityTimeline', self.read(path))

if __name__ == '__main__':
    unittest.main()
