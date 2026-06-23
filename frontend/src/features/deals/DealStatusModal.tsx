import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { changeDealStatus } from './api';
import { DEAL_STATUS_LABELS } from './constants';
import type { Deal, DealStatus } from './types';
import { DEAL_COMPLETED_CONTRACT_LOCK_MESSAGE, DEAL_CONTRACT_LOCK_MESSAGE, dealStatusOptionsForContractLock, hasCompletedContract, hasEffectiveContract } from './workflowGuards';

export function DealStatusModal({ deal, onClose, onSaved }: { deal: Deal; onClose: () => void; onSaved: () => void }) {
  const lockedByCompletedContract = hasCompletedContract(deal);
  const lockedByContract = hasEffectiveContract(deal);
  const statusOptions = dealStatusOptionsForContractLock(deal, Object.entries(DEAL_STATUS_LABELS));
  const [status, setStatus] = useState<DealStatus>(statusOptions.some(([value]) => value === deal.status) ? deal.status : statusOptions[0][0] as DealStatus);
  const [reason, setReason] = useState(deal.lost_reason || '');
  const [note, setNote] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  async function submit(e: any) {
    e.preventDefault();
    if (['lost','cancelled'].includes(status) && lockedByContract) { setErrors([DEAL_CONTRACT_LOCK_MESSAGE]); return; }
    if (['lost','cancelled'].includes(status) && !reason.trim()) { setErrors(['Vui lòng nhập lý do thất bại/hủy giao dịch']); return; }
    try {
      await changeDealStatus(deal.id, { status, lost_reason: ['lost','cancelled'].includes(status) ? reason : null, note: note || null });
      onSaved();
    } catch (err) { setErrors(formatApiError(err)); }
  }
  return <Modal title="Đổi trạng thái" onClose={onClose}><form onSubmit={submit}><FormError messages={errors}/>{lockedByCompletedContract && <div className="form-warning">{DEAL_COMPLETED_CONTRACT_LOCK_MESSAGE}</div>}{!lockedByCompletedContract && lockedByContract && <div className="form-warning">{DEAL_CONTRACT_LOCK_MESSAGE}</div>}<div className="form-grid"><label>Trạng thái<select value={status} onChange={e=>setStatus(e.target.value as DealStatus)}>{statusOptions.map(([v,l])=><option value={v} key={v}>{l}</option>)}</select></label>{['lost','cancelled'].includes(status)&&<label className="full-span">Lý do thất bại / hủy *<textarea required value={reason} onChange={e=>setReason(e.target.value)}/></label>}<label className="full-span">Ghi chú<textarea value={note} onChange={e=>setNote(e.target.value)}/></label></div><footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button>Lưu</button></footer></form></Modal>;
}
