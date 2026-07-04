import { useEffect, useState } from 'react';
import { getCommissionPayoutPolicy, updateCommissionPayoutPolicy, type CommissionPayoutPolicyCode, type CommissionPayoutPolicySetting } from './api';
import { HelpTooltip } from '../../components/help/HelpTooltip';
import { tooltipTexts } from '../help/helpContent';

export function CommissionPayoutPolicySettingsPage() {
  const [setting, setSetting] = useState<CommissionPayoutPolicySetting | null>(null);
  const [selected, setSelected] = useState<CommissionPayoutPolicyCode>('received_amount_capacity');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getCommissionPayoutPolicy().then((response) => {
      setSetting(response.data);
      setSelected(response.data.policy_code);
    }).catch((e) => setError(e instanceof Error ? e.message : 'Không tải được cấu hình chính sách chi hoa hồng sale.'));
  }, []);

  async function save() {
    setError('');
    setMessage('');
    try {
      setSaving(true);
      const response = await updateCommissionPayoutPolicy(selected);
      setSetting(response.data);
      setSelected(response.data.policy_code);
      setMessage('Đã lưu chính sách chi hoa hồng sale.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không lưu được chính sách chi hoa hồng sale.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="admin-page commission-policy-settings-page">
      <header className="page-header"><div><h1>Cài đặt chính sách chi hoa hồng sale</h1><p>Cấu hình toàn hệ thống, áp dụng cho tất cả hợp đồng và sale.</p></div></header>
      {error && <div className="form-error">{error}</div>}
      {message && <div className="form-success">{message}</div>}
      <section className="detail-card">
        <h2>Chính sách đang áp dụng</h2>
        <p className="muted-text">Mặc định là “Chi theo hạn mức tiền hoa hồng công ty đã nhận” để giữ nguyên hành vi Sprint 22. <HelpTooltip content={tooltipTexts.systemFallback} /> <HelpTooltip content={tooltipTexts.projectDefault} /> <HelpTooltip content={tooltipTexts.approvalOverride} /></p>
        <div className="commission-policy-option-list">
          {(setting?.options || [
            { policy_code: 'received_amount_capacity' as const, policy_label: 'Chi theo hạn mức tiền hoa hồng công ty đã nhận', policy_description: 'Sale được chi nếu số tiền chi không vượt quá hoa hồng công ty đã thực nhận còn khả dụng.' },
            { policy_code: 'received_ratio' as const, policy_label: 'Chi theo tỷ lệ hoa hồng công ty đã thu', policy_description: 'Sale chỉ được chi theo tỷ lệ công ty đã thu so với hoa hồng công ty xác nhận.' },
          ]).map((option) => (
            <label key={option.policy_code} className="commission-policy-radio-card">
              <input type="radio" value={option.policy_code} checked={selected === option.policy_code} onChange={() => setSelected(option.policy_code)} />
              <span><b>{option.policy_label} <HelpTooltip content={option.policy_code === 'received_amount_capacity' ? tooltipTexts.policyOption1 : tooltipTexts.policyOption2} /></b><small>{option.policy_description}</small></span>
            </label>
          ))}
        </div>
        <footer className="modal-actions commission-modal-footer"><button type="button" disabled={saving} onClick={() => void save()}>{saving ? 'Đang lưu...' : 'Lưu chính sách'}</button></footer>
      </section>
    </div>
  );
}
