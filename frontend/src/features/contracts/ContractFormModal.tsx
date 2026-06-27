import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import { getDeal, listDeals } from '../deals/api';
import type { Deal } from '../deals/types';
import { createContract, updateContract } from './api';
import type { Contract } from './types';

type ContractFormModalProps = {
  contract?: Contract;
  initialDeal?: Deal;
  lockDeal?: boolean;
  onClose: () => void;
  onSaved: () => void;
};

const displayValue = (value: string | null | undefined) => value || 'Chưa cập nhật';

export function ContractFormModal({
  contract,
  initialDeal,
  lockDeal = false,
  onClose,
  onSaved,
}: ContractFormModalProps) {
  const isEditing = Boolean(contract);
  const dealIsLocked = isEditing || lockDeal;
  const initialDealId = initialDeal?.id ?? contract?.deal_id ?? '';
  const [dealId, setDealId] = useState(initialDealId);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(initialDeal ?? null);
  const [deals, setDeals] = useState<Deal[]>(initialDeal ? [initialDeal] : []);
  const [contractValue, setContractValue] = useState(String(contract?.contract_value ?? ''));
  const [contractNumber, setContractNumber] = useState(contract?.contract_number ?? '');
  const [companyRole, setCompanyRole] = useState(contract?.company_role ?? 'broker');
  const [actualSellerType, setActualSellerType] = useState(contract?.actual_seller_type ?? '');
  const [actualSellerName, setActualSellerName] = useState(contract?.actual_seller_name ?? '');
  const [commissionPayerType, setCommissionPayerType] = useState(contract?.commission_payer_type ?? '');
  const [commissionPayerName, setCommissionPayerName] = useState(contract?.commission_payer_name ?? '');
  const [brokerageContractCode, setBrokerageContractCode] = useState(contract?.brokerage_contract_code ?? '');
  const [brokeragePolicyNote, setBrokeragePolicyNote] = useState(contract?.brokerage_policy_note ?? '');
  const [errors, setErrors] = useState<string[]>([]);
  const [loadingDeals, setLoadingDeals] = useState(!initialDeal && !isEditing);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialDeal || isEditing) return;
    let active = true;
    setLoadingDeals(true);
    listDeals({ page_size: 100 })
      .then((response) => {
        if (active) setDeals(response.data);
      })
      .catch((error) => {
        if (active) setErrors(formatApiError(error));
      })
      .finally(() => {
        if (active) setLoadingDeals(false);
      });
    return () => {
      active = false;
    };
  }, [initialDeal, isEditing]);

  useEffect(() => {
    if (!dealId) {
      setSelectedDeal(null);
      return;
    }
    if (initialDeal?.id === dealId) {
      setSelectedDeal(initialDeal);
      return;
    }
    let active = true;
    getDeal(dealId)
      .then((response) => {
        if (!active) return;
        setSelectedDeal(response.data);
        setDeals((current) => [response.data, ...current.filter((deal) => deal.id !== response.data.id)]);
        setContractValue((current) =>
          current || String(response.data.contract_value ?? response.data.expected_value ?? ''),
        );
      })
      .catch((error) => {
        if (active) setErrors(formatApiError(error));
      });
    return () => {
      active = false;
    };
  }, [dealId, initialDeal]);

  useEffect(() => {
    if (!initialDeal || contractValue) return;
    setContractValue(String(initialDeal.contract_value ?? initialDeal.expected_value ?? ''));
  }, [contractValue, initialDeal]);

  const dealOptions = useMemo(() => {
    if (!initialDeal || deals.some((deal) => deal.id === initialDeal.id)) return deals;
    return [initialDeal, ...deals];
  }, [deals, initialDeal]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setErrors([]);
    setSaving(true);
    try {
      if (contract) {
        await updateContract(contract.id, {
          contract_value: Number(contractValue),
          contract_number: contractNumber || null, company_role: companyRole, actual_seller_type: actualSellerType || null, actual_seller_name: actualSellerName || null, commission_payer_type: commissionPayerType || null, commission_payer_name: commissionPayerName || null, brokerage_contract_code: brokerageContractCode || null, brokerage_policy_note: brokeragePolicyNote || null,
        });
      } else {
        await createContract({
          deal_id: dealId,
          contract_value: Number(contractValue),
          contract_number: contractNumber || null, company_role: companyRole, actual_seller_type: actualSellerType || null, actual_seller_name: actualSellerName || null, commission_payer_type: commissionPayerType || null, commission_payer_name: commissionPayerName || null, brokerage_contract_code: brokerageContractCode || null, brokerage_policy_note: brokeragePolicyNote || null,
        });
      }
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={contract ? 'Sửa hợp đồng' : 'Tạo hợp đồng'} onClose={onClose}>
      <form className="admin-form contract-form" onSubmit={submit}>
        <div className="contract-form-grid">
          <label className="contract-form-deal-field">
            Giao dịch
            <select
              required
              value={dealId}
              disabled={dealIsLocked || loadingDeals}
              aria-label="Giao dịch"
              onChange={(event) => {
                setDealId(event.target.value);
                setContractValue('');
                setErrors([]);
              }}
            >
              <option value="">{loadingDeals ? 'Đang tải giao dịch...' : 'Chọn giao dịch'}</option>
              {dealOptions.map((deal) => (
                <option key={deal.id} value={deal.id}>
                  {deal.deal_code} — {deal.title}
                </option>
              ))}
            </select>
            {dealIsLocked && <input type="hidden" name="deal_id" value={dealId} />}
            {lockDeal && <small>Giao dịch được khóa theo trang chi tiết đang mở.</small>}
          </label>

          <label>
            Giá trị hợp đồng
            <input
              required
              type="number"
              min="1"
              value={contractValue}
              onChange={(event) => setContractValue(event.target.value)}
            />
          </label>

          <label>
            Số hợp đồng
            <input
              value={contractNumber}
              onChange={(event) => setContractNumber(event.target.value)}
              placeholder="Nhập số hợp đồng"
            />
          </label>
        </div>

        <section className="contract-deal-prefill" aria-live="polite">
          <h3>Thông tin từ giao dịch</h3>
          {selectedDeal ? (
            <dl>
              <div>
                <dt>Giao dịch</dt>
                <dd>{selectedDeal.deal_code}</dd>
              </div>
              <div>
                <dt>Khách hàng</dt>
                <dd>{selectedDeal.customer.full_name}</dd>
              </div>
              <div>
                <dt>Bất động sản</dt>
                <dd>{displayValue(selectedDeal.property?.property_code ?? selectedDeal.property_code)}</dd>
              </div>
              <div>
                <dt>Dự án</dt>
                <dd>{displayValue(selectedDeal.project?.name ?? selectedDeal.project_name)}</dd>
              </div>
            </dl>
          ) : (
            <p>Chọn giao dịch để tự động điền khách hàng, bất động sản và dự án.</p>
          )}
        </section>


        <section className="contract-deal-prefill">
          <h3>Thông tin môi giới / bên bán / bên trả hoa hồng</h3>
          <div className="contract-form-grid">
            <label>Vai trò công ty<select value={companyRole} onChange={(event) => setCompanyRole(event.target.value)}><option value="broker">Môi giới</option><option value="distribution_agent">Đại lý phân phối</option><option value="authorized_representative">Đại diện theo ủy quyền</option><option value="direct_seller">Bên bán trực tiếp</option></select></label>
            <label>Bên bán thực tế<select value={actualSellerType} onChange={(event) => setActualSellerType(event.target.value)}><option value="">Chưa cập nhật</option><option value="investor">Chủ đầu tư</option><option value="landowner">Chủ đất</option><option value="homeowner">Chủ nhà</option><option value="our_company">Công ty tôi</option><option value="other">Khác</option></select></label>
            <label>Tên bên bán<input value={actualSellerName} onChange={(event) => setActualSellerName(event.target.value)} placeholder="Công ty CP Đầu tư ABC" /></label>
            <label>Bên trả hoa hồng<select value={commissionPayerType} onChange={(event) => setCommissionPayerType(event.target.value)}><option value="">Chưa cập nhật</option><option value="investor">Chủ đầu tư</option><option value="landowner">Chủ đất</option><option value="homeowner">Chủ nhà</option><option value="distribution_partner">Đối tác phân phối</option><option value="customer">Khách hàng</option><option value="our_company">Công ty tôi</option><option value="other">Khác</option></select></label>
            <label>Tên bên trả hoa hồng<input value={commissionPayerName} onChange={(event) => setCommissionPayerName(event.target.value)} placeholder="Chủ đầu tư Anzen" /></label>
            <label>Mã hợp đồng/chính sách môi giới<input value={brokerageContractCode} onChange={(event) => setBrokerageContractCode(event.target.value)} placeholder="MG-2026-0001" /></label>
          </div>
          <label>Ghi chú căn cứ hoa hồng<textarea value={brokeragePolicyNote} onChange={(event) => setBrokeragePolicyNote(event.target.value)} placeholder="Theo chính sách bán hàng dự án tháng 06/2026" /></label>
        </section>

        <FormError messages={errors} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>
            Hủy
          </button>
          <button disabled={saving || !dealId}>{saving ? 'Đang lưu...' : 'Lưu'}</button>
        </footer>
      </form>
    </Modal>
  );
}
