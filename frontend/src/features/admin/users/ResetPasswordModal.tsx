import { FormEvent, useState } from 'react';

import { Modal } from '../../../components/Modal';
import type { AdminUser } from './api';

type ResetPasswordModalProps = {
  user: AdminUser;
  onClose: () => void;
  onSubmit: (newPassword: string) => Promise<void>;
};

export function ResetPasswordModal({ user, onClose, onSubmit }: ResetPasswordModalProps) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (newPassword.length < 8) return setError('Mật khẩu mới tối thiểu 8 ký tự.');
    if (newPassword !== confirmPassword) return setError('Mật khẩu xác nhận không khớp.');
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit(newPassword);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể đặt lại mật khẩu.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={`Đặt lại mật khẩu: ${user.full_name}`} onClose={onClose}>
      <form className="admin-form" onSubmit={handleSubmit}>
        <label>
          Mật khẩu mới
          <input type="password" value={newPassword} onChange={(event: any) => setNewPassword(event.target.value)} required />
        </label>
        <label>
          Xác nhận mật khẩu mới
          <input type="password" value={confirmPassword} onChange={(event: any) => setConfirmPassword(event.target.value)} required />
        </label>
        {error && <div className="form-error">{error}</div>}
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Hủy</button>
          <button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Đang lưu…' : 'Đặt lại mật khẩu'}</button>
        </footer>
      </form>
    </Modal>
  );
}
