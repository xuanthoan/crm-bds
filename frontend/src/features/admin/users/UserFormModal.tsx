import { FormEvent, useState } from 'react';

import { FormError } from '../../../components/FormError';
import { Modal } from '../../../components/Modal';
import { formatApiError } from '../../../services/apiClient';
import type { RoleSummary } from '../roles/api';
import type { AdminUser } from './api';

type UserFormModalProps = {
  user?: AdminUser | null;
  roles: RoleSummary[];
  onClose: () => void;
  onSubmit: (payload: { email?: string; full_name: string; phone: string; password?: string; status: string; role_codes: string[] }) => Promise<void>;
};

export function UserFormModal({ user, roles, onClose, onSubmit }: UserFormModalProps) {
  const isEdit = Boolean(user);
  const [email, setEmail] = useState(user?.email ?? '');
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState(user?.status ?? 'active');
  const [roleCodes, setRoleCodes] = useState<string[]>(user?.roles.map((role) => role.code) ?? []);
  const [error, setError] = useState<string[] | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function toggleRole(code: string) {
    setRoleCodes((current) => (current.includes(code) ? current.filter((item) => item !== code) : [...current, code].sort()));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!fullName.trim()) return setError(['Họ tên là bắt buộc.']);
    if (!isEdit && !email.trim()) return setError(['Email là bắt buộc.']);
    if (!isEdit && !password.trim()) return setError(['Mật khẩu là bắt buộc.']);
    if (!roleCodes.length) return setError(['Vui lòng chọn ít nhất một vai trò.']);
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({ email, full_name: fullName, phone, password: isEdit ? undefined : password, status, role_codes: roleCodes });
    } catch (err) {
      setError(formatApiError(err, 'Không thể lưu người dùng.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={isEdit ? 'Cập nhật người dùng' : 'Tạo người dùng'} onClose={onClose}>
      <form className="admin-form" onSubmit={handleSubmit}>
        <label>
          Họ tên
          <input value={fullName} onChange={(event: any) => setFullName(event.target.value)} required />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(event: any) => setEmail(event.target.value)} disabled={isEdit} required />
        </label>
        <label>
          Số điện thoại
          <input value={phone} onChange={(event: any) => setPhone(event.target.value)} />
        </label>
        {!isEdit && (
          <label>
            Mật khẩu
            <input type="password" value={password} onChange={(event: any) => setPassword(event.target.value)} required />
          </label>
        )}
        <label>
          Trạng thái
          <select value={status} onChange={(event: any) => setStatus(event.target.value)}>
            <option value="active">active</option>
            <option value="inactive">inactive</option>
            <option value="suspended">suspended</option>
            <option value="resigned">resigned</option>
          </select>
        </label>
        <fieldset className="role-checkboxes">
          <legend>Vai trò</legend>
          {roles.map((role) => (
            <label key={role.code} className="checkbox-row">
              <input type="checkbox" checked={roleCodes.includes(role.code)} onChange={() => toggleRole(role.code)} />
              <span>{role.name} <code>{role.code}</code></span>
            </label>
          ))}
        </fieldset>
        <FormError messages={error} />
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
          <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Đang lưu…' : 'Lưu'}</button>
        </footer>
      </form>
    </Modal>
  );
}
