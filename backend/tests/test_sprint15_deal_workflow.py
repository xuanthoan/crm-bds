from pathlib import Path
import unittest

class Sprint15DealWorkflowSourceTests(unittest.TestCase):
    def test_deal_workflow_guards_and_completed_contract_sync(self):
        service = Path('backend/app/services/deal_service.py').read_text()
        contract = Path('backend/app/services/contract_service.py').read_text()
        self.assertIn('EFFECTIVE_CONTRACT_STATUSES = {"signed", "active", "completed"}', service)
        self.assertIn('CONTRACT_LOCK_ALLOWED_STAGES = {"contract_pending", "contract", "contract_signed", "completed"}', service)
        self.assertIn('target_status not in {"completed", "won"}', service)
        self.assertIn('Hợp đồng {contract.contract_code} đã hoàn tất nên giao dịch được chốt thành công.', contract)
        self.assertIn('contract.deal.status = "completed"', contract)
        self.assertIn('contract.deal.pipeline_stage = "completed"', contract)

    def test_deal_tasks_notifications_and_reassignment(self):
        task = Path('backend/app/services/task_service.py').read_text()
        deal = Path('backend/app/services/deal_service.py').read_text()
        self.assertIn('def auto_task_for_deal_stage', task)
        self.assertIn('"deal_consulting"', task)
        self.assertIn('"deal_contract_pending"', task)
        self.assertIn('"deal_deposited"', task)
        self.assertIn('Task.status.in_(["open","in_progress"])', task)
        self.assertIn('def auto_reassign_deal_tasks', task)
        self.assertIn('create_task_notification(db,t,"Bạn được giao công việc")', task)
        self.assertIn('auto_task_for_deal_stage(db, deal, actor)', deal)
        self.assertIn('_notify_deal(db, deal', deal)

    def test_deal_search_and_list_query_are_narrow(self):
        deal = Path('backend/app/services/deal_service.py').read_text()
        self.assertIn('def _deal_list_load_options', deal)
        self.assertIn('selectinload(Deal.customer).load_only', deal)
        self.assertIn('Deal.contracts.any(Contract.contract_code.ilike(term))', deal)
        self.assertIn('Deal.booking.has(Booking.booking_code.ilike(term))', deal)
        self.assertNotIn('joinedload(', deal)

    def test_frontend_labels_and_task_link_precedence(self):
        constants = Path('frontend/src/features/deals/constants.ts').read_text()
        table = Path('frontend/src/features/tasks/components/TaskTable.tsx').read_text()
        self.assertIn("deposited:'Đã đặt cọc'", constants)
        self.assertIn("contract_pending:'Chờ ký hợp đồng'", constants)
        self.assertIn('if(x.related_deal_id)', table)
        self.assertLess(table.index('if(x.related_contract_id)'), table.index('if(x.related_deal_id)'))

if __name__ == '__main__':
    unittest.main()
