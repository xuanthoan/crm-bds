import { useEffect, useState, type FormEvent } from 'react';

import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import {
  approveCompanyCommission,
  cancelCompanyCommission,
  eligibleCompanyCommissionContracts,
  generateCompanyCommission,
  holdCompanyCommission,
  receiveCompanyCommission,
} from './api';
import { COMPANY_ROLE_LABELS } from './constants';
import type { CompanyCommission, EligibleContract } from './types';

const LEGAL_STATUS_REASON = 'Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng công ty.';
const money = (value: unknown) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value || 0));
const moneyInputValue = (value: unknown) => String(Math.round(Number(value || 0)));
const moneyLimit = (value: unknown) => Math.round(Number(value || 0));
const CONTRACT_STATUS_LABELS: Record<string, string> = { draft: 'Bản nháp', pending_signature: 'Chờ ký', signed: 'Đã ký', active: 'Có hiệu lực', completed: 'Hoàn tất', cancelled: 'Đã hủy' };
const contractStatusLabel = (status?: string) => status ? (CONTRACT_STATUS_LABELS[status] || status) : 'Chưa cập nhật';
const readable = (value?: string | null) => value || 'Chưa cập nhật';

function Context({ item }: { item: CompanyCommission }) {
  return (
    <section className="context-card">
      <strong>Bạn đang thao tác hoa hồng công ty:</strong>
      <p>{item.receivable_code} • HĐ {item.contract_code} • Bên trả hoa hồng {item.commission_payer_name || 'Chưa cập nhật'} • Khách hàng {item.customer_name || 'Chưa cập nhật'}</p>
      <p>HH dự kiến {money(item.expected_commission_amount)} • HH xác nhận {money(item.confirmed_receivable_amount)} • Đã nhận {money(item.received_amount)} • Còn phải thu {money(item.remaining_amount)} • Trạng thái {item.status}</p>
    </section>
  );
}

export function CompanyCommissionGuideModal({ onClose }: { onClose: () => void }) {
  return (
    <Modal title="Hướng dẫn sử dụng Hoa hồng công ty" onClose={onClose}>
      <div className="commission-guide-body">
        <section>
          <h3>Mục đích màn hình</h3>
          <p>Hoa hồng công ty là khoản công ty phải thu từ chủ đầu tư/chủ đất/chủ nhà/đối tác hoặc bên trả hoa hồng khác.</p>
        </section>
        <section>
          <h3>Phân biệt nghiệp vụ</h3>
          <ul>
            <li><b>Hoa hồng công ty:</b> khoản công ty phải thu từ bên trả hoa hồng.</li>
            <li><b>Hoa hồng:</b> khoản công ty chi cho sale nội bộ sau khi phát sinh giao dịch.</li>
          </ul>
        </section>
        <section>
          <h3>Điều kiện tạo</h3>
          <ul>
            <li>Chỉ tạo được từ hợp đồng đã đủ trạng thái pháp lý: Đã ký, Có hiệu lực, Hoàn tất.</li>
            <li>Không tạo được từ hợp đồng Bản nháp, Chờ ký, Đã hủy.</li>
          </ul>
        </section>
        <section>
          <h3>Quy trình</h3>
          <ol>
            <li>Tạo từ hợp đồng.</li>
            <li>Duyệt khoản hoa hồng công ty.</li>
            <li>Ghi nhận đã nhận tiền một phần hoặc nhận đủ.</li>
            <li>Có thể tạm giữ/hủy khi chưa nhận tiền.</li>
          </ol>
        </section>
        <section>
          <h3>Lưu ý</h3>
          <ul>
            <li>Khi đã nhận tiền một phần hoặc nhận đủ thì không được hủy.</li>
            <li>Export CSV dùng để đối chiếu công nợ hoa hồng công ty.</li>
          </ul>
        </section>
      </div>
      <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button></footer>
    </Modal>
  );
}

