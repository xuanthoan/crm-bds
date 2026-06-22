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
  const [showCreate, setShowCreate] = useState(false);

  const load = useCallback(async () => {
    const response = await listContracts(filters);
    setItems(response.data);
  }, [filters]);

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
      <ContractFilters filters={filters} onChange={setFilters} />
      <ContractTable items={items} />
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
