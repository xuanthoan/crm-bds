import { useEffect, useState } from 'react';

import { Badge } from '../../../components/Badge';
import { listPermissions, type PermissionGroup } from '../permissions/api';
import { createRole, getRole, listRoles, updateRole, type RoleDetail, type RoleSummary } from './api';
import { RoleFormModal } from './RoleFormModal';

export function RolesPage() {
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [permissionGroups, setPermissionGroups] = useState<PermissionGroup[]>([]);
  const [editingRole, setEditingRole] = useState<RoleDetail | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [rolesResponse, permissionsResponse] = await Promise.all([listRoles(), listPermissions()]);
      setRoles(rolesResponse.data);
      setPermissionGroups(permissionsResponse.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải dữ liệu vai trò.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function openEdit(roleId: string) {
    const response = await getRole(roleId);
    setEditingRole(response.data);
  }

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Quản trị hệ thống</p>
          <h1>Quản lý vai trò</h1>
        </div>
        <button type="button" onClick={() => setIsCreating(true)}>
          Tạo vai trò
        </button>
      </header>
      {error && <div className="form-error">{error}</div>}
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Role name</th>
              <th>Code</th>
              <th>Description</th>
              <th>System role</th>
              <th>Permission count</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.id}>
                <td>{role.name}</td>
                <td><code>{role.code}</code></td>
                <td>{role.description}</td>
                <td>{role.is_system ? <Badge tone="blue">System</Badge> : <Badge>Custom</Badge>}</td>
                <td>{role.permission_count}</td>
                <td>
                  <button type="button" className="link-button" onClick={() => void openEdit(role.id)}>
                    View / Edit permissions
                  </button>
                </td>
              </tr>
            ))}
            {!roles.length && (
              <tr>
                <td colSpan={6}>{isLoading ? 'Đang tải…' : 'Không có vai trò.'}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {isCreating && (
        <RoleFormModal
          permissionGroups={permissionGroups}
          onClose={() => setIsCreating(false)}
          onSubmit={async (payload) => {
            await createRole({ name: payload.name, code: payload.code ?? '', description: payload.description, permission_codes: payload.permission_codes });
            setIsCreating(false);
            await loadData();
          }}
        />
      )}
      {editingRole && (
        <RoleFormModal
          role={editingRole}
          permissionGroups={permissionGroups}
          onClose={() => setEditingRole(null)}
          onSubmit={async (payload) => {
            await updateRole(editingRole.id, { name: payload.name, code: payload.code, description: payload.description, permission_codes: payload.permission_codes });
            setEditingRole(null);
            await loadData();
          }}
        />
      )}
    </section>
  );
}