export function CreateCompanyCommissionModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [keyword, setKeyword] = useState('');
  const [items, setItems] = useState<EligibleContract[]>([]);
  const [selected, setSelected] = useState<EligibleContract | null>(null);
  const [rate, setRate] = useState('2');
  const [date, setDate] = useState('');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function search(term = keyword) {
    setIsSearching(true);
    eligibleCompanyCommissionContracts({ keyword: term, limit: 20 })
      .then((response) => setItems(response.data.items || []))
      .catch((error) => setErrors(formatApiError(error)))
      .finally(() => setIsSearching(false));
  }

  useEffect(() => {
    const timer = setTimeout(() => search(keyword), 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  const expected = Number(selected?.contract_value || 0) * Number(rate || 0) / 100;

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (isSubmitting) return;
    if (!selected?.is_eligible_for_company_commission) return;
    try {
      setIsSubmitting(true);
      await generateCompanyCommission({ contract_id: selected.contract_id, commission_rate_percent: Number(rate), expected_receive_date: date || null, note });
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Tạo hoa hồng công ty từ hợp đồng" onClose={onClose}>
      <form className="admin-form company-commission-create-form" onSubmit={submit}>
        <label className="company-commission-search-label">Tìm hợp đồng
          <div className="commission-search-row">
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="Mã HĐ / khách hàng" />
            <button type="button" disabled={isSearching} onClick={() => search()}>{isSearching ? 'Đang tìm...' : 'Tìm'}</button>
          </div>
        </label>

        <div className="company-commission-contract-results">
          {items.length ? items.map((contract) => {
            const eligible = contract.is_eligible_for_company_commission;
            const selectedContract = selected?.contract_id === contract.contract_id;
            return (
              <button
                type="button"
                className={`company-commission-contract-option ${selectedContract ? 'selected' : ''}`}
                disabled={!eligible}
                key={contract.contract_id}
                onClick={() => setSelected(contract)}
              >
                <span className="company-commission-contract-line company-commission-contract-main">
                  <b>{contract.contract_code}</b>
                  <span>Khách hàng: {readable(contract.customer_name)}</span>
                  <span>Giá trị: {money(contract.contract_value)}</span>
                  <span>Trạng thái: {contractStatusLabel(contract.contract_status)}</span>
                </span>
                <span className="company-commission-contract-line">
                  <span>Sale: {readable(contract.sale_name)}</span>
                  <span>Vai trò công ty: {COMPANY_ROLE_LABELS[contract.company_role] || readable(contract.company_role)}</span>
                  <span>Bên bán: {readable(contract.actual_seller_name || contract.actual_seller_type)}</span>
                  <span>Bên trả HH: {readable(contract.commission_payer_name || contract.commission_payer_type)}</span>
                </span>
                <span className="company-commission-contract-line">Mã hợp đồng/chính sách môi giới: {readable(contract.brokerage_contract_code)}</span>
                {!eligible && <em>Lý do: {contract.reason || LEGAL_STATUS_REASON}</em>}
              </button>
            );
          }) : <p className="empty-state">Nhập từ khóa để tìm hợp đồng.</p>}
        </div>

        {selected && <div className="form-success">Đã chọn {selected.contract_code} — hoa hồng dự kiến được tính theo giá trị hợp đồng và tỷ lệ nhập bên dưới.</div>}

        <div className="company-commission-create-fields">
          <label>Tỷ lệ hoa hồng công ty (%)<input type="number" min="0.01" step="0.01" value={rate} onChange={(event) => setRate(event.target.value)} /></label>
          <label>Hoa hồng dự kiến tự tính<input readOnly value={money(expected)} /></label>
          <label>Ngày dự kiến nhận<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
          <label className="full-span">Ghi chú<textarea value={note} onChange={(event) => setNote(event.target.value)} /></label>
        </div>

        <FormError messages={errors} />
        <footer className="modal-actions company-commission-create-footer"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button disabled={isSubmitting || !selected?.is_eligible_for_company_commission || Number(rate) <= 0}>{isSubmitting ? 'Đang tạo...' : 'Tạo hoa hồng công ty'}</button></footer>
      </form>
    </Modal>
  );
}

export function ActionModal({ item, type, onClose, onSaved }: { item: CompanyCommission; type: 'approve' | 'receive' | 'hold' | 'cancel'; onClose: () => void; onSaved: () => void }) {
  const approveMaxAmount = moneyLimit(item.expected_commission_amount);
  const receiveMaxAmount = moneyLimit(item.remaining_amount);
  const [amount, setAmount] = useState(type === 'approve' ? moneyInputValue(approveMaxAmount) : '');
  const [reason, setReason] = useState('');
  const [date, setDate] = useState('');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (isSubmitting) return;
    setErrors([]);
    const trimmedReason = reason.trim();
    if (type === 'hold' && !trimmedReason) {
      setErrors(['Vui lòng nhập lý do tạm giữ.']);
      return;
    }
    if (type === 'cancel' && !trimmedReason) {
      setErrors(['Vui lòng nhập lý do hủy.']);
      return;
    }
    try {
      setIsSubmitting(true);
      const numericAmount = Number(amount);
      if ((type === 'approve' || type === 'receive') && numericAmount <= 0) { setErrors(['Số tiền phải lớn hơn 0.']); setIsSubmitting(false); return; }
      if (type === 'approve' && numericAmount > approveMaxAmount) { setErrors([`Hoa hồng xác nhận không được vượt ${money(approveMaxAmount)}.`]); setIsSubmitting(false); return; }
      if (type === 'receive' && numericAmount > receiveMaxAmount) { setErrors([`Số tiền nhận lần này không được vượt ${money(receiveMaxAmount)}.`]); setIsSubmitting(false); return; }
      if (type === 'approve') await approveCompanyCommission(item.id, { confirmed_receivable_amount: numericAmount, note });
      if (type === 'receive') await receiveCompanyCommission(item.id, { amount_received_now: numericAmount, received_date: date || null, note });
      if (type === 'hold') await holdCompanyCommission(item.id, { hold_reason: trimmedReason, note });
      if (type === 'cancel') await cancelCompanyCommission(item.id, { cancel_reason: trimmedReason, note });
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const title = { approve: 'Duyệt hoa hồng công ty', receive: 'Ghi nhận đã nhận tiền', hold: 'Tạm giữ hoa hồng công ty', cancel: 'Hủy hoa hồng công ty' }[type];
  return (
    <Modal title={title} onClose={onClose}>
      <form className="admin-form" onSubmit={submit}>
        <Context item={item} />
        {type === 'hold' && <div className="form-warning">Lý do tạm giữ là bắt buộc để đối chiếu.</div>}
        {type === 'cancel' && <div className="form-warning">Hủy hoa hồng cần lý do để đối chiếu. Khoản hoa hồng công ty đã nhận tiền không được hủy.</div>}
        {type === 'approve' && <label>Hoa hồng xác nhận *<input type="number" min="1" aria-label="Hoa hồng xác nhận *" value={amount} onChange={(event) => setAmount(event.target.value)} /></label>}
        {type === 'receive' && <><label>Số tiền nhận lần này *<input type="number" min="1" aria-label="Số tiền nhận lần này *" value={amount} onChange={(event) => setAmount(event.target.value)} /></label><label>Ngày nhận<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label></>}
        {type === 'hold' && <label>Lý do tạm giữ *<input required aria-label={type === 'hold' ? 'Lý do tạm giữ *' : 'Lý do hủy *'} value={reason} onChange={(event) => { setReason(event.target.value); setErrors([]); }} /></label>}
        {type === 'cancel' && <label>Lý do hủy *<input required aria-label={type === 'hold' ? 'Lý do tạm giữ *' : 'Lý do hủy *'} value={reason} onChange={(event) => { setReason(event.target.value); setErrors([]); }} /></label>}
        <label>Ghi chú<textarea value={note} onChange={(event) => setNote(event.target.value)} /></label>
        <FormError messages={errors} />
        <footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button><button disabled={isSubmitting}>{isSubmitting ? 'Đang xử lý...' : title}</button></footer>
      </form>
    </Modal>
  );
}
