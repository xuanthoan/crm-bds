import { useState, type FormEvent } from 'react';
import { Modal } from '../../components/Modal';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { changeContractStatus } from './api';
import { CONTRACT_STATUS_LABELS } from './constants';
import type { Contract } from './types';

export function ContractStatusModal({ contract, onClose, onSaved }: { contract: Contract; onClose: () => void; onSaved: () => void }) {
  const isCancelled = contract.status === 'cancelled';
  const options = Object.entries(CONTRACT_STATUS_LABELS).filter(([value]) => !isCancelled || value === 'cancelled');
  const [status, setStatus] = useState(contract.status);
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setErrors([]);
    if (isCancelled && status !== 'cancelled') {
      setErrors(['Hợp đồng đã hủy không thể kích hoạt hoặc ký lại. Vui lòng tạo hợp đồng mới.']);
      return;
    }
    try {
      await changeContractStatus(contract.id, { status, note: note.trim() || null });
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  return <Modal title="Đổi trạng thái hợp đồng" onClose={onClose}>
    <form className="property-form" onSubmit={submit}>
      <FormError messages={errors} />
      {isCancelled && <div className="form-warning">Hợp đồng đã hủy. Không thể ký lại hoặc kích hoạt lại. Vui lòng tạo hợp đồng mới nếu cần tiếp tục giao dịch.</div>}
      <label>Trạng thái hiện tại<input readOnly value={CONTRACT_STATUS_LABELS[contract.status] || contract.status} /></label>
      <label>Trạng thái mới<select value={status} disabled={isCancelled} onChange={(event) => setStatus(event.target.value)}>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><div className="workflow-hint-box full-span"><strong>Hướng dẫn nhanh</strong><ul><li><b>Bản nháp:</b> Hợp đồng mới tạo, chưa sẵn sàng ký.</li><li><b>Chờ ký:</b> Hợp đồng đang chờ các bên ký.</li><li><b>Đã ký:</b> Hai bên đã ký hợp đồng.</li><li><b>Có hiệu lực:</b> Hợp đồng đã có hiệu lực thực hiện.</li><li><b>Hoàn tất:</b> Hợp đồng đã hoàn thành nghĩa vụ chính/thanh toán.</li><li><b>Đã hủy:</b> Hợp đồng bị hủy; sau khi hủy không được kích hoạt lại.</li><li><b>Lưu ý:</b> Khi hợp đồng hoàn tất, Deal liên quan phải được chốt thành công/hoàn tất.</li></ul></div>
      <label className="full-span">Ghi chú<textarea style={{ minHeight: 100 }} value={note} onChange={(event) => setNote(event.target.value)} /></label>
      <footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button type="submit" disabled={isCancelled}>Lưu trạng thái</button></footer>
    </form>
  </Modal>;
}
