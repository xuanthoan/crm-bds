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
          contract_number: contractNumber || null,
        });
      } else {
        await createContract({
          deal_id: dealId,
          contract_value: Number(contractValue),
          contract_number: contractNumber || null,
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
