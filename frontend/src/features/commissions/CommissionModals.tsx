import { useEffect, useState } from 'react';
import { Modal } from '../../components/Modal';
import { searchEligibleContracts, type Commission, type EligibleContract } from './api';

const money = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(v || 0);
const moneyInputValue = (value: number | undefined | null) => String(Math.round(Number(value || 0)));
const moneyLimit = (value: number | undefined | null) => Math.round(Number(value || 0));
const CONTRACT_STATUS_LABELS: Record<string, string> = { draft: 'Bản nháp', pending_signature: 'Chờ ký', signed: 'Đã ký', active: 'Có hiệu lực', completed: 'Hoàn tất', cancelled: 'Đã hủy' };
const percent = (v: number | undefined | null) => `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format((Number(v || 0)) * 100)}%`;
const POLICY_LABELS: Record<string,string> = { received_amount_capacity: 'Chi theo hạn mức tiền hoa hồng công ty đã nhận', received_ratio: 'Chi theo tỷ lệ hoa hồng công ty đã thu' };
const policyMax = (commission: Commission, code: string, approvedAmount: number, remainingSalePayout: number) => { const received = moneyLimit(commission.payout_policy?.company_commission_received_amount ?? commission.company_commission_received_amount ?? 0); const confirmed = moneyLimit(commission.payout_policy?.company_commission_confirmed_receivable_amount ?? commission.company_commission_confirmed_receivable_amount ?? 0); const paid = moneyLimit(commission.paid_amount); if (code === 'received_ratio') { if (confirmed <= 0) return 0; return Math.max(Math.min(remainingSalePayout, Math.round(approvedAmount * received / confirmed) - paid), 0); } return Math.max(Math.min(remainingSalePayout, received - paid), 0); };
const contractStatusLabel = (status?: string) => status ? (CONTRACT_STATUS_LABELS[status] || status) : 'Chưa cập nhật';

export function GuideModal({ onClose }: { onClose: () => void }) {
  return (
    <Modal title="Hướng dẫn sử dụng Quản lý hoa hồng" onClose={onClose}>
      <div className="commission-guide-body">
        <section>
          <h3>Mục đích màn hình</h3>
          <p>Trang này dùng để tạo, duyệt, tạm giữ, hủy và đánh dấu đã chi trả hoa hồng cho sale dựa trên hợp đồng đã đủ điều kiện.</p>
        </section>
        <section>
          <h3>Khi nào tạo được hoa hồng?</h3>
          <ul>
            <li>Hợp đồng không bị hủy.</li>
            <li>Hợp đồng đã hoàn tất hoặc đã thu đủ tiền.</li>
            <li>Tiền đã thu = tiền cọc + phiếu thu đã xác nhận.</li>
            <li>Phiếu thu đã hủy không được tính.</li>
            <li>Hóa đơn không quyết định hoa hồng.</li>
          </ul>
        </section>
        <section>
          <h3>Ý nghĩa trạng thái</h3>
          <ul>
            <li><b>Tạm tính:</b> bản ghi mới/tạm.</li>
            <li><b>Đủ điều kiện:</b> hợp đồng đủ điều kiện để duyệt hoa hồng.</li>
            <li><b>Đã duyệt:</b> quản lý/sếp đã duyệt số tiền hoa hồng.</li>
            <li><b>Đã chi một phần:</b> kế toán đã đánh dấu chi trả một phần hoa hồng.</li>
            <li><b>Đã chi trả:</b> kế toán đã đánh dấu đã chi trả đủ.</li>
            <li><b>Tạm giữ:</b> hoa hồng đang bị giữ lại để kiểm tra.</li>
            <li><b>Đã hủy:</b> hoa hồng bị hủy, cần lý do.</li>
          </ul>
        </section>
        <section>
          <h3>Ý nghĩa số tiền</h3>
          <ul>
            <li>Hoa hồng đủ điều kiện = giá trị hợp đồng × tỷ lệ hoa hồng.</li>
            <li>Hoa hồng đã duyệt = số tiền được duyệt chi.</li>
            <li>Đã chi trả = số tiền đã đánh dấu thanh toán.</li>
            <li>Tỷ lệ hoa hồng được snapshot tại thời điểm tạo.</li>
          </ul>
        </section>
        <section>
          <h3>Lưu ý nghiệp vụ</h3>
          <ul>
            <li>Đây chưa phải bảng lương.</li>
            <li>Chưa có phiếu chi kế toán trong Sprint 20.</li>
            <li>Không chia hoa hồng nhiều người trong Sprint 20.</li>
            <li>Hoa hồng đã chi trả không được hủy.</li><li>Hoa hồng sale chỉ được chi trong phạm vi hoa hồng công ty đã nhận.</li>
            <li>Nếu dữ liệu phiếu thu thay đổi sau khi đã duyệt, Sprint 20 chưa tự tạo điều chỉnh.</li>
          </ul>
        </section>
      </div>
      <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button></footer>
    </Modal>
  );
}

