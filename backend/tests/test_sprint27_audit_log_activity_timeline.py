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
        self.assertIn("safe_module = module or 'system'", service)
        self.assertIn("safe_entity_type = entity_type or 'system'", service)
        self.assertIn("safe_entity_id = str(entity_id or actor_id or 'unknown')", service)
        self.assertIn('SENSITIVE_KEYS', service)
        self.assertIn('password', service)
        self.assertIn('token', service)
        self.assertIn('def diff_dict', service)
        self.assertIn("'before'", service)
        self.assertIn("'after'", service)
        for text in ['def _lookup_entity_label', 'contract_code', 'booking_code', 'deal_code', 'property_code', 'commission_code', 'receivable_code', 'entity_display', 'def infer_module_from_action', 'def _lookup_actor_snapshot']:
            self.assertIn(text, service)

    def test_api_routes_and_permissions_exist(self):
        api = self.read('backend/app/api/v1/audit_logs.py')
        router = self.read('backend/app/api/v1/__init__.py')
        perms = self.read('backend/app/permissions/constants.py')
        self.assertIn("prefix='/audit-logs'", api)
        self.assertIn("/entity/{entity_type}/{entity_id}", api)
        self.assertIn('audit_logs.view', api)
        self.assertIn('api_router.include_router(settings.router)', router)
        self.assertIn('api_router.include_router(audit_logs.router)', router)
        self.assertIn('audit_log_to_dict(i, db)', api)
        self.assertIn('audit_log_to_dict(log, db)', api)
        self.assertIn('actor_name, actor_email = _lookup_actor_snapshot(db, actor_id)', self.read('backend/app/services/audit_log_service.py'))
        for line in router.splitlines():
            if line.strip().startswith('api_router.include_router('):
                self.assertNotIn(', audit_logs.router', line)
        self.assertIn('audit_logs.view', perms)


    def test_auth_login_audit_has_required_not_null_fields(self):
        auth_service = self.read('backend/app/services/auth_service.py')
        legacy_audit_service = self.read('backend/app/services/audit_service.py')
        self.assertIn('action="auth.login"', auth_service)
        self.assertIn('module="auth"', auth_service)
        self.assertIn('entity_type="user"', auth_service)
        self.assertIn('entity_id=str(user.id)', auth_service)
        self.assertIn('entity_label=user.email', auth_service)
        self.assertIn('description="Đăng nhập hệ thống"', auth_service)
        self.assertIn('safe_module = module or _module_from_action(safe_action)', legacy_audit_service)
        self.assertIn('safe_entity_type = entity_type or safe_module or "system"', legacy_audit_service)
        self.assertIn('safe_entity_id = str(entity_id or user_id or "unknown")', legacy_audit_service)

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
        constants = self.read('frontend/src/features/auditLogs/constants.ts')
        styles = self.read('frontend/src/styles.css')
        business_timeline = self.read('frontend/src/components/timeline/BusinessTimeline.tsx')
        for text in ['Thời gian','Người thao tác','Module','Hành động','Đối tượng','Mô tả','Lý do','Xem chi tiết','Dữ liệu trước','Dữ liệu sau']:
            self.assertIn(text, page)
        for text in ['auth.login', 'Đăng nhập', 'contracts.create', 'Tạo hợp đồng', 'bookings.status_change', 'Đổi trạng thái booking', 'deals.create_from_booking', 'Tạo giao dịch từ booking', 'inventory.properties.create', 'Tạo bất động sản', 'inferModuleFromAction', 'commissions']:
            self.assertIn(text, constants)
        for text in ['entity_display', 'displayModule', 'inferModuleFromAction', "String(item.entity_label)"]:
            self.assertIn(text, page + self.read('frontend/src/features/auditLogs/api.ts'))
        for text in ['Không xác định', 'ID hoặc email người thao tác', 'Tìm người thao tác, mô tả, mã đối tượng', 'audit-filter-grid', 'audit-detail-summary', 'audit-changed-list']:
            self.assertIn(text, page + styles)
        self.assertIn('business-timeline-card', business_timeline + styles)
        self.assertIn('max-width: 1000px', styles)
        self.assertIn('Dòng thời gian chăm sóc', self.read('frontend/src/features/leads/LeadDetailPage.tsx'))
        self.assertIn('Dòng thời gian chăm sóc', self.read('frontend/src/features/customers/CustomerDetailPage.tsx'))
        for path in ['frontend/src/features/deals/components/DealTimeline.tsx','frontend/src/features/contracts/components/ContractTimeline.tsx','frontend/src/features/bookings/components/BookingTimeline.tsx','frontend/src/features/leads/components/LeadTimeline.tsx']:
            self.assertIn('BusinessTimeline', self.read(path))
        for path in ['frontend/src/features/commissions/CommissionDetailPage.tsx','frontend/src/features/companyCommissions/CompanyCommissionDetailPage.tsx','frontend/src/features/commissionPaymentVouchers/CommissionPaymentVoucherDetailPage.tsx']:
            source = self.read(path)
            self.assertIn('ActivityTimeline', source)
            self.assertIn('components/audit/ActivityTimeline', source)
            self.assertIn('Lịch sử thao tác hệ thống', source)

    def test_audit_log_filter_search_hotfix_source_contract(self):
        api = self.read('backend/app/api/v1/audit_logs.py')
        aliases = self.read('backend/app/audit_search_aliases.py')
        page = self.read('frontend/src/features/auditLogs/AuditLogsPage.tsx')
        api_client = self.read('frontend/src/features/auditLogs/api.ts')
        service_client = self.read('frontend/src/services/apiClient.ts')
        app_layout = self.read('frontend/src/layouts/AppLayout.tsx')
        styles = self.read('frontend/src/styles.css')
        for text in [
            'def _apply_actor_filter', 'def _lookup_actor_user_ids', 'User.full_name.ilike', 'User.email.ilike',
            'actor_name.ilike', 'actor_email.ilike', 'AuditLog.actor_id.in_(actor_user_ids)',
            'def _apply_entity_type_filter', 'ENTITY_TYPE_ALIASES',
            'def _apply_entity_id_filter', 'def _lookup_entity_ids_by_display',
            'contract_code', 'booking_code', 'deal_code',
            'def _keyword_candidate_query', 'EXTRA_ACTION_LABELS', 'EXTRA_MODULE_LABELS',
            'Đăng nhập', 'Đổi trạng thái hợp đồng', 'Booking / Giữ chỗ',
            "entity_label.ilike(term)", "entity_type.in_({'user', 'users', 'auth'})",
            'Defensive final pass keeps display-label behavior exact while SQL prefilter avoids enriching the whole table.',
        ]:
            self.assertIn(text, api)
        for text in [
            "setDraftValue('actor_id'", "setDraftValue('entity_type'", "setDraftValue('entity_id'", "setDraftValue('q'",
            'listAuditLogs(filters)', '.catch(err=>', '.finally(()=>{if(active)setLoading(false)})',
            'formatApiError', 'Không tải được lịch sử thao tác.',
            'ID, tên hoặc email người thao tác', 'VD: contract, booking, deal, user',
            'VD: HD-000066, BK-000107, DL-000086 hoặc UUID',
            'Tìm theo người thao tác, hành động, module, mã đối tượng, mô tả...',
            'getPaginationItems', 'paginationItems.map', 'audit-page-number', 'active',
            "setFilters({...draft,page:'1'})", 'setDraft(initialFilters);setFilters(initialFilters);',
        ]:
            self.assertIn(text, page)
        self.assertIn('/api/v1/audit-logs?', api_client)
        for text in [
            'ACCESS_TOKEN_KEY', 'crm_bds_access_token', "headers.set('Authorization', `Bearer ${token}`)",
            'SESSION_EXPIRED_MESSAGE', 'NETWORK_ERROR_MESSAGE', 'response.status === 401',
            'redirectToLogin()', 'throw new ApiRequestError(401', 'throw new ApiRequestError(0',
        ]:
            self.assertIn(text, service_client)
        self.assertIn('unreadCount()', app_layout)
        for text in ['audit-pagination', 'audit-pagination-controls', 'audit-page-number.active', 'audit-page-ellipsis']:
            self.assertIn(text, styles)
        for text in [
            'def normalize_audit_search_text', 'ENTITY_TYPE_ALIASES', 'ACTION_ALIASES',
            "'booking': {'booking', 'bookings', 'giữ chỗ', 'giu cho'}",
            "'bookings': {'booking', 'bookings', 'giữ chỗ', 'giu cho'}",
            "'contracts.status_change': {'đổi trạng thái hợp đồng', 'doi trang thai hop dong'}",
        ]:
            self.assertIn(text, aliases)

    def test_audit_log_keyword_alias_resolver_contract(self):
        from app.audit_search_aliases import (
            label_action,
            label_module,
            matching_action_values,
            matching_entity_types,
            matching_module_values,
            normalize_audit_search_text,
        )

        self.assertEqual(normalize_audit_search_text('  Giữ chỗ  '), 'giu cho')
        self.assertEqual(normalize_audit_search_text('Hợp đồng'), 'hop dong')
        for keyword in ['Giữ chỗ', 'giu cho', 'Booking']:
            self.assertGreaterEqual(matching_entity_types(keyword), {'booking', 'bookings'})
            self.assertIn('bookings', matching_module_values(keyword))
        for keyword in ['Hợp đồng', 'hop dong']:
            self.assertGreaterEqual(matching_entity_types(keyword), {'contract', 'contracts'})
            self.assertIn('contracts', matching_module_values(keyword))
        self.assertIn('contracts.status_change', matching_action_values('Đổi trạng thái hợp đồng'))
        self.assertIn('contracts.status_change', matching_action_values('doi trang thai hop dong'))
        self.assertEqual(label_module('bookings'), 'Booking / Giữ chỗ')
        self.assertEqual(label_action('contracts.status_change'), 'Đổi trạng thái hợp đồng')

if __name__ == '__main__':
    unittest.main()
