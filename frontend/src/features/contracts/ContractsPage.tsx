import { useCallback, useEffect, useState } from 'react';
import { useQueryHydratedFilters } from '../../utils/queryHydration';

import { Pagination } from '../../components/common/Pagination';
import { FormError } from '../../components/FormError';
import { formatApiError } from '../../services/apiClient';
import { can } from '../auth/authStore';
import { listContracts } from './api';
import { ContractFormModal } from './ContractFormModal';
import { ContractFilters } from './components/ContractFilters';
import { ContractTable } from './components/ContractTable';
import type { Contract } from './types';

export function ContractsPage() {
  const [items, setItems] = useState<Contract[]>([]);
  const [filters, setFilters] = useQueryHydratedFilters<Record<string, string>>({}, { q: 'string', status: 'string', contract_type: 'string', scope: 'string', date_from: 'string', date_to: 'string' });
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState<Record<string, number>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listContracts({ ...filters, page: String(page), page_size: '20' });
      setItems(Array.isArray(response.data) ? response.data : []);
      setMeta(response.meta as Record<string, number>);
      setErrors([]);
    } catch (error) {
      setItems([]);
      setMeta({ page, total_pages: 1, total: 0 });
      setErrors(formatApiError(error, 'Không thể tải danh sách hợp đồng.'));
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <h1>Hợp đồng</h1>
          <p>Quản lý hợp đồng, thanh toán và trạng thái giao dịch bất động sản.</p>
        </div>
        {can('contracts.create') && <button onClick={() => setShowCreate(true)}>Tạo hợp đồng</button>}
      </header>
      <ContractFilters filters={filters} onChange={(next) => { setPage(1); setFilters(next); }} />
      <FormError messages={errors} />
      {loading && <p>Đang tải...</p>}
      <ContractTable items={items} />
      {!loading && !errors.length && items.length === 0 && <p className="empty-state">Không có dữ liệu phù hợp.</p>}
      <Pagination currentPage={Number(meta.page || page)} totalPages={Number(meta.total_pages || 1)} totalItems={Number(meta.total || items.length)} itemLabel="hợp đồng" loading={loading} onPageChange={setPage} />
      {showCreate && (
        <ContractFormModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            setShowCreate(false);
            void load();
          }}
        />
      )}
    </section>
  );
}