export function GenerateModal({ onClose, onSubmit }: { onClose: () => void; onSubmit: (p: Record<string, unknown>) => Promise<void> }) {
  const [query, setQuery] = useState('');
  const [contracts, setContracts] = useState<EligibleContract[]>([]);
  const [selected, setSelected] = useState<EligibleContract | null>(null);
  const [rate, setRate] = useState('1');
  const [note, setNote] = useState('');
  const [err, setErr] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  async function doSearch(term = query) {
    setErr('');
    setIsSearching(true);
    try {
      const res = await searchEligibleContracts(term);
      setContracts(res.data.items);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Không tìm được hợp đồng.');
    } finally {
      setIsSearching(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => { if (query.trim().length >= 2) void doSearch(query); }, 350);
    return () => clearTimeout(timer);
  }, [query]);

  async function submit() {
    if (isSubmitting) return;
    if (!selected) return setErr('Vui lòng chọn hợp đồng đủ điều kiện.');
    if (!selected.is_eligible_for_commission) return setErr(selected.reason || 'Hợp đồng chưa đủ điều kiện tạo hoa hồng.');
    const r = Number(rate);
    if (Number.isNaN(r) || r < 0 || r > 100) return setErr('Tỷ lệ hoa hồng phải từ 0 đến 100%.');
    try {
      setIsSubmitting(true);
      await onSubmit({ contract_id: selected.contract_id, commission_rate_percent: r, note });
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Không tạo được hoa hồng.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Tạo hoa hồng từ hợp đồng" onClose={onClose}>
      <div className="commission-modal-form">
        {err && <div className="form-error">{err}</div>}
        <label className="full-span">Tìm hợp đồng
          <div className="commission-search-row">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nhập mã hợp đồng, tên khách hàng hoặc số điện thoại" />
            <button type="button" disabled={isSearching} onClick={() => void doSearch()}>{isSearching ? 'Đang tìm...' : 'Tìm'}</button>
          </div>
        </label>
        <div className="commission-contract-results full-span">
          {contracts.length ? contracts.map((c) => (
            <button
              type="button"
              key={c.contract_id}
              disabled={!c.is_eligible_for_commission}
              className={`commission-contract-option ${selected?.contract_id === c.contract_id ? 'selected' : ''}`}
              onClick={() => setSelected(c)}
            >
              <span><b>{c.contract_code}</b> — Khách hàng: {c.customer_name || 'Chưa cập nhật'} {c.customer_phone ? `(${c.customer_phone})` : ''} — Giá trị: {money(c.contract_value)} — Trạng thái: {contractStatusLabel(c.contract_status)}</span>
              <small>Đã thu: {money(c.total_collected_with_deposit)} · Còn lại: {money(c.remaining_amount)}</small>
              {!c.is_eligible_for_commission && <em>{c.reason}</em>}
            </button>
          )) : <p className="empty-state">Nhập từ khóa để tìm hợp đồng.</p>}
        </div>
        {selected && <div className="form-success full-span">Đã chọn {selected.contract_code} — hệ thống sẽ dùng UUID nội bộ khi tạo hoa hồng.</div>}
        <label>Tỷ lệ hoa hồng (%)<input type="number" min="0" max="100" step="0.01" value={rate} onChange={(e) => setRate(e.target.value)} /></label>
        <label className="full-span">Ghi chú<textarea value={note} onChange={(e) => setNote(e.target.value)} /></label>
      </div>
      <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button type="button" disabled={isSubmitting} onClick={submit}>{isSubmitting ? 'Đang tạo...' : 'Tạo hoa hồng'}</button></footer>
    </Modal>
  );
}

export function ActionModal({ type, commission, onClose, onSubmit }: { type: 'approve' | 'hold' | 'cancel' | 'paid'; commission: Commission; onClose: () => void; onSubmit: (p: Record<string, unknown>) => Promise<void> }) {
  const titles = { approve: 'Duyệt hoa hồng', hold: 'Tạm giữ hoa hồng', cancel: 'Hủy hoa hồng', paid: 'Lập phiếu chi hoa hồng sale' };
  const approveMaxAmount = moneyLimit(commission.eligible_commission);
  const remainingSalePayout = Math.max(moneyLimit(commission.approved_commission) - moneyLimit(commission.paid_amount), 0);
  const markPaidDefaultAmount = Math.min(remainingSalePayout, moneyLimit(commission.payout_policy?.remaining_payable_capacity ?? commission.remaining_payable_capacity ?? remainingSalePayout));
  const [amount, setAmount] = useState(type === 'approve' ? moneyInputValue(approveMaxAmount) : moneyInputValue(markPaidDefaultAmount));
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');
  const [err, setErr] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('');
  const defaultPolicyLabel = commission.payout_policy?.payout_policy_label || commission.payout_policy_label || 'Chi theo hạn mức tiền hoa hồng công ty đã nhận';
  const defaultPolicySourceLabel = commission.payout_policy?.payout_policy_source_label || commission.payout_policy_source_label || 'mặc định hệ thống';
  const salePolicyNote = (commission.payout_policy?.project_sales_commission_policy_note || commission.project_sales_commission_policy_note || '').trim();
  const companyPolicyNote = (commission.payout_policy?.project_company_commission_policy_note || commission.project_company_commission_policy_note || '').trim();
  async function submit() {
    if (isSubmitting) return;
    const p: Record<string, unknown> = { note };
    if (type === 'approve') { if (commission.payout_policy?.can_approve_sales_commission === false) return setErr(commission.payout_policy.approve_block_reason || 'Chưa đủ điều kiện duyệt hoa hồng sale.'); const v = Number(amount); if (v <= 0) return setErr('Số tiền duyệt phải lớn hơn 0.'); if (v > approveMaxAmount) return setErr(`Số tiền duyệt không được vượt ${money(approveMaxAmount)}.`); p.approved_commission = v; if (selectedPolicy) p.payout_policy_code = selectedPolicy; }
    if (type === 'paid') { if (commission.payout_policy?.can_mark_paid_sales_commission === false) return setErr(commission.payout_policy.mark_paid_block_reason || 'Chưa đủ điều kiện chi hoa hồng sale.'); const v = Number(amount); const cap = moneyLimit(commission.payout_policy?.remaining_payable_capacity ?? commission.remaining_payable_capacity ?? remainingSalePayout); if (v <= 0) return setErr('Số tiền chi trả phải lớn hơn 0.'); if (v > remainingSalePayout) return setErr(`Số tiền chi trả không được vượt ${money(remainingSalePayout)} còn lại.`); if (v > cap) return setErr('Số tiền chi hoa hồng sale vượt tối đa có thể chi theo chính sách hiện tại.'); p.paid_amount = v; p.payment_date = (document.getElementById('commission-payment-date') as HTMLInputElement)?.value; p.payment_method = (document.getElementById('commission-payment-method') as HTMLSelectElement)?.value; p.payment_reference = (document.getElementById('commission-payment-reference') as HTMLInputElement)?.value; p.attachment_url = (document.getElementById('commission-attachment-url') as HTMLInputElement)?.value; p.status = (document.getElementById('commission-voucher-status') as HTMLSelectElement)?.value || 'paid'; }
    if (type === 'hold') { if (!reason.trim()) return setErr('Vui lòng nhập lý do tạm giữ.'); p.hold_reason = reason.trim(); }
    if (type === 'cancel') { if (!reason.trim()) return setErr('Vui lòng nhập lý do hủy.'); p.cancel_reason = reason.trim(); }
    try { setIsSubmitting(true); await onSubmit(p); onClose(); } catch (e) { setErr(e instanceof Error ? e.message : 'Không thực hiện được thao tác.'); } finally { setIsSubmitting(false); }
  }
  return (
    <Modal title={titles[type]} onClose={onClose}>
      <div className="commission-action-summary">
        <strong>Bạn đang thao tác hoa hồng:</strong>
        <dl>
          <div><dt>Mã hoa hồng</dt><dd>{commission.commission_code}</dd></div>
          <div><dt>Hợp đồng</dt><dd>{commission.contract_code}</dd></div>
          <div><dt>Sale</dt><dd>{commission.sale_name || 'Chưa gán sale'}</dd></div>
          <div><dt>Khách hàng</dt><dd>{commission.customer_name || 'Chưa cập nhật'}</dd></div>
          <div><dt>Hoa hồng đủ điều kiện</dt><dd>{money(commission.eligible_commission)}</dd></div>
          <div><dt>Trạng thái hiện tại</dt><dd>{commission.status_label}</dd></div>
          {type === 'paid' && <><div><dt>Hoa hồng đã duyệt</dt><dd>{money(commission.approved_commission)}</dd></div><div><dt>Số đã chi trả hiện tại</dt><dd>{money(commission.paid_amount)}</dd></div><div><dt>Còn phải chi sale</dt><dd>{money(remainingSalePayout)}</dd></div></>}
        </dl>
      </div>
      {type === 'cancel' && <div className="form-warning">Hủy hoa hồng cần lý do để đối chiếu. Hoa hồng đã chi trả không được hủy.</div>}
      {(type === 'approve' || type === 'paid') && commission.payout_policy?.warning_message && <div className="form-warning">{commission.payout_policy.warning_message}</div>}
      {type === 'approve' && <div className="form-warning commission-policy-note-block"><div><strong>Chính sách mặc định:</strong><p>{defaultPolicyLabel} ({defaultPolicySourceLabel})</p></div>{salePolicyNote && <div><strong>Chính sách hoa hồng sale:</strong><p>{salePolicyNote}</p></div>}{companyPolicyNote && <div><strong>Chính sách hoa hồng công ty:</strong><p>{companyPolicyNote}</p></div>}</div>}
      {type === 'approve' && commission.payout_policy?.can_approve_sales_commission === false && <div className="form-error">{commission.payout_policy.approve_block_reason}</div>}
      {type === 'paid' && <div className="form-warning">Chính sách chi: {commission.payout_policy?.payout_policy_label || commission.payout_policy_label || 'Chi theo hạn mức tiền hoa hồng công ty đã nhận'} · HH sale đã duyệt: {money(commission.approved_commission)} · HH công ty xác nhận: {money(commission.payout_policy?.company_commission_confirmed_receivable_amount || commission.company_commission_confirmed_receivable_amount || 0)} · Hoa hồng công ty đã nhận: {money(commission.payout_policy?.company_commission_received_amount || commission.company_commission_received_amount || 0)}{(commission.payout_policy?.payout_policy_code || commission.payout_policy_code) === 'received_ratio' ? ` · Tỷ lệ đã thu: ${percent(commission.payout_policy?.company_commission_received_ratio ?? commission.company_commission_received_ratio)}` : ''} · Tối đa có thể chi lần này: {money(markPaidDefaultAmount)}</div>}
      {type === 'paid' && commission.payout_policy?.can_mark_paid_sales_commission === false && <div className="form-error">{commission.payout_policy.mark_paid_block_reason}</div>}
      <div className="commission-modal-form">
        {err && <div className="form-error full-span">{err}</div>}
        {type === 'approve' && <label className="full-span">Chính sách chi hoa hồng sale áp dụng<select value={selectedPolicy} onChange={(e) => setSelectedPolicy(e.target.value)}><option value="">Dùng chính sách mặc định</option><option value="received_amount_capacity">Option 1 — Chi theo hạn mức tiền hoa hồng công ty đã nhận</option><option value="received_ratio">Option 2 — Chi theo tỷ lệ hoa hồng công ty đã thu</option></select><small>Tối đa có thể chi lần này theo lựa chọn hiện tại: {money(policyMax(commission, selectedPolicy || commission.payout_policy?.payout_policy_code || commission.payout_policy_code || 'received_amount_capacity', Number(amount || 0), Math.max(Number(amount || 0) - moneyLimit(commission.paid_amount), 0)))}</small></label>}
        {(type === 'approve' || type === 'paid') && <label className="full-span">{type === 'approve' ? 'Số tiền duyệt *' : 'Số tiền chi *'}<input type="number" aria-label={type === 'approve' ? 'Số tiền duyệt *' : 'Số tiền chi *'} value={amount} onChange={(e) => setAmount(e.target.value)} /></label>}
        {type === 'paid' && <><label>Ngày chi<input id="commission-payment-date" type="date" defaultValue={new Date().toISOString().slice(0,10)} /></label><label>Phương thức chi<select id="commission-payment-method" defaultValue="bank_transfer"><option value="cash">Tiền mặt</option><option value="bank_transfer">Chuyển khoản</option><option value="other">Khác</option></select></label><label className="full-span">Mã giao dịch/chứng từ<input id="commission-payment-reference" /></label><label className="full-span">Attachment URL<input id="commission-attachment-url" /></label><label>Thao tác<select id="commission-voucher-status" defaultValue="paid"><option value="draft">Lưu nháp</option><option value="paid">Xác nhận đã chi</option></select></label></>}
        {(type === 'hold' || type === 'cancel') && <label className="full-span">{type === 'hold' ? 'Lý do tạm giữ *' : 'Lý do hủy *'}<textarea aria-label={type === 'hold' ? 'Lý do tạm giữ *' : 'Lý do hủy *'} value={reason} onChange={(e) => setReason(e.target.value)} /></label>}
        <label className="full-span">Ghi chú<textarea value={note} onChange={(e) => setNote(e.target.value)} /></label>
      </div>
      <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button><button type="button" disabled={isSubmitting || (type === 'approve' && commission.payout_policy?.can_approve_sales_commission === false) || (type === 'paid' && commission.payout_policy?.can_mark_paid_sales_commission === false)} onClick={submit}>{isSubmitting ? 'Đang xử lý...' : 'Xác nhận'}</button></footer>
    </Modal>
  );
}

// Backward-compatible labels: Đánh dấu đã chi trả; Số tiền đã chi trả *
