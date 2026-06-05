import { useEffect, useState } from 'react';

import { Badge } from '../../../components/Badge';
import { ConfirmDialog } from '../../../components/ConfirmDialog';
import { FormError } from '../../../components/FormError';
import { formatApiError } from '../../../services/apiClient';
import { listRoles, type RoleSummary } from '../roles/api';
import { createUser, deactivateUser, listUsers, resetUserPassword, updateUser, type AdminUser, type UserListMeta } from './api';
import { ResetPasswordModal } from './ResetPasswordModal';
import { UserFormModal } from './UserFormModal';

const statusTone: Record<string, 'green' | 'gray' | 'orange' | 'red'> = {
  active: 'green',
  inactive: 'gray',
  suspended: 'orange',
  resigned: 'red',
};

export function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [meta, setMeta] = useState<UserListMeta>({ page: 1, page_size: 20, total: 0, total_pages: 0 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [resetUser, setResetUser] = useState<AdminUser | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<AdminUser | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function closeAllModals() {
    setIsCreating(false);
    setEditingUser(null);
    setResetUser(null);
    setDeactivateTarget(null);
  }

  function openCreateModal() {
    closeAllModals();
    setIsCreating(true);
  }

  function openEditModal(user: AdminUser) {
    closeAllModals();
    setEditingUser(user);
  }

  function openResetModal(user: AdminUser) {
    closeAllModals();
    setResetUser(user);
  }

  function openDeactivateDialog(user: AdminUser) {
    closeAllModals();
    setDeactivateTarget(user);
  }

  async function loadData(page = 1) {
    setIsLoading(true);
    setError(null);
    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        listUsers({ page, page_size: meta.page_size, search, status: statusFilter, role_code: roleFilter }),
        listRoles(),
      ]);
      setUsers(usersResponse.data);
      setMeta(usersResponse.meta as UserListMeta);
      setRoles(rolesResponse.data);
    } catch (err) {
      setError(formatApiError(err, 'Không thể tải danh sách người dùng.'));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData(1);
  }, []);

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Quản trị hệ thống</p>
          <h1>Quản lý người dùng</h1>
        </div>
        <button type="button" onClick={openCreateModal}>
          Tạo người dùng
        </button>
      </header>
      <div className="filter-panel">
        <input placeholder="Tìm theo tên, email, số điện thoại" value={search} onChange={(event: any) => setSearch(event.target.value)} />
        <select value={statusFilter} onChange={(event: any) => setStatusFilter(event.target.value)}>
          <option value="">Tất cả trạng thái</option>
          <option value="active">active</option>
          <option value="inactive">inactive</option>
          <option value="suspended">suspended</option>
          <option value="resigned">resigned</option>
        </select>
        <select value={roleFilter} onChange={(event: any) => setRoleFilter(event.target.value)}>
          <option value="">Tất cả vai trò</option>
          {roles.map((role) => <option key={role.code} value={role.code}>{role.name}</option>)}
        </select>
        <button type="button" className="secondary-button" onClick={() => void loadData(1)}>Lọc</button>
      </div>
      <FormError messages={error} />
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Full name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Roles</th>
              <th>Created at</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>{user.phone}</td>
                <td><Badge tone={statusTone[user.status] ?? 'gray'}>{user.status}</Badge></td>
                <td>{user.roles.map((role) => <span key={role.code}><Badge tone="blue">{role.code}</Badge></span>)}</td>
                <td>{new Date(user.created_at).toLocaleDateString('vi-VN')}</td>
                <td className="action-cell">
                  <button type="button" className="link-button" onClick={() => openEditModal(user)}>Edit</button>
                  <button type="button" className="link-button" onClick={() => openResetModal(user)}>Reset Password</button>
                  <button type="button" className="link-button danger-link" onClick={() => openDeactivateDialog(user)}>Deactivate</button>
                </td>
              </tr>
            ))}
            {!users.length && (
              <tr>
                <td colSpan={7}>{isLoading ? 'Đang tải…' : 'Không có người dùng.'}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <footer className="pagination-row">
        <span>Trang {meta.page} / {meta.total_pages || 1} · Tổng {meta.total}</span>
        <div>
          <button type="button" className="secondary-button" disabled={meta.page <= 1} onClick={() => void loadData(meta.page - 1)}>Trước</button>
          <button type="button" className="secondary-button" disabled={meta.page >= meta.total_pages} onClick={() => void loadData(meta.page + 1)}>Sau</button>
        </div>
      </footer>
      {isCreating && (
        <UserFormModal
          roles={roles}
          onClose={closeAllModals}
          onSubmit={async (payload) => {
            await createUser(payload);
            closeAllModals();
            await loadData(1);
          }}
        />
      )}
      {editingUser && (
        <UserFormModal
          user={editingUser}
          roles={roles}
          onClose={closeAllModals}
          onSubmit={async (payload) => {
            await updateUser(editingUser.id, payload);
            closeAllModals();
            await loadData(meta.page);
          }}
        />
      )}
      {resetUser && (
        <ResetPasswordModal
          user={resetUser}
          onClose={closeAllModals}
          onSubmit={async (newPassword) => {
            await resetUserPassword(resetUser.id, newPassword);
            closeAllModals();
          }}
        />
      )}
      {deactivateTarget && (
        <ConfirmDialog
          title="Khóa người dùng"
          message="Bạn có chắc muốn khóa người dùng này không?"
          confirmLabel="Khóa"
          onCancel={closeAllModals}
          onConfirm={async () => {
            try {
              await deactivateUser(deactivateTarget.id);
              closeAllModals();
              await loadData(meta.page);
            } catch (err) {
              setError(formatApiError(err, 'Không thể khóa người dùng.'));
              closeAllModals();
            }
          }}
        />
      )}
    </section>
  );
}
