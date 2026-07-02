import { useCallback, useEffect, useState } from 'react';

import { can } from '../auth/authStore';
import { listContracts } from './api';
import { ContractFormModal } from './ContractFormModal';
import { ContractFilters } from './components/ContractFilters';
import { ContractTable } from './components/ContractTable';
import type { Contract } from './types';

export function ContractsPage() {
  const [items, setItems] = useState<Contract[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState<Record<string, number>>({});
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    const response = await listContracts({ ...filters, page: String(page), page_size: '20' });
    setItems(response.data);
    setMeta(response.meta as Record<string, number>);
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
      <ContractTable items={items} />
      <div className="pagination-row">
        <span>Trang {Number(meta.page || page)} / {Number(meta.total_pages || 1)} · Tổng {Number(meta.total || items.length)} hợp đồng</span>
        <div>
          <button className="secondary-button" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>Trang trước</button>
          <button className="secondary-button" disabled={page >= Number(meta.total_pages || 1)} onClick={() => setPage((current) => current + 1)}>Trang sau</button>
        </div>
      </div>
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
