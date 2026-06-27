import { useEffect, useState } from 'react';
import { Modal } from '../../components/Modal';
import { searchEligibleContracts, type Commission, type EligibleContract } from './api';

const money = (v: number) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(v || 0);

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
            <li><b>Đã chi trả:</b> kế toán đã đánh dấu đã chi trả.</li>
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
            <li>Hoa hồng đã chi trả không được hủy.</li>
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

  async function doSearch(term = query) {
    setErr('');
    try {
      const res = await searchEligibleContracts(term);
      setContracts(res.data.items);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Không tìm được hợp đồng.');
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => { if (query.trim().length >= 2) void doSearch(query); }, 350);
    return () => clearTimeout(timer);
  }, [query]);

  async function submit() {
    if (!selected) return setErr('Vui lòng chọn hợp đồng đủ điều kiện.');
    if (!selected.is_eligible_for_commission) return setErr(selected.reason || 'Hợp đồng chưa đủ điều kiện tạo hoa hồng.');
    const r = Number(rate);
    if (Number.isNaN(r) || r < 0 || r > 100) return setErr('Tỷ lệ hoa hồng phải từ 0 đến 100%.');
    try {
      await onSubmit({ contract_id: selected.contract_id, commission_rate_percent: r, note });
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Không tạo được hoa hồng.');
    }
  }

  return (
    <Modal title="Tạo hoa hồng từ hợp đồng" onClose={onClose}>
      <div className="commission-modal-form">
        {err && <div className="form-error">{err}</div>}
        <label className="full-span">Tìm hợp đồng
          <div className="commission-search-row">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nhập mã hợp đồng, tên khách hàng hoặc số điện thoại" />
            <button type="button" onClick={() => void doSearch()}>Tìm</button>
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
              <span><b>{c.contract_code}</b> — Khách hàng: {c.customer_name || 'Chưa cập nhật'} {c.customer_phone ? `(${c.customer_phone})` : ''} — Giá trị: {money(c.contract_value)} — Trạng thái: {c.contract_status}</span>
              <small>Đã thu: {money(c.total_collected_with_deposit)} · Còn lại: {money(c.remaining_amount)}</small>
              {!c.is_eligible_for_commission && <em>{c.reason}</em>}
            </button>
          )) : <p className="empty-state">Nhập từ khóa để tìm hợp đồng.</p>}
        </div>
        {selected && <div className="form-success full-span">Đã chọn {selected.contract_code} — hệ thống sẽ dùng UUID nội bộ khi tạo hoa hồng.</div>}
        <label>Tỷ lệ hoa hồng (%)<input type="number" min="0" max="100" step="0.01" value={rate} onChange={(e) => setRate(e.target.value)} /></label>
        <label className="full-span">Ghi chú<textarea value={note} onChange={(e) => setNote(e.target.value)} /></label>
      </div>
      <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button type="button" onClick={submit}>Tạo hoa hồng</button></footer>
    </Modal>
  );
}

export function ActionModal({ type, commission, onClose, onSubmit }: { type: 'approve' | 'hold' | 'cancel' | 'paid'; commission: Commission; onClose: () => void; onSubmit: (p: Record<string, unknown>) => Promise<void> }) {
  const titles = { approve: 'Duyệt hoa hồng', hold: 'Tạm giữ hoa hồng', cancel: 'Hủy hoa hồng', paid: 'Đánh dấu đã chi trả' };
  const [amount, setAmount] = useState(String(type === 'approve' ? commission.eligible_commission : commission.approved_commission));
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');
  const [err, setErr] = useState('');
  async function submit() {
    const p: Record<string, unknown> = { note };
    if (type === 'approve') { const v = Number(amount); if (v < 0 || v > commission.eligible_commission) return setErr(`Số tiền duyệt phải từ 0 đến ${money(commission.eligible_commission)}.`); p.approved_commission = v; }
    if (type === 'paid') { const v = Number(amount); if (v < 0 || v > commission.approved_commission) return setErr(`Số tiền chi trả phải từ 0 đến ${money(commission.approved_commission)}.`); p.paid_amount = v; }
    if (type === 'hold') { if (!reason.trim()) return setErr('Vui lòng nhập lý do tạm giữ.'); p.hold_reason = reason.trim(); }
    if (type === 'cancel') { if (!reason.trim()) return setErr('Vui lòng nhập lý do hủy.'); p.cancel_reason = reason.trim(); }
    try { await onSubmit(p); onClose(); } catch (e) { setErr(e instanceof Error ? e.message : 'Không thực hiện được thao tác.'); }
  }
  return <Modal title={titles[type]} onClose={onClose}><div className="commission-modal-form">{err && <div className="form-error full-span">{err}</div>}{(type === 'approve' || type === 'paid') && <label className="full-span">{type === 'approve' ? 'Số tiền duyệt' : 'Số tiền đã chi trả'}<input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>}{(type === 'hold' || type === 'cancel') && <label className="full-span">{type === 'hold' ? 'Lý do tạm giữ' : 'Lý do hủy'}<textarea value={reason} onChange={(e) => setReason(e.target.value)} /></label>}<label className="full-span">Ghi chú<textarea value={note} onChange={(e) => setNote(e.target.value)} /></label></div><footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={onClose}>Đóng</button><button type="button" onClick={submit}>Xác nhận</button></footer></Modal>;
}
