from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting
from app.services.audit_log_service import create_audit_log, snapshot_model, diff_dict

SALES_COMMISSION_PAYOUT_POLICY_KEY = 'sales_commission_payout_policy'
POLICY_RECEIVED_AMOUNT_CAPACITY = 'received_amount_capacity'
POLICY_RECEIVED_RATIO = 'received_ratio'
DEFAULT_SALES_COMMISSION_PAYOUT_POLICY = POLICY_RECEIVED_AMOUNT_CAPACITY
VALID_SALES_COMMISSION_PAYOUT_POLICIES = {POLICY_RECEIVED_AMOUNT_CAPACITY, POLICY_RECEIVED_RATIO}
POLICY_LABELS = {
    POLICY_RECEIVED_AMOUNT_CAPACITY: 'Chi theo hạn mức tiền hoa hồng công ty đã nhận',
    POLICY_RECEIVED_RATIO: 'Chi theo tỷ lệ hoa hồng công ty đã thu',
}
POLICY_DESCRIPTIONS = {
    POLICY_RECEIVED_AMOUNT_CAPACITY: 'Sale được chi nếu số tiền chi không vượt quá hoa hồng công ty đã thực nhận còn khả dụng.',
    POLICY_RECEIVED_RATIO: 'Sale chỉ được chi theo tỷ lệ công ty đã thu so với hoa hồng công ty xác nhận.',
}


def now():
    return datetime.now(timezone.utc)


def _setting(db: Session, key: str) -> SystemSetting | None:
    return db.query(SystemSetting).filter(SystemSetting.key == key).first()


def get_sales_commission_payout_policy_code(db: Session) -> str:
    setting = _setting(db, SALES_COMMISSION_PAYOUT_POLICY_KEY)
    if not setting or setting.value not in VALID_SALES_COMMISSION_PAYOUT_POLICIES:
        return DEFAULT_SALES_COMMISSION_PAYOUT_POLICY
    return setting.value


def policy_payload(code: str) -> dict:
    normalized = code if code in VALID_SALES_COMMISSION_PAYOUT_POLICIES else DEFAULT_SALES_COMMISSION_PAYOUT_POLICY
    return {
        'key': SALES_COMMISSION_PAYOUT_POLICY_KEY,
        'policy_code': normalized,
        'policy_label': POLICY_LABELS[normalized],
        'policy_description': POLICY_DESCRIPTIONS[normalized],
        'options': [
            {'policy_code': item, 'policy_label': POLICY_LABELS[item], 'policy_description': POLICY_DESCRIPTIONS[item]}
            for item in [POLICY_RECEIVED_AMOUNT_CAPACITY, POLICY_RECEIVED_RATIO]
        ],
    }


def get_sales_commission_payout_policy(db: Session) -> dict:
    return policy_payload(get_sales_commission_payout_policy_code(db))


def update_sales_commission_payout_policy(db: Session, policy_code: str, actor=None) -> dict:
    if policy_code not in VALID_SALES_COMMISSION_PAYOUT_POLICIES:
        raise HTTPException(400, 'Chính sách chi hoa hồng sale không hợp lệ.')
    setting = _setting(db, SALES_COMMISSION_PAYOUT_POLICY_KEY)
    before = snapshot_model(setting) if setting else None
    if not setting:
        setting = SystemSetting(
            key=SALES_COMMISSION_PAYOUT_POLICY_KEY,
            value=policy_code,
            description='Cấu hình toàn hệ thống cho chính sách chi hoa hồng sale.',
            created_at=now(),
            updated_at=now(),
        )
        db.add(setting)
    else:
        setting.value = policy_code
        setting.updated_at = now()
    db.flush()
    after = snapshot_model(setting)
    create_audit_log(db, actor=actor, action='update_policy', module='commission_payout_policy', entity_type='commission_payout_policy', entity_id=SALES_COMMISSION_PAYOUT_POLICY_KEY, entity_label='Chính sách chi hoa hồng sale', before_data=before, after_data=after, changed_fields=diff_dict(before, after), description='Cập nhật chính sách chi hoa hồng')
    db.commit()
    return policy_payload(policy_code)
