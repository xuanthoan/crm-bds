import { FormEvent, useState } from 'react';

import { FormError } from '../../../components/FormError';
import { Modal } from '../../../components/Modal';
import { formatApiError } from '../../../services/apiClient';
import type { PermissionGroup } from '../permissions/api';
import type { RoleDetail } from './api';
import { PermissionPicker } from './PermissionPicker';

type RoleFormModalProps = {
  role?: RoleDetail | null;
  permissionGroups: PermissionGroup[];
  onClose: () => void;
  onSubmit: (payload: { name: string; code?: string; description: string; permission_codes: string[] }) => Promise<void>;
};

export function RoleFormModal({ role, permissionGroups, onClose, onSubmit }: RoleFormModalProps) {
  const isEdit = Boolean(role);
  const [name, setName] = useState(role?.name ?? '');
  const [code, setCode] = useState(role?.code ?? '');
  const [description, setDescription] = useState(role?.description ?? '');
  const [permissionCodes, setPermissionCodes] = useState<string[]>(role?.permission_codes ?? []);
  const [error, setError] = useState<string[] | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) return setError(['Tên vai trò là bắt buộc.']);
    if (!isEdit && !code.trim()) return setError(['Code là bắt buộc.']);
    if (code && !/^[a-z][a-z0-9_]*$/.test(code)) return setError(['Code phải là lowercase snake_case.']);
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({ name, code, description, permission_codes: permissionCodes });
    } catch (err) {
      setError(formatApiError(err, 'Không thể lưu vai trò.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={isEdit ? 'Cập nhật vai trò' : 'Tạo vai trò'} onClose={onClose}>
      <form className="admin-form" onSubmit={handleSubmit}>
        <label>
          Tên vai trò
          <input value={name} onChange={(event: any) => setName(event.target.value)} required />
        </label>
        <label>
          Code
          <input value={code} onChange={(event: any) => setCode(event.target.value)} disabled={role?.is_system} required={!isEdit} />
        </label>
        <label>
          Mô tả
          <textarea value={description} onChange={(event: any) => setDescription(event.target.value)} rows={3} />
        </label>
        <PermissionPicker groups={permissionGroups} selectedCodes={permissionCodes} onChange={setPermissionCodes} />
        <FormError messages={error} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>
            Hủy
          </button>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Đang lưu…' : 'Lưu'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
