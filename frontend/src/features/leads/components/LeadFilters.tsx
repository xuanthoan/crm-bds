import type { AdminUser } from '../../admin/users/api';
import { PRIORITY_LABELS, SOURCE_LABELS, STATUS_LABELS } from '../constants';
import type { LeadFilters as Filters } from '../api';

export function LeadFilters({ filters, owners, onChange, onSearch }: { filters: Filters; owners: AdminUser[]; onChange: (filters: Filters) => void; onSearch: () => void }) {
  return <div className="filter-panel lead-filters">
    <input aria-label="Tìm kiếm lead" placeholder="Tên, số điện thoại, mã lead, email" value={filters.search ?? ''} onChange={(e: any) => onChange({ ...filters, search: e.target.value })} onKeyDown={(e: any) => e.key === 'Enter' && onSearch()} />
    <select value={filters.status ?? ''} onChange={(e: any) => onChange({ ...filters, status: e.target.value })}><option value="">Tất cả trạng thái</option>{Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
    <select value={filters.priority ?? ''} onChange={(e: any) => onChange({ ...filters, priority: e.target.value })}><option value="">Tất cả ưu tiên</option>{Object.entries(PRIORITY_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
    <select value={filters.source ?? ''} onChange={(e: any) => onChange({ ...filters, source: e.target.value })}><option value="">Tất cả nguồn</option>{Object.entries(SOURCE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
    {owners.length > 0 && <select value={filters.owner_id ?? ''} onChange={(e: any) => onChange({ ...filters, owner_id: e.target.value })}><option value="">Tất cả phụ trách</option>{owners.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select>}
    <button type="button" onClick={onSearch}>Tìm kiếm</button>
  </div>;
}
