import { useCallback, useEffect, useState } from 'react';

import { navigateTo } from '../../routes/AppRoutes';
import { formatApiError } from '../../services/apiClient';
import { getContract } from './api';
import { ContractActivityForm } from './ContractActivityForm';
import { ContractPaymentModal } from './ContractPaymentModal';
import { ContractStatusModal } from './ContractStatusModal';
import { ContractBadge } from './components/ContractBadge';
import { ContractPaymentTable } from './components/ContractPaymentTable';
import { ContractSummaryCard } from './components/ContractSummaryCard';
import { ContractTimeline } from './components/ContractTimeline';
import type { Contract, ContractPayment } from './types';

const show = (value: unknown) => value || 'Chưa cập nhật';
const date = (value?: string | null) => value ? new Date(value).toLocaleString('vi-VN') : 'Chưa cập nhật';

export function ContractDetailPage({ contractId }: { contractId: string }) {
  const [contract, setContract] = useState<Contract | null>(null);
  const [modal, setModal] = useState<'payment' | 'status' | ContractPayment | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const load = useCallback(async () => {
    try {
      setContract((await getContract(contractId)).data);
      setErrors([]);
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }, [contractId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!contract) return <p>Đang tải hợp đồng...</p>;
  const close = () => {
    setModal(null);
    void load();
  };

  const isCancelled = contract.status === 'cancelled';
  const paymentState = contract.remaining_amount <= 0 ? 'Đã thanh toán đủ' : contract.total_paid > 0 ? 'Thanh toán một phần' : 'Chưa thanh toán';

  return (
    <section className="admin-page contract-detail">
      <header className="detail-hero">
        <div><p>Hợp đồng</p><h1>{contract.contract_code}</h1><ContractBadge status={contract.status} /><p><button className="link-button" onClick={() => navigateTo(`/deals/${contract.deal.id}`)}>Deal {contract.deal.deal_code}</button><br /><span>Khách hàng: {contract.customer.full_name}</span><br /><span>BĐS: {contract.property.property_code}</span><br /><span>Dự án: {contract.project?.name || 'Không thuộc dự án'}</span></p></div>
        <div><button disabled={isCancelled} title={isCancelled ? 'Hợp đồng đã hủy không thể đổi trạng thái.' : undefined} onClick={() => setModal('status')}>Đổi trạng thái</button><button disabled={isCancelled} title={isCancelled ? 'Hợp đồng đã hủy không thể thêm thanh toán.' : undefined} onClick={() => setModal('payment')}>Thêm thanh toán</button></div>
      </header>
      {errors.length > 0 && <div className="form-error">{errors.join('. ')}</div>}
      {isCancelled && <div className="form-warning">Hợp đồng đã hủy. Không thể ký lại hoặc kích hoạt lại. Vui lòng tạo hợp đồng mới nếu cần tiếp tục giao dịch.</div>}
      <section className="detail-card"><h2>Tổng quan</h2><dl className="info-grid"><div><dt>Số hợp đồng</dt><dd>{show(contract.contract_number)}</dd></div><div><dt>Loại hợp đồng</dt><dd>{contract.contract_type_label}</dd></div><div><dt>Giao dịch</dt><dd><button onClick={() => navigateTo(`/deals/${contract.deal.id}`)}>{contract.deal.deal_code}</button></dd></div><div><dt>Booking</dt><dd>{contract.booking ? <button onClick={() => navigateTo(`/bookings/${contract.booking!.id}`)}>{contract.booking.booking_code}</button> : 'Chưa cập nhật'}</dd></div><div><dt>Khách hàng</dt><dd>{contract.customer.full_name}</dd></div><div><dt>Bất động sản</dt><dd>{contract.property.property_code}</dd></div><div><dt>Dự án</dt><dd>{contract.project?.name || 'Chưa cập nhật'}</dd></div></dl></section>
      <ContractSummaryCard contract={contract} paymentState={paymentState} />
      <section className="detail-card"><h2>Thời gian</h2><dl className="info-grid"><div><dt>Ngày ký</dt><dd>{date(contract.signed_date)}</dd></div><div><dt>Ngày hiệu lực</dt><dd>{date(contract.effective_date)}</dd></div><div><dt>Ngày bàn giao</dt><dd>{date(contract.handover_date)}</dd></div></dl></section>
      <section className="detail-card"><h2>Người mua</h2><dl className="info-grid"><div><dt>Tên</dt><dd>{show(contract.buyer_name)}</dd></div><div><dt>SĐT</dt><dd>{show(contract.buyer_phone)}</dd></div><div><dt>Email</dt><dd>{show(contract.buyer_email)}</dd></div><div><dt>CCCD/CMND</dt><dd>{show(contract.buyer_id_number)}</dd></div><div className="full-span"><dt>Địa chỉ</dt><dd>{show(contract.buyer_address)}</dd></div></dl></section>
      <section className="detail-card"><h2>Bên bán</h2><dl className="info-grid"><div><dt>Tên</dt><dd>{show(contract.seller_name)}</dd></div><div><dt>SĐT</dt><dd>{show(contract.seller_phone)}</dd></div><div><dt>Email</dt><dd>{show(contract.seller_email)}</dd></div><div><dt>Đại diện</dt><dd>{show(contract.seller_representative)}</dd></div></dl></section>
      <section className="detail-card"><h2>Thanh toán</h2><ContractPaymentTable items={contract.payments || []} onConfirm={(payment) => setModal(payment)} /></section>
      <section className="detail-card"><h2>Timeline</h2><ContractActivityForm contractId={contract.id} onSaved={load} /><ContractTimeline items={contract.activities || []} /></section>
      {modal === 'payment' && <ContractPaymentModal contractId={contract.id} onClose={() => setModal(null)} onSaved={close} />}
      {modal === 'status' && <ContractStatusModal contract={contract} onClose={() => setModal(null)} onSaved={close} />}
      {typeof modal === 'object' && modal && <ContractPaymentModal contractId={contract.id} payment={modal} onClose={() => setModal(null)} onSaved={close} />}
    </section>
  );
}
