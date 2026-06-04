import { useEffect, useMemo, useState } from 'react';

import { listPermissions, type PermissionGroup } from './api';

export function PermissionsPage() {
  const [groups, setGroups] = useState<PermissionGroup[]>([]);
  const [search, setSearch] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listPermissions({ module: moduleFilter, search });
      setGroups(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải danh sách quyền.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  const modules = useMemo(() => Array.from(new Set(groups.map((group) => group.module))).sort(), [groups]);

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Quản trị hệ thống</p>
          <h1>Danh sách quyền</h1>
        </div>
      </header>
      <div className="filter-panel">
        <input placeholder="Tìm quyền" value={search} onChange={(event: any) => setSearch(event.target.value)} />
        <select value={moduleFilter} onChange={(event: any) => setModuleFilter(event.target.value)}>
          <option value="">Tất cả module</option>
          {modules.map((moduleName) => <option key={moduleName} value={moduleName}>{moduleName}</option>)}
        </select>
        <button type="button" className="secondary-button" onClick={() => void loadData()}>Lọc</button>
      </div>
      {error && <div className="form-error">{error}</div>}
      <div className="permission-list">
        {groups.map((group) => (
          <section className="permission-group-card" key={group.module}>
            <h2>{group.module}</h2>
            <div className="permission-code-list">
              {group.permissions.map((permission) => (
                <article key={permission.code}>
                  <code>{permission.code}</code>
                  <span>{permission.name}</span>
                  {permission.description && <small>{permission.description}</small>}
                </article>
              ))}
            </div>
          </section>
        ))}
        {!groups.length && <div className="page-card">{isLoading ? 'Đang tải…' : 'Không có quyền phù hợp.'}</div>}
      </div>
    </section>
  );
}
