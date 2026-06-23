import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { changeDealStage } from './api';
import { PIPELINE_STAGE_LABELS } from './constants';
import type { Deal, DealStage } from './types';
import { DEAL_COMPLETED_CONTRACT_LOCK_MESSAGE, DEAL_CONTRACT_LOCK_MESSAGE, dealStageOptionsForContractLock, hasCompletedContract, hasEffectiveContract } from './workflowGuards';

export function DealStageModal({ deal, onClose, onSaved }: { deal: Deal; onClose: () => void; onSaved: () => void }) {
  const lockedByCompletedContract = hasCompletedContract(deal);
  const lockedByContract = hasEffectiveContract(deal);
  const stageOptions = dealStageOptionsForContractLock(deal, Object.entries(PIPELINE_STAGE_LABELS));
  const [stage, setStage] = useState<DealStage>(stageOptions.some(([value]) => value === deal.pipeline_stage) ? deal.pipeline_stage : stageOptions[0][0] as DealStage);
  const [note, setNote] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState('');
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  async function submit(e: any) {
    e.preventDefault();
    if (stage === 'lost' && lockedByContract) { setErrors([DEAL_CONTRACT_LOCK_MESSAGE]); return; }
    if (stage === 'lost' && !reason.trim()) { setErrors(['Vui lòng nhập lý do thất bại/hủy giao dịch']); return; }
    try {
      await changeDealStage(deal.id, { pipeline_stage: stage, note: note.trim() || null, deposit_amount: stage === 'deposit' && amount ? Number(amount) : null, deposit_date: stage === 'deposit' && date ? new Date(date).toISOString() : null, contract_value: stage === 'contract' && amount ? Number(amount) : null, contract_date: stage === 'contract' && date ? new Date(date).toISOString() : null, lost_reason: stage === 'lost' ? reason : null });
      onSaved();
    } catch (err) { setErrors(formatApiError(err)); }
  }
  return <Modal title="Đổi giai đoạn" onClose={onClose}><form onSubmit={submit}><FormError messages={errors}/>{lockedByCompletedContract && <div className="form-warning">{DEAL_COMPLETED_CONTRACT_LOCK_MESSAGE}</div>}{!lockedByCompletedContract && lockedByContract && <div className="form-warning">{DEAL_CONTRACT_LOCK_MESSAGE}</div>}<div className="form-grid"><label>Giai đoạn<select value={stage} onChange={e=>setStage(e.target.value as DealStage)}>{stageOptions.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label><div className="workflow-hint-box full-span"><strong>Gợi ý sử dụng</strong><ul><li><b>Ký hợp đồng:</b> Giao dịch đã đủ điều kiện tạo/chuẩn bị hợp đồng.</li><li><b>Đã ký hợp đồng:</b> Hợp đồng đã được ký.</li><li><b>Hoàn tất:</b> Giao dịch đã hoàn thành/chốt thành công.</li><li><b>Thất bại/Hủy:</b> Giao dịch không tiếp tục.</li><li><b>Lưu ý:</b> Nếu giao dịch có hợp đồng hiệu lực, không được chuyển về thất bại/hủy; nếu hợp đồng hoàn tất, giao dịch nên giữ ở Hoàn tất.</li></ul></div>{(stage==='deposit'||stage==='contract')&&<><label>{stage==='deposit'?'Tiền đặt cọc':'Giá trị hợp đồng'}<input type="number" min="0" value={amount} onChange={e=>setAmount(e.target.value)}/></label><label>Ngày ghi nhận<input type="datetime-local" value={date} onChange={e=>setDate(e.target.value)}/></label></>}{stage==='lost'&&<label className="full-span">Lý do thất bại / hủy *<textarea required value={reason} onChange={e=>setReason(e.target.value)}/></label>}<label className="full-span">Ghi chú<textarea value={note} onChange={e=>setNote(e.target.value)}/></label></div><footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button>Lưu</button></footer></form></Modal>;
}
